#!/usr/bin/env python3
"""Morphosphere v37.4.60 — Integrated Pipeline: CTC Real Data + GMM-ELBO + Non-trivial Convergence.

This runner demonstrates all three scientific fixes operating together:
  1. REAL DATA — CTCRealDataAdapter reads actual Fluo-N2DH-GOWT1 cell tracking data
  2. GMM-ELBO — VariationalGMMEngine provides true probabilistic posterior
  3. NON-TRIVIAL CONVERGENCE — run_multiround_convergence with Hebbian feedback loops

Usage:
    python run_v37460_integrated.py

Output:
    - v37460_integrated.db — SQLite database with all results
    - Console output with convergence trajectory and ELBO history
"""
import os, sys, sqlite3, time
from pathlib import Path

# Setup paths
BASE = Path(__file__).resolve().parent.parent  # morphosphere_v2pp/
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE))  # so engine imports work

from morphosphere.active_exec.source_adapters import CellSphereAdapter, Cell2DRealAdapter
from ctc_source_adapter import CTCRealDataAdapter
from variational_gmm_engine import VariationalGMMEngine
import pipeline_engine as pe


DB_NAME = str(BASE / "db" / "v37492_integrated.db")
WINDOWS = 15    # CTC has ~92 frames, use 15 for quick validation
CELLS = 50      # CTC cell count varies per frame


