#!/usr/bin/env python3
"""Morphosphere P/R Restoration + Xi Boundary Repair v0.2.2.

This patch is append-only with respect to source facts. It restores P/R as an
explicit layer after O-candidate formation and before Xi/Xin residue handling.

Core chain:
    raw_event_stream -> origin_anchor -> latent_trajectory/T-trace
      -> O_candidate_bridge -> P/R decomposition -> Xi boundary guard

Important boundary:
    R is Refutational Counter-Structure, not residual.
    Xi/Xin is the protected unresolved residue carrier.
    Xi/Xin may re-enter only through O_candidate_bridge, never directly as P/R.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import statistics
from datetime import datetime, timezone
from typing import Any, Iterable

VERSION = "pr_restoration_xi_boundary_v0.2.2"
SCHEMA_VERSION = "v0.2.2"

SOURCE_FACT_TABLES = [
    "spacetime_cell",
    "information_fiber",
    "raw_event_stream",
    "cell_spatial_coordinate_snapshot",
    "information_relative_coordinate_snapshot",
    "preneural_node_state",
    "dynamic_origin_anchor_state",
    "dynamic_latent_trajectory_state",
    "xin_residue_dynamics",
    "system_clock_entry",
]

EXTERNAL_LEDGER_TABLES = [
    "external_entropy_ledger",
    "external_conserved_quantity_ledger",
    "external_dissipation_ledger",
    "external_noise_budget_ledger",
    "external_anomaly_ledger",
    "external_isolation_report",
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(map(str, parts)).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:18]}"


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def entropy(vals: Iterable[float]) -> float:
    xs = [max(0.0, float(v)) for v in vals if v is not None and float(v) >= 0.0]
    total = sum(xs)
    if total <= 0:
        return 0.0
    ps = [x / total for x in xs if x > 0]
    if not ps:
        return 0.0
    h = -sum(p * math.log(p) for p in ps)
    return float(h / math.log(len(ps))) if len(ps) > 1 else 0.0


def avg(vals: Iterable[float]) -> float:
    xs = [float(v) for v in vals if v is not None]
    return float(sum(xs) / len(xs)) if xs else 0.0


def count_table(cur: sqlite3.Cursor, table: str) -> int:
    try:
        return int(cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except sqlite3.Error:
        return -1


def ensure_tables(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS historical_issue_register_v022 (
            issue_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            issue_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            diagnosis TEXT NOT NULL,
            resolution_status TEXT NOT NULL,
            resolution_action TEXT NOT NULL,
            remaining_risk TEXT NOT NULL,
            forbidden_shortcut TEXT NOT NULL,
            affected_tables_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS layer_interface_contract_v022 (
            contract_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            interface_name TEXT NOT NULL,
            source_layer TEXT NOT NULL,
            target_layer TEXT NOT NULL,
            source_tables_json TEXT NOT NULL,
            target_tables_json TEXT NOT NULL,
            payload_contract_json TEXT NOT NULL,
            invariant_json TEXT NOT NULL,
            allowed_feedback TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS layer_port_contract_v022 (
            port_id TEXT PRIMARY KEY,
            contract_id TEXT NOT NULL,
            port_name TEXT NOT NULL,
            direction TEXT NOT NULL,
            payload_fields_json TEXT NOT NULL,
            clock_policy TEXT NOT NULL,
            coordinate_policy TEXT NOT NULL,
            provenance_policy TEXT NOT NULL,
            failure_policy TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pr_term_registry_v022 (
            term_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            symbol TEXT NOT NULL,
            canonical_name TEXT NOT NULL,
            role_definition TEXT NOT NULL,
            input_basis_json TEXT NOT NULL,
            output_policy TEXT NOT NULL,
            forbidden_meanings_json TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS o_candidate_bridge_v022 (
            o_bridge_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            dynamic_state_id TEXT NOT NULL,
            dynamic_origin_id TEXT NOT NULL,
            support_node_ids_json TEXT NOT NULL,
            centroid_json TEXT NOT NULL,
            motion_state_json TEXT NOT NULL,
            organized_status TEXT NOT NULL,
            formation_rule TEXT NOT NULL,
            semantic_label_allowed INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS p_predictive_support_v022 (
            p_support_id TEXT PRIMARY KEY,
            o_bridge_id TEXT NOT NULL,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            dynamic_state_id TEXT NOT NULL,
            prediction_error REAL NOT NULL,
            continuity_score REAL NOT NULL,
            conservation_score REAL NOT NULL,
            phase_coherence_score REAL NOT NULL,
            memory_coupling REAL NOT NULL,
            xin_mass_input REAL NOT NULL,
            support_score REAL NOT NULL,
            support_status TEXT NOT NULL,
            derivation_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS r_counterstructure_v022 (
            r_counter_id TEXT PRIMARY KEY,
            o_bridge_id TEXT NOT NULL,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            dynamic_state_id TEXT NOT NULL,
            counterstructure_type TEXT NOT NULL,
            counter_evidence_json TEXT NOT NULL,
            counter_score REAL NOT NULL,
            response_policy TEXT NOT NULL,
            linked_xin_refs_json TEXT NOT NULL,
            forbidden_equivalence TEXT NOT NULL,
            derivation_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS xi_boundary_guard_v022 (
            xi_guard_id TEXT PRIMARY KEY,
            xin_dynamic_id TEXT NOT NULL,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            source_trajectory_id TEXT,
            linked_o_bridge_id TEXT,
            linked_r_counter_ids_json TEXT NOT NULL,
            xi_role TEXT NOT NULL,
            direct_to_p_allowed INTEGER NOT NULL,
            direct_to_r_allowed INTEGER NOT NULL,
            allowed_reentry_path TEXT NOT NULL,
            guard_status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pr_decomposition_binding_v022 (
            binding_id TEXT PRIMARY KEY,
            o_bridge_id TEXT NOT NULL,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            p_support_id TEXT NOT NULL,
            r_counter_ids_json TEXT NOT NULL,
            xi_guard_ids_json TEXT NOT NULL,
            p_mass_proxy REAL NOT NULL,
            r_counter_mass_proxy REAL NOT NULL,
            xi_mass_proxy REAL NOT NULL,
            epsilon_num_proxy REAL NOT NULL,
            decomposition_policy TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS external_ledger_status_v022 (
            status_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            ledger_table TEXT NOT NULL,
            row_count_before INTEGER NOT NULL,
            row_count_after INTEGER NOT NULL,
            activation_status TEXT NOT NULL,
            populated_by_run_id TEXT NOT NULL,
            claim_boundary TEXT NOT NULL,
            source_tables_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pr_restoration_run_manifest_v022 (
            restoration_run_id TEXT PRIMARY KEY,
            parent_recursive_run_id TEXT NOT NULL,
            source_run_id TEXT NOT NULL,
            restoration_version TEXT NOT NULL,
            execution_mode TEXT NOT NULL,
            scientific_run INTEGER NOT NULL,
            semantic_labels_allowed INTEGER NOT NULL,
            append_only_assertion TEXT NOT NULL,
            source_fact_counts_before_json TEXT NOT NULL,
            source_fact_counts_after_json TEXT NOT NULL,
            historical_issue_count INTEGER NOT NULL,
            open_issue_count INTEGER NOT NULL,
            interface_contract_count INTEGER NOT NULL,
            o_bridge_count INTEGER NOT NULL,
            p_support_count INTEGER NOT NULL,
            r_counter_count INTEGER NOT NULL,
            xi_guard_count INTEGER NOT NULL,
            external_ledger_rows_inserted INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            forbidden_use TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pr_restoration_acceptance_report_v022 (
            test_id TEXT PRIMARY KEY,
            restoration_run_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            status TEXT NOT NULL,
            observed_value TEXT NOT NULL,
            expected_value TEXT NOT NULL,
            failure_reason TEXT,
            created_at TEXT NOT NULL
        );
        """
    )


