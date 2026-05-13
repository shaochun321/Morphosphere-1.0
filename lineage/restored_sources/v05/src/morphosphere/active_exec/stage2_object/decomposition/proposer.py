"""PRProposer: Mainline Object Proposer (V8 Section 8).

Graph Laplacian Smooth + Sparse Residual implementation-grade core.

V8-T3 deliverables:
  - Explicit threshold profile integration
  - Solver diagnostics in result (objective history, convergence, norms, transport gap)
  - Hot path (solve + minimal candidate output) vs cold path separation
  - delta_R_transport (residual transport breakage §8.6)
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..freezing.thresholds import ThresholdProfile


@dataclass
class SolverDiagnostics:
    """V8 §8.11 cold-path solver diagnostics."""
    objective_history: List[float] = field(default_factory=list)
    p_norm_history: List[float] = field(default_factory=list)
    r_norm_history: List[float] = field(default_factory=list)
    convergence_gap: float = 0.0
    converged: bool = False
    iterations: int = 0


@dataclass
class PRDecompositionResult:
    """Result container with V8 §8.6 derived quantities and solver diagnostics."""
    P_m: np.ndarray
    R_m: np.ndarray
    E_P: np.ndarray        # Per-node P energy: ||P_m(i,:)||_2
    E_R: np.ndarray        # Per-node R energy: ||R_m(i,:)||_2
    kappa: np.ndarray      # Per-node local consistency
    delta_R_transport: np.ndarray = field(default_factory=lambda: np.array([]))  # V8 §8.6 residual transport breakage
    iterations: int = 0
    converged: bool = False
    objective_history: list = field(default_factory=list)

    # V8 T3: Solver diagnostics for cold path persistence
    solver_diagnostics: Dict = field(default_factory=dict)

    def to_diagnostics_dict(self) -> Dict:
        """Serialize diagnostics for SQLite persistence."""
        return {
            "iterations": self.iterations,
            "converged": self.converged,
            "final_objective": self.objective_history[-1] if self.objective_history else None,
            "mean_E_P": float(np.mean(self.E_P)),
            "mean_E_R": float(np.mean(self.E_R)),
            "mean_kappa": float(np.mean(self.kappa)),
            "max_E_R": float(np.max(self.E_R)) if len(self.E_R) > 0 else 0.0,
            "mean_delta_R_transport": float(np.mean(self.delta_R_transport)) if len(self.delta_R_transport) > 0 else 0.0,
            **self.solver_diagnostics,
        }


class PRProposer:
    """Mainline Object Proposer (V8 Section 8).

    Graph Laplacian Smooth + Sparse Residual implementation-grade core.
    Hot path: solve + P_m/R_m + minimal derived quantities.
    Cold path diagnostics computed separately via compute_cold_diagnostics().
    """

    def __init__(self, lambda_g: float = 1.0, lambda_r: float = 0.5, lambda_t: float = 0.5,
                 max_iter: int = 10, tol: float = 1e-6,
                 threshold_profile: Optional[ThresholdProfile] = None):
        self.lambda_g = lambda_g
        self.lambda_r = lambda_r
        self.lambda_t = lambda_t
        self.max_iter = max_iter
        self.tol = tol
        self.threshold_profile = threshold_profile or ThresholdProfile.default()

    def _compute_objective(self, X_m, P_m, R_m, L_m, P_prior):
        """Evaluate the full objective function."""
        recon = 0.5 * np.sum((X_m - P_m - R_m) ** 2)
        smooth = self.lambda_g * np.trace(P_m.T @ L_m @ P_m)
        sparse = self.lambda_r * np.sum(np.linalg.norm(R_m, axis=1))
        prior_term = 0.0
        if P_prior is not None:
            prior_term = self.lambda_t * np.sum((P_m - P_prior) ** 2)
        return recon + smooth + sparse + prior_term

    def _compute_kappa(self, P_m, L_m):
        """V8 §8.6: Local consistency kappa_i = mean cosine similarity with neighbors."""
        N = P_m.shape[0]
        kappa = np.zeros(N)
        # Use adjacency from Laplacian: A = D - L
        if sp.issparse(L_m):
            L_dense = L_m.toarray()
        else:
            L_dense = L_m
        D_diag = np.diag(L_dense)
        A = np.diag(D_diag) - L_dense

        for i in range(N):
            neighbors = np.where(A[i, :] > 0)[0]
            if len(neighbors) == 0:
                kappa[i] = 0.0
                continue
            p_i_norm = np.linalg.norm(P_m[i, :])
            if p_i_norm < 1e-12:
                kappa[i] = 0.0
                continue
            cos_sims = []
            for j in neighbors:
                p_j_norm = np.linalg.norm(P_m[j, :])
                if p_j_norm < 1e-12:
                    cos_sims.append(0.0)
                else:
                    cos_sims.append(np.dot(P_m[i, :], P_m[j, :]) / (p_i_norm * p_j_norm))
            kappa[i] = np.mean(cos_sims)
        return kappa

    def solve(self, X_m: np.ndarray, L_m: sp.spmatrix, P_prior: Optional[np.ndarray],
              R_prior: Optional[np.ndarray] = None) -> PRDecompositionResult:
        """Alternating optimization for P_m and R_m (HOT PATH).

        Args:
            X_m: Signal matrix (N x D)
            L_m: Graph Laplacian (N x N)
            P_prior: W_{m-1 -> m} P_{m-1} transport prior (N x D)
            R_prior: Optional previous R_{m-1} for transport breakage computation

        Returns:
            PRDecompositionResult with P_m, R_m, derived quantities, and solver diagnostics
        """
        N, D = X_m.shape

        # Step A: Initialize
        P_m = P_prior.copy() if P_prior is not None else X_m.copy()
        R_m = np.zeros_like(X_m)

        I = sp.eye(N, format="csc")
        if sp.issparse(L_m):
            L_csc = L_m.tocsc()
        else:
            L_csc = sp.csc_matrix(L_m)
        A = I + 2 * self.lambda_g * L_csc + 2 * self.lambda_t * I

        objective_history = []
        p_norm_history = []
        r_norm_history = []
        converged = False

        for iteration in range(self.max_iter):
            # Step B: Update P_m
            B = X_m - R_m + 2 * self.lambda_t * (P_prior if P_prior is not None else np.zeros_like(X_m))
            for d in range(D):
                P_m[:, d] = spla.spsolve(A, B[:, d])

            # Step C: Update R_m
            Z = X_m - P_m
            norms = np.linalg.norm(Z, axis=1, keepdims=True)
            factor = np.maximum(1 - self.lambda_r / (norms + 1e-9), 0)
            R_m = factor * Z

            # Step D: Convergence check
            obj = self._compute_objective(X_m, P_m, R_m, L_m, P_prior)
            objective_history.append(obj)
            p_norm_history.append(float(np.linalg.norm(P_m)))
            r_norm_history.append(float(np.linalg.norm(R_m)))

            if len(objective_history) >= 2:
                delta = abs(objective_history[-2] - objective_history[-1])
                if delta < self.tol:
                    converged = True
                    break

        # Compute V8 §8.6 derived quantities
        E_P = np.linalg.norm(P_m, axis=1)   # Per-node P energy
        E_R = np.linalg.norm(R_m, axis=1)   # Per-node R energy
        kappa = self._compute_kappa(P_m, L_m) # Local consistency

        # V8 §8.6: Residual transport breakage
        if R_prior is not None and R_prior.shape == R_m.shape:
            delta_R_transport = np.linalg.norm(R_m - R_prior, axis=1)
        else:
            delta_R_transport = np.zeros(N)

        # Solver diagnostics (for cold path persistence)
        convergence_gap = abs(objective_history[-2] - objective_history[-1]) if len(objective_history) >= 2 else float('inf')
        solver_diag = {
            "p_norm_history": p_norm_history,
            "r_norm_history": r_norm_history,
            "convergence_gap": convergence_gap,
        }

        return PRDecompositionResult(
            P_m=P_m, R_m=R_m,
            E_P=E_P, E_R=E_R, kappa=kappa,
            delta_R_transport=delta_R_transport,
            iterations=len(objective_history),
            converged=converged,
            objective_history=objective_history,
            solver_diagnostics=solver_diag,
        )

    def classify_candidates(self, result: PRDecompositionResult) -> Dict[str, np.ndarray]:
        """Classify nodes into P/R candidates based on threshold profile (HOT PATH tail).

        Returns dict with boolean masks for candidate classification.
        """
        tp = self.threshold_profile
        N = len(result.E_P)

        # Primary propagation candidates (§8.9)
        p_candidate = (
            (result.E_P > tp.theta_P)
            & (result.kappa > tp.theta_kappa)
            # theta_bw check would require spectral analysis (cold path)
        )

        # Residual candidates (§8.9)
        r_candidate = (
            (result.E_R > tp.theta_R)
            # Additional criteria: support radius, boundary fragility, contradiction
        )

        # Mixed/indeterminate
        mixed = ~p_candidate & ~r_candidate & ((result.E_P > 0.1) | (result.E_R > 0.1))

        return {
            "p_candidate_mask": p_candidate,
            "r_candidate_mask": r_candidate,
            "mixed_mask": mixed,
            "n_p_candidates": int(np.sum(p_candidate)),
            "n_r_candidates": int(np.sum(r_candidate)),
            "n_mixed": int(np.sum(mixed)),
        }
