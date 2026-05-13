#!/usr/bin/env python3
"""v37.4.17 Multi-Round Formula Candidate Competition Runner.

Runs 8 rounds with 5 candidate formula families (A-E) competing.
Each round evaluates all candidates, selects the best by J[ρ],
and tracks selection evolution across rounds.
"""
from __future__ import annotations
import sqlite3, sys, uuid, json, time, math
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
REPORT_DIR = ROOT / "v37.4.17_formula_competition_reports"
REPORT_DIR.mkdir(exist_ok=True)
DB_PATH = ROOT / "v37417_formula_competition.db"

from morphosphere.active_exec.source_adapters import CellSphereAdapter, Cell2DRealAdapter
import pipeline_engine as eng
from formula_candidate_registry import FormulaCandidateCompetitionEngine, CANDIDATES

def now(): return datetime.now(timezone.utc).isoformat()
def jid(p): return f"{p}_{uuid.uuid4().hex[:8]}"

def main():
    t0 = time.time()
    CELLS = 120; WINDOWS = 12; ROUNDS = 8
    print(f"=== v37.4.17 Formula Candidate Competition ===")
    print(f"Cells/source: {CELLS}, Windows: {WINDOWS}, Candidates: {len(CANDIDATES)}, Rounds: {ROUNDS}")

    if DB_PATH.exists(): DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA foreign_keys=OFF")
    eng.apply_migrations(conn)

    run_id = f"v37417_comp_{uuid.uuid4().hex[:8]}"
    conn.execute(
        "INSERT INTO run_manifest (run_id,rules_version,schema_version,calibration_profile,"
        "execution_mode,cell_count,window_count,created_at,notes,physical_cell_count,"
        "spacetime_cell_count,extra_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id,"v37.4.17","v37.4.17","formula_competition",f"competition_{CELLS}",
         CELLS*2, WINDOWS, now(),
         "v37.4.17: multi-round formula candidate competition A-E",
         CELLS*2, CELLS*2*WINDOWS, eng.jdump({"rounds":ROUNDS,"candidates":5})))
    for k in range(WINDOWS):
        conn.execute("INSERT INTO system_clock_entry (clock_n,run_id,time_s,dt_s,clock_hash,schema_version) VALUES (?,?,?,?,?,?)",
                     (k, run_id, k*0.01, 0.01, f"clock_{k:04d}", "v37.4.17"))

    adapters = [CellSphereAdapter(cell_count=CELLS, seed=42), Cell2DRealAdapter(cell_count=CELLS, seed=137)]
    for a in adapters: eng.register_adapter(conn, run_id, a)

    # Phase 1: Build baseline pipeline
    print("\n--- Phase 1: Baseline Pipeline ---")
    all_cells = []
    for a in adapters:
        prev_cells = None; prev_block_id = None; prev_event_id = None
        for k in range(WINDOWS):
            cells = a.generate_cells(k); all_cells.extend(cells)
            env = a.make_envelope(k); env_id = eng.write_envelope(conn, run_id, env)
            ts_id = f"ts_{a.adapter_name}_{k}"
            conn.execute("INSERT INTO t_surface (t_surface_id,stage_k,slice_ids_json,transport_ids_json,transport_mode) VALUES (?,?,?,?,?)",
                         (ts_id, k, eng.jdump([f"win_{a.adapter_name}_{k}"]), eng.jdump([]), "diagnostic_connected"))
            eng.write_cells(conn, run_id, a, k, cells)
            pw_id = eng.write_process_window(conn, run_id, a, k, env_id, len(cells), ["gen","bind"])
            eng.write_v366_measures(conn, run_id, pw_id, a, k, cells)
            eng.write_external_ledgers(conn, run_id, a, k, env, cells)
            if k > 0:
                eng.write_transport(conn, run_id, a, k, prev_cells, cells)
                hyps = eng.write_hypotheses(conn, run_id, a, k, cells)
                support = [cells[i].uid for i in range(0, len(cells), max(1,len(cells)//10))]
                xi_id = eng.write_xi(conn, run_id, a, k, hyps, support)
                xm = max(0.01, 0.25*math.exp(-0.22*k))
                eng.write_v366_xin_binding(conn, run_id, xi_id, pw_id, env_id, xm)
                eng.write_v367_anchors(conn, run_id, a, k, cells, hyps)
                p_m = 0.55 + 0.03*k; r_m = 0.2 + 0.01*k
                res = eng.write_v374_fhpms_rlis_trace(conn, run_id, a, k, pw_id, env_id,
                    [f"oa_{a.adapter_name}_{k}"], p_m, r_m, xm,
                    prev_block_id=prev_block_id, prev_event_id=prev_event_id, cells=cells)
                if prev_block_id:
                    eng.write_fhpms_fiber_transport(conn, run_id, prev_block_id, res["block_id"], p_m, r_m, xm)
                prev_block_id = res["block_id"]; prev_event_id = res["event_id"]
                from morphosphere.active_exec.runtime.fhpms.writer import FHPMSWriter
                from morphosphere.active_exec.runtime.rlis.ledger_sync import RLISLedgerSync
                fw = FHPMSWriter(conn, run_id); rl = RLISLedgerSync(conn, run_id)
                for sk in range(3):
                    fw.write_process_trace(pw_id, k+sk*0.01, k+(sk+1)*0.01, env_id,
                        [f"b0_{a.adapter_name}_{k}_{sk}"], p_m+0.005*sk, r_m, xm, max(0,1-(p_m+r_m+xm)))
                ev = rl.record_event(k+0.7, env_id, async_phase=k*0.15)
                rl.compute_gamma_sync(ev, pw_id, 0.9-0.03*k)
                if prev_block_id:
                    fw.write_hebbian_weight(prev_block_id, res["block_id"], "shadow_guidance",
                        0.05*p_m, 0.9-0.03*k, True, False)
                fw.write_reprojection_trace(res["block_id"], res["origin_anchor_id"],
                    k, k+1, cells[0].x, cells[0].y, cells[0].z, "audit_frame", 0.3, "audit_coarse")
                eng.write_legacy_observable_layer(conn, run_id, a, k, cells, hyps)
                eng.write_legacy_recursive_layer(conn, run_id, a, k, cells, hyps)
                eng.write_legacy_diagnostic_layer(conn, run_id, a, k, cells, env, hyps)
            prev_cells = cells
    # Cross-domain
    for k in range(1, WINDOWS):
        ca = [a.generate_cells(k) for a in adapters]  # re-generate for consistency
        eng.write_cross_domain_transport(conn, run_id, adapters[0],
            [c for c in all_cells if hasattr(c,'uid') and 'sphere' in getattr(c,'uid','')][:CELLS],
            adapters[1],
            [c for c in all_cells if hasattr(c,'uid') and '2d' in getattr(c,'uid','')][:CELLS], k, top_k=10)
    eng.write_v3672_stress_rules(conn, run_id)
    eng.write_v3673_quarantine(conn, run_id)
    eng.write_xi_lifecycle_closure(conn, run_id)
    conn.commit()
    print("  Baseline pipeline complete.")

    # Phase 2: Formula Competition
    print(f"\n--- Phase 2: {ROUNDS}-Round Formula Competition ---")
    engine = FormulaCandidateCompetitionEngine(conn, run_id)
    summary = engine.run_competition(adapters, WINDOWS, num_rounds=ROUNDS)
    conn.commit()

    # Phase 3: Analysis
    print(f"\n{'='*70}")
    print("FORMULA COMPETITION RESULTS")
    print(f"{'='*70}")
    print(f"  Final winner: {summary['final_winner']} ({CANDIDATES[summary['final_winner']].name})")
    print(f"  Stability: {summary['stability']*100:.0f}%")
    print(f"  Rank volatility: {summary['volatility']:.3f}")
    print(f"  Formula switches: {summary['switches']}")
    print(f"  Convergence round: {summary['convergence_round']}")
    print(f"  Verdict: {summary['verdict']}")

    # J_total evolution per candidate
    print(f"\n  J_total evolution:")
    analysis = summary["analysis"]
    header = "  Round  " + "  ".join(f"  {c:>5s}" for c in sorted(CANDIDATES))
    print(header)
    for r in range(ROUNDS):
        vals = "  ".join(f"{analysis['j_total_evolution'][c][r]:7.3f}" for c in sorted(CANDIDATES))
        winner = analysis["winner_sequence"][r]
        print(f"    {r+1:2d}   {vals}  <- {winner}")

    # Rank evolution
    print(f"\n  Rank evolution:")
    header = "  Round  " + "  ".join(f"  {c:>5s}" for c in sorted(CANDIDATES))
    print(header)
    for r in range(ROUNDS):
        vals = "  ".join(f"{analysis['rank_evolution'][c][r]:7d}" for c in sorted(CANDIDATES))
        print(f"    {r+1:2d}   {vals}")

    # Save report
    elapsed = time.time() - t0
    report = {
        "version": "v37.4.17",
        "elapsed_s": round(elapsed, 2),
        "db_size_kb": round(DB_PATH.stat().st_size / 1024, 1),
        "summary": {k: v for k, v in summary.items() if k != "analysis"},
        "analysis": analysis,
        "candidates": {c: {"name": CANDIDATES[c].name,
                          "lambdas": [CANDIDATES[c].lambda_rlis, CANDIDATES[c].lambda_cm,
                                     CANDIDATES[c].lambda_fhpms, CANDIDATES[c].lambda_bottom]}
                      for c in CANDIDATES},
    }
    with open(REPORT_DIR / "formula_competition_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n  DB: {DB_PATH.stat().st_size/1024:.0f}KB  elapsed: {elapsed:.1f}s")
    print(f"  Report: {REPORT_DIR}")
    conn.close()

if __name__ == "__main__":
    main()
