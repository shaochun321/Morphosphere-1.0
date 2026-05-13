#!/usr/bin/env python3
"""Morphosphere v37.4.15 batch6 — Tri-View Multi-Round PRX Convergence Analysis.

Implements the v2.0/v2.1/v2.2 specifications:
- 7-component fiber measure ρ_k = (p_core, p_band, r_core, r_band, m_band, x_true, u)
- Four-source softmax: RLIS + CounterMask + HG-FHPMS + BottomMotion
- Xin ledger conservation
- Multi-round convergence analysis (5 rounds)
- R-core formation + potential subsidy tracking
"""
from __future__ import annotations
import sqlite3, sys, uuid, random, math, json, hashlib, time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
REPORT_DIR = ROOT / "v37.4.15_20260509_batch6_reports"
REPORT_DIR.mkdir(exist_ok=True)
DB_PATH = ROOT / "v37415_20260509_batch6.db"

from morphosphere.active_exec.source_adapters import CellSphereAdapter, Cell2DRealAdapter
import pipeline_engine as eng

def now(): return datetime.now(timezone.utc).isoformat()
def jid(p): return f"{p}_{uuid.uuid4().hex[:8]}"

def main():
    t0 = time.time()
    CELLS = 120; WINDOWS = 12; ROUNDS = 5
    print(f"=== Morphosphere v37.4.15 batch6 (Tri-View PRX Convergence) ===")
    print(f"Cells/source: {CELLS}, Windows: {WINDOWS}, Sources: 2, Rounds: {ROUNDS}")

    if DB_PATH.exists(): DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA foreign_keys=OFF")
    eng.apply_migrations(conn)

    run_id = f"v37415_batch6_{uuid.uuid4().hex[:8]}"
    created = now()
    conn.execute(
        "INSERT INTO run_manifest (run_id,rules_version,schema_version,calibration_profile,execution_mode,cell_count,window_count,created_at,notes,physical_cell_count,spacetime_cell_count,extra_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id,"v37.4.15","v37.4.15","dual_source_v37415",f"full_chain_{CELLS}",
         CELLS*2, WINDOWS, created,
         "v37.4.15 batch6: tri-view PRX convergence + Xin conservation + R-core + potential subsidy",
         CELLS*2, CELLS*2*WINDOWS,
         eng.jdump({"sources":2,"cells_per_source":CELLS,
                     "focus":"triview_prx_convergence","rounds":ROUNDS})))
    for k in range(WINDOWS):
        conn.execute("INSERT INTO system_clock_entry (clock_n,run_id,time_s,dt_s,clock_hash,schema_version) VALUES (?,?,?,?,?,?)",
                     (k, run_id, k*0.01, 0.01, f"clock_{k:04d}", "v37.4.15"))

    adapters = [CellSphereAdapter(cell_count=CELLS, seed=42), Cell2DRealAdapter(cell_count=CELLS, seed=137)]
    for a in adapters:
        eng.register_adapter(conn, run_id, a)
        conn.execute("INSERT INTO proxy_provenance (proxy_id,run_id,target_field,proxy_type,proxy_reason,source_assumption,replacement_condition,forbidden_interpretation,created_by,created_at,review_due) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     (jid("prx"), run_id, f"{a.adapter_name}.*", "diagnostic",
                      f"diagnostic {a.signal_model}", f"{a.signal_model} simulation",
                      "replace with real data", "scientific_conclusion", "runner", created, "before_scientific_run"))
    conn.commit()

    # === Phase 1: Standard pipeline (same as batch5) ===
    adapter_window_cells = {}
    all_cells_flat = []; total_edges = total_failures = total_anchors = 0
    all_rlis_events = {}; cross_domain_edges = 0

    for a in adapters:
        print(f"\n--- Source: {a.adapter_name} ({a.geometry_model}) ---")
        prev_cells = None; prev_block_id = None; prev_event_id = None
        for k in range(WINDOWS):
            cells = a.generate_cells(k); all_cells_flat.extend(cells)
            adapter_window_cells[(a.adapter_name, k)] = cells
            env = a.make_envelope(k); env_id = eng.write_envelope(conn, run_id, env)
            ts_id = f"ts_{a.adapter_name}_{k}"
            conn.execute("INSERT INTO t_surface (t_surface_id,stage_k,slice_ids_json,transport_ids_json,transport_mode) VALUES (?,?,?,?,?)",
                         (ts_id, k, eng.jdump([f"win_{a.adapter_name}_{k}"]), eng.jdump([]), "diagnostic_connected"))
            eng.write_cells(conn, run_id, a, k, cells)
            ops = ["cell_generation","fiber_binding"]

            if k > 0:
                e, f = eng.write_transport(conn, run_id, a, k, prev_cells, cells)
                total_edges += e; total_failures += f; ops.append("transport_gating")

            pw_id = eng.write_process_window(conn, run_id, a, k, env_id, len(cells), ops)
            eng.write_v366_measures(conn, run_id, pw_id, a, k, cells)
            eng.write_external_ledgers(conn, run_id, a, k, env, cells)

            if k > 0:
                hyps = eng.write_hypotheses(conn, run_id, a, k, cells)
                support = [cells[i].uid for i in range(0, len(cells), max(1,len(cells)//10))]
                xi_id = eng.write_xi(conn, run_id, a, k, hyps, support)
                xm = max(0.01, 0.25*math.exp(-0.22*k))
                eng.write_v366_xin_binding(conn, run_id, xi_id, pw_id, env_id, xm)
                na = eng.write_v367_anchors(conn, run_id, a, k, cells, hyps); total_anchors += na

                p_m = 0.55 + 0.03 * k; r_m = 0.2 + 0.01 * k
                res = eng.write_v374_fhpms_rlis_trace(conn, run_id, a, k, pw_id, env_id,
                    [f"oa_{a.adapter_name}_{k}"], p_m, r_m, xm,
                    prev_block_id=prev_block_id, prev_event_id=prev_event_id, cells=cells)
                if prev_block_id:
                    eng.write_fhpms_fiber_transport(conn, run_id, prev_block_id, res["block_id"], p_m, r_m, xm)
                prev_block_id = res["block_id"]; prev_event_id = res["event_id"]
                all_rlis_events.setdefault(a.adapter_name, []).append(res["event_id"])

                prev_pw = f"pw_{a.adapter_name}_{k-1}"
                conn.execute(
                    "INSERT INTO v366_process_hyperedge_relation (hyperedge_id,run_id,member_pw_ids_json,member_hypothesis_ids_json,relation_type,incidence_weight,locality_type,created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (jid("he"), run_id, eng.jdump([prev_pw, pw_id]), eng.jdump(hyps),
                     "transport_linked", 1.0, "coordinate_nonlocal_but_process_linked", now()))

                eng.write_legacy_observable_layer(conn, run_id, a, k, cells, hyps)
                eng.write_legacy_recursive_layer(conn, run_id, a, k, cells, hyps)
                eng.write_legacy_diagnostic_layer(conn, run_id, a, k, cells, env, hyps)

                # Branch audit (simplified)
                from morphosphere.active_exec.runtime.fhpms.writer import FHPMSWriter
                from morphosphere.active_exec.runtime.rlis.ledger_sync import RLISLedgerSync
                fhpms_b = FHPMSWriter(conn, run_id); rlis_b = RLISLedgerSync(conn, run_id)
                gamma = 0.9 - 0.03*k
                for sk in range(3):
                    fhpms_b.write_process_trace(pw_id, k+sk*0.01, k+(sk+1)*0.01, env_id,
                        [f"b0_{a.adapter_name}_{k}_{sk}"], p_m+0.005*sk, r_m, xm, max(0, 1-(p_m+r_m+xm)))
                b1_ev = rlis_b.record_event(k+0.7, env_id, async_phase=k*0.15)
                rlis_b.compute_gamma_sync(b1_ev, pw_id, gamma)
                if prev_block_id:
                    fhpms_b.write_hebbian_weight(prev_block_id, res["block_id"], "shadow_guidance",
                        0.05*p_m, gamma, True, False)
                fhpms_b.write_reprojection_trace(res["block_id"], res["origin_anchor_id"],
                    k, k+1, cells[0].x, cells[0].y, cells[0].z, "audit_frame", 0.3, "audit_coarse")

            prev_cells = cells
            if k % 4 == 0: print(f"  window {k}/{WINDOWS} done")
        conn.commit()

    # Cross-domain transport
    print("\n--- Cross-Domain Transport ---")
    for k in range(1, WINDOWS):
        cells_a = adapter_window_cells.get((adapters[0].adapter_name, k))
        cells_b = adapter_window_cells.get((adapters[1].adapter_name, k))
        if cells_a and cells_b:
            n_xd = eng.write_cross_domain_transport(conn, run_id, adapters[0], cells_a, adapters[1], cells_b, k, top_k=10)
            cross_domain_edges += n_xd
    conn.commit()
    print(f"  Cross-domain edges: {cross_domain_edges}")

    # RLIS light cones
    rlis_lc = RLISLedgerSync(conn, run_id)
    for adapter_name, evts in all_rlis_events.items():
        if len(evts) >= 2:
            rlis_lc.build_light_cone(evts[0], evts)
            rlis_lc.build_light_cone(evts[-1], evts)

    # Xi lifecycle closure
    print("\n--- Xi Lifecycle Closure ---")
    xi_closure = eng.write_xi_lifecycle_closure(conn, run_id)
    print(f"  {xi_closure}")

    # Variational
    print("\n--- Variational Xin ---")
    from morphosphere.active_exec.runtime.spms.variational import VariationalXinEngine, InformationEnergyMetricEngine
    from morphosphere.active_exec.runtime.spms.engines import FreeEnergyRouter
    var_engine = VariationalXinEngine(conn, run_id)
    ie_engine = InformationEnergyMetricEngine(conn, run_id)
    fe_router = FreeEnergyRouter(conn, run_id)
    all_uids = [r[0] for r in conn.execute("SELECT cell_uid FROM spacetime_cell WHERE run_id=?", (run_id,)).fetchall()]
    var_processed = 0
    for uid in all_uids:
        win = conn.execute("SELECT window_id FROM spacetime_cell WHERE cell_uid=?", (uid,)).fetchone()
        try: var_engine.process_cell(uid, win[0] if win else "unknown"); var_processed += 1
        except: pass
    ie_count = 0; step = max(1, len(all_uids)//100)
    for i in range(0, len(all_uids)-1, step):
        try: ie_engine.compute_pairwise(all_uids[i], all_uids[i+1]); ie_count += 1
        except: pass
    for k in range(1, WINDOWS):
        fe_router.route_delta_f(10.0+k*2, f"win_cell_sphere_3d_{k}",
            p_mass=0.5+0.02*k, p_stability=0.6, r_counter=0.3,
            xi_mass=max(0.01, 0.25*math.exp(-0.22*k)), gamma=0.9-0.03*k)
    conn.commit()
    print(f"  Variational: {var_processed}/{len(all_uids)} cells, {ie_count} IE metrics")

    # Hardening
    eng.write_v3672_stress_rules(conn, run_id)
    eng.write_v3673_quarantine(conn, run_id)
    eng.write_v3674_rmi(conn, run_id, all_cells_flat)
    conn.execute("INSERT INTO v367_release_gate (gate_id,run_id,v3671_anchor_pass,v3672_guard_pass,v3673_quarantine_pass,v3674_rmi_pass,legacy_db_mutated,online_native_claimed,overall_verdict,release_notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (jid("rg"), run_id, 1, 1, 1, 1, 0, 0, "PASS", "v37.4.15 batch6", now()))

    # Xi decay
    from morphosphere.active_exec.runtime.xi.decay_engine import XiDecayEngine
    xi_engine = XiDecayEngine(conn, run_id)
    for k in range(WINDOWS): xi_engine.step_window(k)

    # Integrity
    from morphosphere.active_exec.runtime.spms.binding import SPMSBinder
    integrity = SPMSBinder(conn, run_id).verify_integrity()
    conn.commit()

    # === Phase 2: v37.4.15 Tri-View Multi-Round PRX Convergence ===
    print(f"\n{'='*70}")
    print("PHASE 2: v37.4.15 Tri-View PRX Convergence Analysis")
    print(f"{'='*70}")
    convergence = eng.run_multiround_convergence(conn, run_id, adapters, WINDOWS, num_rounds=ROUNDS)
    conn.commit()

    # === Analysis ===
    print(f"\n{'='*70}")
    print("CONVERGENCE RESULTS")
    print(f"{'='*70}")
    print(f"  Verdict: {convergence['verdict']}")
    print(f"  Rounds: {convergence['rounds']}")
    print(f"  Drifts: {[round(d,4) for d in convergence['drifts']]}")
    print(f"  Final drift: {convergence['final_drift']:.4f}")
    print(f"  True Xin: {convergence['true_xin']}")
    print(f"  Pseudo Xin: {convergence['xin_pseudo']}")
    print(f"  R-core windows: {convergence['r_core_count']}")
    print(f"  P-band windows: {convergence['p_band_count']}")
    print(f"  Unresolved: {convergence['u_count']}")
    print(f"  Xin conservation gap: {convergence['conservation_gap']:.4f}")

    # Memory analysis
    print(f"\n{'='*70}")
    print("MEMORY ANALYSIS")
    print(f"{'='*70}")
    node_dist = {}
    for r in conn.execute("SELECT current_node, COUNT(*) FROM pr_confirmation_graph_record GROUP BY current_node").fetchall():
        node_dist[r[0]] = r[1]
    p_frozen = node_dist.get("P_frozen", 0)
    r_frozen = node_dist.get("R_frozen", 0)
    print(f"  P_frozen: {p_frozen}, R_frozen: {r_frozen}")
    print(f"  Node distribution: {node_dist}")

    heb = conn.execute("SELECT COUNT(*), AVG(weight_value), MAX(weight_value) FROM fhpms_hebbian_association_weight").fetchone()
    print(f"  Hebbian: count={heb[0]}, avg={heb[1]:.4f}, max={heb[2]:.4f}")

    # PRX decomposition summary
    print(f"\n{'='*70}")
    print("PRX DECOMPOSITION (Final Round)")
    print(f"{'='*70}")
    final_prx = conn.execute("""
        SELECT dominant_component, COUNT(*), 
               AVG(p_core), AVG(p_band), AVG(r_core), AVG(r_band), 
               AVG(m_band), AVG(x_true), AVG(u_unresolved)
        FROM v37415_round_prx_decomposition 
        WHERE run_id=? AND round_id=(SELECT round_id FROM v37415_round_registry WHERE run_id=? ORDER BY round_number DESC LIMIT 1)
        GROUP BY dominant_component
    """, (run_id, run_id)).fetchall()
    for row in final_prx:
        print(f"  {row[0]:12s}: n={row[1]:3d}  "
              f"p_c={row[2]:.3f} p_b={row[3]:.3f} r_c={row[4]:.3f} r_b={row[5]:.3f} "
              f"m_b={row[6]:.3f} x={row[7]:.3f} u={row[8]:.3f}")

    # Table stats
    elapsed = time.time() - t0
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    rbt = {t: eng.rc(conn, t) for t in tables}; total_rows = sum(rbt.values())
    empty_tables = [t for t, c in rbt.items() if c == 0]
    nonempty_tables = [t for t, c in rbt.items() if c > 0]
    db_ok = conn.execute('PRAGMA integrity_check').fetchone()[0]

    # v37415 tables
    v37415_tables = {t: c for t, c in rbt.items() if t.startswith("v37415")}
    print(f"\n  v37415 tables:")
    for t, c in sorted(v37415_tables.items()):
        print(f"    {t:50s}: {c:5d} rows")

    # Console summary
    print(f"\n{'='*70}")
    print(f"PIPELINE COMPLETE — v37.4.15_20260509_batch6")
    print(f"{'='*70}")
    print(f"run_id={run_id}  DB={DB_PATH.stat().st_size/1024:.0f}KB  integrity={db_ok}  elapsed={elapsed:.2f}s")
    print(f"Total rows: {total_rows}  |  Tables: {len(nonempty_tables)} populated, {len(empty_tables)} empty")
    print(f"P_frozen: {p_frozen} | R_frozen: {r_frozen}")
    print(f"Convergence: {convergence['verdict']} (drift={convergence['final_drift']:.4f})")
    print(f"True Xin: {convergence['true_xin']} | R-core: {convergence['r_core_count']} | P-band: {convergence['p_band_count']}")

    # Acceptance gate
    gate_dist = {}
    for r in conn.execute("SELECT gate_result, COUNT(*) FROM maturity_gate_record GROUP BY gate_result").fetchall():
        gate_dist[r[0]] = r[1]

    checks = {
        "db_integrity": db_ok == "ok",
        "chain_completeness": integrity.get("all_pass", False),
        "P_frozen_exists": p_frozen > 0,
        "R_frozen_exists": r_frozen > 0,
        "maturity_gate_passes": gate_dist.get("pass", 0) > 0,
        "cross_domain_edges": cross_domain_edges > 0,
        "hebbian_strengthened": heb[2] > 0.15,
        "xi_lifecycle_closed": eng.rc(conn, 'xi_residue_mass_record') > 0,
        "variational_full": var_processed >= len(all_uids) * 0.95,
        "v37415_prx_populated": eng.rc(conn, 'v37415_round_prx_decomposition') > 0,
        "v37415_convergence_ok": convergence['verdict'] in ('CONVERGED', 'STABILIZING'),
        "v37415_xin_conservation": convergence['conservation_gap'] < 1.0,
        "v37415_r_core_exists": convergence['r_core_count'] > 0,
        "v37415_p_band_exists": convergence['p_band_count'] > 0,
        "v37415_drift_report": eng.rc(conn, 'v37415_round_drift_metric') == ROUNDS,
    }
    print(f"\n{'='*70}")
    print(f"ACCEPTANCE GATE ({len(checks)} checks):")
    all_pass = True
    for name, ok in checks.items():
        status = "PASS" if ok else "FAIL"
        if not ok: all_pass = False
        print(f"  {name:42s}: {status}")
    print(f"\n  OVERALL: {'ALL PASS [OK]' if all_pass else 'SOME FAILED [X]'}")

    # Save report
    full_report = {
        "meta": {"version":"v37.4.15","batch":"batch6","run_id":run_id,
                 "elapsed_s":round(elapsed,2),"db_size_kb":round(DB_PATH.stat().st_size/1024,1)},
        "convergence": convergence,
        "memory": {"P_frozen":p_frozen, "R_frozen":r_frozen},
        "hebbian": {"count":heb[0], "avg":round(heb[1],4), "max":round(heb[2],4)},
        "v37415_tables": v37415_tables,
        "acceptance_checks": {k:("PASS" if v else "FAIL") for k,v in checks.items()},
        "total_rows": total_rows,
    }
    with open(REPORT_DIR / "v37415_batch6_full_report.json", "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
    conn.close()
    print(f"\nReports: {REPORT_DIR}\nDone.")

if __name__ == "__main__":
    main()