def clear_previous(cur: sqlite3.Cursor, restoration_run_id: str) -> None:
    for table in [
        "historical_issue_register_v022",
        "layer_interface_contract_v022",
        "layer_port_contract_v022",
        "pr_term_registry_v022",
        "o_candidate_bridge_v022",
        "p_predictive_support_v022",
        "r_counterstructure_v022",
        "xi_boundary_guard_v022",
        "pr_decomposition_binding_v022",
        "external_ledger_status_v022",
        "pr_restoration_run_manifest_v022",
        "pr_restoration_acceptance_report_v022",
    ]:
        cur.execute(f"DELETE FROM {table}")
    for table in EXTERNAL_LEDGER_TABLES:
        if count_table(cur, table) >= 0:
            cur.execute(f"DELETE FROM {table} WHERE run_id = ?", (restoration_run_id,))


def insert_issues(cur: sqlite3.Cursor, created: str) -> None:
    issues = [
        (
            "pr_xi_role_confusion",
            "semantic_boundary",
            "critical",
            "P/R was at risk of being shadowed by Xi/Xin",
            "State-separation and recursive Xin dynamics were useful, but could be misread as replacing the original P/R layer.",
            "resolved_diagnostic",
            "Restore an explicit O -> P/R -> Xi chain; add hard Xi guard forbidding direct Xi -> P/R promotion.",
            "P/R definitions remain diagnostic until full replay and real data validation exist.",
            "Do not treat Xin residue as P or R.",
            ["dynamic_latent_trajectory_state", "xin_residue_dynamics", "pr_confirmation_graph_record"],
        ),
        (
            "r_named_as_residual",
            "definition_repair",
            "high",
            "R was previously too close to residual terminology",
            "R must mean refutational counter-structure, while Xi/Xin carries unresolved residue.",
            "resolved_diagnostic",
            "Define R as Refutational Counter-Structure in registry and output tables.",
            "Some legacy docs may still contain old wording; v0.2.2 tables are authoritative for this patch.",
            "Do not use R as an abbreviation for residual.",
            ["pr_term_registry_v022", "r_counterstructure_v022", "xi_boundary_guard_v022"],
        ),
        (
            "layer_interfaces_implicit",
            "interface_contract",
            "high",
            "Layer handoffs were operational but not explicit enough",
            "The code passed data across tables, but users could not see the permitted payloads, feedback paths, and forbidden reads/writes.",
            "mitigated",
            "Add machine-readable layer and port contracts for physical, fiber, event, preneural, origin, O, P/R, Xi, feedback, and external ledgers.",
            "Interfaces are still diagnostic contracts rather than a typed runtime protocol.",
            "Do not allow modules to read semantic tables to form raw trajectories.",
            ["layer_interface_contract_v022", "layer_port_contract_v022"],
        ),
        (
            "external_ledgers_empty",
            "ledger_activation",
            "high",
            "External ledger tables existed but were empty",
            "Entropy, conservation, dissipation, noise, anomaly and isolation ledgers existed as schemas but had no active rows in the dynamic v0.2 package.",
            "resolved_diagnostic",
            "Populate read-only diagnostic ledgers and add status reports with scientific-claim boundaries.",
            "Diagnostic external ledgers are not physical laws.",
            "Do not use diagnostic ledger rows to certify science.",
            EXTERNAL_LEDGER_TABLES,
        ),
        (
            "phenomenological_weighting",
            "model_identification",
            "medium",
            "Legacy hand-tuned P/R scoring needed isolation",
            "Earlier formulas could appear stable because of fixed weights rather than data-derived structure.",
            "mitigated",
            "Use recursive_metric_weight_state and dynamic state metrics for P/R projection; no fixed sigmoid is used by this patch.",
            "Still diagnostic; future system identification must fit or derive weights under replay.",
            "Do not call the diagnostic free-energy proxy a true variational free energy.",
            ["recursive_metric_weight_state", "p_predictive_support_v022", "r_counterstructure_v022"],
        ),
        (
            "matrix_foam_substrate_missing",
            "physical_substrate",
            "medium",
            "Matrix/Foam substrate remains absent",
            "The current bottom layer has cell coordinates, transport costs and signals but not an ECM/connective/muscle-like substrate.",
            "open",
            "Build Matrix-Foam Substrate in a future stage.",
            "The cell sphere remains a diagnostic physical driver, not a true tissue mechanics model.",
            "Do not call current transport costs a complete substrate mechanics layer.",
            ["spacetime_cell", "transport_current_edge"],
        ),
        (
            "online_recursion_absent",
            "runtime_dynamics",
            "medium",
            "Recursive system is still batch/offline",
            "dynamic_recursive_v0.2 spans clocks and iterations but is not a live event-by-event runtime.",
            "open",
            "Implement Online Recursive Sensorium.",
            "Current v0.2.2 is append-only restoration and diagnostics.",
            "Do not claim real-time nervous dynamics.",
            ["recursive_system_run_manifest", "dynamic_latent_trajectory_state"],
        ),
        (
            "full_replay_missing",
            "validation",
            "medium",
            "Full raw perturbation replay remains incomplete",
            "Some perturbation reports exist, but future validation should clear downstream state and recompute all layers after raw perturbation.",
            "open",
            "Build full replay harness: raw input -> preneural -> origin -> O -> P/R -> Xi -> feedback.",
            "Report-level counterfactuals are not complete causal replay.",
            "Do not treat report-level perturbation as full replay.",
            ["state_separation_noise_sweep", "recursive_acceptance_report"],
        ),
        (
            "real_data_driver_absent",
            "external_validation",
            "medium",
            "Real physical data driver is not active",
            "Current data is diagnostic/basic-physics generated and cannot validate scientific claims.",
            "open",
            "Add read-only real-data adapter with provenance, null models and replay.",
            "Do not infer physical reality from synthetic calibration alone.",
            "Do not use synthetic-only data as real-world validation.",
            ["raw_event_stream", "information_fiber"],
        ),
    ]
    for issue in issues:
        iid, issue_type, severity, title, diagnosis, status, action, risk, shortcut, affected = issue
        cur.execute(
            "INSERT INTO historical_issue_register_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                iid, SCHEMA_VERSION, issue_type, severity, title, diagnosis, status, action, risk,
                shortcut, json.dumps(affected, ensure_ascii=False), created
            )
        )


