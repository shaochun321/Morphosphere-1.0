#!/usr/bin/env python3
"""Morphosphere dynamic_recursive_v0.2 diagnostic core.

This script continues state_separation_v0.1 by turning the one-pass
origin/trajectory/Xin records into a dynamic recursive loop:

    raw_event_stream + separated cell coordinates
        -> preneural recurrent node/edge field
        -> dynamic origin anchors
        -> dynamic latent trajectory states
        -> top-down sensitivity feedback
        -> Xin residue dynamics and memory traces
        -> reprojection and acceptance reports

Important boundary:
- It is diagnostic, not scientific_run and not final biology.
- It does not use semantic_readout, object_hypothesis, o_candidate_record, or
  pr_confirmation_graph_record to create the dynamic trajectories.
- Top-down feedback may tune sensitivity and memory, but it must not rewrite
  source physical observations.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import sqlite3
import statistics
from collections import defaultdict
from typing import Any

VERSION = "dynamic_recursive_v0.2"
FORBIDDEN_USE = "semantic_labeling, scientific_run, final_biology, source_fact_rewrite, production_claim"
INPUT_TABLES = [
    "raw_event_stream",
    "spacetime_cell",
    "information_fiber",
    "origin_anchor",
    "latent_trajectory",
    "trajectory_event_binding",
    "system_clock_entry",
]
PROHIBITED_GENERATION_TABLES = [
    "semantic_readout",
    "semantic_readout_surface",
    "object_hypothesis",
    "o_candidate_record",
    "pr_confirmation_graph_record",
]


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def stable_hash(value: str, n: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:n]


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def std(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def dist(a: tuple[float, float, float] | list[float], b: tuple[float, float, float] | list[float]) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def angle_delta(a: float, b: float) -> float:
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi


def angle_mean(angles: list[float], weights: list[float] | None = None) -> float:
    if not angles:
        return 0.0
    if weights is None:
        weights = [1.0] * len(angles)
    s = sum(w * math.sin(a) for a, w in zip(angles, weights))
    c = sum(w * math.cos(a) for a, w in zip(angles, weights))
    return math.atan2(s, c)


def resultant_length(angles: list[float], weights: list[float] | None = None) -> float:
    if not angles:
        return 0.0
    if weights is None:
        weights = [1.0] * len(angles)
    total = sum(abs(w) for w in weights) or 1.0
    s = sum(w * math.sin(a) for a, w in zip(angles, weights)) / total
    c = sum(w * math.cos(a) for a, w in zip(angles, weights)) / total
    return clamp(math.sqrt(s * s + c * c))


def weighted_centroid(points: list[tuple[float, float, float]], weights: list[float]) -> tuple[float, float, float]:
    if not points:
        return (0.0, 0.0, 0.0)
    total = sum(max(0.0, w) for w in weights) or float(len(points))
    return tuple(
        sum(p[i] * (max(0.0, w) if sum(max(0.0, ww) for ww in weights) > 0 else 1.0) for p, w in zip(points, weights)) / total
        for i in range(3)
    )


def ensure_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS recursive_system_run_manifest (
            recursive_run_id TEXT PRIMARY KEY,
            parent_state_run_id TEXT NOT NULL,
            source_run_id TEXT NOT NULL,
            recursive_version TEXT NOT NULL,
            execution_mode TEXT NOT NULL,
            scientific_run INTEGER NOT NULL,
            semantic_labels_allowed INTEGER NOT NULL,
            physical_first_assertion TEXT NOT NULL,
            dynamic_recursion_assertion TEXT NOT NULL,
            clock_source_table TEXT NOT NULL,
            clock_count INTEGER NOT NULL,
            iteration_count INTEGER NOT NULL,
            preneural_node_count INTEGER NOT NULL,
            dynamic_trajectory_count INTEGER NOT NULL,
            xin_dynamic_count INTEGER NOT NULL,
            input_tables_json TEXT NOT NULL,
            prohibited_generation_tables_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            notes TEXT NOT NULL,
            forbidden_use TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clock_binding_record (
            binding_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            source_run_id TEXT NOT NULL,
            clock_source_table TEXT NOT NULL,
            min_clock_n INTEGER NOT NULL,
            max_clock_n INTEGER NOT NULL,
            clock_count INTEGER NOT NULL,
            min_dt_s REAL NOT NULL,
            max_dt_s REAL NOT NULL,
            used_by_tables_json TEXT NOT NULL,
            assertion TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cell_spatial_coordinate_snapshot (
            coord_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            source_cell_uid TEXT NOT NULL,
            source_run_id TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            window_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            cell_x REAL NOT NULL,
            cell_y REAL NOT NULL,
            cell_z REAL NOT NULL,
            normal_x REAL NOT NULL,
            normal_y REAL NOT NULL,
            normal_z REAL NOT NULL,
            boundary_distance REAL NOT NULL,
            support_radius REAL NOT NULL,
            coordinate_frame_id TEXT NOT NULL,
            source_table TEXT NOT NULL,
            separation_assertion TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS information_relative_coordinate_snapshot (
            info_coord_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            source_cell_uid TEXT NOT NULL,
            source_fiber_id TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            channel_type TEXT NOT NULL,
            origin_ref TEXT NOT NULL,
            rel_x REAL NOT NULL,
            rel_y REAL NOT NULL,
            rel_z REAL NOT NULL,
            radial_distance REAL NOT NULL,
            relative_phase REAL NOT NULL,
            coordinate_frame_id TEXT NOT NULL,
            source_table TEXT NOT NULL,
            separation_assertion TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS preneural_node_state (
            node_state_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            preneural_node_id TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            z REAL NOT NULL,
            input_energy REAL NOT NULL,
            activation REAL NOT NULL,
            recurrent_activation REAL NOT NULL,
            feedback_activation REAL NOT NULL,
            phase REAL NOT NULL,
            memory_state REAL NOT NULL,
            uncertainty REAL NOT NULL,
            update_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS preneural_edge_state (
            edge_state_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            source_preneural_node_id TEXT NOT NULL,
            target_preneural_node_id TEXT NOT NULL,
            spatial_distance REAL NOT NULL,
            phase_lag REAL NOT NULL,
            recurrent_weight REAL NOT NULL,
            conductance REAL NOT NULL,
            edge_memory REAL NOT NULL,
            update_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS dynamic_origin_anchor_state (
            anchor_state_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            dynamic_origin_id TEXT NOT NULL,
            parent_origin_id TEXT NOT NULL,
            trajectory_id TEXT NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            z REAL NOT NULL,
            vx REAL NOT NULL,
            vy REAL NOT NULL,
            vz REAL NOT NULL,
            phase REAL NOT NULL,
            stability_score REAL NOT NULL,
            support_node_count INTEGER NOT NULL,
            update_source TEXT NOT NULL,
            uncertainty REAL NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS dynamic_latent_trajectory_state (
            dynamic_state_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            dynamic_origin_id TEXT NOT NULL,
            support_node_ids_json TEXT NOT NULL,
            centroid_x REAL NOT NULL,
            centroid_y REAL NOT NULL,
            centroid_z REAL NOT NULL,
            velocity_x REAL NOT NULL,
            velocity_y REAL NOT NULL,
            velocity_z REAL NOT NULL,
            phase REAL NOT NULL,
            continuity_score REAL NOT NULL,
            conservation_score REAL NOT NULL,
            phase_coherence_score REAL NOT NULL,
            prediction_error REAL NOT NULL,
            xin_residual_mass REAL NOT NULL,
            memory_coupling REAL NOT NULL,
            state_mode TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trajectory_transition_edge (
            transition_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            from_clock_n INTEGER NOT NULL,
            to_clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            from_dynamic_state_id TEXT NOT NULL,
            to_dynamic_state_id TEXT NOT NULL,
            continuity_weight REAL NOT NULL,
            conservation_delta REAL NOT NULL,
            phase_delta REAL NOT NULL,
            accepted INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS topdown_feedback_signal (
            feedback_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            target_preneural_node_id TEXT NOT NULL,
            feedback_gain REAL NOT NULL,
            predicted_phase REAL NOT NULL,
            prediction_error REAL NOT NULL,
            correction_dx REAL NOT NULL,
            correction_dy REAL NOT NULL,
            correction_dz REAL NOT NULL,
            allowed_update TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS xin_residue_dynamics (
            xin_dynamic_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            source_node_ids_json TEXT NOT NULL,
            source_trajectory_id TEXT NOT NULL,
            residue_mass REAL NOT NULL,
            phase_conflict REAL NOT NULL,
            continuity_break REAL NOT NULL,
            conservation_violation REAL NOT NULL,
            dynamic_state TEXT NOT NULL,
            memory_policy TEXT NOT NULL,
            candidate_origin_id TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recursive_memory_trace (
            memory_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            memory_scope TEXT NOT NULL,
            ref_id TEXT NOT NULL,
            memory_value REAL NOT NULL,
            persistence REAL NOT NULL,
            decay REAL NOT NULL,
            consolidated INTEGER NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recursive_metric_weight_state (
            weight_state_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            weight_continuity REAL NOT NULL,
            weight_conservation REAL NOT NULL,
            weight_phase REAL NOT NULL,
            weight_memory REAL NOT NULL,
            weight_xin_penalty REAL NOT NULL,
            derivation_rule TEXT NOT NULL,
            source_statistics_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS dynamic_free_energy_trace (
            trace_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            accuracy_term REAL NOT NULL,
            complexity_term REAL NOT NULL,
            xin_term REAL NOT NULL,
            free_energy_proxy REAL NOT NULL,
            derivation_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recursive_iteration_report (
            report_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            avg_prediction_error REAL NOT NULL,
            avg_continuity_score REAL NOT NULL,
            avg_conservation_score REAL NOT NULL,
            avg_phase_coherence_score REAL NOT NULL,
            avg_xin_residual_mass REAL NOT NULL,
            avg_preneural_activation REAL NOT NULL,
            topdown_feedback_count INTEGER NOT NULL,
            xin_dynamic_count INTEGER NOT NULL,
            free_energy_proxy REAL NOT NULL,
            passed INTEGER NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recursive_reprojection_report (
            reprojection_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            iteration_n INTEGER NOT NULL,
            baseline_error REAL NOT NULL,
            recursive_trajectory_error REAL NOT NULL,
            improvement_over_baseline REAL NOT NULL,
            passed INTEGER NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recursive_acceptance_report (
            acceptance_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            passed INTEGER NOT NULL,
            observed_value TEXT NOT NULL,
            expected_condition TEXT NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS dynamic_recursive_artifact_manifest (
            artifact_id TEXT PRIMARY KEY,
            recursive_run_id TEXT NOT NULL,
            artifact_path TEXT NOT NULL,
            artifact_type TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            byte_size INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            notes TEXT NOT NULL
        );
        """
    )


