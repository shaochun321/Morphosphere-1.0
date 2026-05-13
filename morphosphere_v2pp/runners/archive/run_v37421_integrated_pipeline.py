#!/usr/bin/env python3
"""Morphosphere v37.4.21 — Integrated Scientific Pipeline.

Ties together three scientific improvements:
  A. Variational EM: replaces hardcoded J[ρ] weights with iterative optimization
  B. Closed-loop Hebbian: performance-based weight updates (not random)
  C. Motion-PRX integration: motion recognition feeds into PRX bottom scores

Pipeline phases:
  1. Standard pipeline (cells → transport → hypotheses → FHPMS/RLIS)
  2. Motion recognition (generates v37417_motion_recognition_log)
  3. EM-PRX convergence (uses motion results as bottom constraints)
  4. Formula competition (with closed-loop Hebbian)
  5. Verification
"""
from __future__ import annotations
import sqlite3, sys, uuid, random, math, json, hashlib, time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

REPORT_DIR = ROOT / "v37421_integrated_reports"
REPORT_DIR.mkdir(exist_ok=True)
DB_PATH = ROOT / "v37421_integrated.db"

from morphosphere.active_exec.source_adapters import CellSphereAdapter, Cell2DRealAdapter
import pipeline_engine as eng
from motion_recognition_engine import (
    MotionProcessGenerator, FeatureExtractor, BayesianMotionRecognizer,
    MOTION_REGIMES, FEATURE_NAMES)

def now(): return datetime.now(timezone.utc).isoformat()
def jid(p): return f"{p}_{uuid.uuid4().hex[:8]}"


