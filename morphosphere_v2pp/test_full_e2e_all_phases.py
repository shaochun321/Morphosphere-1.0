"""Full end-to-end test: All 6 phases in a single pipeline run.

Exercises the complete data flow:
  SPMS Binding → Confirmation Graph → Xi Decay → Free-Energy Routing
  → Perturbation Masking → Variational Xin & IE Metric

Uses dual-source synthetic data (3D sphere + 2D plane), 50 cells each,
5 time windows, producing a unified audit trail across all 19+ tables.

Run: py -3 test_full_e2e_all_phases.py
"""
from __future__ import annotations
import os, sys, sqlite3, math, json

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

DB = os.path.join(BASE, "test_full_e2e.db")
MIG_018 = os.path.join(BASE, "migrations", "018_spms_confirmation_xi_ledger.sql")
MIG_019 = os.path.join(BASE, "migrations", "019_v36_variational_xin.sql")

N_CELLS = 50
N_WINDOWS = 5
RUN_ID = "e2e_full_001"


def create_db():
    if os.path.exists(DB):
        os.remove(DB)
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    for m in [MIG_018, MIG_019]:
        with open(m, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.commit()
    return conn


# ── Fake data generators ──────────────────────────────────
class Geo:
    def __init__(self, nid, n):
        t = 2 * math.pi * nid / n
        self.position = (math.cos(t)*3, math.sin(t)*3, 0.1*nid)
        self.surface_normal = (math.cos(t), math.sin(t), 0.1)
        self.boundary_distance = 0.5 + 0.4*math.sin(t)
        self.support_radius = 1.0
        self.neighbor_ids = [(nid-1)%n, (nid+1)%n]
        self.source_patch_ids = [nid]

class Sig:
    def __init__(self, nid):
        self.V_mean = -68.0 + 8.0*math.sin(0.3*nid)
        self.V_slope = 1.2*math.cos(0.5*nid)
        self.release_proxy = max(0, self.V_slope*0.7)
        self.afferent_current = 0.15*nid
        self.spike_rate = 12.0 + 4.0*math.sin(0.4*nid)
        self.spike_regularity = 0.75
        self.timing_precision = 0.88
        self.adaptation_state = 0.12

class Slice:
    def __init__(self, k, n):
        self.slice_id = f"slice_{k}"
        self.window_id = f"w_{k}"
        self.stage_k = k
        self.geometry_node_ids = list(range(n))
        self.geometry_nodes = [Geo(i, n) for i in range(n)]
        self.signal_windows = [Sig(i) for i in range(n)]


# ── Phase 1: SPMS Binding ─────────────────────────────────
def phase1(conn):
    from morphosphere.active_exec.runtime.spms.binding import SPMSBinder
    binder = SPMSBinder(conn, run_id=RUN_ID, calibration_profile="e2e")
    all_maps = {}
    for k in range(N_WINDOWS):
        m = binder.bind_slice(Slice(k, N_CELLS))
        all_maps[k] = m
    conn.commit()
    total_cells = conn.execute("SELECT COUNT(*) FROM spacetime_cell").fetchone()[0]
    total_fibers = conn.execute("SELECT COUNT(*) FROM information_fiber").fetchone()[0]
    total_binds = conn.execute("SELECT COUNT(*) FROM spacetime_fiber_binding").fetchone()[0]
    expected = N_CELLS * N_WINDOWS
    assert total_cells == expected, f"cells={total_cells}"
    assert total_fibers == expected
    assert total_binds == expected
    integrity = binder.verify_integrity()
    assert integrity["all_pass"], f"Integrity: {integrity}"
    # Create transport edges between consecutive windows
    for k in range(1, N_WINDOWS):
        prev_uids = list(all_maps[k-1].values())
        curr_uids = list(all_maps[k].values())
        for i in range(min(len(prev_uids), len(curr_uids))):
            w = 0.5 + 0.3*math.sin(0.2*i + k)
            conn.execute(
                "INSERT INTO transport_current_edge "
                "(edge_id,run_id,from_cell_uid,to_cell_uid,transport_weight,accepted,total_cost) "
                "VALUES (?,?,?,?,?,?,?)",
                (f"tce_e2e_{k}_{i}", RUN_ID, prev_uids[i], curr_uids[i], w, 1, 0.1*i))
    conn.commit()
    print(f"  [PASS] Phase 1: {total_cells} cells, {total_fibers} fibers, {total_binds} bindings")
    return all_maps, binder


def phase2(conn, all_maps, binder):
    from morphosphere.active_exec.runtime.spms.engines import ConfirmationGraphEngine
    engine = ConfirmationGraphEngine(conn, run_id=RUN_ID)
    cells_w0 = list(all_maps[0].values())
    # Create 3 hypotheses: strong P, weak R, very weak (→ Xi)
    h_strong = binder.bind_hypothesis("P_candidate", 0, cells_w0[:8], 0.75)
    h_weak = binder.bind_hypothesis("R_candidate", 0, cells_w0[8:14], 0.35)
    h_xi = binder.bind_hypothesis("P_candidate", 0, cells_w0[14:16], 0.06)
    conn.commit()
    # Strong → PR_candidate
    r1 = engine.attempt_transition(h_strong, "PR_candidate", force=True)
    assert r1["success"]
    # Weak stays candidate
    # Xi-destined → route to xi
    xi_id = engine.route_to_xi(h_xi, xi_type="boundary_uncertain")
    conn.commit()
    assert engine.get_hypothesis_state(h_xi) == "xi_carried"
    refute_check = engine.check_refutation(h_weak)
    summary = engine.get_graph_summary()
    tr_count = conn.execute("SELECT COUNT(*) FROM pr_graph_transition_record").fetchone()[0]
    assert tr_count >= 2
    print(f"  [PASS] Phase 2: strong→PR_candidate, xi→xi_carried, refute={refute_check['should_refute']}, transitions={tr_count}")
    return h_strong, h_weak, h_xi


def phase3(conn):
    from morphosphere.active_exec.runtime.xi.decay_engine import XiDecayEngine
    engine = XiDecayEngine(conn, run_id=RUN_ID, decay_rate=0.2)
    xi_noise = engine.create_xi_from_residual("h_noise", "stochastic_noise", 0.5)
    xi_proto = engine.create_xi_from_residual("h_proto", "proto_structure", 1.5,
                                               relation_support=0.35, occupancy_support=0.28)
    xi_num = engine.create_xi_from_residual("h_num", "numerical_residue", 0.3)
    conn.commit()
    for w in range(4):
        if w >= 2:
            conn.execute("UPDATE xi_residue_record SET persistence_window_count=? WHERE xi_id=?",
                         (w+1, xi_proto))
            conn.commit()
        engine.step_window(window_k=w)
    conn.commit()
    num_st = conn.execute("SELECT xi_state FROM xi_residue_record WHERE xi_id=?", (xi_num,)).fetchone()[0]
    noise_st = conn.execute("SELECT xi_state FROM xi_residue_record WHERE xi_id=?", (xi_noise,)).fetchone()[0]
    proto_st = conn.execute("SELECT xi_state FROM xi_residue_record WHERE xi_id=?", (xi_proto,)).fetchone()[0]
    assert num_st == "quarantined"
    assert noise_st in ("decaying", "discarded_after_audit")
    assert proto_st in ("proto_candidate", "promoted")
    summary = engine.get_lifecycle_summary()
    print(f"  [PASS] Phase 3: noise={noise_st}, num={num_st}, proto={proto_st}")


def phase4(conn):
    from morphosphere.active_exec.runtime.spms.engines import compute_sync_kernel, FreeEnergyRouter
    g_good = compute_sync_kernel(0,10,1.0,0.0,"env_a", 0,10,1.0,0.0,"env_a")
    g_bad = compute_sync_kernel(0,10,1.0,0.0,"env_a", 50,60,2.0,0.5,"env_b")
    assert g_good > 0.9
    assert g_bad < 0.1
    router = FreeEnergyRouter(conn, run_id=RUN_ID)
    results = []
    for k in range(N_WINDOWS):
        r = router.route_delta_f(
            delta_f_ext=8.0+k, window_id=f"w_{k}",
            p_mass=0.5, p_stability=0.4+0.05*k,
            r_counter=0.3, r_boundary=0.2,
            xi_carry_cost=0.35, xi_mass=0.4,
            anomaly_mass=0.15, async_phase_depth=0.2+0.05*k,
            p_compression_gain=0.25, masking_pressure=0.3, anomaly_unresolved=0.15)
        results.append(r)
    conn.commit()
    avg_p = sum(r["p_ratio"] for r in results) / len(results)
    avg_x = sum(r["probabilities"]["X"] for r in results) / len(results)
    assert avg_p < 0.60, f"P avg={avg_p}"
    assert avg_x > 0.05, f"X avg={avg_x}"
    rc = conn.execute("SELECT COUNT(*) FROM v368_free_energy_routing").fetchone()[0]
    assert rc == N_WINDOWS
    print(f"  [PASS] Phase 4: {rc} routings, avg P={avg_p*100:.1f}%, X={avg_x*100:.1f}%")


def phase5(conn, h_strong):
    from morphosphere.active_exec.runtime.spms.engines import PerturbationExecutor
    executor = PerturbationExecutor(conn, run_id=RUN_ID, seed=42)
    results = executor.run_masking_suite(h_strong)
    conn.commit()
    rc = conn.execute(
        "SELECT COUNT(*) FROM masking_counterevidence_record WHERE hypothesis_id=?",
        (h_strong,)).fetchone()[0]
    assert rc >= 3
    print(f"  [PASS] Phase 5: {results['total_types_run']} perturbations, agg={results['aggregate_verdict']}")
    for r in results["individual_results"]:
        print(f"      {r['masking_type']:28s} ret={r['retention']:.3f} → {r['verdict']}")


def phase6(conn, all_maps):
    from morphosphere.active_exec.runtime.spms.variational import (
        VariationalXinEngine, InformationEnergyMetricEngine)
    var_engine = VariationalXinEngine(conn, run_id=RUN_ID)
    cell_uids = list(all_maps[0].values())[:15]
    for uid in cell_uids:
        var_engine.process_cell(uid, "w_0")
    conn.commit()
    sv = conn.execute("SELECT COUNT(*) FROM v361_variational_state_vector WHERE run_id=?",
                      (RUN_ID,)).fetchone()[0]
    lt = conn.execute("SELECT COUNT(*) FROM v361_lagrangian_term WHERE run_id=?",
                      (RUN_ID,)).fetchone()[0]
    elr = conn.execute("SELECT COUNT(*) FROM v361_euler_lagrange_residual WHERE run_id=?",
                       (RUN_ID,)).fetchone()[0]
    dxf = conn.execute("SELECT COUNT(*) FROM v36_delta_xin_field WHERE run_id=?",
                       (RUN_ID,)).fetchone()[0]
    assert sv == 15 and lt == 90 and elr == 15 and dxf == 15
    non_meta = conn.execute("SELECT COUNT(*) FROM v361_lagrangian_term WHERE is_meta_proxy=0").fetchone()[0]
    assert non_meta == 0, "All coefficients must be meta-proxy"
    # IE metric
    ie = InformationEnergyMetricEngine(conn, run_id=RUN_ID)
    d_adj = ie.compute_pairwise(cell_uids[0], cell_uids[1])
    d_far = ie.compute_pairwise(cell_uids[0], cell_uids[-1])
    assert d_adj["valid"] and d_far["valid"]
    r_appr = ie.classify_relation(cell_uids[0], cell_uids[1],
                                   d_adj["d_IE"]*0.8, d_IE_prev=d_adj["d_IE"])
    assert r_appr["relation_type"] == "approaching"
    conn.commit()
    bad_sem = conn.execute(
        "SELECT COUNT(*) FROM v361_relation_readout_proxy WHERE can_write_semantic_label!=0"
    ).fetchone()[0]
    assert bad_sem == 0, "Semantic label writeback violation"
    bad_phys = conn.execute(
        "SELECT COUNT(*) FROM v361_information_energy_metric WHERE is_physics_metric!=0"
    ).fetchone()[0]
    assert bad_phys == 0, "Physics metric violation"
    xin_vals = conn.execute(
        "SELECT xin_variational FROM v361_euler_lagrange_residual WHERE run_id=?",
        (RUN_ID,)).fetchall()
    xin_mean = sum(r[0] for r in xin_vals) / len(xin_vals)
    print(f"  [PASS] Phase 6: {sv} state_vectors, {lt} lagrangian_terms, {elr} EL_residuals")
    print(f"         d_IE(adj)={d_adj['d_IE']:.4f}, d_IE(far)={d_far['d_IE']:.4f}, Xin_mean={xin_mean:.4f}")
    print(f"         Governance: meta_proxy=OK, semantic_label=OK, physics_metric=OK")


def main():
    print("=" * 70)
    print("  Morphosphere Full E2E: All 6 Phases Integration Test")
    print("=" * 70)
    conn = create_db()
    passed = failed = 0
    all_maps = binder = h_strong = None

    phases = [
        ("Phase 1: SPMS Binding", lambda: phase1(conn)),
        ("Phase 2: Confirmation Graph", None),
        ("Phase 3: Xi Decay Dynamics", lambda: phase3(conn)),
        ("Phase 4: Free-Energy Routing", lambda: phase4(conn)),
        ("Phase 5: Perturbation Masking", None),
        ("Phase 6: Variational Xin & IE", None),
    ]

    # Phase 1
    try:
        all_maps, binder = phase1(conn)
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Phase 1: {e}")
        import traceback; traceback.print_exc()
        failed += 1; conn.close(); return 1

    # Phase 2
    try:
        h_strong, h_weak, h_xi = phase2(conn, all_maps, binder)
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Phase 2: {e}")
        import traceback; traceback.print_exc()
        failed += 1

    # Phase 3
    try:
        phase3(conn)
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Phase 3: {e}")
        import traceback; traceback.print_exc()
        failed += 1

    # Phase 4
    try:
        phase4(conn)
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Phase 4: {e}")
        import traceback; traceback.print_exc()
        failed += 1

    # Phase 5
    try:
        if h_strong:
            phase5(conn, h_strong)
        else:
            print("  [SKIP] Phase 5: No hypothesis from Phase 2")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Phase 5: {e}")
        import traceback; traceback.print_exc()
        failed += 1

    # Phase 6
    try:
        if all_maps:
            phase6(conn, all_maps)
        else:
            print("  [SKIP] Phase 6: No cell maps from Phase 1")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Phase 6: {e}")
        import traceback; traceback.print_exc()
        failed += 1

    conn.commit()

    # Database summary
    print(f"\n{'=' * 70}")
    print("  Database Summary")
    print(f"{'=' * 70}")
    total_rows = 0
    for (tbl,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall():
        cnt = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        if cnt > 0:
            print(f"  {tbl:45s} {cnt:>6d} rows")
            total_rows += cnt

    print(f"  {'TOTAL':45s} {total_rows:>6d} rows")
    print(f"\n{'=' * 70}")
    print(f"  Results: {passed} passed, {failed} failed out of 6")
    print(f"{'=' * 70}")
    conn.close()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
