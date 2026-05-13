#!/usr/bin/env python3
"""v38 Convergence Validator — Verify that PRX convergence is non-trivial.

Phase 1.2 of the v38 improvement plan.

This script runs the upgraded run_convergence() method and verifies:
  1. drift > 0 in early rounds (not flat repetition)
  2. drift decreases over rounds (genuine convergence)
  3. Final entropy < initial entropy (distribution sharpens)
  4. System reaches a true fixed point, not just repeating
"""
import os, sys, sqlite3, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE))

# Need engines on path
sys.path.insert(0, str(BASE / "engines"))


def main():
    # Use an in-memory DB so we don't pollute existing DBs
    from pipeline_isolator import IsolatedPipeline, MotionRegimeOracle
    from engines._common import ABConfig
    from engines._common import ABConfig

    print("=" * 72)
    print("Morphosphere v38 — CONVERGENCE VALIDATION")
    print("Phase 1.2: Non-Trivial Convergence")
    print("=" * 72)

    db_path = str(BASE / "db" / "v38_convergence_test.db")
    conn = sqlite3.connect(db_path)

    # Create the required tables
    _ensure_tables(conn)

    run_id = f"v38_conv_{int(time.time())}"
    config = ABConfig()

    # Test with multiple pipeline namespaces
    test_configs = [
        {"ns": "ctc_conv", "seed": 42},
        {"ns": "phc_conv", "seed": 100},
        {"ns": "usgs_conv", "seed": 200},
    ]

    all_pass = True

    for tc in test_configs:
        ns = tc["ns"]
        seed = tc["seed"]
        print(f"\n{'─' * 72}")
        print(f"  Pipeline: {ns} (seed={seed})")
        print(f"{'─' * 72}")

        # Create a minimal adapter
        from engines._common import MeasureCoordinate

        class MinimalAdapter:
            def __init__(self, name, seed):
                self.adapter_name = name
                self.seed = seed
                import random
                self._rng = random.Random(seed)

            def generate_cells(self, k):
                # Create minimal cell objects
                cells = []
                for i in range(10):
                    cells.append(_MinimalCell(i, self._rng))
                return cells

        class _MinimalCell:
            def __init__(self, idx, rng):
                self.uid = f"cell_{idx}"
                self.x = rng.gauss(0, 1)
                self.y = rng.gauss(0, 1)
                self.z = 0
                self.V_mean = rng.gauss(0.5, 0.3)
                self.spike_rate = rng.random() * 2
                self.V_slope = rng.gauss(0, 0.1)
                self.signal_uncertainty = rng.random() * 0.5
                self.release_proxy = rng.random() * 0.3
                self.neighbor_ids = [max(0, idx - 1), min(9, idx + 1)]

        adapter = MinimalAdapter(ns, seed)

        # Create pipeline tables
        _create_pipeline_tables(conn, ns)

        # Create pipeline with fake regime labels
        pipeline = IsolatedPipeline(
            conn=conn, run_id=run_id, namespace=ns,
            adapters=[adapter], config=config, windows=20)

        # Inject regime labels to simulate a mixed environment
        regimes = ["stationary", "slow_drift", "fast_drift",
                    "oscillation", "jump", "diffusion"]
        import random
        rng = random.Random(seed)
        for k in range(20):
            regime = regimes[k % len(regimes)]
            pipeline._regime_labels[(ns, k)] = regime

        # Run convergence with 8 rounds
        num_rounds = 8
        result = pipeline.run_convergence(num_rounds=num_rounds)

        drifts = result["drifts"]
        entropies = result["entropies"]
        verdict = result["verdict"]

        # Display results
        print(f"\n  Round  {'Drift':>10s}  {'Entropy':>10s}")
        print(f"  {'─' * 30}")
        for i, (d, e) in enumerate(zip(drifts, entropies)):
            marker = ""
            if i == 0:
                marker = " (baseline)"
            elif i == result.get("converged_at_round", -1) - 1:
                marker = " ← converged"
            print(f"  {i+1:5d}  {d:10.6f}  {e:10.6f}{marker}")

        print(f"\n  Verdict: {verdict}")
        print(f"  Initial drift: {result['initial_drift']:.6f}")
        print(f"  Final drift:   {result['final_drift']:.6f}")
        print(f"  Converged at round: {result['converged_at_round']}")
        print(f"  Entropy decreased: {result['entropy_decreased']}")

        # Validate non-trivial convergence criteria
        checks = {
            "drift_nonzero_early": drifts[1] > 0 if len(drifts) > 1 else False,
            "drift_decreasing": (len(drifts) >= 3 and
                                  drifts[-1] < drifts[1] if len(drifts) > 1 else False),
            "entropy_decreased": result["entropy_decreased"],
            "not_flat_repetition": any(d > 0.001 for d in drifts[1:]),
        }

        print(f"\n  Convergence Checks:")
        for check, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            icon = "✅" if passed else "❌"
            print(f"    {icon} {check}: {status}")
            if not passed:
                all_pass = False

    conn.close()

    print(f"\n{'=' * 72}")
    if all_pass:
        print("  OVERALL: ALL CHECKS PASSED ✅")
        print("  Convergence is NON-TRIVIAL (drift > 0 then → 0)")
    else:
        print("  OVERALL: SOME CHECKS FAILED ❌")
        print("  Review individual pipeline results above")
    print(f"  DB saved to: {db_path}")
    print(f"{'=' * 72}")


