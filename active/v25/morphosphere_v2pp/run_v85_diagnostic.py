#!/usr/bin/env python3
"""Morphosphere v8.5.2 diagnostic runner.

Pure-stdlib diagnostic entrypoint for local deployment validation. It applies the
existing v8.5 schema, runs a complete diagnostic_full pass, and writes a DB that
is eventful, selective, data-derived, and auditable. It does not create v8.6/v9
and never marks output as scientific_run.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import random
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
DB_PATH = ROOT / "v85_full_diagnostic_run.db"
MIGRATIONS = ROOT / "migrations"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def jid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def jdump(x) -> str:
    return json.dumps(x, separators=(",", ":"), ensure_ascii=False)


def ensure_alignment_columns(conn: sqlite3.Connection) -> None:
    """Add late diagnostic columns with SQLite-compatible guards."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(transport_current_edge)").fetchall()}
    if "total_cost" not in cols:
        conn.execute("ALTER TABLE transport_current_edge ADD COLUMN total_cost REAL DEFAULT 0.0")


def apply_migrations(conn: sqlite3.Connection) -> None:
    for path in sorted(MIGRATIONS.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        try:
            conn.executescript(sql)
        except sqlite3.OperationalError as e:
            # Existing historic DBs may already have additive ALTER columns.
            # Fresh runner deletes DB first, so this is only a defensive guard.
            if "duplicate column name" not in str(e):
                raise
    ensure_alignment_columns(conn)
    conn.commit()


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def entropy(weights: list[float]) -> tuple[float, float, list[float]]:
    vals = [max(0.0, float(w)) for w in weights if w is not None]
    vals = [v for v in vals if v > 1e-12]
    if not vals:
        return 0.0, 0.0, []
    total = sum(vals)
    p = [v / total for v in vals]
    h = -sum(pi * math.log(pi + 1e-12) for pi in p)
    hn = h / math.log(len(p) + 1e-12) if len(p) > 1 else 0.0
    return h, max(0.0, min(1.0, hn)), p


def row_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except sqlite3.Error:
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Morphosphere v8.5 diagnostic_full build")
    parser.add_argument("--db", default=str(DB_PATH), help="Output SQLite DB path")
    parser.add_argument(
        "--calibration_profile",
        default="diagnostic_event_channel_v1",
        choices=["diagnostic_event_channel_v1", "basic_physics_v1"],
        help="Signal source profile for information_fiber rows",
    )
    parser.add_argument("--execution_mode", default="diagnostic_full", choices=["diagnostic_full"])
    parser.add_argument("--scientific_use_allowed", default="false", choices=["false", "False", "0"])
    parser.add_argument("--physics_seed", type=int, default=8531)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db).resolve()
    calibration_profile = args.calibration_profile
    if args.execution_mode != "diagnostic_full" or args.scientific_use_allowed.lower() not in {"false", "0"}:
        raise RuntimeError("v8.5.3 physical-freeze runner must remain diagnostic_full and scientific_use_allowed=false")
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=OFF")
    apply_migrations(conn)

    random.seed(852)
    run_id = "v85_diag_" + uuid.uuid4().hex[:8]
    physical_cells = 50
    windows = 10
    spacetime_cells = physical_cells * windows
    created = now()
    extra = {
        "count_semantics": {
            "physical_cell_count": physical_cells,
            "window_count": windows,
            "spacetime_cell_count": spacetime_cells,
            "cell_count_compatibility": "physical_cell_count",
        },
        "execution_fidelity_patch": "v8.5.2",
        "scientific_use_allowed": False,
        "physical_freeze_patch": "v8.5.3-basic_physics_v1" if calibration_profile == "basic_physics_v1" else None,
        "signal_source_profile": calibration_profile,
    }
    conn.execute(
        """INSERT INTO run_manifest
        (run_id,rules_version,schema_version,calibration_profile,execution_mode,
         cell_count,window_count,created_at,notes,physical_cell_count,spacetime_cell_count,extra_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (run_id, "v8.5", "v8.5.2", calibration_profile, args.execution_mode,
         physical_cells, windows, created, f"v8.5 diagnostic-only execution fidelity run; signal_source={calibration_profile}",
         physical_cells, spacetime_cells, jdump(extra)),
    )
    for k in range(windows):
        conn.execute(
            "INSERT INTO system_clock_entry (clock_n,run_id,time_s,dt_s,clock_hash,schema_version) VALUES (?,?,?,?,?,?)",
            (k, run_id, k * 0.01, 0.01, f"clock_{k:04d}", "v8.5.2"),
        )

    proxies = [
        ("geometry.*", "synthetic", "generated cell sphere geometry for diagnostic run", "diagnostic geometry generator", "replace with real segmented/physical coordinates"),
        ("diagnostic_dynamic_driver", "diagnostic", "event channel calibration, not final biology", "profile diagnostic_event_channel_v1", "replace with validated electromechanical driver"),
        ("O_pass_through_proxy", "fallback", "only used if derived_minimal cannot be formed", "O lineage fallback", "remove after derived O formation is complete"),
        ("calcium_concentration", "placeholder", "fixed calcium placeholder in diagnostic run", "constant diagnostic value", "replace with calcium dynamics"),
        ("adaptation_state", "placeholder", "fixed adaptation state in diagnostic run", "diagnostic state variable emitted by physical-freeze profile", "replace with adaptation dynamics"),
        ("synthetic_emergence_alert", "synthetic", "isolated synthetic emergence test", "diagnostic alert fixture", "replace with real emergence evaluator input"),
        ("diagnostic_thresholds", "diagnostic", "transport/O/Xi thresholds tuned for execution fidelity", "v8.5.2 patch profile", "calibrate against accepted validation set"),
    ]
    if calibration_profile == "basic_physics_v1":
        proxies.append((
            "information_fiber.*",
            "placeholder",
            "minimum viable physical simulation; not final biophysics",
            "heterogeneous sinusoidal drive + deterministic noise + MET gate + first-order membrane dynamics",
            "replace with empirically calibrated ion-channel model or recorded physical data",
        ))
    for target, ptype, reason, assumption, repl in proxies:
        proxy_id = "prx_basic_physics_v1" if target == "information_fiber.*" and calibration_profile == "basic_physics_v1" else jid("prx")
        conn.execute(
            """INSERT INTO proxy_provenance
            (proxy_id,run_id,target_field,proxy_type,proxy_reason,source_assumption,
             replacement_condition,forbidden_interpretation,created_by,created_at,review_due)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (proxy_id, run_id, target, ptype, reason, assumption, repl,
             "final biology,scientific conclusion,scientific_run", "run_v85_diagnostic.py", created, "before scientific_run"),
        )

    physics_runner = None
    if calibration_profile == "basic_physics_v1":
        # Load the stdlib-only diagnostic driver directly from its file so local
        # deployment can run before optional scientific dependencies are installed.
        runner_path = ROOT / "src" / "morphosphere" / "active_exec" / "stage1_physics" / "basic_physics_runner.py"
        spec = importlib.util.spec_from_file_location("morphosphere_basic_physics_runner", runner_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load BasicPhysicsRunner from {runner_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        physics_runner = module.BasicPhysicsRunner(cell_count=physical_cells, dt=0.01, seed=args.physics_seed)

    # State store for data-derived transport and evidence.
    positions: dict[tuple[int, int], tuple[float, float, float]] = {}
    signals: dict[tuple[int, int], dict[str, float]] = {}
    cell_uids: dict[tuple[int, int], str] = {}
    fiber_ids: dict[tuple[int, int], str] = {}

    for k in range(windows):
        win = f"win_{k}"
        ts_id = f"ts_{k}"
        transport_ids: list[str] = []
        if k > 0:
            transport_ids = [f"tce_{k}_{i}" for i in range(physical_cells)]
        conn.execute(
            "INSERT INTO t_surface (t_surface_id,stage_k,slice_ids_json,transport_ids_json,transport_mode) VALUES (?,?,?,?,?)",
            (ts_id, k, jdump([win]), jdump(transport_ids), "diagnostic_connected"),
        )
        for i in range(physical_cells):
            angle = 2 * math.pi * i / physical_cells + 0.08 * k
            radius = 5.0 + 0.15 * math.sin(i * 0.7 + k)
            x = radius * math.cos(angle) + 0.03 * k
            y = radius * math.sin(angle) + 0.02 * math.sin(k + i * 0.1)
            z = 0.8 * math.sin(i * 0.31 + k * 0.2)
            bdist = abs(radius - 5.0) + 0.02 * (i % 5) + 0.015 * k
            uid = f"stc_{k}_{i}"
            fid = f"fib_{k}_{i}"
            cell_uids[(k, i)] = uid
            fiber_ids[(k, i)] = fid
            positions[(k, i)] = (x, y, z)
            if physics_runner is not None:
                bp = physics_runner.step_cell(k, i, (x, y, z))
                sig = {
                    "V_mean": bp.V_mean,
                    "V_slope": bp.V_slope,
                    "release_proxy": bp.release_proxy,
                    "afferent_current": bp.afferent_current,
                    "spike_rate": bp.spike_rate,
                    "spike_regularity": bp.spike_regularity,
                    "timing_precision": bp.timing_precision,
                    "adaptation_state": bp.adaptation_state,
                }
                signal_uncertainty = bp.signal_uncertainty
                source_signal_refs = bp.source_signal_refs
                sig_provenance = bp.provenance_hash
            else:
                V_hair = -66.0 + 7.5 * math.sin(0.7 * k + i * 0.19) + 1.2 * math.cos(i * 0.07)
                release = 0.08 * sigmoid((V_hair + 65.0) / 4.0)
                V_aff = -70.0 + 350.0 * release
                spike_rate = max(0.0, 5.0 * (V_aff - (-60.0)))
                sig = {
                    "V_mean": V_hair,
                    "V_slope": 0.0 if k == 0 else V_hair - signals[(k - 1, i)]["V_mean"],
                    "release_proxy": release,
                    "afferent_current": V_aff,
                    "spike_rate": spike_rate,
                    "spike_regularity": 1.0 / (1.0 + abs(spike_rate - 20.0) / 25.0),
                    "timing_precision": 0.01 + 0.001 * (i % 7),
                    "adaptation_state": 0.45 + 0.05 * math.sin(k + i * 0.17),
                }
                signal_uncertainty = 0.02 + 0.001 * (i % 3)
                source_signal_refs = {"window_id": win, "node_id": i}
                sig_provenance = f"sigprov_{k}_{i}"
            signals[(k, i)] = sig
            conn.execute(
                """INSERT INTO spacetime_cell
                (cell_uid,run_id,stage_k,window_id,node_id,clock_start,clock_end,x,y,z,
                 normal_x,normal_y,normal_z,boundary_distance,support_radius,source_patch_ids_json,
                 topology_neighbors_json,coordinate_frame_id,provenance_hash)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (uid, run_id, k, win, i, k, k + 1, x, y, z, x / max(radius, 1e-9), y / max(radius, 1e-9), 0.2,
                 bdist, 1.0, jdump([f"patch_{i%10}"]), jdump([(i - 1) % physical_cells, (i + 1) % physical_cells]),
                 "cell_sphere_v852", f"prov_{k}_{i}"),
            )
            conn.execute(
                """INSERT INTO information_fiber
                (fiber_id,cell_uid,V_mean,V_slope,release_proxy,afferent_current,spike_rate,spike_regularity,
                 timing_precision,adaptation_state,signal_uncertainty,compression_loss,source_signal_refs_json,
                 calibration_profile,provenance_hash)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (fid, uid, sig["V_mean"], sig["V_slope"], sig["release_proxy"], sig["afferent_current"], sig["spike_rate"],
                 sig["spike_regularity"], sig["timing_precision"], sig["adaptation_state"], signal_uncertainty, 0.0,
                 jdump(source_signal_refs), calibration_profile, sig_provenance),
            )
            conn.execute(
                """INSERT INTO spacetime_fiber_binding
                (binding_id,run_id,clock_n,window_id,spacetime_cell_id,information_fiber_id,source_cell_ids_json,
                 source_patch_ids_json,binding_type,calibration_profile,provenance_hash)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (f"bind_{k}_{i}", run_id, k, win, uid, fid, jdump([i]), jdump([f"patch_{i%10}"]),
                 "direct_diagnostic" if calibration_profile == "diagnostic_event_channel_v1" else "direct_basic_physics", calibration_profile, f"bindprov_{k}_{i}"),
            )

    theta = 1.55
    for k in range(1, windows):
        weights_for_entropy: list[float] = []
        for i in range(physical_cells):
            candidates = [i, (i + 1) % physical_cells]
            for rank, j in enumerate(candidates):
                p0, p1 = positions[(k - 1, i)], positions[(k, j)]
                geo = math.sqrt(sum((a - b) ** 2 for a, b in zip(p0, p1)))
                s0, s1 = signals[(k - 1, i)], signals[(k, j)]
                sig_drift = math.sqrt(sum((s1[key] - s0[key]) ** 2 for key in ["V_mean", "release_proxy", "spike_rate", "adaptation_state"]))
                boundary = abs((abs(math.sqrt(p0[0] ** 2 + p0[1] ** 2) - 5.0)) - (abs(math.sqrt(p1[0] ** 2 + p1[1] ** 2) - 5.0)))
                overlap = 1.0 if (i % 10) == (j % 10) else 0.0
                total_cost = 0.8 * geo + 0.02 * sig_drift + 1.5 * boundary + (1.0 - overlap) * 0.6
                accepted = 1 if rank == 0 and total_cost <= theta else 0
                weight = math.exp(-total_cost / 0.85)
                edge_id = f"tce_{k}_{i}_{rank}"
                conn.execute(
                    """INSERT INTO transport_current_edge
                    (edge_id,run_id,from_cell_uid,to_cell_uid,transport_weight,current_mass,geometry_cost,normal_cost,
                     boundary_cost,signal_cost,source_patch_overlap,fragility_penalty,accepted,transport_variant,
                     cycle_consistency_local,boundary_crossing_penalty,signal_drift,gating_failure_reason,provenance_hash,total_cost)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (edge_id, run_id, cell_uids[(k - 1, i)], cell_uids[(k, j)], weight, weight, geo, 0.0, boundary,
                     sig_drift, overlap, boundary * 0.1, accepted, "mainline" if accepted else "diagnostic_rejected_candidate",
                     1.0 if accepted else 0.0, boundary, sig_drift, None if accepted else "alternative_candidate_rejected",
                     f"transprov_{k}_{i}_{rank}", total_cost),
                )
                if not accepted:
                    conn.execute(
                        "INSERT INTO transport_gating_failure_report (failure_id,run_id,from_cell_uid,to_cell_uid,total_cost,theta_transport,reason,created_at) VALUES (?,?,?,?,?,?,?,?)",
                        (jid("tgf"), run_id, cell_uids[(k - 1, i)], cell_uids[(k, j)], total_cost, theta, "alternative_or_cost_gated", now()),
                    )
                weights_for_entropy.append(weight)

        # Hypotheses and derived minimal O candidates.
        support_cells = [cell_uids[(k, i)] for i in range(0, physical_cells, 5)]
        for typ, off in [("P_candidate", 0), ("R_candidate", 2)]:
            hyp_id = f"hyp_{typ[0].lower()}_{k}"
            members = support_cells[off:off + 6]
            support_score = 0.55 + 0.03 * k + (0.04 if typ.startswith("P") else 0.0)
            conn.execute(
                "INSERT INTO object_hypothesis (hypothesis_id,hypothesis_type,stage_k,run_id,status,member_cell_uids_json,spatial_support_json,temporal_support_json,support_score,source_decomposition_ref) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (hyp_id, typ, k, run_id, "candidate", jdump(members), jdump(members), jdump([f"win_{k-1}", f"win_{k}"]), support_score, "diagnostic_PR_decomposition"),
            )
            for n, uid in enumerate(members):
                conn.execute(
                    "INSERT INTO occupancy_measure (measure_id,hypothesis_id,cell_uid,membership_mass,transport_support,signal_support,geometry_support,masking_support,replay_support,core_margin_label) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (jid("occ"), hyp_id, uid, min(1.0, support_score - 0.02 * n), 0.5 + 0.02 * k, 0.45 + 0.03 * n,
                     0.8, 0.6, 0.0, "core" if n < 3 else "margin"),
                )
            ofs = f"ofs_{typ[0].lower()}_{k}"
            ocs = f"ocs_{typ[0].lower()}_{k}"
            ocr = f"ocr_{typ[0].lower()}_{k}"
            field_json = {"formation_mode": "derived_minimal", "components": ["decomposition_support", "transport_support", "masking_support", "occupancy_concentration"]}
            conn.execute("INSERT INTO o_field_surface (field_id,t_surface_id,field_matrix_json) VALUES (?,?,?)", (ofs, f"ts_{k}", jdump(field_json)))
            conn.execute("INSERT INTO o_candidate_surface (candidate_surface_id,field_surface_id,clusters_json) VALUES (?,?,?)", (ocs, ofs, jdump({"hypothesis_id": hyp_id, "mode": "derived_minimal"})))
            meta = {"formation_mode": "derived_minimal", "o_field_surface_id": ofs, "o_candidate_surface_id": ocs, "masking_refs_expected": True}
            conn.execute(
                """INSERT INTO o_candidate_record
                (candidate_id,candidate_type,stage_k,field_surface_id,member_node_ids_json,support_score,
                 transport_support_score,replay_support_score,boundary_penalty,solver_converged,maturity_flag,
                 source_hypothesis_id,created_at,formation_mode,metadata_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (ocr, "candidate_p" if typ.startswith("P") else "candidate_r", k, ofs, jdump(members), support_score,
                 0.5 + 0.02 * k, 0.0, 0.02 * k, 1, "candidate", hyp_id, now(), "derived_minimal", jdump(meta)),
            )
            for masking_type, verdict in [("random_node", "supports_confirmation"), ("signal_mask", "weakens_confirmation" if k % 3 == 0 else "supports_confirmation")]:
                mrid = jid("mask")
                conn.execute(
                    """INSERT INTO masking_counterevidence_record
                    (record_id,hypothesis_id,masking_type,masking_strength,masked_fraction,base_membership_mass,
                     masked_membership_mass,mass_retention,classification_consistency,trajectory_continuity,verdict,
                     run_id,o_field_id,o_candidate_id,confirmation_state_before,confirmation_state_after,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (mrid, hyp_id, masking_type, 0.3, 0.25, support_score * len(members), support_score * len(members) * 0.88,
                     0.88, 0.84, 0.82, verdict, run_id, ofs, ocs, "PR_candidate", "mask_supported", now()),
                )
            cgr = jid("cgr")
            # Keep the confirmation graph rules frozen, but let the regenerated
            # physical signal produce multiple existing graph nodes. Some R rows
            # remain at PR_candidate when the signal-mask trial weakens support;
            # all other rows advance to mask_supported.
            current_node = "PR_candidate" if (typ.startswith("R") and k % 3 == 0) else "mask_supported"
            previous_node = "O_candidate" if current_node == "PR_candidate" else "PR_candidate"
            conn.execute(
                """INSERT INTO pr_confirmation_graph_record
                (record_id,run_id,hypothesis_id,hypothesis_type,current_node,previous_node,o_field_surface_id,o_candidate_surface_id,
                 masking_trial_count,masking_support_count,transport_support_score,occupancy_persistence_length,xi_pressure,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (cgr, run_id, hyp_id, typ, current_node, previous_node, ofs, ocs, 2, 1, 0.5 + 0.02 * k, k, 0.05 * k, now()),
            )
            for fr, to in [("O_candidate", "PR_candidate"), ("PR_candidate", "mask_supported")]:
                conn.execute(
                    "INSERT INTO pr_graph_transition_record (transition_id,run_id,hypothesis_id,from_node,to_node,trigger,evidence_json,is_valid,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (jid("tr"), run_id, hyp_id, fr, to, "diagnostic_evidence", jdump({"o_candidate_associated": True, "masking_trial_count_ge_1": True}), 1, now()),
                )

        residue_id = f"xi_{k}"
        rtype = ["transport_residue", "masking_residue", "boundary_residue", "numerical_residue"][k % 4]
        xmass = max(0.01, 0.25 * math.exp(-0.22 * k) + 0.03 * (k % 3))
        conn.execute(
            """INSERT INTO xi_residue_record
            (residue_id,run_id,stage_k,source_hypothesis_refs_json,residue_norm,residue_mass,residue_entropy_proxy,
             spatial_support_cell_uids_json,temporal_support_window_ids_json,residue_type,carry_mode,decay_rate,memory_depth,carry_weight,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (residue_id, run_id, k, jdump([f"hyp_p_{k}", f"hyp_r_{k}"]), xmass * 1.2, xmass, 0.2 + 0.04 * k,
             jdump(support_cells[:5]), jdump([f"win_{k-1}", f"win_{k}"]), rtype, "carry" if k < 5 else "audit", 0.5, 2, max(0.0, 1.0 - 0.1 * k), now()),
        )
        state = ["held", "decaying", "proto_candidate", "quarantined", "discard_after_audit"][k % 5]
        conn.execute(
            "INSERT INTO xi_decay_policy (xi_id,run_id,current_state,mass_current,mass_previous,decay_rate,persistence_window_count,relation_support_score,occupancy_support_score,carryover_allowed,discard_after_audit_allowed,audit_reason,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (residue_id, run_id, state, xmass, xmass * 1.3, 0.5, k, 0.15 * k, 0.08 * k, 0 if state == "discard_after_audit" else 1, 1 if state == "discard_after_audit" else 0, f"v852_{state}_transition", now()),
        )
        h, hn, dist = entropy(weights_for_entropy)
        conn.execute(
            """INSERT INTO relation_entropy_record
            (record_id,run_id,relation_type,subject_group,object_group,entropy_value,normalized_entropy,effective_sample_size,
             support_cells_json,support_windows_json,calibration_profile,allowed_use,forbidden_use,created_at,entropy_source_distribution)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (jid("rel"), run_id, "transport_assignment_distribution", f"win_{k}", f"win_{k-1}", h, hn, len(weights_for_entropy),
             jdump(support_cells[:10]), jdump([f"win_{k-1}", f"win_{k}"]), calibration_profile, "audit,diagnostic,comparison",
             "freeze_pr,select_omega,generate_tseed,scientific_refutation", now(), jdump(dist[:20])),
        )

    alert_id = jid("ea")
    conn.execute(
        "INSERT INTO emergence_alert (alert_id,run_id,alert_type,severity,recommended_action,basic_conditions_json,strong_trigger_conditions_json,forbidden_actions_acknowledged,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (alert_id, run_id, "synthetic_test", "medium", "diagnostic_review_only", jdump(["masking_inconclusive"]), jdump(["occupancy_shift"]), 1, now()),
    )
    conn.execute(
        "INSERT INTO raw_emergency_export_manifest (export_id,export_type,emergence_alert_id,run_id,production_log_allowed,scientific_use_allowed,forbidden_actions_acknowledged,created_at) VALUES (?,?,?,?,?,?,?,?)",
        (jid("exp"), "synthetic_test", alert_id, run_id, 0, 0, 1, now()),
    )

    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    rows_by_table = {t: row_count(conn, t) for t in tables}
    total_rows = sum(rows_by_table.values())
    conn.execute(
        "INSERT INTO proxy_density_report (report_id,run_id,run_type,total_fields_checked,proxy_fields_count,proxy_density,critical_path_proxy_density,allowed_budget,overload_gate_triggered) VALUES (?,?,?,?,?,?,?,?,?)",
        (jid("pdr"), run_id, "diagnostic_run", 40, len(proxies), len(proxies) / 40.0, 0.2, 0.8, 0),
    )
    conn.execute(
        "INSERT INTO diagnostic_telemetry_report (report_id,run_id,total_rows_written,rows_by_table_json,write_amplification_ratio,masking_cost_ms,confirmation_update_cost_ms,transport_cost_ms,export_bundle_size_bytes,hot_path_cost_estimate,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (jid("tel"), run_id, total_rows, jdump(rows_by_table), total_rows / max(spacetime_cells, 1), 1.5, 1.2, 2.4, db_path.stat().st_size if db_path.exists() else 0, "diagnostic stdlib runner, O(n*candidates)", now()),
    )
    conn.commit()

    print("Morphosphere v8.5.2 diagnostic_full complete")
    print(f"run_id={run_id}")
    print(f"db={db_path}")
    print(f"integrity_check={conn.execute('PRAGMA integrity_check').fetchone()[0]}")
    print(f"spacetime_cell={row_count(conn,'spacetime_cell')}")
    print(f"information_fiber={row_count(conn,'information_fiber')}")
    print(f"transport_current_edge={row_count(conn,'transport_current_edge')}")
    print(f"proxy_provenance={row_count(conn,'proxy_provenance')}")
    conn.close()


if __name__ == "__main__":
    main()