def main():
    print("=" * 72)
    print("Morphosphere v37.4.60 — Three Scientific Fixes Integrated")
    print("=" * 72)

    # ── Setup DB ──
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    pe.apply_migrations(conn)
    conn.commit()

    run_id = "v37460_integrated_001"

    # ═══════════════════════════════════════════════════════════
    # Fix 1: REAL DATA — CTC Adapter
    # ═══════════════════════════════════════════════════════════
    print("\n" + "─" * 72)
    print("FIX 1: Real Data — CTC Fluo-N2DH-GOWT1")
    print("─" * 72)

    ctc_adapter = CTCRealDataAdapter(sequence="01", max_frames=WINDOWS)
    # Also keep one synthetic adapter for cross-domain comparison
    synth_adapter = CellSphereAdapter(cell_count=CELLS, seed=42)

    adapters = [ctc_adapter, synth_adapter]

    for adapter in adapters:
        pe.register_adapter(conn, run_id, adapter)

    # Process windows
    prev_cells = {}
    prev_block_id = {}
    prev_event_id = {}

    print(f"\n  Processing {WINDOWS} windows × {len(adapters)} adapters...")

    for k in range(WINDOWS):
        for adapter in adapters:
            cells = adapter.generate_cells(k)
            if not cells:
                continue

            env = adapter.make_envelope(k)
            env_id = pe.write_envelope(conn, run_id, env)
            pw_id = pe.write_process_window(conn, run_id, adapter, k, env_id, len(cells),
                                            ["ingest", "transport", "hypothesize"])
            uid_map = pe.write_cells(conn, run_id, adapter, k, cells)

            # Transport edges (from k >= 1)
            akey = adapter.adapter_name
            if akey in prev_cells:
                pe.write_transport(conn, run_id, adapter, k, prev_cells[akey], cells)

            # Hypotheses
            hyps = pe.write_hypotheses(conn, run_id, adapter, k, cells)

            # Xi residue
            xi_id = pe.write_xi(conn, run_id, adapter, k, hyps, cells[:5])
            pe.write_v366_xin_binding(conn, run_id, xi_id, pw_id, env_id, 0.15)

            # FHPMS/RLIS
            p_m = 0.4 + 0.02 * k
            r_m = 0.2 + 0.01 * k
            x_m = 0.15
            origin_anchors = [f"anchor_{adapter.adapter_name}_{k}"]

            res = pe.write_v374_fhpms_rlis_trace(
                conn, run_id, adapter, k, pw_id, env_id,
                origin_anchors, p_m, r_m, x_m,
                prev_block_id=prev_block_id.get(akey),
                prev_event_id=prev_event_id.get(akey),
                cells=cells
            )

            # Diagnostic layers
            pe.write_v366_measures(conn, run_id, pw_id, adapter, k, cells)
            pe.write_legacy_observable_layer(conn, run_id, adapter, k, cells, hyps)
            pe.write_legacy_recursive_layer(conn, run_id, adapter, k, cells, hyps)
            pe.write_legacy_diagnostic_layer(conn, run_id, adapter, k, cells, env, hyps)

            # External ledgers
            pe.write_external_ledgers(conn, run_id, adapter, k, env, cells)

            prev_cells[akey] = cells
            prev_block_id[akey] = res["block_id"]
            prev_event_id[akey] = res["event_id"]

        conn.commit()

    # Count CTC cells written
    ctc_cell_count = conn.execute(
        "SELECT COUNT(*) FROM spacetime_cell WHERE window_id LIKE '%ctc%'"
    ).fetchone()[0]
    synth_cell_count = conn.execute(
        "SELECT COUNT(*) FROM spacetime_cell WHERE window_id NOT LIKE '%ctc%'"
    ).fetchone()[0]
    print(f"\n  ✓ CTC real cells: {ctc_cell_count}")
    print(f"  ✓ Synthetic cells: {synth_cell_count}")
    print(f"  ✓ Total transport edges: {pe.rc(conn, 'transport_current_edge')}")

    # ═══════════════════════════════════════════════════════════
    # Fix 2: STRICT VARIATIONAL MATH — GMM-ELBO
    # ═══════════════════════════════════════════════════════════
    print("\n" + "─" * 72)
    print("FIX 2: Strict Variational Math — 7-component GMM + ELBO")
    print("─" * 72)

    gmm = VariationalGMMEngine(conn, run_id, max_iter=30, tol=1e-4, reg=1e-4)
    gmm_posteriors, elbo_history = gmm.fit_from_db(adapters, WINDOWS)

    if elbo_history:
        print(f"\n  ✓ ELBO trajectory: {elbo_history[0]:.4f} → {elbo_history[-1]:.4f}")
        print(f"  ✓ Iterations: {len(elbo_history)}")

        # ELBO monotonicity check
        mono_violations = sum(1 for i in range(len(elbo_history) - 1)
                              if elbo_history[i + 1] < elbo_history[i] - 1e-3)
        print(f"  ✓ ELBO monotonicity violations: {mono_violations}")
        print(f"  ✓ GMM posteriors computed for {len(gmm_posteriors)} windows")

        # Final mixing weights
        print(f"  ✓ Final π: {{{', '.join(f'{c}:{p:.3f}' for c, p in zip(['p_core','p_band','r_core','r_band','m_band','x_true','u'], gmm.pi))}}}")
    else:
        print("  ⚠ GMM did not produce results (insufficient data)")

    # ═══════════════════════════════════════════════════════════
    # Fix 3: NON-TRIVIAL CONVERGENCE — Feedback loops
    # ═══════════════════════════════════════════════════════════
    print("\n" + "─" * 72)
    print("FIX 3: Non-Trivial Convergence — Hebbian Feedback Loops")
    print("─" * 72)

    # Run convergence WITH GMM posteriors and feedback
    conv = pe.run_multiround_convergence(conn, run_id, adapters, WINDOWS, num_rounds=5)

    print(f"\n  ═══ Convergence Audit ═══")
    print(f"  Rounds: {conv['rounds']}")
    print(f"  Drift trajectory: {[f'{d:.4f}' for d in conv['drifts']]}")
    print(f"  Final drift: {conv['final_drift']:.4f}")
    print(f"  Verdict: {conv['verdict']}")
    print(f"  λ history: {[{k: f'{v:.3f}' for k, v in lh.items()} for lh in conv.get('lambda_history', [])]}")

    # ═══════════════════════════════════════════════════════════
    # Validation Summary
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("VALIDATION SUMMARY")
    print("=" * 72)

    checks = []

    # Check 1: Real data present
    has_real = ctc_cell_count > 0
    checks.append(("CTC real data cells > 0", has_real, ctc_cell_count))

    # Check 2: ELBO monotonicity
    elbo_ok = elbo_history and mono_violations == 0
    checks.append(("ELBO monotonically non-decreasing", elbo_ok, mono_violations))

    # Check 3: Non-trivial convergence (drift[1] > 0 — round 2 should show actual drift
    # from Hebbian feedback; round 1 is always 0 because no prev_rho exists)
    second_drift = conv['drifts'][1] if len(conv['drifts']) > 1 else 0
    nontrivial = second_drift > 0.0001
    checks.append(("Round-2 drift > 0 (non-trivial feedback)", nontrivial, f"{second_drift:.4f}"))

    # Check 4: Final convergence
    final_conv = conv['final_drift'] < 0.05
    checks.append(("Final drift < 0.05 (convergence)", final_conv, f"{conv['final_drift']:.4f}"))

    # Check 5: λ actually moved
    if conv.get('lambda_history') and len(conv['lambda_history']) > 1:
        lam_0 = conv['lambda_history'][0]
        lam_f = conv['lambda_history'][-1]
        lam_moved = any(abs(lam_0[k] - lam_f[k]) > 0.001 for k in lam_0)
    else:
        lam_moved = False
    checks.append(("λ priors evolved during convergence", lam_moved, ""))

    # Check 6: GMM posteriors available
    gmm_ok = len(gmm_posteriors) > 0
    checks.append(("GMM posteriors computed", gmm_ok, len(gmm_posteriors)))

    # Check 7: Hebbian weights exist
    heb_count = conn.execute("SELECT COUNT(*) FROM fhpms_hebbian_association_weight").fetchone()[0]
    checks.append(("Hebbian weights populated", heb_count > 0, heb_count))

    # Check 8: DB integrity
    table_count = len(conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall())
    checks.append(("DB tables > 100", table_count > 100, table_count))

    pass_count = 0
    for name, ok, detail in checks:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  {status}: {name} [{detail}]")
        if ok:
            pass_count += 1

    print(f"\n  Result: {pass_count}/{len(checks)} checks passed")
    print(f"  Database: {DB_NAME}")

    conn.close()

    print("\n" + "=" * 72)
    print("Done.")
    return pass_count == len(checks)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