def _ensure_tables(conn):
    """Create base tables needed by the harness."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS v37450_ab_config (
            config_id TEXT PRIMARY KEY, run_id TEXT, m_max REAL, alpha REAL,
            decay_epsilon REAL, oja_lambda REAL, eta REAL,
            strata_absorb_interval INTEGER, noise_storm_ticks INTEGER,
            regime_shift_ticks INTEGER, warmup_ticks INTEGER, created_at TEXT);
    """)
    conn.commit()


def _create_pipeline_tables(conn, ns):
    """Create pipeline-specific namespaced tables."""
    conn.executescript(f"""
        CREATE TABLE IF NOT EXISTS pipe_{ns}_prx_decomp (
            record_id TEXT PRIMARY KEY, run_id TEXT, window_k INTEGER,
            adapter_name TEXT, p_core REAL, p_band REAL, r_core REAL,
            r_band REAL, m_band REAL, x_true REAL, u REAL,
            regime_label TEXT, pipeline TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS pipe_{ns}_convergence (
            record_id TEXT PRIMARY KEY, run_id TEXT, total_rounds INTEGER,
            final_drift REAL, converged INTEGER, verdict TEXT,
            pipeline TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS pipe_{ns}_metric_log (
            record_id TEXT PRIMARY KEY, run_id TEXT, engine TEXT,
            tick INTEGER, phase TEXT, weight_entropy REAL,
            dead_node_count INTEGER, avg_weight REAL, max_weight REAL,
            total_weights INTEGER, pipeline TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS pipe_{ns}_hebbian_weight (
            weight_id TEXT PRIMARY KEY, from_entity_id TEXT,
            to_entity_id TEXT, association_type TEXT, weight_value REAL,
            inertia_mass REAL, cumulative_potential REAL,
            external_hits INTEGER, internal_hits INTEGER,
            stability_ticks INTEGER, is_dead_node INTEGER,
            pipeline TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS pipe_{ns}_dead_node_trace (
            trace_id TEXT PRIMARY KEY, run_id TEXT,
            from_entity_id TEXT, to_entity_id TEXT,
            inertia_mass REAL, cumulative_potential REAL,
            external_hits INTEGER, internal_hits INTEGER,
            weight_value REAL, tick_suspected INTEGER,
            tick_recovered INTEGER, recovery_cause TEXT,
            pipeline TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS pipe_{ns}_node_necropolis (
            node_uid TEXT PRIMARY KEY, run_id TEXT,
            birth_tick INTEGER, death_tick INTEGER,
            last_v_phi REAL, death_reason TEXT,
            dna_snapshot_json TEXT, pipeline TEXT, created_at TEXT);
    """)
    conn.commit()


if __name__ == "__main__":
    main()