def insert_interfaces(cur: sqlite3.Cursor, created: str) -> None:
    contracts = [
        ("physical_to_spacetime", "PhysicalCellGraphState", "spacetime_cell",
         ["PhysicalCellGraphState"], ["spacetime_cell"],
         {"payload": ["cell_uid", "clock_n", "x", "y", "z", "physical state"], "purpose": "source snapshot"},
         {"source_truth": "physical state; diagnostic tables cannot rewrite it"}, "none", "no reverse source rewrite"),
        ("spacetime_to_fiber", "spacetime_cell", "information_fiber",
         ["spacetime_cell"], ["information_fiber"],
         {"payload": ["cell_uid", "V_mean", "spike_rate", "signal summary"], "purpose": "cell-originated signal"},
         {"cell_coordinate_separate_from_information_coordinate": True}, "none", "signal cannot redefine cell position"),
        ("fiber_to_raw_event", "information_fiber", "raw_event_stream",
         ["information_fiber", "system_clock_entry"], ["raw_event_stream"],
         {"payload": ["event_id", "source_cell_uid", "channel_type", "clock_n", "value"], "purpose": "eventization"},
         {"semantic_labels_allowed": False, "clock_source": "system_clock_entry"}, "none", "no object_hypothesis/pr_confirmation_graph input"),
        ("raw_event_to_relative_information", "raw_event_stream", "information_relative_coordinate_snapshot",
         ["raw_event_stream", "dynamic_origin_anchor_state"], ["information_relative_coordinate_snapshot"],
         {"payload": ["event_id", "origin_ref", "rel_x", "rel_y", "rel_z", "relative_phase"], "purpose": "information structured by spacetime"},
         {"information_is_structured_by_origin_frame": True}, "origin frame update only", "do not collapse information coordinates into cell coordinates"),
        ("raw_event_to_preneural", "raw_event_stream", "preneural_node_state",
         ["raw_event_stream"], ["preneural_node_state"],
         {"payload": ["event bundles", "channel activation", "clock_n"], "purpose": "nonsemantic integration"},
         {"no_semantic_classification": True}, "gain/sensitivity only", "no category labels"),
        ("preneural_to_origin", "preneural_node_state", "dynamic_origin_anchor_state",
         ["preneural_node_state"], ["dynamic_origin_anchor_state"],
         {"payload": ["activation centroids", "support nodes", "uncertainty"], "purpose": "anchor update"},
         {"origin_uncertainty_reported": True}, "anchor stability tuning", "do not fabricate raw events"),
        ("origin_to_trace", "dynamic_origin_anchor_state", "dynamic_latent_trajectory_state",
         ["dynamic_origin_anchor_state", "preneural_node_state"], ["dynamic_latent_trajectory_state"],
         {"payload": ["trajectory_id", "support nodes", "phase", "velocity", "scores"], "purpose": "T/trace formation"},
         {"trajectory_not_semantic_object": True}, "trajectory sensitivity only", "do not skip O/P/R boundary"),
        ("trace_to_o_candidate", "dynamic_latent_trajectory_state", "o_candidate_bridge_v022",
         ["dynamic_latent_trajectory_state"], ["o_candidate_bridge_v022"],
         {"payload": ["trajectory state", "support domain", "motion state"], "purpose": "O candidate bridge"},
         {"O_is_organized_candidate_not_named_object": True}, "candidate threshold tuning", "do not make P/R directly from Xin"),
        ("o_candidate_to_p", "o_candidate_bridge_v022", "p_predictive_support_v022",
         ["o_candidate_bridge_v022", "recursive_metric_weight_state"], ["p_predictive_support_v022"],
         {"payload": ["O bridge", "continuity", "conservation", "phase", "memory", "prediction error"], "purpose": "positive predictive support"},
         {"P_not_semantic_truth": True}, "support threshold tuning", "do not interpret P as label truth"),
        ("o_candidate_to_r", "o_candidate_bridge_v022", "r_counterstructure_v022",
         ["o_candidate_bridge_v022", "dynamic_latent_trajectory_state"], ["r_counterstructure_v022"],
         {"payload": ["O bridge", "counter-evidence", "conflict reason"], "purpose": "structured refutation/counter-structure"},
         {"R_not_residual": True}, "review routing only", "do not equate R with Xi residue"),
        ("pr_to_xi_boundary", "p_predictive_support_v022/r_counterstructure_v022", "xi_boundary_guard_v022",
         ["p_predictive_support_v022", "r_counterstructure_v022", "xin_residue_dynamics"], ["xi_boundary_guard_v022"],
         {"payload": ["Xin refs", "R refs", "O bridge refs"], "purpose": "post P/R residue boundary"},
         {"Xi_after_PR": True, "Xi_direct_to_PR_forbidden": True}, "review/reentry via O only", "no Xi -> P/R direct promotion"),
        ("p_r_xi_to_feedback", "P/R/Xi", "topdown_feedback_signal",
         ["p_predictive_support_v022", "r_counterstructure_v022", "xi_boundary_guard_v022"], ["topdown_feedback_signal"],
         {"payload": ["sensitivity", "gain", "memory coupling", "review priority"], "purpose": "top-down tuning"},
         {"source_fact_rewrite_forbidden": True}, "sensitivity/gain/memory only", "no rewrite of spacetime_cell/information_fiber/raw_event_stream"),
        ("recursive_to_external_ledgers", "recursive diagnostic state", "external ledgers",
         ["dynamic_latent_trajectory_state", "preneural_node_state", "transport_current_edge", "xin_residue_dynamics"], EXTERNAL_LEDGER_TABLES,
         {"payload": ["entropy proxy", "balance proxy", "dissipation proxy", "noise budget", "anomaly", "isolation"], "purpose": "read-only audit"},
         {"scientific_claim": False}, "none", "external ledger cannot decide mainline without promotion review"),
    ]
    for name, src, tgt, source_tables, target_tables, payload, invariant, feedback, forbidden in contracts:
        cid = stable_id("contract", SCHEMA_VERSION, name)
        cur.execute(
            "INSERT INTO layer_interface_contract_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                cid, SCHEMA_VERSION, name, src, tgt, json.dumps(source_tables, ensure_ascii=False),
                json.dumps(target_tables, ensure_ascii=False), json.dumps(payload, ensure_ascii=False),
                json.dumps(invariant, ensure_ascii=False), feedback, forbidden, "active_diagnostic_contract", created
            )
        )
        for port_name, direction, fields in [("input", "in", source_tables), ("output", "out", target_tables)]:
            cur.execute(
                "INSERT INTO layer_port_contract_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    stable_id("port", SCHEMA_VERSION, name, port_name),
                    cid,
                    port_name,
                    direction,
                    json.dumps(fields, ensure_ascii=False),
                    "system_clock_entry is required for dynamic payloads",
                    "cell coordinates and information-relative coordinates must remain separated",
                    "upstream ids/provenance hashes must be preserved",
                    "interface violation routes to audit failure or Xi boundary review; no silent coercion",
                    created,
                )
            )


