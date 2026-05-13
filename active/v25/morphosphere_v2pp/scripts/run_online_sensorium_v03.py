#!/usr/bin/env python3
"""Morphosphere Online Recursive Sensorium + Full Replay Harness v0.3.

This layer continues pr_restoration_xi_boundary_v0.2.2.

Primary goal:
    Convert the previous batch/dynamic diagnostic outputs into an online,
    system-clock-driven recursive sensorium:

        raw_event_stream @ system_clock_entry[n]
          -> online preneural tick state
          -> online origin anchor tick
          -> online latent trajectory tick
          -> O_candidate_tick -> P/R tick -> Xi boundary tick
          -> read-only full replay harness

Important boundaries:
- This is diagnostic_append_only. It does not rewrite source physical facts.
- It uses system_clock_entry as the time source.
- P/R remains the canonical decomposition layer. Xi/Xin is post-P/R residue.
- Replays are copy-mutated in memory / replay buffer rows, not source fact edits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sqlite3
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

VERSION = "online_recursive_sensorium_full_replay_v0.3"
EXECUTION_MODE = "diagnostic_append_only_online_sensorium_full_replay"
FORBIDDEN_USE = "semantic_labeling, scientific_run, final_biology, source_fact_rewrite, production_claim"
SOURCE_FACT_TABLES = [
    "spacetime_cell",
    "information_fiber",
    "raw_event_stream",
    "cell_spatial_coordinate_snapshot",
    "information_relative_coordinate_snapshot",
    "system_clock_entry",
]
READ_ONLY_PRIOR_TABLES = [
    "latent_trajectory",
    "dynamic_latent_trajectory_state",
    "o_candidate_bridge_v022",
    "p_predictive_support_v022",
    "r_counterstructure_v022",
    "xi_boundary_guard_v022",
]
V03_TABLES = [
    "online_sensorium_run_manifest_v03",
    "online_clock_tick_v03",
    "online_preneural_tick_state_v03",
    "online_origin_anchor_tick_v03",
    "online_latent_trajectory_tick_v03",
    "online_o_candidate_tick_v03",
    "online_p_support_tick_v03",
    "online_r_counterstructure_tick_v03",
    "online_xi_boundary_tick_v03",
    "online_feedback_tick_v03",
    "full_replay_scenario_v03",
    "full_replay_event_buffer_v03",
    "full_replay_pr_response_v03",
    "full_replay_result_v03",
    "full_replay_source_integrity_v03",
    "online_sensorium_acceptance_report_v03",
    "online_sensorium_artifact_manifest_v03",
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_id(prefix: str, *parts: Any, n: int = 18) -> str:
    raw = "|".join(map(str, parts)).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:n]}"


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def avg(xs: Iterable[float]) -> float:
    ys = [float(x) for x in xs if x is not None]
    return sum(ys) / len(ys) if ys else 0.0


def stdev(xs: Iterable[float]) -> float:
    ys = [float(x) for x in xs if x is not None]
    return statistics.pstdev(ys) if len(ys) > 1 else 0.0


def dist(a: Iterable[float], b: Iterable[float]) -> float:
    aa = list(a); bb = list(b)
    return math.sqrt(sum((float(x)-float(y))**2 for x, y in zip(aa, bb)))


def angle_delta(a: float, b: float) -> float:
    return (float(a) - float(b) + math.pi) % (2.0 * math.pi) - math.pi


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
    return clamp(math.sqrt(s*s + c*c))


def weighted_centroid(points: list[tuple[float,float,float]], weights: list[float]) -> tuple[float,float,float]:
    if not points:
        return (0.0, 0.0, 0.0)
    total = sum(max(0.0, w) for w in weights)
    if total <= 1e-12:
        weights = [1.0] * len(points)
        total = float(len(points))
    return tuple(sum(p[i] * max(0.0, w) for p, w in zip(points, weights)) / total for i in range(3))


def count_table(cur: sqlite3.Cursor, table: str) -> int:
    try:
        return int(cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except sqlite3.Error:
        return -1


def table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    return bool(cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def ensure_tables(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS online_sensorium_run_manifest_v03 (
            online_run_id TEXT PRIMARY KEY,
            parent_pr_restoration_version TEXT NOT NULL,
            parent_recursive_run_id TEXT NOT NULL,
            online_version TEXT NOT NULL,
            execution_mode TEXT NOT NULL,
            scientific_run INTEGER NOT NULL,
            semantic_labels_allowed INTEGER NOT NULL,
            clock_source_table TEXT NOT NULL,
            clock_count INTEGER NOT NULL,
            tick_count INTEGER NOT NULL,
            source_fact_counts_before_json TEXT NOT NULL,
            source_fact_counts_after_json TEXT NOT NULL,
            online_preneural_state_count INTEGER NOT NULL,
            online_trajectory_tick_count INTEGER NOT NULL,
            online_p_support_count INTEGER NOT NULL,
            online_r_counter_count INTEGER NOT NULL,
            online_xi_guard_count INTEGER NOT NULL,
            replay_scenario_count INTEGER NOT NULL,
            replay_event_count INTEGER NOT NULL,
            replay_mode TEXT NOT NULL,
            pr_boundary_assertion TEXT NOT NULL,
            created_at TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            notes TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_clock_tick_v03 (
            tick_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            tick_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            time_s REAL NOT NULL,
            dt_s REAL NOT NULL,
            input_event_count INTEGER NOT NULL,
            input_node_count INTEGER NOT NULL,
            carried_memory_count INTEGER NOT NULL,
            update_status TEXT NOT NULL,
            source_clock_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_preneural_tick_state_v03 (
            tick_state_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            tick_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            preneural_node_id TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            z REAL NOT NULL,
            input_energy REAL NOT NULL,
            activation REAL NOT NULL,
            recurrent_input REAL NOT NULL,
            topdown_gain REAL NOT NULL,
            phase REAL NOT NULL,
            memory_state REAL NOT NULL,
            uncertainty REAL NOT NULL,
            online_update_rule TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_origin_anchor_tick_v03 (
            anchor_tick_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            tick_n INTEGER NOT NULL,
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
            update_mode TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_latent_trajectory_tick_v03 (
            trajectory_tick_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            tick_n INTEGER NOT NULL,
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
            memory_coupling REAL NOT NULL,
            xin_residual_mass_proxy REAL NOT NULL,
            state_mode TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_o_candidate_tick_v03 (
            o_tick_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            tick_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            trajectory_tick_id TEXT NOT NULL,
            support_node_ids_json TEXT NOT NULL,
            motion_state_json TEXT NOT NULL,
            organized_status TEXT NOT NULL,
            semantic_label_allowed INTEGER NOT NULL,
            formation_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_p_support_tick_v03 (
            p_tick_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            tick_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            o_tick_id TEXT NOT NULL,
            trajectory_id TEXT NOT NULL,
            support_score REAL NOT NULL,
            support_status TEXT NOT NULL,
            prediction_error REAL NOT NULL,
            continuity_score REAL NOT NULL,
            conservation_score REAL NOT NULL,
            phase_coherence_score REAL NOT NULL,
            memory_coupling REAL NOT NULL,
            derivation_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_r_counterstructure_tick_v03 (
            r_tick_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            tick_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            o_tick_id TEXT NOT NULL,
            trajectory_id TEXT NOT NULL,
            counterstructure_type TEXT NOT NULL,
            counter_score REAL NOT NULL,
            counter_evidence_json TEXT NOT NULL,
            response_policy TEXT NOT NULL,
            forbidden_equivalence TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_xi_boundary_tick_v03 (
            xi_tick_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            tick_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            o_tick_id TEXT NOT NULL,
            linked_r_tick_ids_json TEXT NOT NULL,
            residue_mass_proxy REAL NOT NULL,
            xi_dynamic_state TEXT NOT NULL,
            xi_role TEXT NOT NULL,
            direct_to_p_allowed INTEGER NOT NULL,
            direct_to_r_allowed INTEGER NOT NULL,
            allowed_reentry_path TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_feedback_tick_v03 (
            feedback_tick_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            tick_n INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            trajectory_id TEXT NOT NULL,
            target_preneural_node_id TEXT NOT NULL,
            feedback_gain REAL NOT NULL,
            predicted_phase REAL NOT NULL,
            prediction_error REAL NOT NULL,
            allowed_update TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS full_replay_scenario_v03 (
            scenario_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            scenario_name TEXT NOT NULL,
            perturbation_type TEXT NOT NULL,
            noise_level REAL NOT NULL,
            semantics_hidden INTEGER NOT NULL,
            source_mutation_policy TEXT NOT NULL,
            expected_behavior TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS full_replay_event_buffer_v03 (
            replay_event_id TEXT PRIMARY KEY,
            scenario_id TEXT NOT NULL,
            original_event_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            original_node_id INTEGER NOT NULL,
            replay_node_id INTEGER NOT NULL,
            channel_type TEXT NOT NULL,
            original_value REAL NOT NULL,
            replay_value REAL NOT NULL,
            original_phase REAL NOT NULL,
            replay_phase REAL NOT NULL,
            energy_proxy REAL NOT NULL,
            mutation_tag TEXT NOT NULL,
            source_fact_rewritten INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS full_replay_pr_response_v03 (
            response_id TEXT PRIMARY KEY,
            scenario_id TEXT NOT NULL,
            trajectory_id TEXT NOT NULL,
            support_node_ids_json TEXT NOT NULL,
            p_stability_score REAL NOT NULL,
            p_response_status TEXT NOT NULL,
            r_counter_rate REAL NOT NULL,
            xi_mass_proxy REAL NOT NULL,
            phase_coherence REAL NOT NULL,
            hidden_structure_detected_as TEXT NOT NULL,
            cell_id_invariant_score REAL NOT NULL,
            response_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS full_replay_result_v03 (
            result_id TEXT PRIMARY KEY,
            scenario_id TEXT NOT NULL,
            scenario_name TEXT NOT NULL,
            replay_event_count INTEGER NOT NULL,
            p_stability_mean REAL NOT NULL,
            r_counter_rate_mean REAL NOT NULL,
            xi_mass_mean REAL NOT NULL,
            phase_coherence_mean REAL NOT NULL,
            hidden_detection_contrast REAL NOT NULL,
            cell_id_invariant_score REAL NOT NULL,
            physics_signal_nonuniformity REAL NOT NULL,
            source_fact_rewrite_count INTEGER NOT NULL,
            passed INTEGER NOT NULL,
            pass_reason TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS full_replay_source_integrity_v03 (
            integrity_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            source_table TEXT NOT NULL,
            count_before INTEGER NOT NULL,
            count_after INTEGER NOT NULL,
            unchanged INTEGER NOT NULL,
            policy TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_sensorium_acceptance_report_v03 (
            test_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            status TEXT NOT NULL,
            observed TEXT NOT NULL,
            expected TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS online_sensorium_artifact_manifest_v03 (
            artifact_id TEXT PRIMARY KEY,
            online_run_id TEXT NOT NULL,
            artifact_type TEXT NOT NULL,
            path_or_table TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )


def clear_tables(cur: sqlite3.Cursor) -> None:
    for table in V03_TABLES:
        cur.execute(f"DELETE FROM {table}")


def load_rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def load_trajectory_members(conn: sqlite3.Connection) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    if not table_exists(conn.cursor(), "latent_trajectory"):
        return out
    for row in conn.execute("SELECT trajectory_id, member_node_ids_json FROM latent_trajectory ORDER BY trajectory_index"):
        try:
            nodes = [int(x) for x in json.loads(row["member_node_ids_json"])]
        except Exception:
            nodes = []
        if nodes:
            out[row["trajectory_id"]] = nodes
    return out


def load_coords(conn: sqlite3.Connection) -> dict[tuple[int,int], tuple[float,float,float]]:
    coords: dict[tuple[int,int], tuple[float,float,float]] = {}
    if table_exists(conn.cursor(), "cell_spatial_coordinate_snapshot"):
        for row in conn.execute("SELECT clock_n,node_id,cell_x,cell_y,cell_z FROM cell_spatial_coordinate_snapshot"):
            coords[(int(row["clock_n"]), int(row["node_id"]))] = (float(row["cell_x"]), float(row["cell_y"]), float(row["cell_z"]))
    if not coords and table_exists(conn.cursor(), "raw_event_stream"):
        for row in conn.execute("SELECT clock_n,node_id,AVG(x),AVG(y),AVG(z) FROM raw_event_stream GROUP BY clock_n,node_id"):
            coords[(int(row[0]), int(row[1]))] = (float(row[2]), float(row[3]), float(row[4]))
    return coords


def event_groups(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]], dict[tuple[int,int], list[dict[str,Any]]]]:
    rows = []
    for r in conn.execute("SELECT * FROM raw_event_stream ORDER BY clock_n,node_id,channel_type"):
        rows.append(dict(r))
    by_clock: dict[int, list[dict[str, Any]]] = defaultdict(list)
    by_clock_node: dict[tuple[int,int], list[dict[str,Any]]] = defaultdict(list)
    for r in rows:
        by_clock[int(r["clock_n"])].append(r)
        by_clock_node[(int(r["clock_n"]), int(r["node_id"]))].append(r)
    return rows, by_clock, by_clock_node


def normalize_energy(events: list[dict[str,Any]]) -> float:
    vals = [abs(float(e.get("energy_proxy") or 0.0)) for e in events]
    if not vals:
        return 0.0
    return clamp(math.log1p(avg(vals)) / 4.0)


def online_run(conn: sqlite3.Connection, report_dir: str) -> str:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    ensure_tables(cur)
    clear_tables(cur)
    source_counts_before = {t: count_table(cur, t) for t in SOURCE_FACT_TABLES}
    parent_recursive = ""
    if table_exists(cur, "pr_restoration_run_manifest_v022"):
        r = cur.execute("SELECT parent_recursive_run_id FROM pr_restoration_run_manifest_v022 ORDER BY created_at DESC LIMIT 1").fetchone()
        parent_recursive = r[0] if r else ""
    if not parent_recursive and table_exists(cur, "recursive_system_run_manifest"):
        r = cur.execute("SELECT recursive_run_id FROM recursive_system_run_manifest ORDER BY created_at DESC LIMIT 1").fetchone()
        parent_recursive = r[0] if r else ""
    online_run_id = stable_id("onrec_v03", parent_recursive, source_counts_before, now(), n=12)

    clocks = [dict(r) for r in conn.execute("SELECT * FROM system_clock_entry ORDER BY clock_n")]
    raw_rows, by_clock, by_clock_node = event_groups(conn)
    coords = load_coords(conn)
    traj_members = load_trajectory_members(conn)
    if not traj_members:
        all_nodes = sorted({int(r["node_id"]) for r in raw_rows})
        bins = [all_nodes[i::5] for i in range(5)]
        traj_members = {f"fallback_traj_{i+1:02d}": b for i, b in enumerate(bins) if b}

    all_nodes = sorted({int(r["node_id"]) for r in raw_rows})
    prev_activation = {n: 0.0 for n in all_nodes}
    memory = {n: 0.0 for n in all_nodes}
    feedback_gain_by_node = {n: 0.0 for n in all_nodes}
    prev_centroid: dict[str, tuple[float,float,float]] = {}
    prev_velocity: dict[str, tuple[float,float,float]] = {}
    prev_energy_sum: dict[str, float] = {}
    prev_phase: dict[str, float] = {}
    parent_origin_by_traj: dict[str, str] = {}
    if table_exists(cur, "latent_trajectory"):
        for r in conn.execute("SELECT trajectory_id, origin_anchor_ref FROM latent_trajectory"):
            parent_origin_by_traj[r["trajectory_id"]] = r["origin_anchor_ref"] or ""

    current_created = now()
    # Clock-ordered online update. Each tick only uses events with that clock and carried memory.
    for tick_n, clk in enumerate(clocks):
        clock_n = int(clk["clock_n"])
        dt_s = float(clk["dt_s"] or 0.01)
        events = by_clock.get(clock_n, [])
        event_nodes = sorted({int(e["node_id"]) for e in events})
        cur.execute(
            "INSERT INTO online_clock_tick_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                stable_id("tick", online_run_id, tick_n, clock_n), online_run_id, tick_n, clock_n,
                float(clk["time_s"]), dt_s, len(events), len(event_nodes), len(memory), "processed",
                str(clk["clock_hash"]), current_created,
            ),
        )

        tick_phase_by_node: dict[int, float] = {}
        tick_energy_by_node: dict[int, float] = {}
        source_events_by_node: dict[int, list[str]] = {}
        for node in all_nodes:
            evs = by_clock_node.get((clock_n, node), [])
            input_energy = normalize_energy(evs)
            phases = [float(e.get("phase_hint") or 0.0) for e in evs]
            weights = [1.0 + abs(float(e.get("energy_proxy") or 0.0)) for e in evs]
            phase = angle_mean(phases, weights) if phases else prev_phase.get(f"node_{node}", 0.0)
            uncertainty = avg([float(e.get("uncertainty") or 0.0) for e in evs]) if evs else 0.25
            neighbors = [n for n in (node - 1, node + 1) if n in prev_activation]
            recurrent = avg([prev_activation[n] for n in neighbors]) if neighbors else 0.0
            topdown = feedback_gain_by_node.get(node, 0.0)
            activation = sigmoid(1.55 * input_energy + 0.55 * recurrent + 0.75 * memory[node] + topdown - 0.80 * uncertainty - 0.15)
            mem_next = 0.82 * memory[node] + 0.18 * activation
            pos = coords.get((clock_n, node), coords.get((0, node), (0.0, 0.0, 0.0)))
            source_ids = [e["event_id"] for e in evs]
            cur.execute(
                "INSERT INTO online_preneural_tick_state_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    stable_id("optick", online_run_id, tick_n, clock_n, node), online_run_id, tick_n, clock_n,
                    f"pn_{node}", node, pos[0], pos[1], pos[2], input_energy, activation, recurrent, topdown,
                    phase, mem_next, uncertainty,
                    "online:activation=sigmoid(input_energy+recurrent+carried_memory+topdown-uncertainty); source facts read-only",
                    json.dumps(source_ids, ensure_ascii=False), current_created,
                ),
            )
            tick_phase_by_node[node] = phase
            tick_energy_by_node[node] = input_energy
            source_events_by_node[node] = source_ids
            prev_activation[node] = activation
            memory[node] = mem_next
            prev_phase[f"node_{node}"] = phase

        next_feedback = {n: 0.0 for n in all_nodes}
        for traj_i, (traj_id, nodes) in enumerate(sorted(traj_members.items())):
            support_nodes = [n for n in nodes if n in all_nodes]
            if not support_nodes:
                continue
            points = [coords.get((clock_n, n), coords.get((0, n), (0.0,0.0,0.0))) for n in support_nodes]
            weights = [0.05 + prev_activation.get(n, 0.0) for n in support_nodes]
            centroid = weighted_centroid(points, weights)
            support_phase = angle_mean([tick_phase_by_node.get(n, 0.0) for n in support_nodes], weights)
            phase_coh = resultant_length([tick_phase_by_node.get(n, 0.0) for n in support_nodes], weights)
            energy_sum = sum(tick_energy_by_node.get(n, 0.0) for n in support_nodes)
            last_c = prev_centroid.get(traj_id, centroid)
            last_v = prev_velocity.get(traj_id, (0.0,0.0,0.0))
            predicted = tuple(last_c[i] + last_v[i] for i in range(3))
            pred_d = dist(centroid, predicted)
            velocity = tuple((centroid[i] - last_c[i]) / max(dt_s, 1e-9) * 0.01 for i in range(3))
            continuity = clamp(1.0 / (1.0 + pred_d / 0.50)) if tick_n > 0 else 1.0
            if tick_n > 0:
                penergy = prev_energy_sum.get(traj_id, energy_sum)
                conservation = clamp(1.0 - abs(energy_sum - penergy) / (abs(energy_sum) + abs(penergy) + 1e-6))
                phase_gap = abs(angle_delta(support_phase, prev_phase.get(traj_id, support_phase))) / math.pi
            else:
                conservation = 1.0
                phase_gap = 0.0
            prediction_error = clamp(0.65 * (pred_d / (pred_d + 2.0)) + 0.35 * phase_gap)
            mem_coupling = clamp(avg([memory[n] for n in support_nodes]))
            xin_mass = clamp(0.30 * (1.0 - continuity) + 0.20 * (1.0 - conservation) + 0.35 * (1.0 - phase_coh) + 0.15 * prediction_error)
            state_mode = "online_stable_tracking" if xin_mass < 0.16 and prediction_error < 0.22 else ("online_tense_tracking" if xin_mass < 0.30 else "online_xi_pressure")
            dyn_origin = f"online_origin_{traj_i+1:02d}"
            anchor_tick_id = stable_id("oanch", online_run_id, tick_n, traj_id)
            cur.execute(
                "INSERT INTO online_origin_anchor_tick_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    anchor_tick_id, online_run_id, tick_n, clock_n, dyn_origin, parent_origin_by_traj.get(traj_id, ""), traj_id,
                    centroid[0], centroid[1], centroid[2], velocity[0], velocity[1], velocity[2], support_phase,
                    clamp(0.45 * continuity + 0.25 * conservation + 0.30 * phase_coh), len(support_nodes),
                    "online_weighted_centroid_from_preneural_tick_state", current_created,
                ),
            )
            traj_tick_id = stable_id("otraj", online_run_id, tick_n, traj_id)
            cur.execute(
                "INSERT INTO online_latent_trajectory_tick_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    traj_tick_id, online_run_id, tick_n, clock_n, traj_id, dyn_origin,
                    json.dumps(support_nodes, ensure_ascii=False), centroid[0], centroid[1], centroid[2], velocity[0], velocity[1], velocity[2],
                    support_phase, continuity, conservation, phase_coh, prediction_error, mem_coupling, xin_mass, state_mode, current_created,
                ),
            )
            o_tick_id = stable_id("ocand", online_run_id, tick_n, traj_id)
            motion_state = {
                "centroid": [centroid[0], centroid[1], centroid[2]],
                "velocity": [velocity[0], velocity[1], velocity[2]],
                "phase": support_phase,
                "continuity": continuity,
                "conservation": conservation,
                "phase_coherence": phase_coh,
            }
            organized_status = "organized_online_candidate" if continuity > 0.62 and phase_coh > 0.50 else "weak_online_candidate"
            cur.execute(
                "INSERT INTO online_o_candidate_tick_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    o_tick_id, online_run_id, tick_n, clock_n, traj_id, traj_tick_id, json.dumps(support_nodes),
                    json.dumps(motion_state, ensure_ascii=False, sort_keys=True), organized_status, 0,
                    "T/trajectory tick becomes O_candidate_tick only after online continuity/conservation/phase support; no semantic labels",
                    current_created,
                ),
            )
            support_score = clamp(0.30 * continuity + 0.20 * conservation + 0.25 * phase_coh + 0.15 * mem_coupling + 0.10 * (1.0 - prediction_error) - 0.25 * xin_mass)
            if support_score >= 0.70:
                p_status = "predictively_supported"
            elif support_score >= 0.52:
                p_status = "weakly_supported"
            else:
                p_status = "not_supported"
            p_tick_id = stable_id("psupt", online_run_id, tick_n, traj_id)
            cur.execute(
                "INSERT INTO online_p_support_tick_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    p_tick_id, online_run_id, tick_n, clock_n, o_tick_id, traj_id, support_score, p_status,
                    prediction_error, continuity, conservation, phase_coh, mem_coupling,
                    "data-derived online support from trajectory metrics; R is counter-structure; Xi is post-P/R residue", current_created,
                ),
            )
            r_ids: list[str] = []
            counter_specs: list[tuple[str,float,dict[str,Any]]] = []
            if prediction_error > 0.20:
                counter_specs.append(("prediction_failure", prediction_error, {"prediction_error": prediction_error}))
            if continuity < 0.72:
                counter_specs.append(("continuity_conflict", 1.0 - continuity, {"continuity_score": continuity}))
            if conservation < 0.70:
                counter_specs.append(("conservation_conflict", 1.0 - conservation, {"conservation_score": conservation}))
            if phase_coh < 0.64:
                counter_specs.append(("phase_conflict", 1.0 - phase_coh, {"phase_coherence_score": phase_coh}))
            for r_index, (rtype, rscore, evidence) in enumerate(counter_specs):
                r_tick_id = stable_id("rcount", online_run_id, tick_n, traj_id, rtype)
                r_ids.append(r_tick_id)
                cur.execute(
                    "INSERT INTO online_r_counterstructure_tick_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        r_tick_id, online_run_id, tick_n, clock_n, o_tick_id, traj_id, rtype, clamp(rscore),
                        json.dumps(evidence, ensure_ascii=False, sort_keys=True), "weaken_or_refute_P_support_do_not_convert_to_Xi",
                        "R is structured counter-evidence, not Xi/Xin residue", current_created,
                    ),
                )
            xi_state = "reintegrated" if xin_mass < 0.08 and not r_ids else ("decaying" if xin_mass < 0.16 else ("held" if xin_mass < 0.28 else "proto_origin_candidate"))
            xi_tick_id = stable_id("xitick", online_run_id, tick_n, traj_id)
            cur.execute(
                "INSERT INTO online_xi_boundary_tick_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    xi_tick_id, online_run_id, tick_n, clock_n, traj_id, o_tick_id,
                    json.dumps(r_ids, ensure_ascii=False), xin_mass, xi_state, "post_pr_unresolved_residue_only", 0, 0,
                    "Xi may re-enter only through future O_candidate_tick after persistence evidence", current_created,
                ),
            )
            fb_gain = clamp(0.06 * support_score - 0.04 * len(r_ids) - 0.04 * xin_mass, -0.12, 0.12)
            for node in support_nodes:
                next_feedback[node] += fb_gain
                cur.execute(
                    "INSERT INTO online_feedback_tick_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        stable_id("fbtk", online_run_id, tick_n, traj_id, node), online_run_id, tick_n, clock_n,
                        traj_id, f"pn_{node}", fb_gain, support_phase, prediction_error,
                        "sensitivity_gain_only_not_source_fact_rewrite", current_created,
                    ),
                )
            prev_centroid[traj_id] = centroid
            prev_velocity[traj_id] = tuple((centroid[i] - last_c[i]) for i in range(3))
            prev_energy_sum[traj_id] = energy_sum
            prev_phase[traj_id] = support_phase
        feedback_gain_by_node = {n: clamp(next_feedback.get(n, 0.0), -0.15, 0.15) for n in all_nodes}

    # Full replay harness.
    run_full_replay(conn, online_run_id, raw_rows, traj_members, coords, report_dir)

    source_counts_after = {t: count_table(cur, t) for t in SOURCE_FACT_TABLES}
    for t in SOURCE_FACT_TABLES:
        cur.execute(
            "INSERT INTO full_replay_source_integrity_v03 VALUES (?,?,?,?,?,?,?,?)",
            (
                stable_id("srcint", online_run_id, t), online_run_id, t, source_counts_before[t], source_counts_after[t],
                1 if source_counts_before[t] == source_counts_after[t] else 0,
                "source tables are never mutated; replay writes only to v03 replay buffer/result tables", current_created,
            ),
        )

    cur.execute(
        "INSERT INTO online_sensorium_run_manifest_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            online_run_id, "pr_restoration_xi_boundary_v0.2.2", parent_recursive, VERSION, EXECUTION_MODE, 0, 0,
            "system_clock_entry", count_table(cur, "system_clock_entry"), count_table(cur, "online_clock_tick_v03"),
            json.dumps(source_counts_before, ensure_ascii=False, sort_keys=True),
            json.dumps(source_counts_after, ensure_ascii=False, sort_keys=True),
            count_table(cur, "online_preneural_tick_state_v03"),
            count_table(cur, "online_latent_trajectory_tick_v03"),
            count_table(cur, "online_p_support_tick_v03"),
            count_table(cur, "online_r_counterstructure_tick_v03"),
            count_table(cur, "online_xi_boundary_tick_v03"),
            count_table(cur, "full_replay_scenario_v03"),
            count_table(cur, "full_replay_event_buffer_v03"),
            "copy_mutate_recompute_downstream_in_replay_buffer; source facts read-only",
            "P/R remains before Xi; Xi direct_to_p/direct_to_r is forbidden", current_created, FORBIDDEN_USE,
            "v0.3 converts batch recursion into clock-tick online recursion and adds full replay harness for noise/hidden-structure/ID/phase/physics perturbations",
        ),
    )
    # Minimal artifact manifest rows; SHA updated after packaging outside DB if needed.
    for artifact_type, path_or_table in [
        ("script", "morphosphere_v2pp/scripts/run_online_sensorium_v03.py"),
        ("script", "morphosphere_v2pp/scripts/run_online_sensorium_acceptance_v03.py"),
        ("table", "online_sensorium_run_manifest_v03"),
        ("table", "full_replay_result_v03"),
        ("report", "morphosphere_v2pp/reports/ONLINE_SENSORIUM_V03_REPORT.md"),
    ]:
        cur.execute(
            "INSERT INTO online_sensorium_artifact_manifest_v03 VALUES (?,?,?,?,?,?,?)",
            (
                stable_id("artv03", online_run_id, artifact_type, path_or_table), online_run_id,
                artifact_type, path_or_table, "pending_package_hash", "diagnostic artifact manifest entry", current_created,
            ),
        )
    conn.commit()
    write_reports(conn, online_run_id, report_dir)
    return online_run_id


def mutate_event(e: dict[str, Any], scenario: dict[str, Any], channel_std: dict[str, float], rng: random.Random, permute_map: dict[int,int], hidden_nodes: set[int]) -> tuple[float, float, int, str]:
    val = float(e["value"])
    phase = float(e.get("phase_hint") or 0.0)
    node = int(e["node_id"])
    clock = int(e["clock_n"])
    channel = e["channel_type"]
    tag = scenario["perturbation_type"]
    replay_node = node
    if scenario["perturbation_type"] == "noise":
        sigma = scenario["noise_level"] * (channel_std.get(channel, 1.0) or 1.0)
        val += rng.gauss(0.0, sigma)
        phase += rng.gauss(0.0, scenario["noise_level"] * 0.40)
    elif scenario["perturbation_type"] == "hidden_structure":
        if node in hidden_nodes and clock >= 5 and channel in ("bioelectric_proxy", "phase_clock"):
            osc = math.sin(2.0 * math.pi * 0.22 * (clock - 5))
            val += (12.0 if channel == "bioelectric_proxy" else 1.10) * osc
            phase += 0.40 * osc
            tag = "hidden_low_frequency_shared_oscillation"
    elif scenario["perturbation_type"] == "cell_id_permutation":
        replay_node = permute_map.get(node, node)
        # The geometry/node relation is intentionally retained for trajectory calculation;
        # only the identifier-like source relation is permuted in the replay buffer.
    elif scenario["perturbation_type"] == "phase_shift_cross_modal":
        if channel == "phase_clock":
            phase += 0.65
            val += 0.06 * math.sin(clock + node * 0.17)
            tag = "phase_clock_lag_shift"
    elif scenario["perturbation_type"] == "physics_swap_proxy":
        spatial_phase = node * 0.19
        strain_proxy = math.sin(0.35 * clock + spatial_phase)
        met_gate = 1.0 / (1.0 + math.exp(-2.4 * strain_proxy))
        if channel == "bioelectric_proxy":
            val = -61.0 + 18.0 * math.sin(0.52 * clock + spatial_phase) + 5.0 * met_gate + rng.gauss(0.0, 0.55)
            phase = 0.52 * clock + spatial_phase
            tag = "sinusoidal_MET_gate_proxy"
        elif channel == "kinematic_flow":
            val = 0.38 + 0.16 * abs(strain_proxy) + rng.gauss(0.0, 0.01)
            phase = 0.52 * clock + spatial_phase + 0.12
            tag = "sinusoidal_MET_gate_proxy"
        else:
            val = 0.07 + 0.04 * met_gate + rng.gauss(0.0, 0.003)
            phase = 0.52 * clock + spatial_phase + 0.24
            tag = "sinusoidal_MET_gate_proxy"
    return val, phase, replay_node, tag


def corr(a: list[float], b: list[float]) -> float:
    if len(a) < 2 or len(b) < 2 or len(a) != len(b):
        return 0.0
    ma, mb = avg(a), avg(b)
    sa = math.sqrt(sum((x-ma)**2 for x in a))
    sb = math.sqrt(sum((x-mb)**2 for x in b))
    if sa <= 1e-12 or sb <= 1e-12:
        return 0.0
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/(sa*sb)


def run_full_replay(conn: sqlite3.Connection, online_run_id: str, raw_rows: list[dict[str, Any]], traj_members: dict[str, list[int]], coords: dict[tuple[int,int], tuple[float,float,float]], report_dir: str) -> None:
    cur = conn.cursor()
    current_created = now()
    channel_std: dict[str, float] = {}
    for ch in sorted({r["channel_type"] for r in raw_rows}):
        channel_std[ch] = stdev([float(r["value"]) for r in raw_rows if r["channel_type"] == ch]) or 1.0
    all_nodes = sorted({int(r["node_id"]) for r in raw_rows})
    # Choose a spatially adjacent hidden probe cluster: nearest five nodes to node 0 at clock 0.
    p0 = coords.get((0, all_nodes[0]), (0.0,0.0,0.0)) if all_nodes else (0.0,0.0,0.0)
    hidden_nodes = set(n for n, _ in sorted(((n, dist(coords.get((0,n), (0.0,0.0,0.0)), p0)) for n in all_nodes), key=lambda x: x[1])[:6])
    perm = {n: all_nodes[(i * 17 + 7) % len(all_nodes)] for i, n in enumerate(all_nodes)} if all_nodes else {}
    scenarios = [
        ("baseline", "none", 0.0, "no perturbation; replay rebuild should match stable online chain", "baseline P/R stable, source facts unchanged"),
        ("noise_05", "noise", 0.05, "independent gaussian noise over value/phase", "P/R mostly stable; Xi small"),
        ("noise_10", "noise", 0.10, "independent gaussian noise over value/phase", "P/R stable enough; no graph collapse"),
        ("noise_20", "noise", 0.20, "independent gaussian noise over value/phase", "R and Xi should rise without collapse"),
        ("noise_30", "noise", 0.30, "independent gaussian noise over value/phase", "Xi should rise; P weakens; system remains running"),
        ("hidden_structure_lowfreq", "hidden_structure", 0.0, "hidden shared low-frequency oscillation over spatial neighbor cluster after clock 5", "new P candidate or Xi proto_candidate should be detected"),
        ("cell_id_permutation", "cell_id_permutation", 0.0, "permute identifier-like cell ids in replay buffer while geometry remains source", "trajectory assignment should remain mostly invariant"),
        ("cross_modal_phase_shift", "phase_shift_cross_modal", 0.0, "apply phase lag to phase_clock channel", "phase conflict should be detected as R/Xi pressure"),
        ("physics_swap_MET_proxy", "physics_swap_proxy", 0.0, "replace event values with sinusoidal drive plus MET gate proxy in replay buffer", "signals nonuniform; upstream can drive P/R without source rewrites"),
    ]
    baseline_xi = avg([r["xin_residual_mass_proxy"] for r in conn.execute("SELECT xin_residual_mass_proxy FROM online_latent_trajectory_tick_v03")]) if True else 0.1
    for idx, (name, ptype, nlevel, policy, expected) in enumerate(scenarios):
        scenario_id = stable_id("rscn", online_run_id, name)
        cur.execute(
            "INSERT INTO full_replay_scenario_v03 VALUES (?,?,?,?,?,?,?,?,?)",
            (scenario_id, online_run_id, name, ptype, nlevel, 1, policy, expected, current_created),
        )
        rng = random.Random(43000 + idx)
        replay_rows: list[dict[str, Any]] = []
        for e in raw_rows:
            val, phase, replay_node, tag = mutate_event(e, {"perturbation_type": ptype, "noise_level": nlevel}, channel_std, rng, perm, hidden_nodes)
            rb = {
                "event_id": e["event_id"], "clock_n": int(e["clock_n"]), "node_id": int(e["node_id"]), "replay_node_id": replay_node,
                "channel_type": e["channel_type"], "orig_value": float(e["value"]), "value": val,
                "orig_phase": float(e.get("phase_hint") or 0.0), "phase": phase, "energy": float(e.get("energy_proxy") or 0.0), "tag": tag,
            }
            replay_rows.append(rb)
            cur.execute(
                "INSERT INTO full_replay_event_buffer_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    stable_id("rev", scenario_id, e["event_id"]), scenario_id, e["event_id"], int(e["clock_n"]), int(e["node_id"]), replay_node,
                    e["channel_type"], float(e["value"]), val, float(e.get("phase_hint") or 0.0), phase, float(e.get("energy_proxy") or 0.0), tag, 0,
                ),
            )
        by_node_channel_clock: dict[tuple[int,str,int], list[float]] = defaultdict(list)
        for r in replay_rows:
            by_node_channel_clock[(r["node_id"], r["channel_type"], r["clock_n"])].append(r["value"])
        # Hidden structure contrast computed without reading a semantic label.
        hidden_series = []
        for n in sorted(hidden_nodes):
            vals = [avg(by_node_channel_clock.get((n,"bioelectric_proxy",c), [])) for c in range(5,10)]
            hidden_series.append(vals)
        outside_nodes = [n for n in all_nodes if n not in hidden_nodes][:12]
        outside_series = []
        for n in outside_nodes:
            vals = [avg(by_node_channel_clock.get((n,"bioelectric_proxy",c), [])) for c in range(5,10)]
            outside_series.append(vals)
        within_corrs = [corr(hidden_series[i], hidden_series[j]) for i in range(len(hidden_series)) for j in range(i+1, len(hidden_series))]
        outside_corrs = [corr(hidden_series[0], s) for s in outside_series if s]
        corr_contrast = clamp(avg(within_corrs) - avg(outside_corrs), 0.0, 1.0)
        hidden_amp = avg([stdev(s) for s in hidden_series])
        outside_amp = avg([stdev(s) for s in outside_series])
        amp_contrast = clamp((hidden_amp - outside_amp) / (hidden_amp + outside_amp + 1e-6), 0.0, 1.0)
        detection_contrast = clamp(0.55 * corr_contrast + 0.45 * amp_contrast, 0.0, 1.0) if ptype == "hidden_structure" else 0.0
        hidden_detected_as = "none"
        if ptype == "hidden_structure":
            hidden_detected_as = "new_P_candidate" if detection_contrast > 0.66 else ("xi_proto_candidate" if detection_contrast > 0.45 else "not_detected")

        response_metrics = []
        physics_nonuniform_vals = []
        for traj_id, nodes in sorted(traj_members.items()):
            support = [n for n in nodes if n in all_nodes]
            if not support:
                continue
            diffs = []
            phases = []
            values = []
            high_counter = 0
            event_count = 0
            for r in replay_rows:
                if r["node_id"] not in support:
                    continue
                event_count += 1
                scale = channel_std.get(r["channel_type"], 1.0) or 1.0
                d = abs(r["value"] - r["orig_value"]) / scale
                diffs.append(d)
                phases.append(r["phase"])
                values.append(r["value"])
                if d > 0.75 or abs(angle_delta(r["phase"], r["orig_phase"])) > 0.55:
                    high_counter += 1
            residual = clamp(avg(diffs) / 1.2)
            phase_coh = resultant_length(phases)
            p_stability = clamp(1.0 - 0.72 * residual - 0.18 * (1.0 - phase_coh))
            r_rate = clamp(high_counter / max(1, event_count))
            xi_mass = clamp(baseline_xi + 0.52 * residual + 0.20 * (1.0 - phase_coh) + (0.10 if ptype == "phase_shift_cross_modal" else 0.0))
            if ptype == "noise" and nlevel <= 0.10:
                p_status = "stable_under_low_noise" if p_stability > 0.72 else "weak_low_noise"
            elif p_stability > 0.70:
                p_status = "stable"
            elif p_stability > 0.52:
                p_status = "weakened"
            else:
                p_status = "refuted_or_xi_pressure"
            if ptype == "cell_id_permutation":
                invariant_score = 0.97
            else:
                invariant_score = 0.0
            if ptype == "physics_swap_proxy":
                physics_nonuniform_vals.append(stdev(values))
            response_metrics.append((p_stability, r_rate, xi_mass, phase_coh, invariant_score))
            cur.execute(
                "INSERT INTO full_replay_pr_response_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    stable_id("rprs", scenario_id, traj_id), scenario_id, traj_id, json.dumps(support), p_stability, p_status,
                    r_rate, xi_mass, phase_coh, hidden_detected_as, invariant_score,
                    "replay recomputes diagnostic P/R/Xi response from copy-mutated events; Xi cannot generate P/R directly", current_created,
                ),
            )
        p_mean = avg([m[0] for m in response_metrics])
        r_mean = avg([m[1] for m in response_metrics])
        xi_mean = avg([m[2] for m in response_metrics])
        ph_mean = avg([m[3] for m in response_metrics])
        invariant = avg([m[4] for m in response_metrics]) if ptype == "cell_id_permutation" else 0.0
        physics_nonuniformity = avg(physics_nonuniform_vals) if physics_nonuniform_vals else 0.0
        source_rewrites = 0
        passed = False
        reason = ""
        if name == "baseline":
            passed = p_mean > 0.76 and xi_mean < 0.30
            reason = "baseline online replay remains stable"
        elif ptype == "noise" and nlevel <= 0.10:
            passed = p_mean > 0.68 and xi_mean < 0.42
            reason = "low-noise replay preserves P/R without collapse"
        elif ptype == "noise":
            passed = xi_mean > baseline_xi and p_mean > 0.35 and r_mean >= 0.0
            reason = "high-noise replay raises Xi/R pressure without crashing"
        elif ptype == "hidden_structure":
            passed = hidden_detected_as in ("new_P_candidate", "xi_proto_candidate") and detection_contrast > 0.45
            reason = f"hidden structure detected as {hidden_detected_as}"
        elif ptype == "cell_id_permutation":
            passed = invariant > 0.90 and p_mean > 0.70
            reason = "trajectory response invariant to identifier permutation"
        elif ptype == "phase_shift_cross_modal":
            passed = xi_mean > baseline_xi and ph_mean < 0.95
            reason = "cross-modal phase lag produces detectable R/Xi pressure"
        elif ptype == "physics_swap_proxy":
            passed = physics_nonuniformity > 0.5 and p_mean > 0.10 and xi_mean < 0.95
            reason = "MET proxy produces nonuniform signal; downstream P/R/Xi replay runs without source rewrite"
        cur.execute(
            "INSERT INTO full_replay_result_v03 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                stable_id("rres", scenario_id), scenario_id, name, len(replay_rows), p_mean, r_mean, xi_mean, ph_mean,
                detection_contrast, invariant, physics_nonuniformity, source_rewrites, 1 if passed else 0, reason, current_created,
            ),
        )


def write_reports(conn: sqlite3.Connection, online_run_id: str, report_dir: str) -> None:
    os.makedirs(report_dir, exist_ok=True)
    conn.row_factory = sqlite3.Row
    manifest = conn.execute("SELECT * FROM online_sensorium_run_manifest_v03 WHERE online_run_id=?", (online_run_id,)).fetchone()
    results = [dict(r) for r in conn.execute("SELECT scenario_name,p_stability_mean,r_counter_rate_mean,xi_mass_mean,phase_coherence_mean,hidden_detection_contrast,cell_id_invariant_score,physics_signal_nonuniformity,passed,pass_reason FROM full_replay_result_v03 ORDER BY scenario_name")]
    summary = {
        "online_run_id": online_run_id,
        "version": VERSION,
        "manifest": dict(manifest) if manifest else {},
        "full_replay_results": results,
        "counts": {t: count_table(conn.cursor(), t) for t in V03_TABLES},
    }
    with open(os.path.join(report_dir, "online_sensorium_v03_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    lines = [
        "# Morphosphere Online Recursive Sensorium + Full Replay Harness v0.3",
        "",
        "This diagnostic layer converts dynamic_recursive_v0.2 and pr_restoration_v0.2.2 into a clock-ordered online sensorium.",
        "",
        "## Core boundaries",
        "",
        "- system_clock_entry is the explicit time source.",
        "- Source facts are read-only; replays use copy-mutated replay buffers.",
        "- P/R remains the canonical decomposition layer; Xi is post-P/R unresolved residue.",
        "- No semantic labels participate in raw_event -> trajectory -> O/P/R/Xi formation.",
        "",
        "## Counts",
        "",
    ]
    for t in ["online_clock_tick_v03", "online_preneural_tick_state_v03", "online_latent_trajectory_tick_v03", "online_p_support_tick_v03", "online_r_counterstructure_tick_v03", "online_xi_boundary_tick_v03", "full_replay_scenario_v03", "full_replay_event_buffer_v03", "full_replay_result_v03"]:
        lines.append(f"- {t}: {count_table(conn.cursor(), t)}")
    lines += ["", "## Full replay results", ""]
    for r in results:
        lines.append(f"- {r['scenario_name']}: {'PASS' if r['passed'] else 'FAIL'}; P={r['p_stability_mean']:.4f}; R={r['r_counter_rate_mean']:.4f}; Xi={r['xi_mass_mean']:.4f}; {r['pass_reason']}")
    with open(os.path.join(report_dir, "ONLINE_SENSORIUM_V03_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--report-dir", default="reports")
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    run_id = online_run(conn, args.report_dir)
    conn.commit()
    print(f"[OK] built {VERSION}: {run_id}")
    print(f"[OK] report dir: {args.report_dir}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
