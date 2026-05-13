"""Variational GMM Engine — 7-component Gaussian Mixture Model with true ELBO.

Replaces the ad-hoc J[ρ] objective in variational_em_engine.py with a
mathematically rigorous ELBO (Evidence Lower BOund) optimization.

Generative model:
    p(x_i | z_i = k) = N(x_i | μ_k, Σ_k)     k ∈ {p_core, p_band, r_core, r_band, m_band, x_true, u}
    p(z_i = k) = π_k

E-step:
    γ_ik = π_k · N(x_i | μ_k, Σ_k) / Σ_j [π_j · N(x_i | μ_j, Σ_j)]

M-step:
    π_k = Σ_i γ_ik / N
    μ_k = Σ_i γ_ik · x_i / Σ_i γ_ik
    Σ_k = Σ_i γ_ik · (x_i - μ_k)(x_i - μ_k)^T / Σ_i γ_ik

ELBO = Σ_i Σ_k γ_ik · [log π_k + log N(x_i | μ_k, Σ_k) - log γ_ik]

Guarantees:
    1. ELBO is monotonically non-decreasing (EM theorem)
    2. Converged γ_ik gives proper posterior probabilities
    3. Four-source fusion (RLIS, CM, FHPMS, BM) enters as structured prior on π_k

This module is external analysis — it does NOT modify mainline facts.
"""
from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

def _now(): return datetime.now(timezone.utc).isoformat()
def _jid(p): return f"{p}_{uuid.uuid4().hex[:8]}"

# Component names (matches pipeline_engine's 7-way decomposition)
COMPONENTS = ["p_core", "p_band", "r_core", "r_band", "m_band", "x_true", "u"]
K = len(COMPONENTS)

# Feature dimensions for each cell observation
FEATURE_NAMES = ["V_mean", "spike_rate", "release_proxy",
                 "adaptation_state", "displacement", "boundary_distance"]
D = len(FEATURE_NAMES)