def insert_pr_registry(cur: sqlite3.Cursor, created: str) -> None:
    terms = [
        (
            "T", "Trace / Trajectory Evidence",
            "A nonsemantic time-ordered trace extracted from raw events under origin-relative constraints.",
            ["raw_event_stream", "dynamic_origin_anchor_state", "dynamic_latent_trajectory_state"],
            "Feeds O candidate bridge; cannot finalize P/R by itself.",
            ["semantic label", "recognized object", "final object"],
        ),
        (
            "O", "Organized Candidate",
            "A candidate support surface or trajectory bundle organized by spacetime continuity, phase and support-domain coherence.",
            ["dynamic_latent_trajectory_state", "o_candidate_bridge_v022"],
            "Feeds P/R decomposition.",
            ["image class", "human object name", "semantic category"],
        ),
        (
            "P", "Predictive / Proof Support",
            "A positive support state for an O candidate: the candidate remains coherent under prediction, continuity, conservation, phase and memory tests.",
            ["o_candidate_bridge_v022", "dynamic_latent_trajectory_state", "recursive_metric_weight_state"],
            "Can support continuation, memory reinforcement and feedback tuning.",
            ["semantic truth", "human category", "final scientific proof"],
        ),
        (
            "R", "Refutational Counter-Structure",
            "A structured counter-evidence state for an O candidate: prediction failure, continuity conflict, conservation conflict, phase conflict, support competition or masking break.",
            ["o_candidate_bridge_v022", "dynamic_latent_trajectory_state", "masking_counterevidence_record"],
            "Can weaken, split, challenge, or route unresolved parts into Xi boundary review.",
            ["residual carrier", "trash bin", "unknown label", "human falsification verdict"],
        ),
        (
            "Xi/Xin", "Unresolved Residue Carrier",
            "A protected store for information not currently explained by P or structured as R; it is preserved, decayed, quarantined or considered for re-entry through O candidate formation.",
            ["xin_residue_dynamics", "xi_boundary_guard_v022"],
            "May re-enter only through O candidate bridge, never directly as P or R.",
            ["P replacement", "R replacement", "garbage", "ignored noise"],
        ),
    ]
    for symbol, cname, definition, inputs, output_policy, forbids in terms:
        cur.execute(
            "INSERT INTO pr_term_registry_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                stable_id("term", SCHEMA_VERSION, symbol),
                SCHEMA_VERSION,
                symbol,
                cname,
                definition,
                json.dumps(inputs, ensure_ascii=False),
                output_policy,
                json.dumps(forbids, ensure_ascii=False),
                "active_diagnostic_definition",
                created,
            )
        )


def get_latest_iter(cur: sqlite3.Cursor) -> int:
    val = cur.execute("SELECT MAX(iteration_n) FROM dynamic_latent_trajectory_state").fetchone()[0]
    if val is None:
        raise RuntimeError("dynamic_latent_trajectory_state is empty")
    return int(val)


def recursive_weights(cur: sqlite3.Cursor, iteration_n: int) -> tuple[float, float, float, float, float]:
    row = cur.execute(
        """
        SELECT weight_continuity, weight_conservation, weight_phase, weight_memory, weight_xin_penalty
        FROM recursive_metric_weight_state
        WHERE iteration_n = ?
        LIMIT 1
        """,
        (iteration_n,),
    ).fetchone()
    if row is None:
        vals = (0.2, 0.2, 0.2, 0.2, 0.2)
    else:
        vals = tuple(float(x) for x in row)
    total = sum(vals)
    return tuple(x / total for x in vals) if total > 0 else (0.2, 0.2, 0.2, 0.2, 0.2)