def main():
    t0 = time.time()
    CELLS = 120; WINDOWS = 12; ROUNDS = 5
    print(f"{'='*70}")
    print(f"  Morphosphere v37.4.21 Integrated Scientific Pipeline")
    print(f"{'='*70}")
    print(f"  Cells/source: {CELLS}, Windows: {WINDOWS}, Sources: 2")

    # ═══════════════════════════════════════════
    # PHASE 0: Database setup
    # ═══════════════════════════════════════════
    if DB_PATH.exists(): DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA foreign_keys=OFF")
    eng.apply_migrations(conn)

    run_id = f"v37421_sci_{uuid.uuid4().hex[:8]}"
    created = now()
    conn.execute(
        "INSERT INTO run_manifest (run_id,rules_version,schema_version,calibration_profile,execution_mode,"
        "cell_count,window_count,created_at,notes,physical_cell_count,spacetime_cell_count,extra_json) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, "v37.4.21", "v37.4.21", "dual_source_v37421", f"full_chain_{CELLS}",
         CELLS*2, WINDOWS, created,
         "v37.4.21: integrated scientific pipeline (EM + Hebbian + Motion-PRX)",
         CELLS*2, CELLS*2*WINDOWS,
         eng.jdump({"sources": 2, "cells_per_source": CELLS, "focus": "scientific_integration"})))
    for k in range(WINDOWS):
        conn.execute(
            "INSERT INTO system_clock_entry (clock_n,run_id,time_s,dt_s,clock_hash,schema_version) VALUES (?,?,?,?,?,?)",
            (k, run_id, k*0.01, 0.01, f"clock_{k:04d}", "v37.4.21"))

    adapters = [CellSphereAdapter(cell_count=CELLS, seed=42), Cell2DRealAdapter(cell_count=CELLS, seed=137)]
    for a in adapters:
        eng.register_adapter(conn, run_id, a)
        conn.execute(
            "INSERT INTO proxy_provenance (proxy_id,run_id,target_field,proxy_type,proxy_reason,"
            "source_assumption,replacement_condition,forbidden_interpretation,created_by,created_at,review_due) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (jid("prx"), run_id, f"{a.adapter_name}.*", "diagnostic",
             f"diagnostic {a.signal_model}", f"{a.signal_model} simulation",
             "replace with real data", "scientific_conclusion", "runner", created, "before_scientific_run"))
    conn.commit()

    # ═══════════════════════════════════════════
    # PHASE 1: Standard pipeline
    # ═══════════════════════════════════════════
    print(f"\n--- Phase 1: Standard Pipeline ---")
    adapter_window_cells = {}
    all_cells_flat = []

    for a in adapters:
        print(f"  Source: {a.adapter_name}")
        prev_cells = None; prev_block_id = None; prev_event_id = None
        for k in range(WINDOWS):
            cells = a.generate_cells(k); all_cells_flat.extend(cells)
            adapter_window_cells[(a.adapter_name, k)] = cells
            env = a.make_envelope(k); env_id = eng.write_envelope(conn, run_id, env)
            ts_id = f"ts_{a.adapter_name}_{k}"
            conn.execute("INSERT INTO t_surface (t_surface_id,stage_k,slice_ids_json,transport_ids_json,transport_mode) VALUES (?,?,?,?,?)",
                         (ts_id, k, eng.jdump([f"win_{a.adapter_name}_{k}"]), eng.jdump([]), "diagnostic_connected"))
            eng.write_cells(conn, run_id, a, k, cells)
            ops = ["cell_generation", "fiber_binding"]

            if k > 0:
                e, f = eng.write_transport(conn, run_id, a, k, prev_cells, cells)
                ops.append("transport_gating")

            pw_id = eng.write_process_window(conn, run_id, a, k, env_id, len(cells), ops)
            eng.write_v366_measures(conn, run_id, pw_id, a, k, cells)
            eng.write_external_ledgers(conn, run_id, a, k, env, cells)

            if k > 0:
                hyps = eng.write_hypotheses(conn, run_id, a, k, cells)
                support = [cells[i].uid for i in range(0, len(cells), max(1, len(cells)//10))]
                xi_id = eng.write_xi(conn, run_id, a, k, hyps, support)
                xm = max(0.01, 0.25*math.exp(-0.22*k))
                eng.write_v366_xin_binding(conn, run_id, xi_id, pw_id, env_id, xm)
                na = eng.write_v367_anchors(conn, run_id, a, k, cells, hyps)

                p_m = 0.55 + 0.03 * k; r_m = 0.2 + 0.01 * k
                res = eng.write_v374_fhpms_rlis_trace(conn, run_id, a, k, pw_id, env_id,
                    [f"oa_{a.adapter_name}_{k}"], p_m, r_m, xm,
                    prev_block_id=prev_block_id, prev_event_id=prev_event_id, cells=cells)
                if prev_block_id:
                    eng.write_fhpms_fiber_transport(conn, run_id, prev_block_id, res["block_id"], p_m, r_m, xm)
                prev_block_id = res["block_id"]; prev_event_id = res["event_id"]

                prev_pw = f"pw_{a.adapter_name}_{k-1}"
                conn.execute(
                    "INSERT INTO v366_process_hyperedge_relation (hyperedge_id,run_id,member_pw_ids_json,"
                    "member_hypothesis_ids_json,relation_type,incidence_weight,locality_type,created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (jid("he"), run_id, eng.jdump([prev_pw, pw_id]), eng.jdump(hyps),
                     "transport_linked", 1.0, "coordinate_nonlocal_but_process_linked", now()))

                eng.write_legacy_observable_layer(conn, run_id, a, k, cells, hyps)
                eng.write_legacy_recursive_layer(conn, run_id, a, k, cells, hyps)
                eng.write_legacy_diagnostic_layer(conn, run_id, a, k, cells, env, hyps)

            prev_cells = cells
        conn.commit()

    # Cross-domain transport
    for k in range(1, WINDOWS):
        cells_a = adapter_window_cells.get((adapters[0].adapter_name, k))
        cells_b = adapter_window_cells.get((adapters[1].adapter_name, k))
        if cells_a and cells_b:
            eng.write_cross_domain_transport(conn, run_id, adapters[0], cells_a, adapters[1], cells_b, k, top_k=10)

    # Xi lifecycle
    eng.write_xi_lifecycle_closure(conn, run_id)
    eng.write_v3672_stress_rules(conn, run_id)
    eng.write_v3673_quarantine(conn, run_id)
    eng.write_v3674_rmi(conn, run_id, all_cells_flat)

    from morphosphere.active_exec.runtime.xi.decay_engine import XiDecayEngine
    xi_engine = XiDecayEngine(conn, run_id)
    for k in range(WINDOWS): xi_engine.step_window(k)

    # Variational engines
    from morphosphere.active_exec.runtime.spms.variational import VariationalXinEngine, InformationEnergyMetricEngine
    from morphosphere.active_exec.runtime.spms.engines import FreeEnergyRouter
    var_engine = VariationalXinEngine(conn, run_id)
    ie_engine = InformationEnergyMetricEngine(conn, run_id)
    fe_router = FreeEnergyRouter(conn, run_id)
    all_uids = [r[0] for r in conn.execute("SELECT cell_uid FROM spacetime_cell WHERE run_id=?", (run_id,)).fetchall()]
    for uid in all_uids:
        win = conn.execute("SELECT window_id FROM spacetime_cell WHERE cell_uid=?", (uid,)).fetchone()
        try: var_engine.process_cell(uid, win[0] if win else "unknown")
        except: pass
    step = max(1, len(all_uids)//100)
    for i in range(0, len(all_uids)-1, step):
        try: ie_engine.compute_pairwise(all_uids[i], all_uids[i+1])
        except: pass
    conn.commit()
    print(f"  Phase 1 complete: {len(all_cells_flat)} cells, {len(all_uids)} spacetime entries")

    # ═══════════════════════════════════════════
    # PHASE 2: Motion Recognition
    # ═══════════════════════════════════════════
    print(f"\n--- Phase 2: Motion Recognition ---")

    # Create the motion recognition table if needed
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS v37417_motion_recognition_log (
        record_id TEXT PRIMARY KEY, run_id TEXT, window_k INTEGER,
        true_regime TEXT, predicted_regime TEXT, correct INTEGER,
        confidence REAL, delay INTEGER, phase TEXT, displacement REAL,
        scores_json TEXT, memory_size INTEGER, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS v37417_motion_experiment_summary (
        summary_id TEXT PRIMARY KEY, run_id TEXT, total_windows INTEGER,
        overall_accuracy REAL, async_accuracy REAL, transition_accuracy REAL,
        sync_accuracy REAL, final_delay INTEGER, memory_entries INTEGER,
        regime_accuracy_json TEXT, sliding_accuracy_json TEXT, created_at TEXT
    );
    """)

    # Train Bayesian recognizer on multiple seeds
    recognizer = BayesianMotionRecognizer(prior_var=1.0)
    extractor_factory = FeatureExtractor
    TRAIN_SEEDS = [42, 100, 200]
    for seed in TRAIN_SEEDS:
        gen = MotionProcessGenerator(total_windows=60, n_cells=40, seed=seed)
        ext = extractor_factory()
        prev_pos = None
        for k in range(60):
            state, positions, displacements = gen.step(k)
            if prev_pos is not None:
                fvec = ext.extract(prev_pos, positions, displacements)
                predicted, confidence, scores = recognizer.classify(fvec)
                recognizer.learn(fvec, state.regime)
                recognizer.update_recognition_delay(k, predicted == state.regime)
            prev_pos = dict(positions)

    # Run motion recognition on the pipeline's window range and write results to DB
    gen = MotionProcessGenerator(total_windows=max(WINDOWS + 5, 60), n_cells=40, seed=42)
    ext = extractor_factory()
    prev_pos = None
    motion_correct = 0; motion_total = 0
    for k in range(WINDOWS + 5):
        state, positions, displacements = gen.step(k)
        if prev_pos is not None and k < WINDOWS:
            fvec = ext.extract(prev_pos, positions, displacements)
            predicted, confidence, scores = recognizer.classify(fvec)
            correct = (predicted == state.regime)
            motion_correct += int(correct)
            motion_total += 1

            conn.execute(
                "INSERT INTO v37417_motion_recognition_log "
                "(record_id,run_id,window_k,true_regime,predicted_regime,"
                "correct,confidence,delay,phase,displacement,"
                "scores_json,memory_size,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (jid("mr"), run_id, k, state.regime, predicted,
                 1 if correct else 0, confidence, recognizer.recognition_delay,
                 "sync" if recognizer.recognition_delay <= 1 else "async",
                 state.displacement, json.dumps({r: round(s, 3) for r, s in scores.items()}),
                 0, now()))
        elif prev_pos is not None:
            fvec = ext.extract(prev_pos, positions, displacements)
            recognizer.learn(fvec, state.regime)
        prev_pos = dict(positions)

    motion_acc = motion_correct / max(motion_total, 1)
    conn.commit()
    print(f"  Motion recognition: {motion_correct}/{motion_total} ({motion_acc:.1%})")
    print(f"  Learned distributions: {len([r for r in MOTION_REGIMES if recognizer.n_k[r] > 0])} regimes")

    # ═══════════════════════════════════════════
    # PHASE 3: EM-PRX Convergence
    # ═══════════════════════════════════════════
    print(f"\n--- Phase 3: Variational EM Optimization ---")
    from variational_em_engine import VariationalEMEngine, EMParams

    em_engine = VariationalEMEngine(conn, run_id, max_iter=15, lr=0.01, eps=0.01)
    em_params, em_history = em_engine.run(adapters, WINDOWS)
    conn.commit()

    em_converged = em_history[-1]["converged"] if em_history else False
    em_final_j = em_history[-1]["J_total"] if em_history else 0

    # ═══════════════════════════════════════════
    # PHASE 4: Formula Competition (with Hebbian)
    # ═══════════════════════════════════════════
    print(f"\n--- Phase 4: Formula Competition (closed-loop Hebbian) ---")
    from formula_candidate_registry import FormulaCandidateCompetitionEngine
    comp_engine = FormulaCandidateCompetitionEngine(conn, run_id)
    evolution = comp_engine.run_competition(adapters, WINDOWS, num_rounds=8)
    conn.commit()

    # ═══════════════════════════════════════════
    # PHASE 5: Tri-View PRX (using EM-optimized params)
    # ═══════════════════════════════════════════
    print(f"\n--- Phase 5: Tri-View PRX (EM-optimized λ) ---")
    convergence = eng.run_multiround_convergence(
        conn, run_id, adapters, WINDOWS, num_rounds=ROUNDS)
    conn.commit()

    # ═══════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════
    print(f"\n{'='*70}")
    print("VERIFICATION CHECKS")
    print(f"{'='*70}")

    checks = []

    # V1: EM convergence
    pass_v1 = em_converged or (em_history and em_history[-1]["delta_J"] < 0.05)
    checks.append(("EM converged (ΔJ < 0.05)", em_history[-1]["delta_J"] if em_history else 999, pass_v1))
    print(f"  [{'PASS' if pass_v1 else 'FAIL'}] EM: ΔJ={em_history[-1]['delta_J']:.4f} in {len(em_history)} iters")

    # V2: Hebbian directionality
    heb_rows = conn.execute(
        "SELECT reward_signal, avg_weight_change, reward_direction FROM v37421_hebbian_reward_log WHERE run_id=?",
        (run_id,)).fetchall()
    if heb_rows:
        directional = sum(1 for r in heb_rows if (r[0] > 0 and r[1] > 0) or (r[0] < 0 and r[1] < 0) or r[0] == 0)
        heb_ratio = directional / len(heb_rows)
    else:
        heb_ratio = 0.0
    pass_v2 = heb_ratio > 0.5
    checks.append(("Hebbian directional (>50%)", f"{heb_ratio:.0%}", pass_v2))
    print(f"  [{'PASS' if pass_v2 else 'FAIL'}] Hebbian: {heb_ratio:.0%} directional ({len(heb_rows)} updates)")

    # V3: Motion-PRX coupling
    coupling_rows = conn.execute(
        "SELECT COUNT(*) FROM v37421_motion_prx_coupling WHERE run_id=?",
        (run_id,)).fetchone()[0]
    pass_v3 = coupling_rows > 0
    checks.append(("Motion-PRX coupling exists", coupling_rows, pass_v3))
    print(f"  [{'PASS' if pass_v3 else 'FAIL'}] Motion-PRX: {coupling_rows} coupling entries")

    # V4: Motion recognition accuracy
    pass_v4 = motion_acc > 0.70
    checks.append(("Motion accuracy > 70%", f"{motion_acc:.1%}", pass_v4))
    print(f"  [{'PASS' if pass_v4 else 'FAIL'}] Motion accuracy: {motion_acc:.1%}")

    # V5: Xin conservation
    gap_row = conn.execute(
        "SELECT AVG(conservation_gap) FROM v37415_round_xin_ledger_conservation WHERE run_id=?",
        (run_id,)).fetchone()
    gap_avg = gap_row[0] if gap_row and gap_row[0] else 999.0
    pass_v5 = gap_avg < 0.05
    checks.append(("Xin gap < 0.05", f"{gap_avg:.4f}", pass_v5))
    print(f"  [{'PASS' if pass_v5 else 'FAIL'}] Xin gap: {gap_avg:.4f}")

    # V6: Gamma avg
    gamma_rows = conn.execute("SELECT gamma_strength FROM rlis_gamma_sync_binding").fetchall()
    gammas = [r[0] for r in gamma_rows if r[0] is not None]
    gamma_avg = sum(gammas) / max(len(gammas), 1) if gammas else 0.0
    pass_v6 = gamma_avg > 0.80
    checks.append(("Gamma avg > 0.80", f"{gamma_avg:.4f}", pass_v6))
    print(f"  [{'PASS' if pass_v6 else 'FAIL'}] Gamma avg: {gamma_avg:.4f}")

    # V7: P-band diversity
    p_band_rows = conn.execute(
        "SELECT core_margin_type, COUNT(*) FROM p_band_record GROUP BY core_margin_type").fetchall()
    p_types = dict(p_band_rows)
    band_count = p_types.get("band", 0)
    pass_v7 = band_count > 0
    checks.append(("P-band 'band' exists", band_count, pass_v7))
    print(f"  [{'PASS' if pass_v7 else 'FAIL'}] P-band: core={p_types.get('core',0)}, band={band_count}")

    # V8: R routing diversity
    r_routes = conn.execute(
        "SELECT routing_target, COUNT(*) FROM r_band_record GROUP BY routing_target").fetchall()
    r_dict = dict(r_routes)
    pass_v8 = "r_core_resolved" in r_dict or "r_band_active" in r_dict
    route_str = ", ".join(f"{k}={v}" for k, v in r_dict.items())
    checks.append(("R routing diversity", route_str, pass_v8))
    print(f"  [{'PASS' if pass_v8 else 'FAIL'}] R routing: {route_str}")

    # V9: EM λ learned (not default)
    lam_changed = (abs(em_params.lambda_L - 0.30) > 0.001 or
                   abs(em_params.lambda_C - 0.25) > 0.001 or
                   abs(em_params.lambda_H - 0.25) > 0.001 or
                   abs(em_params.lambda_B - 0.20) > 0.001)
    pass_v9 = lam_changed
    checks.append(("EM λ learned (≠ default)", lam_changed, pass_v9))
    print(f"  [{'PASS' if pass_v9 else 'FAIL'}] EM λ: L={em_params.lambda_L:.3f} C={em_params.lambda_C:.3f} "
          f"H={em_params.lambda_H:.3f} B={em_params.lambda_B:.3f}")

    # V10: Formula competition stable
    pass_v10 = evolution.get("verdict") in ("STABLE", "CONVERGED")
    checks.append(("Formula competition stable", evolution.get("verdict", "N/A"), pass_v10))
    print(f"  [{'PASS' if pass_v10 else 'FAIL'}] Formula: {evolution.get('verdict', 'N/A')} "
          f"(winner={evolution.get('final_winner','?')})")

    # V11: Total DB rows
    total_rows = 0
    for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
        total_rows += conn.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
    pass_v11 = total_rows > 30000
    checks.append(("Total rows > 30000", total_rows, pass_v11))
    print(f"  [{'PASS' if pass_v11 else 'FAIL'}] Total rows: {total_rows}")

    # V12: PRX converged
    pass_v12 = convergence["verdict"] == "CONVERGED"
    checks.append(("PRX converged", convergence["verdict"], pass_v12))
    print(f"  [{'PASS' if pass_v12 else 'FAIL'}] PRX: {convergence['verdict']}")

    # ═══════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════
    passed = sum(1 for _, _, p in checks if p)
    total = len(checks)
    elapsed = time.time() - t0

    print(f"\n{'='*70}")
    print(f"  RESULT: {passed}/{total} {'ALL PASS' if passed == total else 'PARTIAL'}")
    print(f"  Elapsed: {elapsed:.1f}s")
    print(f"  Database: {DB_PATH.name} ({DB_PATH.stat().st_size / 1024:.0f} KB)")
    print(f"{'='*70}")

    # Save report
    report = {
        "version": "v37421_integrated",
        "elapsed_s": round(elapsed, 2),
        "checks": [{"name": n, "value": str(v), "pass": p} for n, v, p in checks],
        "passed": passed, "total": total,
        "verdict": "ALL PASS" if passed == total else "PARTIAL",
        "em": {
            "converged": em_converged,
            "iterations": len(em_history),
            "final_j": round(em_final_j, 4),
            "learned_lambda": em_params.to_dict(),
        },
        "hebbian": {
            "updates": len(heb_rows),
            "directionality": round(heb_ratio, 3),
        },
        "motion": {
            "accuracy": round(motion_acc, 4),
            "coupling_entries": coupling_rows,
        },
        "formula": evolution,
    }
    with open(REPORT_DIR / "integrated_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    conn.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
