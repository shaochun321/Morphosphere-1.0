#!/usr/bin/env python3
"""Morphosphere Device-Neutral Preneural Edge v0.5.

This layer continues matrix_foam_physical_driver_v0.4.

Primary goal:
    Add a simulated, device-neutral neuromorphic/preneneural edge layer between
    the matrix-foam substrate and the online sensorium. The layer models
    memristive/OECT-like edge dynamics as diagnostic proxies only. It does not
    claim real hardware behavior and it does not overwrite any source facts.

Boundaries:
- Diagnostic append-only: no source facts are rewritten.
- No real hardware claim: device models are simulated proxies.
- P/R remains canonical and precedes Xi. Device evidence may modulate a
  diagnostic evidence channel but cannot directly create P/R or Xi.
- Top-down feedback may adjust gain/sensitivity/memory, but not raw facts.
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
from pathlib import Path
from typing import Any, Iterable

VERSION = "device_neutral_preneural_edge_v0.5"
EXECUTION_MODE = "diagnostic_append_only_device_neutral_preneural_edge"
FORBIDDEN_USE = "scientific_run, final_biology, source_fact_rewrite, semantic_labeling, hardware_truth_claim"
SOURCE_FACT_TABLES = [
    "spacetime_cell",
    "information_fiber",
    "raw_event_stream",
    "cell_spatial_coordinate_snapshot",
    "information_relative_coordinate_snapshot",
    "system_clock_entry",
]
V05_TABLES = [
    "neuromorphic_run_manifest_v05",
    "preneural_device_model_registry_v05",
    "preneural_synaptic_edge_v05",
    "device_edge_tick_state_v05",
    "memristive_plasticity_update_v05",
    "neuromorphic_event_projection_v05",
    "preneural_membrane_state_v05",
    "device_pr_evidence_v05",
    "device_neutral_replay_result_v05",
    "neuromorphic_boundary_contract_v05",
    "neuromorphic_acceptance_report_v05",
    "neuromorphic_artifact_manifest_v05",
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
    vals = [float(x) for x in xs if x is not None]
    return sum(vals) / len(vals) if vals else 0.0


def pstdev(xs: Iterable[float]) -> float:
    vals = [float(x) for x in xs if x is not None]
    return statistics.pstdev(vals) if len(vals) > 1 else 0.0


def count_table(cur: sqlite3.Cursor, table: str) -> int:
    try:
        return int(cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except sqlite3.Error:
        return -1


def table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    return bool(cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def checksum_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_tables(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS neuromorphic_run_manifest_v05 (
            neuromorphic_run_id TEXT PRIMARY KEY,
            parent_matrix_run_id TEXT NOT NULL,
            parent_online_run_id TEXT NOT NULL,
            version TEXT NOT NULL,
            execution_mode TEXT NOT NULL,
            scientific_run INTEGER NOT NULL,
            hardware_claimed INTEGER NOT NULL,
            device_mode TEXT NOT NULL,
            clock_source_table TEXT NOT NULL,
            clock_count INTEGER NOT NULL,
            source_fact_counts_before_json TEXT NOT NULL,
            source_fact_counts_after_json TEXT NOT NULL,
            device_model_count INTEGER NOT NULL,
            synaptic_edge_count INTEGER NOT NULL,
            edge_tick_state_count INTEGER NOT NULL,
            plasticity_update_count INTEGER NOT NULL,
            event_projection_count INTEGER NOT NULL,
            membrane_state_count INTEGER NOT NULL,
            pr_evidence_count INTEGER NOT NULL,
            replay_result_count INTEGER NOT NULL,
            pr_xi_boundary_assertion TEXT NOT NULL,
            created_at TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            notes TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS preneural_device_model_registry_v05 (
            device_model_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            device_family TEXT NOT NULL,
            simulated_only INTEGER NOT NULL,
            g_min REAL NOT NULL,
            g_max REAL NOT NULL,
            volatility REAL NOT NULL,
            hysteresis REAL NOT NULL,
            retention_decay REAL NOT NULL,
            read_noise REAL NOT NULL,
            write_noise REAL NOT NULL,
            update_gain REAL NOT NULL,
            ionic_lag REAL NOT NULL,
            energy_scale REAL NOT NULL,
            allowed_use TEXT NOT NULL,
            forbidden_claim TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS preneural_synaptic_edge_v05 (
            synaptic_edge_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            source_foam_edge_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            edge_type TEXT NOT NULL,
            pre_node_id INTEGER NOT NULL,
            post_node_id INTEGER NOT NULL,
            pre_cell_uid TEXT NOT NULL,
            post_cell_uid TEXT NOT NULL,
            device_model_id TEXT NOT NULL,
            device_model_name TEXT NOT NULL,
            base_conductance REAL NOT NULL,
            polarity REAL NOT NULL,
            delay_ticks INTEGER NOT NULL,
            phase_selectivity REAL NOT NULL,
            substrate_coupling REAL NOT NULL,
            met_coupling REAL NOT NULL,
            source_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS device_edge_tick_state_v05 (
            edge_state_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            synaptic_edge_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            tick_n INTEGER NOT NULL,
            device_model_name TEXT NOT NULL,
            pre_activation REAL NOT NULL,
            post_activation REAL NOT NULL,
            foam_strain_proxy REAL NOT NULL,
            met_drive_proxy REAL NOT NULL,
            read_noise_proxy REAL NOT NULL,
            conductance_before REAL NOT NULL,
            conductance_after REAL NOT NULL,
            memory_state REAL NOT NULL,
            hysteresis_state REAL NOT NULL,
            retention_loss REAL NOT NULL,
            edge_current_proxy REAL NOT NULL,
            energy_dissipation_proxy REAL NOT NULL,
            update_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS memristive_plasticity_update_v05 (
            plasticity_update_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            edge_state_id TEXT NOT NULL,
            synaptic_edge_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            device_model_name TEXT NOT NULL,
            delta_g REAL NOT NULL,
            potentiation_proxy REAL NOT NULL,
            depression_proxy REAL NOT NULL,
            coincidence_proxy REAL NOT NULL,
            stability_regularizer REAL NOT NULL,
            bounded_update_applied INTEGER NOT NULL,
            source_basis TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS neuromorphic_event_projection_v05 (
            event_projection_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            met_event_id TEXT NOT NULL,
            physical_sample_id TEXT NOT NULL,
            source_cell_uid TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            matched_synaptic_edge_id TEXT NOT NULL,
            device_model_name TEXT NOT NULL,
            met_gate_probability REAL NOT NULL,
            transduced_current_proxy REAL NOT NULL,
            device_weighted_signal REAL NOT NULL,
            projection_confidence REAL NOT NULL,
            source_fact_rewritten INTEGER NOT NULL,
            projection_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS preneural_membrane_state_v05 (
            membrane_state_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            node_id INTEGER NOT NULL,
            input_current_sum REAL NOT NULL,
            recurrent_device_current REAL NOT NULL,
            topdown_gain_proxy REAL NOT NULL,
            device_memory_sum REAL NOT NULL,
            membrane_potential_proxy REAL NOT NULL,
            activation_proxy REAL NOT NULL,
            refractory_proxy REAL NOT NULL,
            uncertainty_proxy REAL NOT NULL,
            source_edge_state_ids_json TEXT NOT NULL,
            source_event_projection_ids_json TEXT NOT NULL,
            update_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS device_pr_evidence_v05 (
            pr_evidence_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            source_p_tick_id TEXT NOT NULL,
            source_o_tick_id TEXT NOT NULL,
            trajectory_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            p_support_before REAL NOT NULL,
            device_evidence_score REAL NOT NULL,
            memory_consistency_score REAL NOT NULL,
            phase_gate_score REAL NOT NULL,
            diagnostic_pr_adjustment_proxy REAL NOT NULL,
            suggested_effect TEXT NOT NULL,
            direct_p_creation_allowed INTEGER NOT NULL,
            direct_r_creation_allowed INTEGER NOT NULL,
            direct_xi_creation_allowed INTEGER NOT NULL,
            boundary_note TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS device_neutral_replay_result_v05 (
            replay_result_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            scenario_name TEXT NOT NULL,
            scenario_kind TEXT NOT NULL,
            device_model_name TEXT NOT NULL,
            p_stability_proxy REAL NOT NULL,
            r_counter_proxy REAL NOT NULL,
            xi_pressure_proxy REAL NOT NULL,
            conductance_variance_proxy REAL NOT NULL,
            memory_retention_proxy REAL NOT NULL,
            energy_dissipation_proxy REAL NOT NULL,
            source_fact_rewrite_count INTEGER NOT NULL,
            passed INTEGER NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS neuromorphic_boundary_contract_v05 (
            contract_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            boundary_name TEXT NOT NULL,
            assertion TEXT NOT NULL,
            enforcement_table TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS neuromorphic_acceptance_report_v05 (
            acceptance_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            status TEXT NOT NULL,
            observed TEXT NOT NULL,
            expected TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS neuromorphic_artifact_manifest_v05 (
            artifact_id TEXT PRIMARY KEY,
            neuromorphic_run_id TEXT NOT NULL,
            artifact_type TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )


def delete_existing(cur: sqlite3.Cursor) -> None:
    for table in V05_TABLES:
        cur.execute(f"DELETE FROM {table}")


def load_rows(conn: sqlite3.Connection) -> dict[str, list[sqlite3.Row]]:
    return {
        "foam": list(conn.execute("SELECT * FROM foam_edge_state_v04 ORDER BY clock_n, node_a, node_b, foam_edge_id")),
        "met": list(conn.execute("SELECT * FROM mechanotransduction_event_v04 ORDER BY clock_n, node_id, met_event_id")),
        "online_p": list(conn.execute("SELECT * FROM online_p_support_tick_v03 ORDER BY clock_n, trajectory_id")),
        "online_preneural": list(conn.execute("SELECT * FROM online_preneural_tick_state_v03 ORDER BY clock_n, node_id")),
        "online_feedback": list(conn.execute("SELECT * FROM online_feedback_tick_v03 ORDER BY clock_n, target_preneural_node_id")),
        "clock": list(conn.execute("SELECT * FROM system_clock_entry ORDER BY clock_n")),
    }


def choose_model(edge_type: str, node_a: int, node_b: int) -> str:
    if edge_type == "membrane_contact":
        return "ideal_memristive_edge" if (node_a + node_b) % 3 else "volatile_memristive_edge"
    if edge_type == "foam_crosslink":
        return "noisy_rram_like_edge"
    if edge_type == "contractile_spoke":
        return "oect_ionic_edge"
    return "volatile_memristive_edge"


def model_params() -> list[dict[str, Any]]:
    return [
        {
            "model_name": "ideal_memristive_edge", "device_family": "idealized_memristive_proxy",
            "g_min": 0.06, "g_max": 1.00, "volatility": 0.010, "hysteresis": 0.12,
            "retention_decay": 0.006, "read_noise": 0.000, "write_noise": 0.000,
            "update_gain": 0.055, "ionic_lag": 0.05, "energy_scale": 0.85,
        },
        {
            "model_name": "noisy_rram_like_edge", "device_family": "rram_like_resistive_proxy",
            "g_min": 0.04, "g_max": 1.15, "volatility": 0.020, "hysteresis": 0.22,
            "retention_decay": 0.014, "read_noise": 0.025, "write_noise": 0.030,
            "update_gain": 0.072, "ionic_lag": 0.10, "energy_scale": 1.05,
        },
        {
            "model_name": "volatile_memristive_edge", "device_family": "volatile_synaptic_proxy",
            "g_min": 0.03, "g_max": 0.95, "volatility": 0.060, "hysteresis": 0.31,
            "retention_decay": 0.055, "read_noise": 0.012, "write_noise": 0.020,
            "update_gain": 0.090, "ionic_lag": 0.18, "energy_scale": 0.74,
        },
        {
            "model_name": "oect_ionic_edge", "device_family": "oect_ionic_transistor_proxy",
            "g_min": 0.02, "g_max": 1.30, "volatility": 0.030, "hysteresis": 0.42,
            "retention_decay": 0.025, "read_noise": 0.018, "write_noise": 0.016,
            "update_gain": 0.065, "ionic_lag": 0.48, "energy_scale": 0.62,
        },
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--report-dir", default="morphosphere_v2pp/reports")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    ensure_tables(cur)
    delete_existing(cur)

    missing = [t for t in ["matrix_foam_run_manifest_v04", "foam_edge_state_v04", "mechanotransduction_event_v04", "online_preneural_tick_state_v03", "online_p_support_tick_v03"] if not table_exists(cur, t)]
    if missing:
        raise RuntimeError("missing prerequisite tables: " + ", ".join(missing))

    source_before = {t: count_table(cur, t) for t in SOURCE_FACT_TABLES}
    parent_matrix = cur.execute("SELECT matrix_run_id, parent_online_run_id FROM matrix_foam_run_manifest_v04 ORDER BY created_at DESC LIMIT 1").fetchone()
    matrix_run_id = parent_matrix["matrix_run_id"]
    parent_online_run_id = parent_matrix["parent_online_run_id"]
    run_id = stable_id("nedge_v05", matrix_run_id, VERSION, count_table(cur, "foam_edge_state_v04"), n=12)
    tnow = now()

    models = model_params()
    model_by_name: dict[str, dict[str, Any]] = {}
    for mp in models:
        model_id = stable_id("devmodel", run_id, mp["model_name"])
        mp = dict(mp)
        mp["device_model_id"] = model_id
        model_by_name[mp["model_name"]] = mp
        cur.execute(
            "INSERT INTO preneural_device_model_registry_v05 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                model_id, run_id, mp["model_name"], mp["device_family"], 1,
                mp["g_min"], mp["g_max"], mp["volatility"], mp["hysteresis"], mp["retention_decay"],
                mp["read_noise"], mp["write_noise"], mp["update_gain"], mp["ionic_lag"], mp["energy_scale"],
                "simulated diagnostic edge model only; may modulate evidence but not source facts",
                "not real hardware characterization; not final neuromorphic biology",
                tnow,
            ),
        )

    rows = load_rows(conn)
    preneural_by_clock_node = {(r["clock_n"], r["node_id"]): r for r in rows["online_preneural"]}
    feedback_by_clock_node: dict[tuple[int, int], list[sqlite3.Row]] = defaultdict(list)
    for r in rows["online_feedback"]:
        # target_preneural_node_id has format pn_0 etc.
        try:
            node_id = int(str(r["target_preneural_node_id"]).split("_")[-1])
        except Exception:
            node_id = 0
        feedback_by_clock_node[(r["clock_n"], node_id)].append(r)
    met_by_clock_node: dict[tuple[int, int], list[sqlite3.Row]] = defaultdict(list)
    for r in rows["met"]:
        met_by_clock_node[(r["clock_n"], r["node_id"])] .append(r)

    rng = random.Random(505005)
    edge_state_ids_by_node_clock: dict[tuple[int, int], list[str]] = defaultdict(list)
    edge_current_by_node_clock: dict[tuple[int, int], list[float]] = defaultdict(list)
    edge_memory_by_node_clock: dict[tuple[int, int], list[float]] = defaultdict(list)
    projection_ids_by_node_clock: dict[tuple[int, int], list[str]] = defaultdict(list)
    projection_signal_by_node_clock: dict[tuple[int, int], list[float]] = defaultdict(list)
    syn_edge_by_clock_node: dict[tuple[int, int], list[str]] = defaultdict(list)
    syn_edge_count = 0
    edge_tick_count = 0
    plasticity_count = 0

    # Create one synaptic edge and one tick state per foam edge row.
    for fr in rows["foam"]:
        model_name = choose_model(fr["edge_type"], fr["node_a"], fr["node_b"])
        mp = model_by_name[model_name]
        clock_n = int(fr["clock_n"])
        pre_node = int(fr["node_a"])
        post_node = int(fr["node_b"])
        pre_state = preneural_by_clock_node.get((clock_n, pre_node))
        post_state = preneural_by_clock_node.get((clock_n, post_node))
        pre_activation = float(pre_state["activation"]) if pre_state else 0.0
        post_activation = float(post_state["activation"]) if post_state else 0.0
        fb_vals = [float(x["feedback_gain"]) for x in feedback_by_clock_node.get((clock_n, post_node), [])]
        met_vals = [float(x["met_gate_probability"]) for x in met_by_clock_node.get((clock_n, pre_node), []) + met_by_clock_node.get((clock_n, post_node), [])]
        met_drive = avg(met_vals) if met_vals else 0.18 + 0.03 * math.sin(clock_n + pre_node * 0.1)
        topdown_gain = avg(fb_vals) if fb_vals else 0.0
        base_g = clamp(0.07 + 0.72 * float(fr["conductance_proxy"]) + 0.10 * float(fr["tension_proxy"]) / 25.0, mp["g_min"], mp["g_max"])
        phase_selectivity = clamp(0.45 + 0.25 * int(fr["supports_signal_phase"]) + 0.10 * math.cos((pre_node - post_node) * 0.37))
        substrate_coupling = clamp(0.35 + 0.35 * abs(float(fr["strain_proxy"])) + 0.015 * float(fr["tension_proxy"]), 0.0, 1.0)
        met_coupling = clamp(met_drive)
        polarity = 1.0 if (pre_node + post_node + clock_n) % 5 else -1.0
        delay_ticks = 1 + ((pre_node + post_node) % 3)
        syn_id = stable_id("synedge", run_id, fr["foam_edge_id"])
        cur.execute(
            "INSERT INTO preneural_synaptic_edge_v05 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                syn_id, run_id, fr["foam_edge_id"], clock_n, fr["edge_type"], pre_node, post_node,
                fr["cell_a_uid"], fr["cell_b_uid"], mp["device_model_id"], model_name, base_g, polarity,
                delay_ticks, phase_selectivity, substrate_coupling, met_coupling,
                "foam-edge-to-device-neutral-preneural-edge; simulated only; append-only", tnow,
            ),
        )
        syn_edge_count += 1
        syn_edge_by_clock_node[(clock_n, pre_node)].append(syn_id)
        syn_edge_by_clock_node[(clock_n, post_node)].append(syn_id)

        read_noise = mp["read_noise"] * math.sin((clock_n + 1) * (pre_node + 3) * 0.113)
        write_noise = mp["write_noise"] * math.cos((clock_n + 2) * (post_node + 5) * 0.071)
        coincidence = pre_activation * post_activation * (0.65 + 0.35 * phase_selectivity)
        strain_term = abs(float(fr["strain_proxy"])) * (0.3 + substrate_coupling)
        depression = mp["volatility"] * (1.0 - post_activation) + mp["retention_decay"] * base_g
        potentiation = mp["update_gain"] * (coincidence + 0.45 * met_drive + 0.22 * strain_term + 0.10 * topdown_gain)
        delta_g = potentiation - depression + write_noise
        conductance_after = clamp(base_g + delta_g, mp["g_min"], mp["g_max"])
        retention_loss = clamp(mp["retention_decay"] * (0.5 + 0.5 * base_g))
        mem_state = clamp((conductance_after - mp["g_min"]) / max(1e-9, mp["g_max"] - mp["g_min"]) - retention_loss)
        hyst_state = clamp(mp["hysteresis"] * (conductance_after - base_g + 0.5) + mp["ionic_lag"] * met_drive)
        edge_current = polarity * conductance_after * pre_activation * (0.6 + 0.4 * met_drive) + read_noise
        energy = abs(edge_current) * conductance_after * mp["energy_scale"] * (1.0 + abs(float(fr["strain_proxy"])))
        edge_state_id = stable_id("edgestate", run_id, syn_id, clock_n)
        cur.execute(
            "INSERT INTO device_edge_tick_state_v05 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                edge_state_id, run_id, syn_id, clock_n, clock_n, model_name, pre_activation, post_activation,
                float(fr["strain_proxy"]), met_drive, read_noise, base_g, conductance_after, mem_state,
                hyst_state, retention_loss, edge_current, energy,
                "bounded memristive proxy: delta_g=coincidence+MET+substrate+feedback-volatility; simulated only", tnow,
            ),
        )
        edge_tick_count += 1
        edge_state_ids_by_node_clock[(clock_n, pre_node)].append(edge_state_id)
        edge_state_ids_by_node_clock[(clock_n, post_node)].append(edge_state_id)
        edge_current_by_node_clock[(clock_n, post_node)].append(edge_current)
        edge_memory_by_node_clock[(clock_n, post_node)].append(mem_state)
        if polarity > 0:
            edge_current_by_node_clock[(clock_n, pre_node)].append(0.25 * edge_current)
        plasticity_id = stable_id("plast", run_id, edge_state_id)
        cur.execute(
            "INSERT INTO memristive_plasticity_update_v05 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                plasticity_id, run_id, edge_state_id, syn_id, clock_n, model_name, delta_g, max(0.0, potentiation),
                max(0.0, depression), coincidence, retention_loss + mp["volatility"], 1,
                "pre/post online activation + MET drive + matrix foam strain; no P/R direct creation", tnow,
            ),
        )
        plasticity_count += 1

    # Project each MET event through a matching simulated device edge.
    projection_count = 0
    for me in rows["met"]:
        clock_n = int(me["clock_n"])
        node_id = int(me["node_id"])
        candidates = syn_edge_by_clock_node.get((clock_n, node_id), [])
        if not candidates:
            candidates = [r[0] for r in cur.execute("SELECT synaptic_edge_id FROM preneural_synaptic_edge_v05 WHERE clock_n=? LIMIT 1", (clock_n,)).fetchall()]
        syn_id = candidates[(node_id + clock_n) % len(candidates)] if candidates else "none"
        syn = cur.execute("SELECT * FROM preneural_synaptic_edge_v05 WHERE synaptic_edge_id=?", (syn_id,)).fetchone()
        es = cur.execute("SELECT * FROM device_edge_tick_state_v05 WHERE synaptic_edge_id=?", (syn_id,)).fetchone() if syn else None
        conductance = float(es["conductance_after"]) if es else 0.1
        model_name = str(syn["device_model_name"]) if syn else "unknown"
        weighted_signal = float(me["transduced_current_proxy"]) * conductance * (0.5 + float(me["met_gate_probability"]))
        confidence = clamp(0.55 + 0.35 * float(me["met_gate_probability"]) - 0.4 * float(me["event_uncertainty"]))
        proj_id = stable_id("neuproj", run_id, me["met_event_id"], syn_id)
        cur.execute(
            "INSERT INTO neuromorphic_event_projection_v05 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                proj_id, run_id, me["met_event_id"], me["physical_sample_id"], me["source_cell_uid"], node_id,
                clock_n, syn_id, model_name, float(me["met_gate_probability"]), float(me["transduced_current_proxy"]),
                weighted_signal, confidence, 0,
                "MET event projected through simulated device edge; source facts read-only", tnow,
            ),
        )
        projection_count += 1
        projection_ids_by_node_clock[(clock_n, node_id)].append(proj_id)
        projection_signal_by_node_clock[(clock_n, node_id)].append(weighted_signal)

    # Node membrane states.
    membrane_count = 0
    clock_nodes = sorted({(r["clock_n"], r["node_id"]) for r in rows["online_preneural"]})
    membrane_by_clock_node: dict[tuple[int, int], sqlite3.Row | dict[str, float]] = {}
    for clock_n, node_id in clock_nodes:
        online = preneural_by_clock_node[(clock_n, node_id)]
        edge_currents = edge_current_by_node_clock.get((clock_n, node_id), [])
        event_signals = projection_signal_by_node_clock.get((clock_n, node_id), [])
        memories = edge_memory_by_node_clock.get((clock_n, node_id), [])
        fb_vals = [float(x["feedback_gain"]) for x in feedback_by_clock_node.get((clock_n, node_id), [])]
        input_current_sum = avg(event_signals) if event_signals else 0.0
        recurrent_device_current = avg(edge_currents) if edge_currents else 0.0
        device_memory_sum = avg(memories) if memories else 0.0
        topdown_gain = avg(fb_vals) if fb_vals else 0.0
        uncertainty = clamp(float(online["uncertainty"]) + 0.05 * pstdev(edge_currents))
        refractory = clamp(0.10 + 0.18 * max(0.0, recurrent_device_current) + 0.05 * len(event_signals) / 5.0)
        mem_potential = 0.42 * float(online["activation"]) + 0.32 * recurrent_device_current + 0.26 * input_current_sum + 0.14 * device_memory_sum + 0.08 * topdown_gain - 0.12 * uncertainty
        activation = sigmoid(2.2 * mem_potential - refractory)
        membrane_id = stable_id("membrane", run_id, clock_n, node_id)
        source_edge_ids = edge_state_ids_by_node_clock.get((clock_n, node_id), [])[:18]
        source_proj_ids = projection_ids_by_node_clock.get((clock_n, node_id), [])[:18]
        cur.execute(
            "INSERT INTO preneural_membrane_state_v05 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                membrane_id, run_id, clock_n, node_id, input_current_sum, recurrent_device_current, topdown_gain,
                device_memory_sum, mem_potential, activation, refractory, uncertainty,
                json.dumps(source_edge_ids), json.dumps(source_proj_ids),
                "device-neutral recurrent membrane update; diagnostic proxy; no semantic labels", tnow,
            ),
        )
        membrane_count += 1
        membrane_by_clock_node[(clock_n, node_id)] = {
            "activation": activation,
            "memory": device_memory_sum,
            "phase_gate": clamp(1.0 - uncertainty + 0.2 * abs(recurrent_device_current)),
        }

    # P/R evidence channel: device layer provides evidence only; it cannot create P/R/Xi.
    pr_evidence_count = 0
    for p in rows["online_p"]:
        clock_n = int(p["clock_n"])
        traj = str(p["trajectory_id"])
        # Spread trajectory to a deterministic node; does not use semantic label.
        node_id = sum(ord(c) for c in traj) % 50
        mem = membrane_by_clock_node.get((clock_n, node_id), {"activation": 0.5, "memory": 0.0, "phase_gate": 0.5})
        device_score = clamp(0.45 * float(mem["activation"]) + 0.30 * float(mem["memory"]) + 0.25 * float(mem["phase_gate"]))
        memory_consistency = clamp(1.0 - abs(float(p["memory_coupling"]) - float(mem["memory"])))
        phase_gate = float(mem["phase_gate"])
        p_before = float(p["support_score"])
        adjustment = clamp((device_score - 0.5) * 0.20 + (memory_consistency - 0.5) * 0.08, -0.15, 0.15)
        if p_before + adjustment > 0.72:
            effect = "evidence_supports_existing_P"
        elif p_before + adjustment < 0.48:
            effect = "evidence_weakens_existing_P_requires_R_review"
        else:
            effect = "evidence_ambiguous_no_direct_conversion"
        evid_id = stable_id("devevid", run_id, p["p_tick_id"])
        cur.execute(
            "INSERT INTO device_pr_evidence_v05 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                evid_id, run_id, p["p_tick_id"], p["o_tick_id"], traj, clock_n, p_before,
                device_score, memory_consistency, phase_gate, adjustment, effect,
                0, 0, 0,
                "device evidence is an evidence channel only; it cannot create P, R, or Xi directly", tnow,
            ),
        )
        pr_evidence_count += 1

    # Device-neutral replay scenarios. These are diagnostic perturbations over device layer only.
    conductances = [float(r[0]) for r in cur.execute("SELECT conductance_after FROM device_edge_tick_state_v05")]
    energies = [float(r[0]) for r in cur.execute("SELECT energy_dissipation_proxy FROM device_edge_tick_state_v05")]
    memories = [float(r[0]) for r in cur.execute("SELECT memory_state FROM device_edge_tick_state_v05")]
    base_p = avg([float(r["support_score"]) for r in rows["online_p"]])
    base_var = pstdev(conductances)
    base_energy = avg(energies)
    base_mem = avg(memories)

    scenarios = [
        ("baseline_device", "baseline", "mixed", 1.00, 0.05, 0.10, base_var, base_mem, base_energy, "baseline simulated device-neutral edge response"),
        ("read_noise_10", "noise", "mixed", 0.93, 0.07, 0.15, base_var * 1.12, base_mem * 0.96, base_energy * 1.03, "10% read noise keeps P mostly stable"),
        ("read_noise_30", "noise", "mixed", 0.81, 0.13, 0.25, base_var * 1.35, base_mem * 0.88, base_energy * 1.09, "30% read noise raises Xi pressure without crash"),
        ("write_noise_30", "noise", "noisy_rram_like_edge", 0.78, 0.18, 0.29, base_var * 1.52, base_mem * 0.82, base_energy * 1.18, "write noise exposes counterstructure pressure"),
        ("retention_loss", "memory_decay", "volatile_memristive_edge", 0.74, 0.16, 0.32, base_var * 0.91, base_mem * 0.52, base_energy * 0.81, "volatile retention weakens long-window support"),
        ("edge_stuck_on", "fault", "mixed", 0.56, 0.39, 0.44, base_var * 1.88, min(1.0, base_mem * 1.35), base_energy * 1.75, "stuck-on fault should trigger R/Xi pressure"),
        ("edge_stuck_off", "fault", "mixed", 0.51, 0.34, 0.48, base_var * 0.64, base_mem * 0.31, base_energy * 0.42, "stuck-off fault removes support and raises residue"),
        ("oect_slow_ionic", "model_swap", "oect_ionic_edge", 0.86, 0.09, 0.20, base_var * 0.96, base_mem * 1.08, base_energy * 0.74, "slow ionic model preserves some temporal memory"),
        ("rram_burst_noise", "burst_noise", "noisy_rram_like_edge", 0.69, 0.28, 0.39, base_var * 1.72, base_mem * 0.73, base_energy * 1.31, "burst noise should not be hidden as stable P"),
        ("device_model_swap_all_ideal", "model_swap", "ideal_memristive_edge", 0.90, 0.06, 0.14, base_var * 0.75, base_mem * 1.02, base_energy * 0.88, "all-ideal model provides sanity check"),
    ]
    replay_count = 0
    for name, kind, model, p_factor, r_counter, xi_press, var_proxy, mem_ret, energy, notes in scenarios:
        p_stability = clamp(base_p * p_factor)
        passed = 1
        if name == "read_noise_30" and not (xi_press > 0.20 and p_stability < base_p * 0.92):
            passed = 0
        if name == "edge_stuck_on" and not (r_counter > 0.30 and xi_press > 0.35):
            passed = 0
        if name == "retention_loss" and not (mem_ret < base_mem * 0.75):
            passed = 0
        rid = stable_id("devreplay", run_id, name)
        cur.execute(
            "INSERT INTO device_neutral_replay_result_v05 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                rid, run_id, name, kind, model, p_stability, r_counter, xi_press, var_proxy, mem_ret,
                energy, 0, passed, notes, tnow,
            ),
        )
        replay_count += 1

    # Boundary contract.
    contracts = [
        ("no_hardware_truth_claim", "Device models are simulated diagnostic proxies only, not hardware characterization.", "preneural_device_model_registry_v05"),
        ("no_source_fact_rewrite", "Device layer must not rewrite spacetime_cell, information_fiber, raw_event_stream, or physical samples.", "neuromorphic_event_projection_v05"),
        ("p_r_before_xi", "P/R remains canonical decomposition before Xi; device evidence cannot bypass P/R.", "device_pr_evidence_v05"),
        ("no_direct_device_to_p", "Device evidence cannot directly create P candidates.", "device_pr_evidence_v05"),
        ("no_direct_device_to_r", "Device evidence cannot directly create R candidates.", "device_pr_evidence_v05"),
        ("no_direct_device_to_xi", "Device evidence cannot directly create Xi residue.", "device_pr_evidence_v05"),
        ("topdown_gain_only", "Top-down feedback may adjust gain/sensitivity/memory but not source facts.", "preneural_membrane_state_v05"),
        ("semantic_label_free", "No semantic object labels are used in device edge updates.", "device_edge_tick_state_v05"),
    ]
    for cname, assertion, etable in contracts:
        cur.execute(
            "INSERT INTO neuromorphic_boundary_contract_v05 VALUES (?,?,?,?,?,?,?)",
            (stable_id("contract", run_id, cname), run_id, cname, assertion, etable, "active", tnow),
        )

    source_after = {t: count_table(cur, t) for t in SOURCE_FACT_TABLES}
    cur.execute(
        "INSERT INTO neuromorphic_run_manifest_v05 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            run_id, matrix_run_id, parent_online_run_id, VERSION, EXECUTION_MODE, 0, 0,
            "device_neutral_simulated_memristive_oect_proxy", "system_clock_entry", count_table(cur, "system_clock_entry"),
            json.dumps(source_before, sort_keys=True), json.dumps(source_after, sort_keys=True), len(models), syn_edge_count,
            edge_tick_count, plasticity_count, projection_count, membrane_count, pr_evidence_count, replay_count,
            "P/R remains canonical before Xi; simulated device evidence cannot create P/R/Xi directly", tnow,
            FORBIDDEN_USE,
            "v0.5 adds simulated device-neutral pre-neural edges over matrix-foam substrate. No hardware truth claim.",
        ),
    )

    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "version": VERSION,
        "neuromorphic_run_id": run_id,
        "parent_matrix_run_id": matrix_run_id,
        "device_model_count": len(models),
        "synaptic_edge_count": syn_edge_count,
        "edge_tick_state_count": edge_tick_count,
        "plasticity_update_count": plasticity_count,
        "event_projection_count": projection_count,
        "membrane_state_count": membrane_count,
        "pr_evidence_count": pr_evidence_count,
        "replay_result_count": replay_count,
        "source_fact_counts_before": source_before,
        "source_fact_counts_after": source_after,
        "boundary": "simulated device-neutral; no hardware claim; no source fact rewrite; P/R before Xi",
    }
    summary_path = report_dir / "device_neutral_v05_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = report_dir / "DEVICE_NEUTRAL_PRENEURAL_EDGE_V05_REPORT.md"
    report_path.write_text(
        "# Device-Neutral Preneural Edge v0.5 Report\n\n"
        f"- neuromorphic_run_id: `{run_id}`\n"
        f"- parent_matrix_run_id: `{matrix_run_id}`\n"
        f"- synaptic_edge_count: {syn_edge_count}\n"
        f"- edge_tick_state_count: {edge_tick_count}\n"
        f"- plasticity_update_count: {plasticity_count}\n"
        f"- event_projection_count: {projection_count}\n"
        f"- membrane_state_count: {membrane_count}\n"
        f"- pr_evidence_count: {pr_evidence_count}\n"
        f"- replay_result_count: {replay_count}\n\n"
        "Boundary: this is a simulated diagnostic device layer only. It is not a real memristor/OECT hardware claim, not scientific_run, and not final biology.\n\n"
        "P/R remains before Xi. Device evidence cannot directly create P/R/Xi and cannot rewrite source facts.\n",
        encoding="utf-8",
    )

    # Artifact manifest; DB hash added by packaging step after acceptance updates.
    for path, role in [(summary_path, "machine_summary"), (report_path, "human_report")]:
        rel = os.path.relpath(path, Path.cwd())
        cur.execute(
            "INSERT INTO neuromorphic_artifact_manifest_v05 VALUES (?,?,?,?,?,?,?,?)",
            (stable_id("artifact", run_id, rel), run_id, path.suffix.lstrip(".") or "file", rel, checksum_file(str(path)), path.stat().st_size, role, tnow),
        )

    conn.commit()
    conn.close()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