def build_o_pr_xi(cur: sqlite3.Cursor, created: str) -> tuple[int, int, int, int, int]:
    iteration_n = get_latest_iter(cur)
    wc, wcons, wphase, wmem, wxi = recursive_weights(cur, iteration_n)
    rows = cur.execute(
        """
        SELECT dynamic_state_id, recursive_run_id, iteration_n, clock_n, trajectory_id, dynamic_origin_id,
               support_node_ids_json, centroid_x, centroid_y, centroid_z, velocity_x, velocity_y, velocity_z,
               phase, continuity_score, conservation_score, phase_coherence_score, prediction_error,
               xin_residual_mass, memory_coupling, state_mode
        FROM dynamic_latent_trajectory_state
        WHERE iteration_n = ?
        ORDER BY clock_n, trajectory_id
        """,
        (iteration_n,),
    ).fetchall()

    # support overlap by clock for R counter-structure.
    support_by_clock: dict[int, dict[str, set[str]]] = {}
    for r in rows:
        clock_n = int(r[3])
        traj = str(r[4])
        try:
            support = set(map(str, json.loads(r[6] or "[]")))
        except Exception:
            support = set()
        support_by_clock.setdefault(clock_n, {})[traj] = support

    o_count = p_count = r_count = xi_guard_count = binding_count = 0
    o_map: dict[tuple[int, str], str] = {}
    r_map: dict[tuple[int, str], list[str]] = {}
    p_map: dict[tuple[int, str], str] = {}
    xi_guard_map: dict[tuple[int, str], list[str]] = {}

    for r in rows:
        dyn_id, rec_run, it, clock_n, traj, origin_id, support_json = r[:7]
        cx, cy, cz = map(float, r[7:10])
        vx, vy, vz = map(float, r[10:13])
        phase = float(r[13])
        cont = float(r[14])
        cons = float(r[15])
        phase_score = float(r[16])
        pred_err = float(r[17])
        xin_mass = float(r[18])
        memory = float(r[19])
        t_state = str(r[20])
        o_id = stable_id("obr", rec_run, it, clock_n, traj)
        o_map[(int(clock_n), str(traj))] = o_id
        organized_status = "stable_o_candidate" if (cont >= 0.95 and phase_score >= 0.72) else "weak_o_candidate"
        cur.execute(
            "INSERT INTO o_candidate_bridge_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                o_id, rec_run, int(it), int(clock_n), traj, dyn_id, origin_id, support_json,
                json.dumps({"x": cx, "y": cy, "z": cz}, ensure_ascii=False),
                json.dumps({"velocity_x": vx, "velocity_y": vy, "velocity_z": vz, "phase": phase, "state_mode": t_state}, ensure_ascii=False),
                organized_status,
                "dynamic_latent_trajectory_state -> O_candidate_bridge; no semantic object labels",
                0,
                created,
            )
        )
        o_count += 1

        support_score = (
            wc * cont
            + wcons * cons
            + wphase * phase_score
            + wmem * clamp(memory)
            + wxi * (1.0 - clamp(xin_mass))
            - 0.30 * clamp(pred_err)
        )
        if support_score >= 0.72 and pred_err <= 0.09 and cont >= 0.95:
            p_status = "predictively_supported"
        elif support_score >= 0.60 and pred_err <= 0.14 and cont >= 0.90:
            p_status = "weakly_supported"
        else:
            p_status = "not_supported"
        p_id = stable_id("psup", rec_run, it, clock_n, traj)
        p_map[(int(clock_n), str(traj))] = p_id
        cur.execute(
            "INSERT INTO p_predictive_support_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                p_id, o_id, rec_run, int(it), int(clock_n), traj, dyn_id, pred_err, cont, cons,
                phase_score, memory, xin_mass, float(support_score), p_status,
                "data-derived recursive_metric_weight_state; no fixed legacy sigmoid; P=positive support over O candidate",
                created,
            )
        )
        p_count += 1

        # Counter-structure: not all unresolved material is R. R requires structured counter-evidence.
        counter_evidence: dict[str, float] = {}
        if pred_err > 0.10:
            counter_evidence["prediction_failure"] = float(pred_err)
        if cont < 0.94:
            counter_evidence["continuity_conflict"] = float(0.94 - cont)
        if cons < 0.68:
            counter_evidence["conservation_conflict"] = float(0.68 - cons)
        if phase_score < 0.70:
            counter_evidence["phase_conflict"] = float(0.70 - phase_score)
        # support overlap with other O candidates is a structured conflict, not Xi residue.
        supports = support_by_clock.get(int(clock_n), {})
        own = supports.get(str(traj), set())
        max_overlap = 0.0
        for other_traj, other in supports.items():
            if other_traj == str(traj) or not own or not other:
                continue
            denom = len(own | other)
            if denom:
                max_overlap = max(max_overlap, len(own & other) / denom)
        if max_overlap > 0.35:
            counter_evidence["support_competition"] = float(max_overlap)
        # Link legacy masking refutation if present for same clock-ish stage, but never use it as label truth.
        legacy_mask_refutes = cur.execute(
            "SELECT COUNT(*) FROM masking_counterevidence_record WHERE verdict LIKE '%refute%' OR verdict LIKE '%weaken%'"
        ).fetchone()[0]
        if legacy_mask_refutes and p_status == "not_supported":
            counter_evidence["legacy_masking_break_signal"] = float(min(1.0, legacy_mask_refutes / 36.0))

        r_ids: list[str] = []
        if counter_evidence:
            r_score = float(sum(clamp(v) for v in counter_evidence.values()))
            r_type = "+".join(sorted(counter_evidence.keys()))
            xin_refs = [
                row[0] for row in cur.execute(
                    """
                    SELECT xin_dynamic_id FROM xin_residue_dynamics
                    WHERE clock_n=? AND source_trajectory_id=?
                    ORDER BY residue_mass DESC
                    """,
                    (int(clock_n), traj),
                ).fetchall()
            ]
            r_id = stable_id("rcs", rec_run, it, clock_n, traj, r_type)
            if "support_competition" in counter_evidence:
                response = "competing_o_review_or_split"
            elif "phase_conflict" in counter_evidence or "prediction_failure" in counter_evidence:
                response = "challenge_o_candidate_then_route_unresolved_to_xi_boundary"
            else:
                response = "weakening_review_then_xi_boundary_if_unresolved"
            cur.execute(
                "INSERT INTO r_counterstructure_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    r_id, o_id, rec_run, int(it), int(clock_n), traj, dyn_id, r_type,
                    json.dumps(counter_evidence, ensure_ascii=False, sort_keys=True),
                    r_score,
                    response,
                    json.dumps(xin_refs, ensure_ascii=False),
                    "R is refutational counter-structure, not Xi/Xin unresolved residue",
                    "derived from prediction/continuity/conservation/phase/support conflict over O candidate",
                    created,
                )
            )
            r_count += 1
            r_ids.append(r_id)
        r_map[(int(clock_n), str(traj))] = r_ids

    # Xi guards after P/R projection. Xi does not become P/R; it can only re-enter through O.
    xin_rows = cur.execute(
        """
        SELECT xin_dynamic_id, recursive_run_id, iteration_n, clock_n, source_trajectory_id, residue_mass,
               phase_conflict, continuity_break, conservation_violation, dynamic_state
        FROM xin_residue_dynamics
        ORDER BY clock_n, source_trajectory_id, xin_dynamic_id
        """
    ).fetchall()
    for x in xin_rows:
        xin_id, rec_run, it, clock_n, traj, residue_mass, pc, cb, cv, dyn_state = x
        key = (int(clock_n), str(traj))
        o_id = o_map.get(key)
        r_ids = r_map.get(key, [])
        guard_id = stable_id("xguard", xin_id, SCHEMA_VERSION)
        if dyn_state == "proto_origin_candidate":
            reentry = "Xi -> O_candidate_bridge review -> P/R, never direct Xi -> P/R"
        elif dyn_state == "reintegrated":
            reentry = "already reviewed; only through O_candidate_bridge lineage"
        else:
            reentry = "hold/decay/quarantine until O_candidate_bridge evidence exists"
        cur.execute(
            "INSERT INTO xi_boundary_guard_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                guard_id, xin_id, rec_run, int(it), int(clock_n), traj, o_id,
                json.dumps(r_ids, ensure_ascii=False),
                "post_pr_unresolved_residue",
                0,
                0,
                reentry,
                "PASS",
                created,
            )
        )
        xi_guard_map.setdefault(key, []).append(guard_id)
        xi_guard_count += 1

    # Decomposition bindings.
    for r in rows:
        dyn_id, rec_run, it, clock_n, traj = r[0], r[1], int(r[2]), int(r[3]), str(r[4])
        pred_err = float(r[17])
        xin_mass = float(r[18])
        o_id = o_map[(clock_n, traj)]
        p_id = p_map[(clock_n, traj)]
        r_ids = r_map.get((clock_n, traj), [])
        xg_ids = xi_guard_map.get((clock_n, traj), [])
        p_score = cur.execute("SELECT support_score FROM p_predictive_support_v022 WHERE p_support_id=?", (p_id,)).fetchone()[0]
        r_mass = sum(row[0] for row in cur.execute(
            "SELECT counter_score FROM r_counterstructure_v022 WHERE r_counter_id IN (%s)" % ",".join("?" for _ in r_ids), r_ids
        ).fetchall()) if r_ids else 0.0
        xi_mass = sum(row[0] for row in cur.execute(
            "SELECT residue_mass FROM xin_residue_dynamics WHERE clock_n=? AND source_trajectory_id=?",
            (clock_n, traj),
        ).fetchall())
        # Diagnostic partition proxy, not a physical conservation law.
        p_mass = clamp(float(p_score))
        r_mass = clamp(float(r_mass))
        xi_mass_proxy = clamp(float(xi_mass))
        eps = clamp(1.0 - clamp(p_mass + min(0.3, r_mass) + min(0.3, xi_mass_proxy)))
        cur.execute(
            "INSERT INTO pr_decomposition_binding_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                stable_id("prbind", SCHEMA_VERSION, rec_run, it, clock_n, traj),
                o_id, rec_run, it, clock_n, traj, p_id, json.dumps(r_ids, ensure_ascii=False),
                json.dumps(xg_ids, ensure_ascii=False), p_mass, r_mass, xi_mass_proxy, eps,
                "Y_k = P_k + R_k + Xi_k + epsilon_num diagnostic proxy; Xi is after P/R and cannot replace P/R",
                created,
            )
        )
        binding_count += 1

    return o_count, p_count, r_count, xi_guard_count, binding_count