class VariationalGMMEngine:
    """7-component Gaussian Mixture Model with true ELBO optimization.

    Usage:
        engine = VariationalGMMEngine(conn, run_id)
        posteriors, elbo_history = engine.fit(feature_matrix)
        # posteriors: dict of (adapter_name, k) -> {component: float}
    """

    def __init__(self, conn, run_id, max_iter=30, tol=1e-4, reg=1e-4):
        """Initialize the GMM engine.

        Args:
            conn: SQLite connection for logging
            run_id: current run ID
            max_iter: maximum EM iterations
            tol: ELBO convergence tolerance
            reg: diagonal regularization for covariance (Σ_k + reg·I)
        """
        self.conn = conn
        self.run_id = run_id
        self.max_iter = max_iter
        self.tol = tol
        self.reg = reg

        # Model parameters (initialized in fit())
        self.pi = None      # mixing weights: [K]
        self.mu = None      # means: [K][D]
        self.sigma = None   # covariances: [K][D][D] (diagonal for stability)
        self.elbo_history = []

    def _extract_features(self, conn, run_id, adapters, windows):
        """Extract feature matrix from DB cell data.

        Returns:
            X: list of D-dim feature vectors
            keys: list of (adapter_name, k) keys corresponding to each feature
        """
        X = []
        keys = []

        for adapter in adapters:
            aname = adapter.adapter_name
            for k in range(1, windows):
                # Query cell data: join spacetime_cell (coords) with information_fiber (signals)
                rows = conn.execute(
                    "SELECT sc.x, sc.y, sc.z, "
                    "COALESCE(fi.V_mean, 0), COALESCE(fi.spike_rate, 0), "
                    "COALESCE(fi.release_proxy, 0), COALESCE(fi.adaptation_state, 0), "
                    "sc.boundary_distance "
                    "FROM spacetime_cell sc "
                    "LEFT JOIN information_fiber fi ON sc.cell_uid = fi.cell_uid "
                    "WHERE sc.run_id=? AND sc.window_id=?",
                    (run_id, f"win_{aname}_{k}")
                ).fetchall()

                if not rows:
                    continue

                n = len(rows)
                # Compute per-window aggregate features
                avg_V = sum(r[3] for r in rows) / n
                avg_spike = sum(r[4] for r in rows) / n
                avg_release = sum(r[5] for r in rows) / n
                avg_adapt = sum(r[6] for r in rows) / n
                avg_bdist = sum(r[7] for r in rows) / n

                # Displacement from previous window
                if k > 1:
                    prev_rows = conn.execute(
                        "SELECT x, y, z FROM spacetime_cell WHERE run_id=? AND window_id=?",
                        (run_id, f"win_{aname}_{k-1}")
                    ).fetchall()
                    if prev_rows:
                        m = min(n, len(prev_rows))
                        disp = sum(
                            math.sqrt((rows[i][0] - prev_rows[i][0])**2 +
                                      (rows[i][1] - prev_rows[i][1])**2 +
                                      (rows[i][2] - prev_rows[i][2])**2)
                            for i in range(m)
                        ) / max(m, 1)
                    else:
                        disp = 0.0
                else:
                    disp = 0.0

                feature = [avg_V, avg_spike, avg_release, avg_adapt, disp, avg_bdist]
                X.append(feature)
                keys.append((aname, k))

        return X, keys

    @staticmethod
    def _log_normal_pdf(x, mu, sigma_diag):
        """Log probability of x under N(mu, diag(sigma_diag)).

        Args:
            x: D-dim observation
            mu: D-dim mean
            sigma_diag: D-dim diagonal variances

        Returns:
            log N(x | mu, diag(sigma_diag))
        """
        d = len(x)
        log_det = sum(math.log(max(s, 1e-10)) for s in sigma_diag)
        diff_sq = sum((x[j] - mu[j])**2 / max(sigma_diag[j], 1e-10) for j in range(d))
        return -0.5 * (d * math.log(2 * math.pi) + log_det + diff_sq)

    def _initialize(self, X, prior_scores=None):
        """Initialize GMM parameters.

        Uses K-means++ style initialization for means,
        and optionally uses four-source prior scores for π.

        Args:
            X: list of D-dim feature vectors
            prior_scores: optional dict mapping component -> prior weight from four-source fusion
        """
        N = len(X)

        # Initialize π from prior scores or uniform
        if prior_scores:
            raw = [max(0.01, prior_scores.get(c, 1.0 / K)) for c in COMPONENTS]
            total = sum(raw)
            self.pi = [r / total for r in raw]
        else:
            self.pi = [1.0 / K] * K

        # Initialize means by spreading across the data range
        if N >= K:
            # Stratified sampling
            step = N // K
            self.mu = [list(X[min(c * step, N - 1)]) for c in range(K)]
        else:
            self.mu = [list(X[0])] * K

        # Add small perturbation to avoid identical means
        import random
        rng = random.Random(42)
        for c in range(K):
            for j in range(D):
                self.mu[c][j] += rng.gauss(0, 0.1)

        # Initialize covariance as data variance + regularization
        global_var = [0.0] * D
        global_mean = [sum(X[i][j] for i in range(N)) / max(N, 1) for j in range(D)]
        for i in range(N):
            for j in range(D):
                global_var[j] += (X[i][j] - global_mean[j])**2
        global_var = [max(v / max(N, 1), self.reg) for v in global_var]

        self.sigma = [list(global_var) for _ in range(K)]

    def _e_step(self, X):
        """E-step: compute responsibilities γ_ik = p(z_i = k | x_i, θ).

        Returns:
            gamma: [N][K] matrix of posterior probabilities
        """
        N = len(X)
        gamma = []

        for i in range(N):
            log_probs = []
            for c in range(K):
                log_p = math.log(max(self.pi[c], 1e-10)) + \
                        self._log_normal_pdf(X[i], self.mu[c], self.sigma[c])
                log_probs.append(log_p)

            # Log-sum-exp for numerical stability
            max_lp = max(log_probs)
            exp_sum = sum(math.exp(lp - max_lp) for lp in log_probs)
            log_norm = max_lp + math.log(exp_sum)

            row = [math.exp(lp - log_norm) for lp in log_probs]
            gamma.append(row)

        return gamma

    def _m_step(self, X, gamma):
        """M-step: update parameters to maximize ELBO given γ.

        Updates self.pi, self.mu, self.sigma in place.
        """
        N = len(X)

        for c in range(K):
            # N_k = Σ_i γ_ik
            n_k = sum(gamma[i][c] for i in range(N))
            n_k = max(n_k, 1e-10)  # prevent division by zero

            # Update π_k
            self.pi[c] = max(1e-6, n_k / N)

            # Update μ_k
            for j in range(D):
                self.mu[c][j] = sum(gamma[i][c] * X[i][j] for i in range(N)) / n_k

            # Update Σ_k (diagonal)
            for j in range(D):
                var_j = sum(gamma[i][c] * (X[i][j] - self.mu[c][j])**2
                            for i in range(N)) / n_k
                self.sigma[c][j] = max(var_j, self.reg)  # floor with regularization

        # Re-normalize π
        pi_sum = sum(self.pi)
        self.pi = [p / pi_sum for p in self.pi]

    def _compute_elbo(self, X, gamma):
        """Compute ELBO = Σ_i Σ_k γ_ik · [log π_k + log N(x_i|μ_k,Σ_k) - log γ_ik].

        Returns:
            ELBO value (scalar)
        """
        N = len(X)
        elbo = 0.0

        for i in range(N):
            for c in range(K):
                g = gamma[i][c]
                if g < 1e-15:
                    continue
                log_pi = math.log(max(self.pi[c], 1e-10))
                log_lik = self._log_normal_pdf(X[i], self.mu[c], self.sigma[c])
                log_g = math.log(max(g, 1e-10))
                elbo += g * (log_pi + log_lik - log_g)

        return elbo

    def fit(self, X, keys=None, prior_scores=None):
        """Run full EM optimization.

        Args:
            X: list of D-dim feature vectors
            keys: optional list of (adapter_name, k) keys
            prior_scores: optional dict mapping component -> prior weight

        Returns:
            posteriors: dict of key -> {component: float} (γ_ik per key)
            elbo_history: list of ELBO values per iteration
        """
        N = len(X)
        if N < 2:
            # Degenerate case: return uniform posteriors
            uniform = {c: 1.0 / K for c in COMPONENTS}
            if keys:
                return {k: dict(uniform) for k in keys}, [0.0]
            return {}, [0.0]

        # Initialize
        self._initialize(X, prior_scores)

        print(f"  GMM-ELBO: N={N}, D={D}, K={K}, max_iter={self.max_iter}, tol={self.tol}")
        print(f"  Initial π: {[f'{p:.3f}' for p in self.pi]}")

        prev_elbo = -float('inf')
        self.elbo_history = []

        for t in range(1, self.max_iter + 1):
            # E-step
            gamma = self._e_step(X)

            # M-step
            self._m_step(X, gamma)

            # Compute ELBO
            elbo = self._compute_elbo(X, gamma)
            self.elbo_history.append(elbo)

            delta = elbo - prev_elbo

            # ELBO monotonicity check (should never decrease significantly)
            if delta < -1e-3:
                print(f"    WARNING: ELBO decreased at iter {t}: {delta:.6f} "
                      f"(numerical instability)")

            # Log to DB
            self.conn.execute(
                "INSERT INTO v37421_em_iteration_log "
                "(record_id,run_id,iteration,j_total,delta_j,"
                "lambda_l,lambda_c,lambda_h,lambda_b,"
                "w_motion,w_prx,w_xin_cons,w_r_core,w_p_band,"
                "converged,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("gmm"), self.run_id, t, elbo, delta,
                 self.pi[0], self.pi[1], self.pi[2], self.pi[3],
                 self.pi[4], self.pi[5], self.pi[6] if K > 6 else 0,
                 0, 0,  # unused columns
                 1 if abs(delta) < self.tol and t > 1 else 0, _now()))

            converged = (t > 1 and abs(delta) < self.tol)
            print(f"    Iter {t:2d}: ELBO={elbo:.4f}  ΔELBO={delta:.6f}  "
                  f"π=[{','.join(f'{p:.3f}' for p in self.pi)}]"
                  f"{'  CONVERGED' if converged else ''}")

            if converged:
                break

            prev_elbo = elbo

        # Write converged params
        self.conn.execute(
            "INSERT INTO v37421_em_converged_params "
            "(record_id,run_id,total_iterations,final_j,converged,"
            "lambda_l,lambda_c,lambda_h,lambda_b,"
            "w_motion,w_prx,w_xin_cons,w_r_core,w_p_band,"
            "params_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (_jid("gmmc"), self.run_id, len(self.elbo_history),
             self.elbo_history[-1] if self.elbo_history else 0,
             1 if converged else 0,
             self.pi[0], self.pi[1], self.pi[2], self.pi[3],
             self.pi[4], self.pi[5], self.pi[6] if K > 6 else 0,
             0, 0,
             json.dumps({
                 "pi": {COMPONENTS[c]: round(self.pi[c], 6) for c in range(K)},
                 "mu": {COMPONENTS[c]: [round(v, 4) for v in self.mu[c]] for c in range(K)},
                 "sigma_diag": {COMPONENTS[c]: [round(v, 4) for v in self.sigma[c]] for c in range(K)},
             }, separators=(",", ":"), ensure_ascii=False),
             _now()))

        self.conn.commit()

        # Build posteriors dict
        posteriors = {}
        if keys and len(keys) == N:
            for i, key in enumerate(keys):
                posteriors[key] = {COMPONENTS[c]: gamma[i][c] for c in range(K)}

        return posteriors, self.elbo_history

    def fit_from_db(self, adapters, windows, prior_scores=None):
        """Convenience method: extract features from DB and fit.

        Args:
            adapters: list of source adapters
            windows: number of time windows
            prior_scores: optional dict mapping component -> prior weight

        Returns:
            posteriors: dict of (adapter_name, k) -> {component: float}
            elbo_history: list of ELBO values
        """
        X, keys = self._extract_features(self.conn, self.run_id, adapters, windows)
        if not X:
            print("  GMM-ELBO: No features extracted, skipping.")
            return {}, []
        return self.fit(X, keys, prior_scores)


def blend_posteriors(rho_softmax: dict, gmm_posterior: dict, alpha: float = 0.5) -> dict:
    """Blend softmax-based ρ with GMM posterior γ.

    Args:
        rho_softmax: {component: float} from pipeline's softmax fusion
        gmm_posterior: {component: float} from GMM E-step
        alpha: blend weight (0 = pure softmax, 1 = pure GMM)

    Returns:
        blended {component: float}, normalized to sum to 1
    """
    blended = {}
    for c in COMPONENTS:
        s = rho_softmax.get(c, 0.0)
        g = gmm_posterior.get(c, 0.0)
        blended[c] = (1 - alpha) * s + alpha * g

    # Re-normalize
    total = sum(blended.values())
    if total > 0:
        blended = {c: v / total for c, v in blended.items()}
    else:
        blended = {c: 1.0 / K for c in COMPONENTS}

    return blended
