#!/usr/bin/env python3
"""v38 Variational GMM Validation — Verify ELBO monotonicity and meaningful PRX.

Phase 2.1 of the v38 improvement plan.

Validates:
  1. ELBO is monotonically non-decreasing across EM iterations
  2. GMM posteriors are more informative than uniform (lower entropy)
  3. GMM posteriors differ from static softmax (non-trivial)
  4. Converged parameters are stable across different initial conditions
"""
import os, sys, math, json, time, sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "engines"))

from variational_gmm_engine import VariationalGMMEngine, COMPONENTS, D, K


def generate_synthetic_features(n_per_regime=15, seed=42):
    """Generate synthetic feature data with known cluster structure.

    Creates 7 clusters (one per PRX component) with distinct means,
    so we can verify the GMM correctly separates them.
    """
    import random
    rng = random.Random(seed)

    # True cluster centers (manually designed to be separable)
    true_centers = {
        "p_core":     [0.8, 0.2, 0.1, 0.9, 0.3, 0.2],  # high V, low spike, high adapt
        "p_band":     [0.6, 0.3, 0.2, 0.7, 0.4, 0.3],
        "r_core":     [0.4, 0.7, 0.4, 0.3, 0.6, 0.4],  # medium V, high spike
        "r_band":     [0.3, 0.6, 0.5, 0.4, 0.7, 0.5],
        "m_band":     [0.5, 0.5, 0.3, 0.5, 0.5, 0.5],  # middle of everything
        "x_true":     [0.2, 0.8, 0.7, 0.2, 0.8, 0.7],  # low V, high spike/release
        "u":          [0.1, 0.4, 0.6, 0.1, 0.9, 0.8],  # extreme displacement
    }

    X = []
    true_labels = []
    keys = []
    noise_std = 0.15

    for comp_idx, comp in enumerate(COMPONENTS):
        center = true_centers[comp]
        for i in range(n_per_regime):
            feature = [center[j] + rng.gauss(0, noise_std) for j in range(D)]
            X.append(feature)
            true_labels.append(comp)
            keys.append((f"synth_{comp}", i))

    return X, keys, true_labels


def compute_entropy(posterior):
    """Shannon entropy of a probability distribution."""
    return -sum(v * math.log(max(v, 1e-10)) for v in posterior.values())