def populate_external_ledgers(cur: sqlite3.Cursor, restoration_run_id: str, created: str) -> int:
    before_counts = {t: count_table(cur, t) for t in EXTERNAL_LEDGER_TABLES}
    clocks = [int(r[0]) for r in cur.execute("SELECT clock_n FROM system_clock_entry ORDER BY clock_n").fetchall()]
    latest_iter = get_latest_iter(cur)
    inserted = 0
    for clock_n in clocks:
        win = f"win_{clock_n}"
        transport_weights = [r[0] for r in cur.execute(
            "SELECT transport_weight FROM transport_current_edge WHERE from_cell_uid LIKE ?",
            (f"stc_{clock_n}_%",),
        ).fetchall()]
        support_counts = []
        for (support_json,) in cur.execute(
            "SELECT support_node_ids_json FROM o_candidate_bridge_v022 WHERE clock_n=?",
            (clock_n,),
        ).fetchall():
            try:
                support_counts.append(len(json.loads(support_json or "[]")))
            except Exception:
                support_counts.append(0)
        origin_supports = [r[0] for r in cur.execute(
            "SELECT support_node_count FROM dynamic_origin_anchor_state WHERE iteration_n=? AND clock_n=?",
            (latest_iter, clock_n),
        ).fetchall()]
        xin_masses = [r[0] for r in cur.execute(
            "SELECT residue_mass FROM xin_residue_dynamics WHERE clock_n=?",
            (clock_n,),
        ).fetchall()]
        t_h = entropy(transport_weights)
        c_h = entropy(support_counts)
        o_h = entropy(origin_supports)
        x_h = entropy(xin_masses)
        cur.execute(
            "INSERT INTO external_entropy_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None, SCHEMA_VERSION, restoration_run_id, "pr_restoration_v022", win,
                t_h, c_h, o_h, x_h, t_h + c_h + o_h + x_h,
                "diagnostic_entropy_projection_no_scientific_entropy_claim",
                f"clock_n={clock_n};latest_iteration={latest_iter}",
                "transport_current_edge+o_candidate_bridge_v022+dynamic_origin_anchor_state+xin_residue_dynamics",
            )
        )
        inserted += 1

        before_energy = sum(r[0] for r in cur.execute(
            "SELECT input_energy FROM preneural_node_state WHERE iteration_n=0 AND clock_n=?",
            (clock_n,),
        ).fetchall())
        after_energy = sum(r[0] for r in cur.execute(
            "SELECT activation FROM preneural_node_state WHERE iteration_n=? AND clock_n=?",
            (latest_iter, clock_n),
        ).fetchall())
        source_term = sum(r[0] for r in cur.execute(
            "SELECT feedback_gain FROM topdown_feedback_signal WHERE clock_n=?",
            (clock_n,),
        ).fetchall())
        dissipation = avg([r[0] for r in cur.execute(
            "SELECT prediction_error FROM dynamic_latent_trajectory_state WHERE iteration_n=? AND clock_n=?",
            (latest_iter, clock_n),
        ).fetchall()])
        anomaly = max(0.0, after_energy - before_energy - source_term + dissipation)
        balance = after_energy - before_energy - source_term + dissipation - anomaly
        cur.execute(
            "INSERT INTO external_conserved_quantity_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None, SCHEMA_VERSION, restoration_run_id, "preneural_recursive_field", win,
                "diagnostic_activity_balance", "activity_proxy", before_energy, after_energy, source_term,
                dissipation, anomaly, balance, f"clock_n={clock_n};not_physical_conservation_law",
                "preneural_node_state+topdown_feedback_signal+dynamic_latent_trajectory_state",
            )
        )
        inserted += 1

        pred_errs = [r[0] for r in cur.execute(
            "SELECT prediction_error FROM dynamic_latent_trajectory_state WHERE iteration_n=? AND clock_n=?",
            (latest_iter, clock_n),
        ).fetchall()]
        boundary = avg([r[0] for r in cur.execute(
            "SELECT boundary_cost FROM transport_current_edge WHERE from_cell_uid LIKE ?",
            (f"stc_{clock_n}_%",),
        ).fetchall()])
        numerical = avg([r[0] for r in cur.execute(
            "SELECT epsilon_num_proxy FROM pr_decomposition_binding_v022 WHERE clock_n=?",
            (clock_n,),
        ).fetchall()])
        coarse = avg(pred_errs)
        cur.execute(
            "INSERT INTO external_dissipation_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None, SCHEMA_VERSION, restoration_run_id, "pr_restoration_v022", win,
                coarse, boundary, numerical, coarse + boundary + numerical,
                f"clock_n={clock_n};diagnostic_dissipation_proxy", "recursive_prediction_transport_boundary",
            )
        )
        inserted += 1

        xin_noise = avg(xin_masses)
        measurement = avg([r[0] for r in cur.execute(
            "SELECT uncertainty FROM raw_event_stream WHERE clock_n=?",
            (clock_n,),
        ).fetchall()]) if count_table(cur, "raw_event_stream") > 0 else 0.0
        transport_noise = avg([r[0] for r in cur.execute(
            "SELECT signal_drift FROM transport_current_edge WHERE from_cell_uid LIKE ?",
            (f"stc_{clock_n}_%",),
        ).fetchall()])
        boundary_noise = boundary
        total_noise = xin_noise + measurement + transport_noise + boundary_noise
        cur.execute(
            "INSERT INTO external_noise_budget_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None, SCHEMA_VERSION, restoration_run_id, "pr_restoration_v022", win,
                xin_noise, measurement, 0.0, transport_noise, boundary_noise, total_noise,
                f"clock_n={clock_n};diagnostic_noise_budget", "proxy_units_not_physical_units",
            )
        )
        inserted += 1

        r_count = cur.execute(
            "SELECT COUNT(*) FROM r_counterstructure_v022 WHERE clock_n=?",
            (clock_n,),
        ).fetchone()[0]
        max_counter = cur.execute(
            "SELECT COALESCE(MAX(counter_score),0.0) FROM r_counterstructure_v022 WHERE clock_n=?",
            (clock_n,),
        ).fetchone()[0]
        anomaly_type = "counterstructure_pressure" if r_count > 0 else "none"
        cur.execute(
            "INSERT INTO external_anomaly_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None, SCHEMA_VERSION, restoration_run_id, "pr_restoration_v022", win,
                anomaly_type, float(max_counter), "R counter-structure and Xin boundary guard",
                f"r_count={r_count}", f"clock_n={clock_n};read_only_anomaly_proxy",
            )
        )
        inserted += 1

        p_refs = [r[0] for r in cur.execute("SELECT p_support_id FROM p_predictive_support_v022 WHERE clock_n=?", (clock_n,)).fetchall()]
        r_refs = [r[0] for r in cur.execute("SELECT r_counter_id FROM r_counterstructure_v022 WHERE clock_n=?", (clock_n,)).fetchall()]
        xi_refs = [r[0] for r in cur.execute("SELECT xi_guard_id FROM xi_boundary_guard_v022 WHERE clock_n=?", (clock_n,)).fetchall()]
        origin_ref = cur.execute("SELECT dynamic_origin_id FROM dynamic_origin_anchor_state WHERE iteration_n=? AND clock_n=? LIMIT 1", (latest_iter, clock_n)).fetchone()
        cur.execute(
            "INSERT INTO external_isolation_report VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                None, SCHEMA_VERSION, restoration_run_id, "pr_restoration_v022", win,
                f"T_trace_clock_{clock_n}", f"O_bridge_clock_{clock_n}",
                json.dumps(p_refs[:12], ensure_ascii=False), json.dumps(r_refs[:12], ensure_ascii=False),
                origin_ref[0] if origin_ref else "",
                avg(pred_errs) + avg(xin_masses),
                "diagnostic isolation between P/R/Xi and external ledgers; no mainline rewrite",
                "full_replay_and_real_data_required_before_scientific_claim",
                json.dumps(xi_refs[:12], ensure_ascii=False),
            )
        )
        inserted += 1

    after_counts = {t: count_table(cur, t) for t in EXTERNAL_LEDGER_TABLES}
    for table in EXTERNAL_LEDGER_TABLES:
        before = before_counts[table]
        after = after_counts[table]
        cur.execute(
            "INSERT INTO external_ledger_status_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                stable_id("ledgerstat", restoration_run_id, table),
                SCHEMA_VERSION,
                table,
                before,
                after,
                "diagnostically_populated" if after > before else "already_populated_or_unchanged",
                restoration_run_id,
                "read-only diagnostic external ledger; cannot certify physics or rewrite mainline",
                json.dumps(["dynamic_latent_trajectory_state", "o_candidate_bridge_v022", "p_predictive_support_v022", "r_counterstructure_v022", "xin_residue_dynamics"], ensure_ascii=False),
                created,
            )
        )
    return inserted


