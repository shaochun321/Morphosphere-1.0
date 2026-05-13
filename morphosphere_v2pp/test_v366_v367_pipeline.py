#!/usr/bin/env python3
"""v36.6 + v36.7 full pipeline verification test."""
import sqlite3, sys
from pathlib import Path

DB = Path(__file__).resolve().parent / "v366_v367_dual_source.db"

def check(name, actual, expected, op="=="):
    if op == "==": ok = actual == expected
    elif op == ">=": ok = actual >= expected
    elif op == ">": ok = actual > expected
    else: ok = False
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: {actual} (expected {op} {expected})")
    return ok

def main():
    if not DB.exists():
        print("ERROR: DB not found. Run run_v366_v367_dual_source.py first."); return 1
    conn = sqlite3.connect(DB)
    rc = lambda t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    passed = failed = 0

    def do(name, actual, expected, op="=="):
        nonlocal passed, failed
        if check(name, actual, expected, op): passed += 1
        else: failed += 1

    print("=== 底层 1:1:1 映射验证 ===")
    do("spacetime_cell", rc("spacetime_cell"), 3000)
    do("information_fiber", rc("information_fiber"), 3000)
    do("spacetime_fiber_binding", rc("spacetime_fiber_binding"), 3000)
    # Verify 1:1 binding
    orphan_fibers = conn.execute("SELECT COUNT(*) FROM information_fiber WHERE cell_uid NOT IN (SELECT cell_uid FROM spacetime_cell)").fetchone()[0]
    do("fiber→cell orphans", orphan_fibers, 0)
    orphan_bindings = conn.execute("SELECT COUNT(*) FROM spacetime_fiber_binding WHERE spacetime_cell_id NOT IN (SELECT cell_uid FROM spacetime_cell)").fetchone()[0]
    do("binding→cell orphans", orphan_bindings, 0)

    print("\n=== 双源对称性验证 ===")
    sph_cells = conn.execute("SELECT COUNT(*) FROM spacetime_cell WHERE cell_uid LIKE 'sph_%'").fetchone()[0]
    c2d_cells = conn.execute("SELECT COUNT(*) FROM spacetime_cell WHERE cell_uid LIKE 'c2d_%'").fetchone()[0]
    do("sphere cells", sph_cells, 1500)
    do("2d cells", c2d_cells, 1500)

    print("\n=== 信号特征差异验证 ===")
    sph_v = conn.execute("SELECT AVG(V_mean) FROM information_fiber WHERE fiber_id LIKE 'fib_sph_%'").fetchone()[0]
    c2d_v = conn.execute("SELECT AVG(V_mean) FROM information_fiber WHERE fiber_id LIKE 'fib_c2d_%'").fetchone()[0]
    do("sphere V_mean in [-70,-60]", -70 < sph_v < -60, True)
    do("2d V_mean in [0,1]", 0 < c2d_v < 1, True)
    do("signal ranges differ", abs(sph_v - c2d_v) > 10, True)

    print("\n=== v36.6 过程窗口验证 ===")
    do("process_window_registry", rc("v366_process_window_registry"), 20)
    do("external_envelope_ref", rc("v366_external_envelope_ref"), 20)
    do("coordinate_hidden_measure", rc("v366_coordinate_hidden_measure_binding"), 400)
    do("semantic_null_guard", rc("v366_semantic_null_guard"), 20)
    do("source_adapter_envelope", rc("v366_source_adapter_envelope"), 2)
    do("process_hyperedge", rc("v366_process_hyperedge_relation"), 18)
    do("xin_carrier_binding", rc("v366_xin_carrier_minimal_binding"), 18)
    # Verify all guards are CLEAN
    dirty = conn.execute("SELECT COUNT(*) FROM v366_semantic_null_guard WHERE guard_verdict != 'CLEAN'").fetchone()[0]
    do("semantic guards all CLEAN", dirty, 0)

    print("\n=== 传输层验证 ===")
    do("transport_current_edge", rc("transport_current_edge"), 5400)
    accepted = conn.execute("SELECT COUNT(*) FROM transport_current_edge WHERE accepted=1").fetchone()[0]
    rejected = conn.execute("SELECT COUNT(*) FROM transport_current_edge WHERE accepted=0").fetchone()[0]
    do("accepted edges > 0", accepted, 0, ">")
    do("rejected edges > 0", rejected, 0, ">")
    do("gating failures match rejected", rc("transport_gating_failure_report"), rejected)

    print("\n=== 假设层验证 ===")
    do("object_hypothesis", rc("object_hypothesis"), 36)
    do("pr_confirmation_graph", rc("pr_confirmation_graph_record"), 36)
    do("pr_transitions (2 per hyp)", rc("pr_graph_transition_record"), 72)
    do("masking_counterevidence (2 per hyp)", rc("masking_counterevidence_record"), 72)

    print("\n=== Xi 残余验证 ===")
    do("xi_residue_record", rc("xi_residue_record"), 18)
    do("xi_decay_policy", rc("xi_decay_policy"), 18)

    print("\n=== v36.7 硬化验证 ===")
    do("v367 anchors >= 300", rc("v367_native_anchor_fact"), 300, ">=")
    anchor_pass = conn.execute("SELECT COUNT(*) FROM v367_anchor_validation_result WHERE overall_verdict='PASS'").fetchone()[0]
    do("all anchors validated PASS", anchor_pass, rc("v367_anchor_validation_result"))
    do("v3672 stress rules", rc("v3672_safe_stress_envelope_rule"), 13)
    do("v3673 quarantine >= 36", rc("v3673_semantic_quarantine_sidecar"), 36, ">=")
    backwrite = conn.execute("SELECT verdict FROM v3673_semantic_backwrite_regression LIMIT 1").fetchone()
    do("semantic backwrite regression", backwrite[0] if backwrite else "MISSING", "PASS")
    do("v3674 RMI H2+H3", rc("v3674_rmi_hash_index"), 100, ">=")
    gate = conn.execute("SELECT overall_verdict FROM v367_release_gate LIMIT 1").fetchone()
    do("v36.7.5 release gate", gate[0] if gate else "MISSING", "PASS")

    print("\n=== 全链路追溯验证 ===")
    # Pick one cell, trace it through the entire pipeline
    sample = conn.execute("SELECT cell_uid FROM spacetime_cell LIMIT 1").fetchone()[0]
    has_fiber = conn.execute("SELECT COUNT(*) FROM information_fiber WHERE cell_uid=?", (sample,)).fetchone()[0]
    has_binding = conn.execute("SELECT COUNT(*) FROM spacetime_fiber_binding WHERE spacetime_cell_id=?", (sample,)).fetchone()[0]
    do(f"cell {sample} → fiber exists", has_fiber, 0, ">")
    do(f"cell {sample} → binding exists", has_binding, 0, ">")

    print(f"\n{'='*50}")
    print(f"TOTAL: {passed} passed, {failed} failed out of {passed+failed}")
    if failed == 0:
        print("ALL TESTS PASSED [OK]")
    conn.close()
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
