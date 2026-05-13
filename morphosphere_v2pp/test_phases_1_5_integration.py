"""End-to-end integration test for Phases 1-5.

Tests the complete pipeline:
  Phase 1: SPMS Binding (PreNeural -> spacetime_cell + fiber + binding)
  Phase 2: P/R Confirmation Graph (9-node state machine)
  Phase 3: Xi Decay Dynamics (lifecycle management)
  Phase 4: Ledger Free-Energy Routing (softmax decomposition)
  Phase 5: Perturbation Executor (8 masking types)

Run: python test_phases_1_5_integration.py
"""
from __future__ import annotations
import os, sys, sqlite3, math, json

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "src")
sys.path.insert(0, SRC)

DB_PATH = os.path.join(BASE, "test_phases_1_5.db")
MIGRATION = os.path.join(BASE, "migrations", "018_spms_confirmation_xi_ledger.sql")


def create_test_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    with open(MIGRATION, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def make_test_slice(n_nodes=30, stage_k=0, window_id="w_0"):
    class FakeGeo:
        def __init__(self, nid):
            theta = 2 * math.pi * nid / n_nodes
            self.position = (math.cos(theta), math.sin(theta), 0.1 * nid)
            self.surface_normal = (0, 0, 1)
            self.boundary_distance = abs(math.sin(theta))
            self.support_radius = 1.0
            self.neighbor_ids = [(nid - 1) % n_nodes, (nid + 1) % n_nodes]
            self.source_patch_ids = [nid]

    class FakeSig:
        def __init__(self, nid):
            self.V_mean = -70.0 + 5.0 * math.sin(0.1 * nid)
            self.V_slope = 0.5 * math.cos(0.2 * nid)
            self.release_proxy = max(0, self.V_slope)
            self.afferent_current = 0.1 * nid
            self.spike_rate = 10.0 + 2.0 * math.sin(0.3 * nid)
            self.spike_regularity = 0.8
            self.timing_precision = 0.9
            self.adaptation_state = 0.1

    class FakeSlice:
        def __init__(self):
            self.slice_id = f"slice_{stage_k}"
            self.window_id = window_id
            self.stage_k = stage_k
            self.geometry_node_ids = list(range(n_nodes))
            self.geometry_nodes = [FakeGeo(i) for i in range(n_nodes)]
            self.signal_windows = [FakeSig(i) for i in range(n_nodes)]

    return FakeSlice()


# ============================================================
# Phase 1: SPMS Binding
# ============================================================
def test_phase1_spms_binding(conn):
    from morphosphere.active_exec.runtime.spms.binding import SPMSBinder
    binder = SPMSBinder(conn, run_id="test_run_001", calibration_profile="test")
    slice0 = make_test_slice(n_nodes=30, stage_k=0, window_id="w_0")
    slice1 = make_test_slice(n_nodes=30, stage_k=1, window_id="w_1")
    map0 = binder.bind_slice(slice0)
    map1 = binder.bind_slice(slice1)
    conn.commit()

    sc = conn.execute("SELECT COUNT(*) FROM spacetime_cell").fetchone()[0]
    fb = conn.execute("SELECT COUNT(*) FROM information_fiber").fetchone()[0]
    bd = conn.execute("SELECT COUNT(*) FROM spacetime_fiber_binding").fetchone()[0]
    assert sc == 60, f"spacetime_cell={sc}"
    assert fb == 60, f"information_fiber={fb}"
    assert bd == 60, f"spacetime_fiber_binding={bd}"

    integrity = binder.verify_integrity()
    assert integrity["all_pass"], f"Integrity failed: {integrity}"
    print(f"  [PASS] Phase 1: {sc} cells, {fb} fibers, {bd} bindings, integrity=OK")
    return map0, map1


# ============================================================
# Phase 2: Confirmation Graph
# ============================================================
def test_phase2_confirmation_graph(conn):
    from morphosphere.active_exec.runtime.spms.binding import SPMSBinder
    from morphosphere.active_exec.runtime.spms.engines import ConfirmationGraphEngine

    binder = SPMSBinder(conn, run_id="test_run_001")
    engine = ConfirmationGraphEngine(conn, run_id="test_run_001")

    cells = conn.execute("SELECT cell_uid FROM spacetime_cell WHERE stage_k=0 LIMIT 10").fetchall()
    cell_uids = [r[0] for r in cells]

    h_p = binder.bind_hypothesis("P_candidate", 0, cell_uids[:5], 0.8)
    h_r = binder.bind_hypothesis("R_candidate", 0, cell_uids[5:], 0.3)
    h_weak = binder.bind_hypothesis("P_candidate", 0, cell_uids[:2], 0.05)
    conn.commit()

    r1 = engine.attempt_transition(h_p, "PR_candidate", force=True)
    assert r1["success"], f"P->PR failed: {r1}"

    r2 = engine.attempt_transition(h_weak, "PR_candidate", force=True)
    xi_id = engine.route_to_xi(h_weak, xi_type="boundary_uncertain")
    conn.commit()

    state = engine.get_hypothesis_state(h_weak)
    assert state == "xi_carried", f"Expected xi_carried, got {state}"

    refute = engine.check_refutation(h_r)
    summary = engine.get_graph_summary()
    print(f"  [PASS] Phase 2: P->PR_candidate, weak->xi_carried, refute={refute['should_refute']}, summary={summary}")
    return h_p, h_r


# ============================================================
# Phase 3: Xi Decay
# ============================================================
def test_phase3_xi_decay(conn):
    from morphosphere.active_exec.runtime.xi.decay_engine import XiDecayEngine
    engine = XiDecayEngine(conn, run_id="test_run_001", decay_rate=0.2)

    xi_noise = engine.create_xi_from_residual("hyp_noise", "stochastic_noise", 0.5)
    xi_memory = engine.create_xi_from_residual("hyp_mem", "unresolved_memory", 2.0,
                                                relation_support=0.3, occupancy_support=0.25)
    xi_proto = engine.create_xi_from_residual("hyp_proto", "proto_structure", 1.5,
                                               relation_support=0.4, occupancy_support=0.3)
    xi_num = engine.create_xi_from_residual("hyp_num", "numerical_residue", 0.3)
    conn.commit()

    for w in range(5):
        if w >= 2:
            conn.execute("UPDATE xi_residue_record SET persistence_window_count=? WHERE xi_id=?", (w+1, xi_proto))
            conn.commit()
        engine.step_window(window_k=w)
    conn.commit()

    num_st = conn.execute("SELECT xi_state FROM xi_residue_record WHERE xi_id=?", (xi_num,)).fetchone()[0]
    noise_st = conn.execute("SELECT xi_state FROM xi_residue_record WHERE xi_id=?", (xi_noise,)).fetchone()[0]
    proto_st = conn.execute("SELECT xi_state FROM xi_residue_record WHERE xi_id=?", (xi_proto,)).fetchone()[0]

    assert num_st == "quarantined", f"numerical_residue={num_st}"
    assert noise_st in ("decaying","discarded_after_audit"), f"noise={noise_st}"
    assert proto_st in ("proto_candidate","promoted"), f"proto={proto_st}"

    summary = engine.get_lifecycle_summary()
    print(f"  [PASS] Phase 3: noise={noise_st}, num={num_st}, proto={proto_st}, states={list(summary.keys())}")


# ============================================================
# Phase 4: Ledger Routing
# ============================================================
def test_phase4_ledger_routing(conn):
    from morphosphere.active_exec.runtime.spms.engines import compute_sync_kernel, FreeEnergyRouter

    g_good = compute_sync_kernel(0,10,1.0,0.0,"env_a", 0,10,1.0,0.0,"env_a")
    g_bad = compute_sync_kernel(0,10,1.0,0.0,"env_a", 50,60,2.0,0.5,"env_b")
    assert g_good > 0.9, f"Perfect sync={g_good}"
    assert g_bad < 0.1, f"Mismatch sync={g_bad}"

    router = FreeEnergyRouter(conn, run_id="test_run_001")
    result = router.route_delta_f(
        delta_f_ext=10.0, window_id="w_0",
        p_mass=0.5, p_stability=0.5,
        r_counter=0.3, r_boundary=0.2,
        xi_carry_cost=0.4, xi_mass=0.5,
        anomaly_mass=0.2, async_phase_depth=0.3,
        p_compression_gain=0.3,
        masking_pressure=0.3, anomaly_unresolved=0.2)
    conn.commit()

    pr = result["p_ratio"]
    xr = result["probabilities"]["X"]
    assert pr < 0.6, f"P ratio={pr*100:.1f}%"
    assert xr > 0.05, f"Xi ratio={xr*100:.1f}%"

    probs = result["probabilities"]
    print(f"  [PASS] Phase 4: P={pr*100:.1f}% R={probs['R']*100:.1f}% X={xr*100:.1f}% M={probs['M']*100:.1f}% U={probs['U']*100:.1f}%")


# ============================================================
# Phase 5: Perturbation
# ============================================================
def test_phase5_perturbation(conn):
    from morphosphere.active_exec.runtime.spms.engines import PerturbationExecutor

    executor = PerturbationExecutor(conn, run_id="test_run_001", seed=42)
    hyp = conn.execute("SELECT hypothesis_id FROM object_hypothesis WHERE status='PR_candidate' LIMIT 1").fetchone()
    if not hyp:
        print("  [SKIP] Phase 5: No PR_candidate hypothesis")
        return
    hid = hyp[0]
    results = executor.run_masking_suite(hid)
    conn.commit()

    rc = conn.execute("SELECT COUNT(*) FROM masking_counterevidence_record WHERE hypothesis_id=?", (hid,)).fetchone()[0]
    assert rc >= 3, f"masking records={rc}"

    print(f"  [PASS] Phase 5: {results['total_types_run']} perturbations, aggregate={results['aggregate_verdict']}")
    for r in results["individual_results"]:
        print(f"      {r['masking_type']:28s} ret={r['retention']:.3f} -> {r['verdict']}")


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 65)
    print("  Morphosphere Phases 1-5 Integration Test")
    print("=" * 65)

    conn = create_test_db()
    passed = failed = 0
    tests = [
        ("Phase 1: SPMS Binding", test_phase1_spms_binding),
        ("Phase 2: Confirmation Graph", test_phase2_confirmation_graph),
        ("Phase 3: Xi Decay Dynamics", test_phase3_xi_decay),
        ("Phase 4: Ledger Routing", test_phase4_ledger_routing),
        ("Phase 5: Perturbation Executor", test_phase5_perturbation),
    ]

    for name, fn in tests:
        try:
            fn(conn)
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            import traceback; traceback.print_exc()
            failed += 1

    conn.commit()

    print(f"\n{'=' * 65}")
    print("  Database Summary")
    print(f"{'=' * 65}")
    for (tbl,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        cnt = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        if cnt > 0:
            print(f"  {tbl:45s} {cnt:>6d} rows")

    print(f"\n{'=' * 65}")
    print(f"  Results: {passed} passed, {failed} failed out of {len(tests)}")
    print(f"{'=' * 65}")

    conn.close()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