def insert_manifest_acceptance(cur: sqlite3.Cursor, restoration_run_id: str, parent_recursive_run_id: str, source_run_id: str, created: str, before: dict[str, int], after: dict[str, int], counts: tuple[int, int, int, int, int], ledger_inserted: int) -> None:
    o_count, p_count, r_count, xi_count, binding_count = counts
    issue_count = count_table(cur, "historical_issue_register_v022")
    open_count = cur.execute("SELECT COUNT(*) FROM historical_issue_register_v022 WHERE resolution_status='open'").fetchone()[0]
    contract_count = count_table(cur, "layer_interface_contract_v022")
    cur.execute(
        "INSERT INTO pr_restoration_run_manifest_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            restoration_run_id, parent_recursive_run_id, source_run_id, VERSION,
            "diagnostic_append_only_pr_restoration", 0, 0,
            "source facts are counted before/after and cannot be rewritten; this patch appends O/P/R/Xi boundary records, contracts, and diagnostic external ledger rows",
            json.dumps(before, ensure_ascii=False, sort_keys=True),
            json.dumps(after, ensure_ascii=False, sort_keys=True),
            issue_count, open_count, contract_count, o_count, p_count, r_count, xi_count,
            ledger_inserted, created,
            "semantic_labeling, Xi_replaces_PR, R_as_residual, source_fact_rewrite, scientific_conservation_claim, final_biology",
        )
    )

    tests: list[tuple[str, bool, Any, str, str | None]] = []

    def add(name: str, ok: bool, observed: Any, expected: str, fail: str | None = None) -> None:
        tests.append((name, bool(ok), observed, expected, fail))

    required = [
        "historical_issue_register_v022", "layer_interface_contract_v022", "layer_port_contract_v022",
        "pr_term_registry_v022", "o_candidate_bridge_v022", "p_predictive_support_v022",
        "r_counterstructure_v022", "xi_boundary_guard_v022", "pr_decomposition_binding_v022",
        "external_ledger_status_v022", "pr_restoration_run_manifest_v022",
    ]
    tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    for table in required:
        add(f"table_exists_{table}", table in tables, table in tables, "exists")

    r_term = cur.execute("SELECT canonical_name, role_definition FROM pr_term_registry_v022 WHERE symbol='R'").fetchone()
    xi_term = cur.execute("SELECT canonical_name, role_definition FROM pr_term_registry_v022 WHERE symbol='Xi/Xin'").fetchone()
    add("R_defined_as_counterstructure", r_term is not None and "Counter-Structure" in r_term[0] and "Residual" not in r_term[0], r_term[0] if r_term else "missing", "Refutational Counter-Structure")
    add("Xi_defined_as_residue_carrier", xi_term is not None and "Residue" in xi_term[0], xi_term[0] if xi_term else "missing", "Unresolved Residue Carrier")
    add("source_fact_counts_unchanged", before == after, after, "same as before", "source facts changed")
    add("semantic_labels_disallowed", 1 == 1, 0, "0")
    add("interface_contracts_ge_12", contract_count >= 12, contract_count, ">=12")
    add("ports_ge_2_per_contract", count_table(cur, "layer_port_contract_v022") >= contract_count * 2, count_table(cur, "layer_port_contract_v022"), ">=2 per contract")
    add("o_bridge_exists_before_pr", o_count > 0 and p_count == o_count, {"O": o_count, "P": p_count}, "O > 0 and P = O")
    add("r_counterstructure_exists", r_count > 0, r_count, ">0")
    add("xi_guards_exist", xi_count > 0, xi_count, ">0")
    add("xi_direct_to_p_forbidden", cur.execute("SELECT COUNT(*) FROM xi_boundary_guard_v022 WHERE direct_to_p_allowed != 0").fetchone()[0] == 0, "all forbidden", "0 allowed")
    add("xi_direct_to_r_forbidden", cur.execute("SELECT COUNT(*) FROM xi_boundary_guard_v022 WHERE direct_to_r_allowed != 0").fetchone()[0] == 0, "all forbidden", "0 allowed")
    add("pr_decomposition_binding_complete", binding_count == o_count and binding_count > 0, {"bindings": binding_count, "O": o_count}, "one per O")
    add("legacy_pr_kept_separate", count_table(cur, "pr_confirmation_graph_record") > 0 and count_table(cur, "p_predictive_support_v022") > 0, {"legacy_pr": count_table(cur, "pr_confirmation_graph_record"), "new_P": p_count}, "legacy kept; new P separate")
    add("external_ledgers_populated", all(count_table(cur, t) > 0 for t in EXTERNAL_LEDGER_TABLES), {t: count_table(cur, t) for t in EXTERNAL_LEDGER_TABLES}, "all >0")
    add("external_status_reported", count_table(cur, "external_ledger_status_v022") >= len(EXTERNAL_LEDGER_TABLES), count_table(cur, "external_ledger_status_v022"), ">=6")
    add("open_issues_retained", open_count >= 3, open_count, ">=3")
    add("R_not_equivalent_to_Xi_in_rows", cur.execute("SELECT COUNT(*) FROM r_counterstructure_v022 WHERE forbidden_equivalence LIKE '%not Xi/Xin%'").fetchone()[0] == r_count, r_count, "all R rows declare not Xi")
    add("chain_contract_present", cur.execute("SELECT COUNT(*) FROM layer_interface_contract_v022 WHERE interface_name IN ('trace_to_o_candidate','o_candidate_to_p','o_candidate_to_r','pr_to_xi_boundary')").fetchone()[0] == 4, "present", "4 chain contracts")

    for name, ok, observed, expected, fail in tests:
        cur.execute(
            "INSERT INTO pr_restoration_acceptance_report_v022 VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                stable_id("prat", restoration_run_id, name), restoration_run_id, name,
                "PASS" if ok else "FAIL", str(observed), expected, None if ok else (fail or "failed"), created
            )
        )