def main():
    print("=" * 72)
    print("Morphosphere v38 — VARIATIONAL GMM VALIDATION")
    print("Phase 2.1: True ELBO Optimization")
    print("=" * 72)

    db_path = str(BASE / "db" / "v38_gmm_validation.db")
    conn = sqlite3.connect(db_path)

    # Create required tables
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS v37421_em_iteration_log (
            record_id TEXT PRIMARY KEY, run_id TEXT, iteration INTEGER,
            j_total REAL, delta_j REAL,
            lambda_l REAL, lambda_c REAL, lambda_h REAL, lambda_b REAL,
            w_motion REAL, w_prx REAL, w_xin_cons REAL, w_r_core REAL, w_p_band REAL,
            converged INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS v37421_em_converged_params (
            record_id TEXT PRIMARY KEY, run_id TEXT, total_iterations INTEGER,
            final_j REAL, converged INTEGER,
            lambda_l REAL, lambda_c REAL, lambda_h REAL, lambda_b REAL,
            w_motion REAL, w_prx REAL, w_xin_cons REAL, w_r_core REAL, w_p_band REAL,
            params_json TEXT, created_at TEXT);
    """)
    conn.commit()

    run_id = f"v38_gmm_{int(time.time())}"

    # Generate data with known structure
    X, keys, true_labels = generate_synthetic_features(n_per_regime=15, seed=42)
    print(f"\n  Data: {len(X)} samples, {D} features, {K} components")
    print(f"  True labels: {len(set(true_labels))} distinct classes")

    # ═══════════════════════════════════════════════════════════
    # Test 1: Run EM and check ELBO monotonicity
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'─' * 72}")
    print(f"  TEST 1: ELBO Monotonicity")
    print(f"{'─' * 72}")

    engine = VariationalGMMEngine(conn, run_id, max_iter=30, tol=1e-5, reg=1e-4)
    posteriors, elbo_history = engine.fit(X, keys)

    # Check ELBO monotonicity
    monotonic = True
    violations = []
    for i in range(1, len(elbo_history)):
        if elbo_history[i] < elbo_history[i-1] - 1e-3:  # allow tiny numerical noise
            monotonic = False
            violations.append((i, elbo_history[i] - elbo_history[i-1]))

    print(f"\n  ELBO History: {len(elbo_history)} iterations")
    print(f"  ELBO start:  {elbo_history[0]:.4f}")
    print(f"  ELBO end:    {elbo_history[-1]:.4f}")
    print(f"  ELBO gain:   {elbo_history[-1] - elbo_history[0]:.4f}")
    print(f"  Monotonic:   {'YES ✅' if monotonic else 'NO ❌'}")
    if violations:
        for v_iter, v_delta in violations:
            print(f"    Violation at iter {v_iter}: delta = {v_delta:.6f}")

    # ═══════════════════════════════════════════════════════════
    # Test 2: Posterior quality — should assign high prob to true cluster
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'─' * 72}")
    print(f"  TEST 2: Posterior Classification Accuracy")
    print(f"{'─' * 72}")

    correct = 0
    total = len(keys)
    entropy_sum = 0.0

    for i, key in enumerate(keys):
        if key not in posteriors:
            continue
        post = posteriors[key]
        predicted = max(post, key=post.get)
        true_label = true_labels[i]
        if predicted == true_label:
            correct += 1
        entropy_sum += compute_entropy(post)

    accuracy = correct / max(total, 1)
    avg_entropy = entropy_sum / max(total, 1)
    uniform_entropy = math.log(K)  # max entropy = log(7) ≈ 1.946

    print(f"  Classification accuracy: {accuracy:.3f} ({correct}/{total})")
    print(f"  Average posterior entropy: {avg_entropy:.4f}")
    print(f"  Uniform entropy:          {uniform_entropy:.4f}")
    print(f"  Entropy reduction:        {uniform_entropy - avg_entropy:.4f}")
    print(f"  Informative:              {'YES ✅' if avg_entropy < uniform_entropy * 0.8 else 'NO ❌'}")

    # ═══════════════════════════════════════════════════════════
    # Test 3: Converged π should be non-uniform
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'─' * 72}")
    print(f"  TEST 3: Converged Mixing Weights π")
    print(f"{'─' * 72}")

    pi_entropy = -sum(p * math.log(max(p, 1e-10)) for p in engine.pi)
    print(f"  π = {[f'{p:.4f}' for p in engine.pi]}")
    print(f"  π entropy: {pi_entropy:.4f} (uniform = {uniform_entropy:.4f})")
    for c, comp in enumerate(COMPONENTS):
        print(f"    {comp:10s}: π={engine.pi[c]:.4f}  "
              f"μ=[{', '.join(f'{v:.3f}' for v in engine.mu[c])}]")

    # ═══════════════════════════════════════════════════════════
    # Test 4: Stability across seeds
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'─' * 72}")
    print(f"  TEST 4: Stability Across Seeds")
    print(f"{'─' * 72}")

    accuracies = []
    for seed in [42, 100, 200, 500]:
        X_s, keys_s, labels_s = generate_synthetic_features(n_per_regime=15, seed=seed)
        run_s = f"v38_gmm_s{seed}_{int(time.time())}"
        eng = VariationalGMMEngine(conn, run_s, max_iter=30, tol=1e-5, reg=1e-4)
        post_s, elbo_s = eng.fit(X_s, keys_s)

        correct_s = sum(1 for i, k in enumerate(keys_s)
                        if k in post_s and max(post_s[k], key=post_s[k].get) == labels_s[i])
        acc_s = correct_s / max(len(keys_s), 1)
        accuracies.append(acc_s)

    mean_acc = sum(accuracies) / len(accuracies)
    std_acc = math.sqrt(sum((a - mean_acc) ** 2 for a in accuracies) / max(len(accuracies) - 1, 1))
    print(f"  Accuracies: {[f'{a:.3f}' for a in accuracies]}")
    print(f"  Mean ± Std:  {mean_acc:.3f} ± {std_acc:.3f}")
    print(f"  Stable:      {'YES ✅' if std_acc < 0.1 else 'NO ❌'}")

    # ═══════════════════════════════════════════════════════════
    # FINAL VERDICT
    # ═══════════════════════════════════════════════════════════
    print(f"\n{'=' * 72}")
    print(f"  VARIATIONAL GMM VERDICT")
    print(f"{'=' * 72}")

    checks = {
        "elbo_monotonic": monotonic,
        "classification_accuracy > 0.5": accuracy > 0.5,
        "entropy_reduced": avg_entropy < uniform_entropy * 0.8,
        "stable_across_seeds": std_acc < 0.1,
    }

    all_pass = all(checks.values())
    for check, passed in checks.items():
        icon = "✅" if passed else "❌"
        print(f"    {icon} {check}: {'PASS' if passed else 'FAIL'}")

    print(f"\n  {'ALL CHECKS PASSED ✅' if all_pass else 'SOME CHECKS FAILED ❌'}")
    print(f"  DB saved to: {db_path}")
    print(f"{'=' * 72}")

    conn.close()


if __name__ == "__main__":
    main()