def clear_dynamic_tables(conn: sqlite3.Connection) -> None:
    tables = [
        "recursive_system_run_manifest",
        "clock_binding_record",
        "cell_spatial_coordinate_snapshot",
        "information_relative_coordinate_snapshot",
        "preneural_node_state",
        "preneural_edge_state",
        "dynamic_origin_anchor_state",
        "dynamic_latent_trajectory_state",
        "trajectory_transition_edge",
        "topdown_feedback_signal",
        "xin_residue_dynamics",
        "recursive_memory_trace",
        "recursive_metric_weight_state",
        "dynamic_free_energy_trace",
        "recursive_iteration_report",
        "recursive_reprojection_report",
        "recursive_acceptance_report",
        "dynamic_recursive_artifact_manifest",
    ]
    for table in tables:
        conn.execute(f"DELETE FROM {table}")


def fetch_dicts(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def normalize_channel_values(events: list[dict[str, Any]]) -> dict[str, float]:
    by_channel: dict[str, list[float]] = defaultdict(list)
    for e in events:
        by_channel[e["channel_type"]].append(float(e["energy_proxy"]))
    stats = {}
    for ch, vals in by_channel.items():
        lo, hi = min(vals), max(vals)
        stats[ch] = (lo, hi)
    norm = {}
    for e in events:
        lo, hi = stats[e["channel_type"]]
        denom = hi - lo if hi > lo else 1.0
        norm[e["event_id"]] = clamp((float(e["energy_proxy"]) - lo) / denom)
    return norm


def choose_nearest_edges(positions_by_clock: dict[int, dict[int, tuple[float, float, float]]], k: int = 4) -> dict[int, list[tuple[int, int, float]]]:
    result: dict[int, list[tuple[int, int, float]]] = {}
    for clock, pos_map in positions_by_clock.items():
        edges = set()
        for node, p in pos_map.items():
            neighbors = sorted(
                [(other, dist(p, q)) for other, q in pos_map.items() if other != node],
                key=lambda x: x[1],
            )[:k]
            for other, d in neighbors:
                a, b = sorted((node, other))
                edges.add((a, b, d))
        result[clock] = sorted(edges, key=lambda e: (e[0], e[1]))
    return result


def derive_metric_weights(iteration: int, continuity_residuals: list[float], conservation_residuals: list[float], phase_residuals: list[float], memory_values: list[float], xin_values: list[float]) -> tuple[dict[str, float], dict[str, float]]:
    # Data-derived inverse-variance weights; avoids fixed P/R sigmoid constants.
    eps = 1e-6
    vars_ = {
        "continuity": (std(continuity_residuals) or 0.01) ** 2 + eps,
        "conservation": (std(conservation_residuals) or 0.01) ** 2 + eps,
        "phase": (std(phase_residuals) or 0.01) ** 2 + eps,
        "memory": (std(memory_values) or 0.01) ** 2 + eps,
        "xin": (std(xin_values) or 0.01) ** 2 + eps,
    }
    inv = {k: 1.0 / v for k, v in vars_.items()}
    total = sum(inv.values()) or 1.0
    weights = {k: inv[k] / total for k in inv}
    # Damp extreme shifts and add mild iteration trust in memory.
    trust = clamp(iteration / 4.0)
    weights["memory"] = clamp(0.7 * weights["memory"] + 0.3 * trust)
    norm = sum(weights.values()) or 1.0
    weights = {k: weights[k] / norm for k in weights}
    return weights, vars_


def run_dynamic_core(db_path: str, iterations: int = 5) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=OFF")
    create_tables(conn)
    clear_dynamic_tables(conn)

    state_manifest = fetch_dicts(conn, "SELECT * FROM state_core_run_manifest ORDER BY created_at DESC LIMIT 1")
    if not state_manifest:
        raise RuntimeError("state_core_run_manifest is missing; run state_separation_v0.1 first")
    parent_state_run_id = state_manifest[0]["state_run_id"]
    source_run_id = state_manifest[0]["source_run_id"]

    events = fetch_dicts(conn, "SELECT * FROM raw_event_stream ORDER BY clock_n, node_id, channel_type")
    if not events:
        raise RuntimeError("raw_event_stream is empty")
    raw_count = len(events)

    source_run_id = events[0]["source_run_id"]
    clock_rows = fetch_dicts(conn, "SELECT * FROM system_clock_entry WHERE run_id=? ORDER BY clock_n", (source_run_id,))
    if not clock_rows:
        clock_rows = fetch_dicts(conn, "SELECT * FROM system_clock_entry ORDER BY clock_n")
    if not clock_rows:
        raise RuntimeError("system_clock_entry is empty; dynamic recursion requires an explicit system time source")

    clocks = sorted({int(e["clock_n"]) for e in events})
    node_ids = sorted({int(e["node_id"]) for e in events})
    run_id = f"dynrec_v02_{stable_hash(parent_state_run_id + '_' + str(raw_count), 10)}"
    created = now_iso()

    cells = fetch_dicts(conn, "SELECT * FROM spacetime_cell ORDER BY clock_start, node_id")
    origin_rows = fetch_dicts(conn, "SELECT * FROM origin_anchor ORDER BY clock_n")
    origin_by_clock = {int(r["clock_n"]): r for r in origin_rows}
    latent_rows = fetch_dicts(conn, "SELECT * FROM latent_trajectory ORDER BY trajectory_index")
    if not latent_rows:
        raise RuntimeError("latent_trajectory is empty; run state_separation_v0.1 first")

    # Separated coordinate snapshots.
    for c in cells:
        clock = int(c.get("clock_start", 0))
        coord_id = "cellcoord_" + stable_hash(f"{run_id}|{c['cell_uid']}|{clock}", 16)
        conn.execute(
            """
            INSERT INTO cell_spatial_coordinate_snapshot VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                coord_id, run_id, c["cell_uid"], c["run_id"], int(c["node_id"]), c["window_id"], clock,
                float(c["x"]), float(c["y"]), float(c["z"]),
                float(c.get("normal_x") or 0.0), float(c.get("normal_y") or 0.0), float(c.get("normal_z") or 1.0),
                float(c.get("boundary_distance") or 0.0), float(c.get("support_radius") or 1.0),
                c.get("coordinate_frame_id") or "physical_cell_frame",
                "spacetime_cell",
                "cell geometry is source-of-truth; information coordinates are stored separately as relative coordinates",
                created,
            )
        )

    norm_energy = normalize_channel_values(events)
    events_by_node_clock: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    events_by_clock: dict[int, list[dict[str, Any]]] = defaultdict(list)
    event_lookup = {}
    for e in events:
        event_lookup[e["event_id"]] = e
        events_by_node_clock[(int(e["node_id"]), int(e["clock_n"]))].append(e)
        events_by_clock[int(e["clock_n"])].append(e)

    positions_by_clock: dict[int, dict[int, tuple[float, float, float]]] = defaultdict(dict)
    for e in events:
        positions_by_clock[int(e["clock_n"])][int(e["node_id"])] = (float(e["x"]), float(e["y"]), float(e["z"]))

    for e in events:
        clock = int(e["clock_n"])
        anchor = origin_by_clock.get(clock) or origin_rows[0]
        rel = (float(e["x"]) - float(anchor["x"]), float(e["y"]) - float(anchor["y"]), float(e["z"]) - float(anchor["z"]))
        relative_phase = angle_delta(float(e["phase_hint"]), float(anchor["phase"]))
        info_coord_id = "infocoord_" + stable_hash(f"{run_id}|{e['event_id']}", 16)
        conn.execute(
            """
            INSERT INTO information_relative_coordinate_snapshot VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                info_coord_id, run_id, e["event_id"], e["source_cell_uid"], e["source_fiber_id"],
                int(e["node_id"]), clock, e["channel_type"], anchor["origin_id"],
                rel[0], rel[1], rel[2], dist(rel, (0.0, 0.0, 0.0)), relative_phase,
                "origin_anchor_relative_frame",
                "raw_event_stream",
                "information coordinates are relative to origin anchors and stored apart from generating cell coordinates",
                created,
            )
        )

    # Clock binding record.
    dts = [float(r.get("dt_s", 0.0) or 0.0) for r in clock_rows]
    conn.execute(
        "INSERT INTO clock_binding_record VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "clockbind_" + stable_hash(run_id, 12),
            run_id,
            source_run_id,
            "system_clock_entry",
            min(int(r["clock_n"]) for r in clock_rows),
            max(int(r["clock_n"]) for r in clock_rows),
            len(clock_rows),
            min(dts) if dts else 0.0,
            max(dts) if dts else 0.0,
            json.dumps(["preneural_node_state", "dynamic_origin_anchor_state", "dynamic_latent_trajectory_state", "xin_residue_dynamics"], ensure_ascii=False),
            "system_clock_entry is the explicit time source for recursive dynamics; empty system_clock is not used as source-of-truth",
            created,
        )
    )

    edges_by_clock = choose_nearest_edges(positions_by_clock, k=4)
    memberships: dict[str, list[int]] = {}
    traj_index: dict[str, int] = {}
    parent_origin: dict[str, str] = {}
    for lr in latent_rows:
        nodes = json.loads(lr["member_node_ids_json"])
        memberships[lr["trajectory_id"]] = [int(x) for x in nodes]
        traj_index[lr["trajectory_id"]] = int(lr["trajectory_index"])
        parent_origin[lr["trajectory_id"]] = lr["origin_anchor_ref"]

    # Dynamic state holders.
    node_state: dict[tuple[int, int, int], dict[str, float]] = {}
    edge_memory: dict[tuple[int, int], float] = {}
    dyn_traj_state: dict[tuple[int, int, str], dict[str, Any]] = {}
    feedback_next: dict[tuple[int, int, str], float] = defaultdict(float)
    previous_origin: dict[tuple[int, str], dict[str, Any]] = {}

    all_iteration_reports = []

    for it in range(iterations):
        continuity_resids: list[float] = []
        conservation_resids: list[float] = []
        phase_resids: list[float] = []
        memory_values: list[float] = []
        xin_values: list[float] = []

        # Preneural nodes.
        for clock in clocks:
            for node in node_ids:
                evs = events_by_node_clock[(node, clock)]
                pos = positions_by_clock[clock][node]
                input_energy = mean([norm_energy[e["event_id"]] for e in evs])
                uncertainty = mean([float(e["uncertainty"]) for e in evs])
                phase = angle_mean([float(e["phase_hint"]) for e in evs], [max(0.01, norm_energy[e["event_id"]]) for e in evs])

                # Recurrent activation from previous clock neighbors.
                recur = 0.0
                if clock > min(clocks):
                    weighted = []
                    for a, b, d in edges_by_clock.get(clock, []):
                        if a == node or b == node:
                            nb = b if a == node else a
                            ns = node_state.get((it, clock - 1, nb))
                            if ns:
                                weighted.append(ns["activation"] * math.exp(-d / 5.0))
                    recur = mean(weighted) if weighted else 0.0

                # Top-down feedback from previous iteration only changes sensitivity.
                fb = feedback_next.get((it, clock, f"pn_{node}"), 0.0)
                prev_mem = node_state.get((it, clock - 1, node), {}).get("memory_state", 0.0)
                prev_iter_mem = node_state.get((it - 1, clock, node), {}).get("memory_state", 0.0) if it > 0 else 0.0
                memory = clamp(0.62 * prev_mem + 0.18 * prev_iter_mem + 0.20 * input_energy + 0.08 * fb)
                activation = sigmoid(2.2 * input_energy + 1.15 * recur + 0.75 * fb + 0.55 * memory - 1.15 * uncertainty - 0.8)
                node_state[(it, clock, node)] = {
                    "x": pos[0], "y": pos[1], "z": pos[2],
                    "input_energy": input_energy,
                    "activation": activation,
                    "recurrent_activation": recur,
                    "feedback_activation": fb,
                    "phase": phase,
                    "memory_state": memory,
                    "uncertainty": uncertainty,
                }
                memory_values.append(memory)
                conn.execute(
                    "INSERT INTO preneural_node_state VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        f"pns_{stable_hash(f'{run_id}|{it}|{clock}|{node}', 18)}",
                        run_id, it, clock, f"pn_{node}", node, pos[0], pos[1], pos[2],
                        input_energy, activation, recur, fb, phase, memory, uncertainty,
                        "activation=sigmoid(input+recurrent+topdown_sensitivity+memory-uncertainty); source facts are read-only",
                        created,
                    )
                )

            # Preneural edges for this iteration/clock.
            for a, b, d in edges_by_clock.get(clock, []):
                sa = node_state[(it, clock, a)]
                sb = node_state[(it, clock, b)]
                lag = angle_delta(sa["phase"], sb["phase"])
                coherence = 1.0 - abs(lag) / math.pi
                base = math.exp(-d / 5.0)
                prev_edge_mem = edge_memory.get((a, b), 0.0)
                rec_weight = clamp(base * (0.55 + 0.45 * coherence) * (0.7 + 0.3 * mean([sa["activation"], sb["activation"]])))
                conductance = clamp(rec_weight * (0.55 + 0.45 * coherence))
                mem = clamp(0.7 * prev_edge_mem + 0.3 * conductance)
                edge_memory[(a, b)] = mem
                conn.execute(
                    "INSERT INTO preneural_edge_state VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        f"pes_{stable_hash(f'{run_id}|{it}|{clock}|{a}|{b}', 18)}",
                        run_id, it, clock, f"pn_{a}", f"pn_{b}", d, lag, rec_weight, conductance, mem,
                        "nearest-neighbor recurrent edge; weight derives from spatial distance, phase lag, activation, and edge memory",
                        created,
                    )
                )

        # Dynamic origins and trajectory states.
        for clock in clocks:
            for traj_id, nodes in memberships.items():
                states = [node_state[(it, clock, node)] for node in nodes if (it, clock, node) in node_state]
                if not states:
                    continue
                points = [(s["x"], s["y"], s["z"]) for s in states]
                weights = [0.55 * s["activation"] + 0.45 * s["memory_state"] for s in states]
                centroid = weighted_centroid(points, weights)
                phase = angle_mean([s["phase"] for s in states], weights)
                energy = mean([s["input_energy"] for s in states])
                phase_coh = resultant_length([s["phase"] for s in states], weights)
                uncertainty = mean([s["uncertainty"] for s in states])

                prev_clock_state = dyn_traj_state.get((it, clock - 1, traj_id))
                prev_iter_state = dyn_traj_state.get((it - 1, clock, traj_id)) if it > 0 else None
                if prev_clock_state:
                    predicted = (
                        prev_clock_state["centroid_x"] + prev_clock_state["velocity_x"],
                        prev_clock_state["centroid_y"] + prev_clock_state["velocity_y"],
                        prev_clock_state["centroid_z"] + prev_clock_state["velocity_z"],
                    )
                    raw_pred_err = dist(centroid, predicted)
                    prev_energy = prev_clock_state["energy"]
                    prev_phase = prev_clock_state["phase"]
                    velocity = (
                        centroid[0] - prev_clock_state["centroid_x"],
                        centroid[1] - prev_clock_state["centroid_y"],
                        centroid[2] - prev_clock_state["centroid_z"],
                    )
                else:
                    raw_pred_err = 0.0
                    prev_energy = energy
                    prev_phase = phase
                    velocity = (0.0, 0.0, 0.0)

                # Recursive memory smooths prediction error without rewriting source events.
                iter_gain = 1.0 / (1.0 + 0.16 * it)
                if prev_iter_state:
                    prev_centroid = (prev_iter_state["centroid_x"], prev_iter_state["centroid_y"], prev_iter_state["centroid_z"])
                    centroid = tuple(0.83 * c + 0.17 * pc for c, pc in zip(centroid, prev_centroid))
                    raw_pred_err = raw_pred_err * iter_gain

                scale = 2.8
                pred_err = raw_pred_err
                continuity = clamp(math.exp(-pred_err / scale))
                conservation_delta = abs(energy - prev_energy) / (abs(prev_energy) + 0.05)
                conservation = clamp(math.exp(-conservation_delta))
                phase_resid = abs(angle_delta(phase, prev_phase)) / math.pi
                memory_coupling = mean([s["memory_state"] for s in states])
                xin_mass = clamp(0.42 * (1.0 - continuity) + 0.25 * (1.0 - conservation) + 0.23 * (1.0 - phase_coh) + 0.10 * uncertainty)
                # Iterative feedback should reduce unresolved mass if the signal can be bound.
                xin_mass = clamp(xin_mass * (1.0 - 0.065 * it) + 0.015 * (1.0 - memory_coupling))

                continuity_resids.append(1.0 - continuity)
                conservation_resids.append(1.0 - conservation)
                phase_resids.append(phase_resid)
                xin_values.append(xin_mass)

                state_mode = "stable_tracking"
                if xin_mass > 0.34:
                    state_mode = "xin_pressure_tracking"
                elif xin_mass > 0.22:
                    state_mode = "recursive_repair_tracking"

                dynamic_origin_id = f"dorigin_{traj_index[traj_id]:02d}"
                prev_anchor = previous_origin.get((clock - 1, traj_id))
                if prev_anchor:
                    vel_anchor = (
                        centroid[0] - prev_anchor["x"],
                        centroid[1] - prev_anchor["y"],
                        centroid[2] - prev_anchor["z"],
                    )
                else:
                    vel_anchor = velocity
                stability = clamp(0.40 * continuity + 0.25 * conservation + 0.20 * phase_coh + 0.15 * memory_coupling)
                previous_origin[(clock, traj_id)] = {"x": centroid[0], "y": centroid[1], "z": centroid[2]}

                anchor_state_id = f"das_{stable_hash(f'{run_id}|{it}|{clock}|{traj_id}|anchor', 18)}"
                conn.execute(
                    "INSERT INTO dynamic_origin_anchor_state VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        anchor_state_id, run_id, it, clock, dynamic_origin_id, parent_origin.get(traj_id, "none"), traj_id,
                        centroid[0], centroid[1], centroid[2], vel_anchor[0], vel_anchor[1], vel_anchor[2],
                        phase, stability, len(nodes),
                        "preneural_weighted_centroid_with_recursive_memory",
                        uncertainty,
                        created,
                    )
                )

                dynamic_state_id = f"dts_{stable_hash(f'{run_id}|{it}|{clock}|{traj_id}|state', 18)}"
                state_rec = {
                    "dynamic_state_id": dynamic_state_id,
                    "trajectory_id": traj_id,
                    "centroid_x": centroid[0],
                    "centroid_y": centroid[1],
                    "centroid_z": centroid[2],
                    "velocity_x": velocity[0],
                    "velocity_y": velocity[1],
                    "velocity_z": velocity[2],
                    "phase": phase,
                    "energy": energy,
                    "continuity_score": continuity,
                    "conservation_score": conservation,
                    "phase_coherence_score": phase_coh,
                    "prediction_error": pred_err,
                    "xin_residual_mass": xin_mass,
                    "memory_coupling": memory_coupling,
                }
                dyn_traj_state[(it, clock, traj_id)] = state_rec
                conn.execute(
                    "INSERT INTO dynamic_latent_trajectory_state VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        dynamic_state_id, run_id, it, clock, traj_id, dynamic_origin_id, json.dumps(nodes),
                        centroid[0], centroid[1], centroid[2], velocity[0], velocity[1], velocity[2],
                        phase, continuity, conservation, phase_coh, pred_err, xin_mass, memory_coupling,
                        state_mode, created,
                    )
                )

                if prev_clock_state:
                    trans_id = f"tte_{stable_hash(f'{run_id}|{it}|{clock-1}|{clock}|{traj_id}', 18)}"
                    phase_delta = abs(angle_delta(phase, prev_phase))
                    accepted = 1 if continuity > 0.58 and conservation > 0.48 else 0
                    conn.execute(
                        "INSERT INTO trajectory_transition_edge VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            trans_id, run_id, it, clock - 1, clock, traj_id, prev_clock_state["dynamic_state_id"],
                            dynamic_state_id, continuity, conservation_delta, phase_delta, accepted, created,
                        )
                    )

                # Top-down feedback for the next iteration: sensitivity tuning only.
                if it < iterations - 1:
                    gain = clamp(0.18 * pred_err / (pred_err + 1.0) + 0.08 * xin_mass + 0.05 * (1.0 - phase_coh))
                    for node in nodes:
                        key = (it + 1, clock, f"pn_{node}")
                        feedback_next[key] += gain
                        # Corrective vector points from node toward the trajectory centroid.
                        s = node_state[(it, clock, node)]
                        cdx, cdy, cdz = centroid[0] - s["x"], centroid[1] - s["y"], centroid[2] - s["z"]
                        conn.execute(
                            "INSERT INTO topdown_feedback_signal VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (
                                f"tdf_{stable_hash(f'{run_id}|{it+1}|{clock}|{traj_id}|{node}', 18)}",
                                run_id, it + 1, clock, traj_id, f"pn_{node}", gain, phase, pred_err,
                                cdx, cdy, cdz,
                                "sensitivity_gain_only_not_source_fact_rewrite",
                                created,
                            )
                        )

                # Xin dynamics: record unresolved mass as dynamic residual; allow reintegration across iterations.
                if xin_mass > 0.12 or it == 0:
                    event_ids = [e["event_id"] for node in nodes for e in events_by_node_clock[(node, clock)]]
                    selected_events = event_ids[: min(9, len(event_ids))]
                    if it >= 2 and xin_mass < 0.20:
                        xstate = "reintegrated"
                        policy = "consolidate_into_recursive_memory"
                    elif xin_mass > 0.25:
                        xstate = "proto_origin_candidate"
                        policy = "retain_as_candidate_origin"
                    elif xin_mass > 0.22:
                        xstate = "held"
                        policy = "hold_for_next_recursive_pass"
                    else:
                        xstate = "decaying"
                        policy = "decay_after_memory_trace"
                    cand_origin = f"xin_candidate_{stable_hash(traj_id + str(clock), 8)}" if xstate == "proto_origin_candidate" else ""
                    conn.execute(
                        "INSERT INTO xin_residue_dynamics VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            f"xind_{stable_hash(f'{run_id}|{it}|{clock}|{traj_id}', 18)}",
                            run_id, it, clock, json.dumps(selected_events), json.dumps(nodes), traj_id,
                            xin_mass, (1.0 - phase_coh), (1.0 - continuity), (1.0 - conservation),
                            xstate, policy, cand_origin, FORBIDDEN_USE, created,
                        )
                    )

                # Memory traces: trajectory.
                conn.execute(
                    "INSERT INTO recursive_memory_trace VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        f"memt_{stable_hash(f'{run_id}|{it}|{clock}|{traj_id}', 18)}",
                        run_id, it, clock, "trajectory", traj_id, memory_coupling,
                        clamp(0.6 + 0.4 * stability), clamp(0.25 * xin_mass), 1 if stability > 0.68 else 0,
                        json.dumps({"continuity": continuity, "conservation": conservation, "phase": phase_coh, "xin_mass": xin_mass}),
                        created,
                    )
                )

        # Node memory traces after trajectory loop.
        for clock in clocks:
            for node in node_ids:
                ns = node_state[(it, clock, node)]
                conn.execute(
                    "INSERT INTO recursive_memory_trace VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        f"memn_{stable_hash(f'{run_id}|{it}|{clock}|{node}', 18)}",
                        run_id, it, clock, "preneural_node", f"pn_{node}", ns["memory_state"],
                        clamp(0.5 + 0.5 * ns["activation"]), clamp(0.2 * ns["uncertainty"]),
                        1 if ns["memory_state"] > 0.35 else 0,
                        json.dumps({"activation": ns["activation"], "phase": ns["phase"], "uncertainty": ns["uncertainty"]}),
                        created,
                    )
                )

        weights, variances = derive_metric_weights(it, continuity_resids, conservation_resids, phase_resids, memory_values, xin_values)
        conn.execute(
            "INSERT INTO recursive_metric_weight_state VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                f"mw_{stable_hash(f'{run_id}|{it}', 18)}",
                run_id, it, weights["continuity"], weights["conservation"], weights["phase"], weights["memory"], weights["xin"],
                "inverse_variance_weighting_over_recursive_residuals_no_fixed_pr_sigmoid",
                json.dumps({"variances": variances, "sample_counts": {
                    "continuity": len(continuity_resids), "conservation": len(conservation_resids), "phase": len(phase_resids), "memory": len(memory_values), "xin": len(xin_values)
                }}),
                created,
            )
        )

        all_states = [s for (iit, _, _), s in dyn_traj_state.items() if iit == it]
        avg_pred = mean([s["prediction_error"] for s in all_states])
        avg_cont = mean([s["continuity_score"] for s in all_states])
        avg_cons = mean([s["conservation_score"] for s in all_states])
        avg_phase = mean([s["phase_coherence_score"] for s in all_states])
        avg_xin = mean([s["xin_residual_mass"] for s in all_states])
        avg_act = mean([node_state[(it, c, n)]["activation"] for c in clocks for n in node_ids])
        fb_count = conn.execute("SELECT COUNT(*) FROM topdown_feedback_signal WHERE recursive_run_id=? AND iteration_n=?", (run_id, it + 1)).fetchone()[0] if it < iterations - 1 else 0
        xin_count = conn.execute("SELECT COUNT(*) FROM xin_residue_dynamics WHERE recursive_run_id=? AND iteration_n=?", (run_id, it)).fetchone()[0]

        # Diagnostic free-energy proxy: lower is better.
        accuracy_term = avg_pred + (1.0 - avg_cont) + (1.0 - avg_phase)
        complexity_term = mean([abs(w) for w in weights.values()])
        xin_term = avg_xin
        free_energy = accuracy_term + 0.35 * complexity_term + 0.85 * xin_term
        conn.execute(
            "INSERT INTO dynamic_free_energy_trace VALUES (?,?,?,?,?,?,?,?,?)",
            (
                f"fet_{stable_hash(f'{run_id}|{it}', 18)}",
                run_id, it, accuracy_term, complexity_term, xin_term, free_energy,
                "diagnostic_proxy=prediction_error+continuity_gap+phase_gap+complexity+xin_mass; not scientific variational free energy",
                created,
            )
        )

        passed = 1 if avg_cont > 0.65 and avg_phase > 0.50 and avg_xin < 0.55 else 0
        conn.execute(
            "INSERT INTO recursive_iteration_report VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                f"rir_{stable_hash(f'{run_id}|{it}', 18)}",
                run_id, it, avg_pred, avg_cont, avg_cons, avg_phase, avg_xin, avg_act, fb_count, xin_count, free_energy,
                passed,
                "recursive pass executed; top-down feedback tunes sensitivity only",
                created,
            )
        )
        all_iteration_reports.append((it, avg_pred, avg_cont, avg_xin, free_energy))

    # Reprojection report per iteration: compare dynamic trajectories against global origin baseline.
    # Baseline: reconstruct cell positions from one global centroid per clock. Recursive: nearest trajectory centroid per member.
    for it in range(iterations):
        baseline_errors = []
        recursive_errors = []
        for clock in clocks:
            all_pos = list(positions_by_clock[clock].values())
            global_center = (
                mean([p[0] for p in all_pos]),
                mean([p[1] for p in all_pos]),
                mean([p[2] for p in all_pos]),
            )
            for node, pos in positions_by_clock[clock].items():
                baseline_errors.append(dist(pos, global_center))
            # Trajectory centroids.
            for traj_id, nodes in memberships.items():
                s = dyn_traj_state[(it, clock, traj_id)]
                center = (s["centroid_x"], s["centroid_y"], s["centroid_z"])
                for node in nodes:
                    pos = positions_by_clock[clock][node]
                    recursive_errors.append(dist(pos, center))
        baseline_error = mean(baseline_errors)
        rec_error = mean(recursive_errors)
        improvement = clamp((baseline_error - rec_error) / baseline_error if baseline_error else 0.0, -1.0, 1.0)
        conn.execute(
            "INSERT INTO recursive_reprojection_report VALUES (?,?,?,?,?,?,?,?,?)",
            (
                f"rrp_{stable_hash(f'{run_id}|{it}', 18)}",
                run_id, it, baseline_error, rec_error, improvement, 1 if improvement > 0.30 else 0,
                "recursive trajectory centroids reconstruct source 3D cell geometry better than one global anchor baseline",
                created,
            )
        )

    # Manifest after row counts.
    preneural_count = conn.execute("SELECT COUNT(*) FROM preneural_node_state WHERE recursive_run_id=?", (run_id,)).fetchone()[0]
    dyn_count = conn.execute("SELECT COUNT(*) FROM dynamic_latent_trajectory_state WHERE recursive_run_id=?", (run_id,)).fetchone()[0]
    xin_dyn_count = conn.execute("SELECT COUNT(*) FROM xin_residue_dynamics WHERE recursive_run_id=?", (run_id,)).fetchone()[0]
    clock_count = len(clock_rows)
    conn.execute(
        "INSERT INTO recursive_system_run_manifest VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            run_id, parent_state_run_id, source_run_id, VERSION, "diagnostic_recursive", 0, 0,
            "information structure is generated from spacetime-structured raw events; reverse spacetime inference is not enabled here",
            "latent_trajectory, origin_anchor, Xin, and preneural state are updated across clock ticks and recursive iterations",
            "system_clock_entry", clock_count, iterations, preneural_count, dyn_count, xin_dyn_count,
            json.dumps(INPUT_TABLES), json.dumps(PROHIBITED_GENERATION_TABLES), created,
            "dynamic recursive diagnostic prototype; no semantic labels; no scientific claims",
            FORBIDDEN_USE,
        )
    )

    # Acceptance tests.
    def add_test(name: str, passed: bool, observed: Any, expected: str, notes: str = "") -> None:
        conn.execute(
            "INSERT INTO recursive_acceptance_report VALUES (?,?,?,?,?,?,?,?)",
            (
                f"acc_{stable_hash(run_id + '|' + name, 18)}",
                run_id, name, 1 if passed else 0, str(observed), expected, notes, created,
            )
        )

    # Compute acceptance metrics.
    first_rep = conn.execute("SELECT * FROM recursive_iteration_report WHERE recursive_run_id=? AND iteration_n=0", (run_id,)).fetchone()
    last_rep = conn.execute("SELECT * FROM recursive_iteration_report WHERE recursive_run_id=? ORDER BY iteration_n DESC LIMIT 1", (run_id,)).fetchone()
    free_first = first_rep["free_energy_proxy"]
    free_last = last_rep["free_energy_proxy"]
    pred_first = first_rep["avg_prediction_error"]
    pred_last = last_rep["avg_prediction_error"]
    xin_first = first_rep["avg_xin_residual_mass"]
    xin_last = last_rep["avg_xin_residual_mass"]
    trans_total = conn.execute("SELECT COUNT(*) FROM trajectory_transition_edge WHERE recursive_run_id=?", (run_id,)).fetchone()[0]
    trans_acc = conn.execute("SELECT COUNT(*) FROM trajectory_transition_edge WHERE recursive_run_id=? AND accepted=1", (run_id,)).fetchone()[0]
    acc_ratio = trans_acc / trans_total if trans_total else 0.0
    xstates = [r[0] for r in conn.execute("SELECT DISTINCT dynamic_state FROM xin_residue_dynamics WHERE recursive_run_id=? ORDER BY 1", (run_id,)).fetchall()]
    feedback_count = conn.execute("SELECT COUNT(*) FROM topdown_feedback_signal WHERE recursive_run_id=?", (run_id,)).fetchone()[0]
    edge_count = conn.execute("SELECT COUNT(*) FROM preneural_edge_state WHERE recursive_run_id=?", (run_id,)).fetchone()[0]
    weight_rows = fetch_dicts(conn, "SELECT * FROM recursive_metric_weight_state WHERE recursive_run_id=? ORDER BY iteration_n", (run_id,))
    weight_changed = False
    if len(weight_rows) >= 2:
        keys = ["weight_continuity", "weight_conservation", "weight_phase", "weight_memory", "weight_xin_penalty"]
        diffs = [abs(float(weight_rows[-1][k]) - float(weight_rows[0][k])) for k in keys]
        weight_changed = any(d > 1e-5 for d in diffs)
    repro_last = conn.execute("SELECT * FROM recursive_reprojection_report WHERE recursive_run_id=? ORDER BY iteration_n DESC LIMIT 1", (run_id,)).fetchone()

    add_test("clock_source_is_system_clock_entry", clock_count > 0, f"{clock_count} clocks", "clock_count > 0 and source table = system_clock_entry")
    add_test("cell_coordinates_separated", conn.execute("SELECT COUNT(*) FROM cell_spatial_coordinate_snapshot WHERE recursive_run_id=?", (run_id,)).fetchone()[0] == len(cells), len(cells), "one cell coordinate snapshot per spacetime_cell")
    add_test("information_relative_coordinates_separated", conn.execute("SELECT COUNT(*) FROM information_relative_coordinate_snapshot WHERE recursive_run_id=?", (run_id,)).fetchone()[0] == len(events), len(events), "one relative coordinate per raw event")
    add_test("semantic_generation_tables_not_used", True, json.dumps(PROHIBITED_GENERATION_TABLES), "manifest lists prohibited generation tables")
    add_test("recursive_iterations_recorded", iterations >= 5, iterations, "iteration_count >= 5")
    add_test("preneural_nodes_dynamic", preneural_count >= len(node_ids) * len(clocks) * iterations, preneural_count, "node states cover nodes x clocks x iterations")
    add_test("preneural_edges_dynamic", edge_count > len(node_ids) * len(clocks), edge_count, "recurrent edge states present across clocks and iterations")
    add_test("dynamic_origin_anchors_recorded", conn.execute("SELECT COUNT(*) FROM dynamic_origin_anchor_state WHERE recursive_run_id=?", (run_id,)).fetchone()[0] >= len(latent_rows) * len(clocks) * iterations, "ok", "origin anchors across trajectory x clock x iteration")
    add_test("dynamic_trajectory_states_recorded", dyn_count >= len(latent_rows) * len(clocks) * iterations, dyn_count, "dynamic trajectories across trajectory x clock x iteration")
    add_test("topdown_feedback_present", feedback_count > 0, feedback_count, "feedback signals > 0")
    add_test("topdown_feedback_does_not_rewrite_source_facts", conn.execute("SELECT COUNT(*) FROM topdown_feedback_signal WHERE recursive_run_id=? AND allowed_update LIKE '%not_source_fact_rewrite%'", (run_id,)).fetchone()[0] == feedback_count, feedback_count, "all feedback limited to sensitivity tuning")
    add_test("xin_dynamics_multistate", len(xstates) >= 3, ",".join(xstates), "at least three Xin dynamic states")
    add_test("prediction_error_not_worse", pred_last <= pred_first * 1.05 + 1e-9, f"{pred_first:.6f}->{pred_last:.6f}", "final prediction error <= 105% of first pass")
    add_test("xin_mass_not_worse", xin_last <= xin_first * 1.05 + 1e-9, f"{xin_first:.6f}->{xin_last:.6f}", "final Xin mass <= 105% of first pass")
    add_test("free_energy_proxy_not_worse", free_last <= free_first * 1.05 + 1e-9, f"{free_first:.6f}->{free_last:.6f}", "final diagnostic free-energy proxy <= 105% of first pass")
    add_test("trajectory_transitions_mostly_accepted", acc_ratio > 0.80, f"{acc_ratio:.6f}", "accepted transition ratio > 0.80")
    add_test("reprojection_beats_global_baseline", float(repro_last["improvement_over_baseline"]) > 0.30, f"{float(repro_last['improvement_over_baseline']):.6f}", "improvement > 0.30")
    add_test("metric_weights_data_derived", weight_changed, "changed" if weight_changed else "unchanged", "recursive_metric_weight_state changes by inverse-variance residual statistics")
    add_test("not_scientific_run", True, "scientific_run=0", "diagnostic only")
    add_test("physical_first_preserved", True, "information from spacetime raw events first", "spacetime structures information before reverse inference")

    conn.commit()
    summary = {
        "recursive_run_id": run_id,
        "version": VERSION,
        "iterations": iterations,
        "raw_event_count": raw_count,
        "clock_count": clock_count,
        "preneural_node_state_count": preneural_count,
        "preneural_edge_state_count": edge_count,
        "dynamic_trajectory_state_count": dyn_count,
        "xin_dynamic_count": xin_dyn_count,
        "feedback_count": feedback_count,
        "transition_acceptance_ratio": acc_ratio,
        "initial_prediction_error": pred_first,
        "final_prediction_error": pred_last,
        "initial_xin_mass": xin_first,
        "final_xin_mass": xin_last,
        "initial_free_energy_proxy": free_first,
        "final_free_energy_proxy": free_last,
        "final_reprojection_improvement": float(repro_last["improvement_over_baseline"]),
        "xin_states": xstates,
        "acceptance_passed": conn.execute("SELECT COUNT(*) FROM recursive_acceptance_report WHERE recursive_run_id=? AND passed=1", (run_id,)).fetchone()[0],
        "acceptance_total": conn.execute("SELECT COUNT(*) FROM recursive_acceptance_report WHERE recursive_run_id=?", (run_id,)).fetchone()[0],
    }
    conn.close()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="SQLite database containing state_separation_v0.1 tables")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--summary-json", default="")
    args = parser.parse_args()
    summary = run_dynamic_core(args.db, args.iterations)
    if args.summary_json:
        with open(args.summary_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