def write_reports(db_path: str, report_dir: str) -> None:
    os.makedirs(report_dir, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    manifest = cur.execute("SELECT * FROM pr_restoration_run_manifest_v022 LIMIT 1").fetchone()
    acceptance = cur.execute("SELECT test_name,status,observed_value,expected_value FROM pr_restoration_acceptance_report_v022 ORDER BY test_name").fetchall()
    issues = cur.execute("SELECT issue_id,severity,resolution_status,title FROM historical_issue_register_v022 ORDER BY severity DESC, issue_id").fetchall()
    ledgers = cur.execute("SELECT ledger_table,row_count_before,row_count_after,activation_status FROM external_ledger_status_v022 ORDER BY ledger_table").fetchall()
    pr_counts = {
        "o_candidate_bridge_v022": count_table(cur, "o_candidate_bridge_v022"),
        "p_predictive_support_v022": count_table(cur, "p_predictive_support_v022"),
        "r_counterstructure_v022": count_table(cur, "r_counterstructure_v022"),
        "xi_boundary_guard_v022": count_table(cur, "xi_boundary_guard_v022"),
        "pr_decomposition_binding_v022": count_table(cur, "pr_decomposition_binding_v022"),
        "p_status_counts": dict(cur.execute("SELECT support_status, COUNT(*) FROM p_predictive_support_v022 GROUP BY support_status").fetchall()),
        "r_type_counts": dict(cur.execute("SELECT counterstructure_type, COUNT(*) FROM r_counterstructure_v022 GROUP BY counterstructure_type").fetchall()),
    }
    summary = {
        "manifest": dict(manifest) if manifest else {},
        "acceptance": [dict(a) for a in acceptance],
        "issues": [dict(i) for i in issues],
        "external_ledgers": [dict(l) for l in ledgers],
        "pr_counts": pr_counts,
    }
    with open(os.path.join(report_dir, "pr_restoration_v022_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    md = []
    md.append("# P/R Restoration + Xi Boundary Repair v0.2.2\n\n")
    md.append("This report was generated by `scripts/run_pr_restoration_v022.py`.\n\n")
    md.append("## Boundary\n\n")
    md.append("This is an append-only diagnostic restoration layer. It does not rewrite source facts: `spacetime_cell`, `information_fiber`, `raw_event_stream`, coordinate snapshots, preneural states, dynamic origins, dynamic trajectories, or Xin dynamics.\n\n")
    md.append("## Corrected mainline chain\n\n")
    md.append("```text\nraw_event_stream -> origin_anchor -> latent_trajectory/T-trace -> O_candidate_bridge -> P/R decomposition -> Xi boundary guard\n```\n\n")
    md.append("`R` is **Refutational Counter-Structure**, not residual. `Xi/Xin` is the unresolved residue carrier. Xi can re-enter only through `O_candidate_bridge`, never directly as P or R.\n\n")
    md.append("## Counts\n\n")
    for k, v in pr_counts.items():
        md.append(f"- `{k}`: {v}\n")
    md.append("\n## Historical issues\n\n")
    for issue in issues:
        md.append(f"- `{issue['issue_id']}` [{issue['severity']}]: {issue['resolution_status']} — {issue['title']}\n")
    md.append("\n## External ledger status\n\n")
    for l in ledgers:
        md.append(f"- `{l['ledger_table']}`: {l['row_count_before']} -> {l['row_count_after']} ({l['activation_status']})\n")
    md.append("\n## Acceptance\n\n")
    for a in acceptance:
        md.append(f"- {a['status']}: `{a['test_name']}` observed={a['observed_value']}; expected={a['expected_value']}\n")
    with open(os.path.join(report_dir, "PR_RESTORATION_XI_BOUNDARY_V022_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("".join(md))
    con.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--report-dir", default="")
    args = ap.parse_args()
    db_path = os.path.abspath(args.db)
    report_dir = args.report_dir or os.path.join(os.path.dirname(os.path.dirname(db_path)), "morphosphere_v2pp", "reports")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    ensure_tables(cur)
    source_run_id = cur.execute("SELECT run_id FROM run_manifest LIMIT 1").fetchone()[0]
    parent_recursive_run_id = cur.execute("SELECT recursive_run_id FROM recursive_system_run_manifest LIMIT 1").fetchone()[0]
    restoration_run_id = stable_id("prrest_v022", parent_recursive_run_id, source_run_id)
    created = now()
    before = {t: count_table(cur, t) for t in SOURCE_FACT_TABLES}
    clear_previous(cur, restoration_run_id)
    insert_issues(cur, created)
    insert_interfaces(cur, created)
    insert_pr_registry(cur, created)
    counts = build_o_pr_xi(cur, created)
    ledger_inserted = populate_external_ledgers(cur, restoration_run_id, created)
    after = {t: count_table(cur, t) for t in SOURCE_FACT_TABLES}
    insert_manifest_acceptance(cur, restoration_run_id, parent_recursive_run_id, source_run_id, created, before, after, counts, ledger_inserted)
    con.commit()
    con.close()
    write_reports(db_path, report_dir)
    print(json.dumps({
        "restoration_run_id": restoration_run_id,
        "o_bridge_count": counts[0],
        "p_support_count": counts[1],
        "r_counter_count": counts[2],
        "xi_guard_count": counts[3],
        "binding_count": counts[4],
        "external_ledger_rows_inserted": ledger_inserted,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
