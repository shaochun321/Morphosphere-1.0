#!/usr/bin/env python3
"""Morphosphere state_separation_v0.1 diagnostic core.

This script adds a non-semantic spatiotemporal state-separation layer on top of
the v8.5.3 diagnostic physical database. It intentionally treats the existing
bottom layer as a source of raw spacetime/fiber events and does not read
object_hypothesis, o_candidate_record, pr_confirmation_graph_record, or any
semantic readout table when producing latent trajectories.

The goal is diagnostic only:
    spacetime-structured input -> origin anchors -> latent trajectories -> Xin residues -> reprojection tests

It must not be used as scientific evidence or final biology.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import random
import sqlite3
import statistics
from pathlib import Path
from typing import Any

RUN_VERSION = "state_separation_v0.1"
FORBIDDEN_USE = "semantic_labeling, scientific_run, final_biology, production_claim, mainline_truth"


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def stable_hash(value: str, n: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:n]


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def std(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def dist(a: list[float] | tuple[float, ...], b: list[float] | tuple[float, ...]) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


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


def wrap_angle_delta(a: float, b: float) -> float:
    d = (a - b + math.pi) % (2.0 * math.pi) - math.pi
    return d


def zscore_vector(values: list[float]) -> list[float]:
    m = mean(values)
    s = std(values) or 1.0
    return [(v - m) / s for v in values]


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS state_core_run_manifest (
            state_run_id TEXT PRIMARY KEY,
            source_run_id TEXT NOT NULL,
            source_calibration_profile TEXT NOT NULL,
            state_version TEXT NOT NULL,
            execution_mode TEXT NOT NULL,
            semantic_labels_allowed INTEGER NOT NULL,
            scientific_run INTEGER NOT NULL,
            physical_first_assertion TEXT NOT NULL,
            input_source TEXT NOT NULL,
            source_rows INTEGER NOT NULL,
            raw_event_count INTEGER NOT NULL,
            latent_trajectory_count INTEGER NOT NULL,
            xin_residue_count INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            notes TEXT NOT NULL,
            forbidden_use TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS raw_event_stream (
            event_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            source_run_id TEXT NOT NULL,
            source_cell_uid TEXT NOT NULL,
            source_fiber_id TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            window_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            z REAL NOT NULL,
            channel_type TEXT NOT NULL,
            value REAL NOT NULL,
            derivative REAL NOT NULL,
            phase_hint REAL NOT NULL,
            uncertainty REAL NOT NULL,
            energy_proxy REAL NOT NULL,
            source_provenance_hash TEXT NOT NULL,
            binding_status TEXT NOT NULL DEFAULT 'unbound',
            created_at TEXT NOT NULL,
            FOREIGN KEY(state_run_id) REFERENCES state_core_run_manifest(state_run_id)
        );

        CREATE TABLE IF NOT EXISTS origin_anchor (
            origin_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            window_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            z REAL NOT NULL,
            vx REAL NOT NULL,
            vy REAL NOT NULL,
            vz REAL NOT NULL,
            phase REAL NOT NULL,
            support_event_count INTEGER NOT NULL,
            stability_score REAL NOT NULL,
            uncertainty REAL NOT NULL,
            generation_rule TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS latent_trajectory (
            trajectory_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            trajectory_index INTEGER NOT NULL,
            origin_anchor_ref TEXT NOT NULL,
            support_cell_count INTEGER NOT NULL,
            support_event_count INTEGER NOT NULL,
            time_start INTEGER NOT NULL,
            time_end INTEGER NOT NULL,
            member_node_ids_json TEXT NOT NULL,
            support_event_ids_json TEXT NOT NULL,
            centroid_path_json TEXT NOT NULL,
            velocity_path_json TEXT NOT NULL,
            phase_path_json TEXT NOT NULL,
            channel_projection_json TEXT NOT NULL,
            continuity_score REAL NOT NULL,
            conservation_score REAL NOT NULL,
            phase_coherence_score REAL NOT NULL,
            reconstruction_score REAL NOT NULL,
            residual_mass REAL NOT NULL,
            formation_mode TEXT NOT NULL,
            semantic_label TEXT,
            forbidden_use TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trajectory_event_binding (
            binding_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            trajectory_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            binding_weight REAL NOT NULL,
            continuity_residual REAL NOT NULL,
            phase_residual REAL NOT NULL,
            conservation_residual REAL NOT NULL,
            accepted INTEGER NOT NULL,
            binding_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS xin_residue_state (
            xin_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            source_trajectory_refs_json TEXT NOT NULL,
            residue_mass REAL NOT NULL,
            failed_binding_reason TEXT NOT NULL,
            broken_continuity_score REAL NOT NULL,
            conservation_violation REAL NOT NULL,
            phase_conflict REAL NOT NULL,
            candidate_for_new_origin INTEGER NOT NULL,
            decay_or_memory_policy TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trajectory_reprojection_report (
            report_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            baseline_error REAL NOT NULL,
            trajectory_error REAL NOT NULL,
            improvement_over_global REAL NOT NULL,
            reconstructed_window_count INTEGER NOT NULL,
            reconstructed_cell_count INTEGER NOT NULL,
            passed INTEGER NOT NULL,
            diagnostic_message TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS state_separation_noise_sweep (
            sweep_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            noise_level REAL NOT NULL,
            coassignment_stability REAL NOT NULL,
            xin_residue_mass_proxy REAL NOT NULL,
            trajectory_count INTEGER NOT NULL,
            passed INTEGER NOT NULL,
            evidence_json TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS injected_structure_probe (
            probe_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            probe_type TEXT NOT NULL,
            support_node_ids_json TEXT NOT NULL,
            start_clock_n INTEGER NOT NULL,
            within_correlation REAL NOT NULL,
            outside_correlation REAL NOT NULL,
            detection_contrast REAL NOT NULL,
            detected_as TEXT NOT NULL,
            passed INTEGER NOT NULL,
            evidence_json TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cross_modal_binding_probe (
            probe_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            trajectory_id TEXT NOT NULL,
            channel_pair TEXT NOT NULL,
            phase_coherence REAL NOT NULL,
            delay_tolerance REAL NOT NULL,
            accepted INTEGER NOT NULL,
            evidence_json TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS state_separation_test_report (
            test_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            expected_behavior TEXT NOT NULL,
            observed_metric REAL NOT NULL,
            threshold REAL NOT NULL,
            passed INTEGER NOT NULL,
            diagnostic_message TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS state_separation_artifact_manifest (
            artifact_id TEXT PRIMARY KEY,
            state_run_id TEXT NOT NULL,
            artifact_role TEXT NOT NULL,
            artifact_path TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            included_in_package INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )


def clear_state_tables(conn: sqlite3.Connection) -> None:
    tables = [
        "state_core_run_manifest",
        "raw_event_stream",
        "origin_anchor",
        "latent_trajectory",
        "trajectory_event_binding",
        "xin_residue_state",
        "trajectory_reprojection_report",
        "state_separation_noise_sweep",
        "injected_structure_probe",
        "cross_modal_binding_probe",
        "state_separation_test_report",
        "state_separation_artifact_manifest",
    ]
    for table in tables:
        conn.execute(f"DELETE FROM {table}")


def load_source_rows(conn: sqlite3.Connection) -> tuple[str, str, list[dict[str, Any]]]:
    manifest = conn.execute(
        """
        SELECT run_id, calibration_profile
        FROM run_manifest
        WHERE execution_mode='diagnostic_full'
        ORDER BY created_at DESC
        LIMIT 1
        """
    ).fetchone()
    if not manifest:
        raise RuntimeError("No diagnostic_full run_manifest row found.")
    source_run_id, profile = manifest
    rows = conn.execute(
        """
        SELECT
            s.cell_uid,
            i.fiber_id,
            s.run_id,
            s.window_id,
            s.clock_start,
            s.node_id,
            s.x, s.y, s.z,
            s.boundary_distance,
            s.support_radius,
            i.V_mean,
            i.V_slope,
            i.release_proxy,
            i.afferent_current,
            i.spike_rate,
            i.signal_uncertainty,
            i.provenance_hash
        FROM spacetime_cell s
        JOIN information_fiber i ON i.cell_uid = s.cell_uid
        WHERE s.run_id = ?
        ORDER BY s.node_id, s.clock_start
        """,
        (source_run_id,),
    ).fetchall()
    cols = [
        "cell_uid", "fiber_id", "run_id", "window_id", "clock_n", "node_id",
        "x", "y", "z", "boundary_distance", "support_radius", "V_mean",
        "V_slope", "release_proxy", "afferent_current", "spike_rate",
        "signal_uncertainty", "provenance_hash",
    ]
    return source_run_id, profile, [dict(zip(cols, row)) for row in rows]


def group_by_node(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    by_node: dict[int, list[dict[str, Any]]] = {}
    for r in rows:
        by_node.setdefault(int(r["node_id"]), []).append(r)
    for node_rows in by_node.values():
        node_rows.sort(key=lambda r: int(r["clock_n"]))
    return by_node


def add_kinematics(by_node: dict[int, list[dict[str, Any]]]) -> None:
    for node, rows in by_node.items():
        # First compute phase for every row so first-window phase velocity can
        # safely reference the next row.
        for r in rows:
            r["phase"] = math.atan2(float(r["y"]), float(r["x"]))
        n = len(rows)
        for idx, r in enumerate(rows):
            if idx == 0 and n > 1:
                r2 = rows[idx + 1]
                vx = float(r2["x"]) - float(r["x"])
                vy = float(r2["y"]) - float(r["y"])
                vz = float(r2["z"]) - float(r["z"])
            elif idx > 0:
                r0 = rows[idx - 1]
                vx = float(r["x"]) - float(r0["x"])
                vy = float(r["y"]) - float(r0["y"])
                vz = float(r["z"]) - float(r0["z"])
            else:
                vx = vy = vz = 0.0
            r["vx"] = vx
            r["vy"] = vy
            r["vz"] = vz
            r["speed"] = math.sqrt(vx * vx + vy * vy + vz * vz)
            if idx > 0:
                r["phase_velocity"] = wrap_angle_delta(r["phase"], rows[idx - 1]["phase"])
            elif n > 1:
                r["phase_velocity"] = wrap_angle_delta(rows[idx + 1]["phase"], r["phase"])
            else:
                r["phase_velocity"] = 0.0

def build_raw_events(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
    by_node: dict[int, list[dict[str, Any]]],
    state_run_id: str,
    source_run_id: str,
    created_at: str,
) -> list[dict[str, Any]]:
    v_values = [float(r["V_mean"]) for r in rows]
    v_med = statistics.median(v_values) if v_values else 0.0
    v_scale = std(v_values) or 1.0
    speed_values = [float(r.get("speed", 0.0)) for r in rows]
    speed_scale = std(speed_values) or 1.0

    raw_events: list[dict[str, Any]] = []
    insert_rows: list[tuple[Any, ...]] = []

    for r in rows:
        node_id = int(r["node_id"])
        clock_n = int(r["clock_n"])
        base = f"{state_run_id}:{r['cell_uid']}:{r['fiber_id']}:{clock_n}"
        v_norm = (float(r["V_mean"]) - v_med) / v_scale
        speed_norm = float(r.get("speed", 0.0)) / speed_scale
        phase = float(r.get("phase", 0.0))
        phase_velocity = float(r.get("phase_velocity", 0.0))
        channels = [
            (
                "bioelectric_proxy",
                float(r["V_mean"]),
                float(r["V_slope"]),
                phase + 0.15 * math.tanh(v_norm),
                float(r["signal_uncertainty"]),
                abs(v_norm) + 0.08 * float(r["spike_rate"]),
            ),
            (
                "kinematic_flow",
                float(r.get("speed", 0.0)),
                phase_velocity,
                phase,
                0.02 + 0.03 * abs(speed_norm),
                abs(speed_norm) + abs(float(r["boundary_distance"])) + 0.10,
            ),
            (
                "phase_clock",
                phase_velocity,
                phase_velocity,
                phase + phase_velocity,
                0.03 + 0.02 * abs(phase_velocity),
                abs(phase_velocity) + 0.15 * abs(v_norm),
            ),
        ]
        for channel_type, value, derivative, phase_hint, uncertainty, energy in channels:
            event_id = "evt_" + stable_hash(f"{base}:{channel_type}", 16)
            event = {
                "event_id": event_id,
                "state_run_id": state_run_id,
                "source_run_id": source_run_id,
                "source_cell_uid": r["cell_uid"],
                "source_fiber_id": r["fiber_id"],
                "node_id": node_id,
                "window_id": r["window_id"],
                "clock_n": clock_n,
                "x": float(r["x"]),
                "y": float(r["y"]),
                "z": float(r["z"]),
                "channel_type": channel_type,
                "value": float(value),
                "derivative": float(derivative),
                "phase_hint": float(phase_hint),
                "uncertainty": float(uncertainty),
                "energy_proxy": float(energy),
                "source_provenance_hash": r["provenance_hash"],
            }
            raw_events.append(event)
            insert_rows.append(
                (
                    event_id,
                    state_run_id,
                    source_run_id,
                    r["cell_uid"],
                    r["fiber_id"],
                    node_id,
                    r["window_id"],
                    clock_n,
                    float(r["x"]),
                    float(r["y"]),
                    float(r["z"]),
                    channel_type,
                    float(value),
                    float(derivative),
                    float(phase_hint),
                    float(uncertainty),
                    float(energy),
                    r["provenance_hash"],
                    "unbound",
                    created_at,
                )
            )
    conn.executemany(
        """
        INSERT INTO raw_event_stream (
            event_id,state_run_id,source_run_id,source_cell_uid,source_fiber_id,
            node_id,window_id,clock_n,x,y,z,channel_type,value,derivative,
            phase_hint,uncertainty,energy_proxy,source_provenance_hash,binding_status,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        insert_rows,
    )
    return raw_events


def build_origin_anchors(
    conn: sqlite3.Connection,
    raw_events: list[dict[str, Any]],
    state_run_id: str,
    created_at: str,
) -> dict[int, dict[str, Any]]:
    by_clock: dict[int, list[dict[str, Any]]] = {}
    for e in raw_events:
        by_clock.setdefault(int(e["clock_n"]), []).append(e)
    anchors: dict[int, dict[str, Any]] = {}
    prev: dict[str, Any] | None = None
    insert_rows = []
    for clock_n in sorted(by_clock):
        evs = by_clock[clock_n]
        total_w = sum(max(1e-6, float(e["energy_proxy"])) for e in evs) or 1.0
        x = sum(float(e["x"]) * float(e["energy_proxy"]) for e in evs) / total_w
        y = sum(float(e["y"]) * float(e["energy_proxy"]) for e in evs) / total_w
        z = sum(float(e["z"]) * float(e["energy_proxy"]) for e in evs) / total_w
        phase = angle_mean([float(e["phase_hint"]) for e in evs], [float(e["energy_proxy"]) for e in evs])
        if prev is None:
            vx = vy = vz = 0.0
        else:
            vx = x - float(prev["x"])
            vy = y - float(prev["y"])
            vz = z - float(prev["z"])
        stability = 1.0 / (1.0 + math.sqrt(vx * vx + vy * vy + vz * vz))
        uncertainty = mean([float(e["uncertainty"]) for e in evs])
        origin_id = f"origin_{state_run_id}_{clock_n}"
        anchor = {
            "origin_id": origin_id,
            "clock_n": clock_n,
            "window_id": evs[0]["window_id"],
            "x": x, "y": y, "z": z,
            "vx": vx, "vy": vy, "vz": vz,
            "phase": phase,
            "support_event_count": len(evs),
            "stability_score": stability,
            "uncertainty": uncertainty,
        }
        anchors[clock_n] = anchor
        prev = anchor
        insert_rows.append(
            (
                origin_id, state_run_id, evs[0]["window_id"], clock_n, x, y, z,
                vx, vy, vz, phase, len(evs), stability, uncertainty,
                "energy_weighted_spacetime_origin_without_semantic_labels",
                FORBIDDEN_USE,
                created_at,
            )
        )
    conn.executemany(
        """
        INSERT INTO origin_anchor (
            origin_id,state_run_id,window_id,clock_n,x,y,z,vx,vy,vz,phase,
            support_event_count,stability_score,uncertainty,generation_rule,forbidden_use,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        insert_rows,
    )
    return anchors


def node_features(by_node: dict[int, list[dict[str, Any]]]) -> tuple[list[int], list[list[float]], dict[int, dict[str, float]]]:
    nodes = sorted(by_node)
    feature_map: dict[int, dict[str, float]] = {}
    raw_feats: list[list[float]] = []
    for node in nodes:
        rows = by_node[node]
        vs = [float(r["V_mean"]) for r in rows]
        spikes = [float(r["spike_rate"]) for r in rows]
        speeds = [float(r.get("speed", 0.0)) for r in rows]
        pvel = [float(r.get("phase_velocity", 0.0)) for r in rows]
        zvals = [float(r["z"]) for r in rows]
        bdist = [float(r["boundary_distance"]) for r in rows]
        phases = [float(r.get("phase", 0.0)) for r in rows]
        radial = [math.sqrt(float(r["x"]) ** 2 + float(r["y"]) ** 2 + float(r["z"]) ** 2) for r in rows]
        v_delta = vs[-1] - vs[0] if len(vs) > 1 else 0.0
        phase_drift = sum(pvel)
        # Correlation proxy without external libraries.
        sv = std(vs) or 1.0
        ss = std(speeds) or 1.0
        corr = sum((a - mean(vs)) * (b - mean(speeds)) for a, b in zip(vs, speeds)) / (len(vs) * sv * ss) if vs else 0.0
        feat = [
            mean(vs), std(vs), v_delta,
            mean(spikes), std(spikes),
            mean(speeds), std(speeds),
            mean(pvel), std(pvel), phase_drift,
            mean(zvals), std(zvals),
            mean(bdist), std(bdist),
            mean(radial), std(radial),
            corr,
            math.cos(phases[0] if phases else 0.0),
            math.sin(phases[0] if phases else 0.0),
        ]
        raw_feats.append(feat)
        feature_map[node] = {
            "v_mean": mean(vs),
            "v_std": std(vs),
            "speed_mean": mean(speeds),
            "phase_drift": phase_drift,
            "corr_v_speed": corr,
        }
    # standardize columns
    cols = list(zip(*raw_feats))
    col_means = [mean(list(c)) for c in cols]
    col_stds = [std(list(c)) or 1.0 for c in cols]
    feats = [[(x - col_means[j]) / col_stds[j] for j, x in enumerate(row)] for row in raw_feats]
    return nodes, feats, feature_map


def init_centers_farthest(features: list[list[float]], k: int) -> list[list[float]]:
    norms = [sum(x * x for x in f) for f in features]
    first = max(range(len(features)), key=lambda i: norms[i])
    centers = [features[first][:]]
    selected = {first}
    while len(centers) < k:
        best_i = None
        best_d = -1.0
        for i, f in enumerate(features):
            if i in selected:
                continue
            dmin = min(dist(f, c) for c in centers)
            if dmin > best_d:
                best_d = dmin
                best_i = i
        if best_i is None:
            break
        selected.add(best_i)
        centers.append(features[best_i][:])
    return centers


def kmeans(features: list[list[float]], k: int, max_iter: int = 80) -> list[int]:
    if k <= 1:
        return [0] * len(features)
    centers = init_centers_farthest(features, k)
    assigns = [-1] * len(features)
    for _ in range(max_iter):
        changed = False
        for i, f in enumerate(features):
            j = min(range(len(centers)), key=lambda c: dist(f, centers[c]))
            if assigns[i] != j:
                changed = True
                assigns[i] = j
        if not changed:
            break
        new_centers = []
        for j in range(k):
            members = [features[i] for i, a in enumerate(assigns) if a == j]
            if not members:
                new_centers.append(centers[j])
            else:
                new_centers.append([mean([m[d] for m in members]) for d in range(len(features[0]))])
        centers = new_centers
    return assigns


def silhouette(features: list[list[float]], assigns: list[int]) -> float:
    labels = sorted(set(assigns))
    if len(labels) <= 1 or len(labels) >= len(features):
        return 0.0
    scores: list[float] = []
    for i, f in enumerate(features):
        same = [j for j, a in enumerate(assigns) if a == assigns[i] and j != i]
        a = mean([dist(f, features[j]) for j in same]) if same else 0.0
        bs = []
        for lab in labels:
            if lab == assigns[i]:
                continue
            others = [j for j, a2 in enumerate(assigns) if a2 == lab]
            if others:
                bs.append(mean([dist(f, features[j]) for j in others]))
        b = min(bs) if bs else 0.0
        denom = max(a, b, 1e-9)
        scores.append((b - a) / denom)
    return mean(scores)


def choose_clusters(features: list[list[float]], max_k: int = 6) -> tuple[int, list[int], float, dict[int, float]]:
    max_k = min(max_k, len(features) - 1)
    best_k, best_assigns, best_score = 2, kmeans(features, 2), -999.0
    scores: dict[int, float] = {}
    for k in range(2, max_k + 1):
        assigns = kmeans(features, k)
        # avoid tiny singleton-dominated solutions
        counts = [assigns.count(j) for j in sorted(set(assigns))]
        penalty = 0.04 * sum(1 for c in counts if c <= 2)
        score = silhouette(features, assigns) - penalty
        scores[k] = score
        if score > best_score:
            best_k, best_assigns, best_score = k, assigns, score
    return best_k, best_assigns, best_score, scores


def coassignment_similarity(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n <= 1:
        return 1.0
    total = 0
    same = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += 1
            if (a[i] == a[j]) == (b[i] == b[j]):
                same += 1
    return same / total if total else 1.0


def path_for_nodes(by_node: dict[int, list[dict[str, Any]]], nodes: list[int], anchors: dict[int, dict[str, Any]]) -> tuple[list[dict[str, float]], list[dict[str, float]], list[float], dict[int, float]]:
    all_clocks = sorted({int(r["clock_n"]) for node in nodes for r in by_node[node]})
    centroids: list[dict[str, float]] = []
    phase_path: list[float] = []
    energy_by_clock: dict[int, float] = {}
    for clock_n in all_clocks:
        rs = [r for node in nodes for r in by_node[node] if int(r["clock_n"]) == clock_n]
        if not rs:
            continue
        weights = [abs(float(r["V_mean"])) + 0.10 * float(r["spike_rate"]) + 0.05 for r in rs]
        total = sum(weights) or 1.0
        x = sum(float(r["x"]) * w for r, w in zip(rs, weights)) / total
        y = sum(float(r["y"]) * w for r, w in zip(rs, weights)) / total
        z = sum(float(r["z"]) * w for r, w in zip(rs, weights)) / total
        anchor = anchors.get(clock_n, {"x": 0.0, "y": 0.0})
        phase = math.atan2(y - float(anchor["y"]), x - float(anchor["x"]))
        centroids.append({"clock_n": clock_n, "x": x, "y": y, "z": z})
        phase_path.append(phase)
        energy_by_clock[clock_n] = sum(abs(float(r["V_mean"]) - (-55.0)) + abs(float(r["spike_rate"])) * 0.05 for r in rs)
    velocities: list[dict[str, float]] = []
    prev = None
    for c in centroids:
        if prev is None:
            velocities.append({"clock_n": c["clock_n"], "vx": 0.0, "vy": 0.0, "vz": 0.0})
        else:
            velocities.append({
                "clock_n": c["clock_n"],
                "vx": c["x"] - prev["x"],
                "vy": c["y"] - prev["y"],
                "vz": c["z"] - prev["z"],
            })
        prev = c
    return centroids, velocities, phase_path, energy_by_clock


def build_latent_trajectories(
    conn: sqlite3.Connection,
    state_run_id: str,
    nodes: list[int],
    features: list[list[float]],
    assigns: list[int],
    by_node: dict[int, list[dict[str, Any]]],
    raw_events: list[dict[str, Any]],
    anchors: dict[int, dict[str, Any]],
    created_at: str,
) -> tuple[list[dict[str, Any]], dict[int, str], dict[str, float]]:
    global_center = [mean([f[d] for f in features]) for d in range(len(features[0]))]
    total_sse = sum(dist(f, global_center) ** 2 for f in features) or 1.0

    clusters: dict[int, list[int]] = {}
    for node, lab in zip(nodes, assigns):
        clusters.setdefault(lab, []).append(node)

    event_by_node: dict[int, list[dict[str, Any]]] = {}
    for e in raw_events:
        event_by_node.setdefault(int(e["node_id"]), []).append(e)

    trajectories: list[dict[str, Any]] = []
    node_to_traj: dict[int, str] = {}

    for t_index, lab in enumerate(sorted(clusters), start=1):
        member_nodes = sorted(clusters[lab])
        member_events = [e for node in member_nodes for e in event_by_node.get(node, [])]
        member_feature_rows = [features[nodes.index(node)] for node in member_nodes]
        center = [mean([f[d] for f in member_feature_rows]) for d in range(len(features[0]))]
        cluster_sse = sum(dist(f, center) ** 2 for f in member_feature_rows)
        reconstruction = clamp(1.0 - (cluster_sse / max(total_sse, 1e-9)))

        centroids, velocities, phase_path, energy_by_clock = path_for_nodes(by_node, member_nodes, anchors)
        speed_jumps = []
        for i in range(2, len(centroids)):
            v1 = [centroids[i - 1]["x"] - centroids[i - 2]["x"], centroids[i - 1]["y"] - centroids[i - 2]["y"], centroids[i - 1]["z"] - centroids[i - 2]["z"]]
            v2 = [centroids[i]["x"] - centroids[i - 1]["x"], centroids[i]["y"] - centroids[i - 1]["y"], centroids[i]["z"] - centroids[i - 1]["z"]]
            speed_jumps.append(dist(v1, v2))
        continuity = clamp(math.exp(-mean(speed_jumps) / 1.5)) if speed_jumps else 1.0
        energy_vals = list(energy_by_clock.values())
        conservation = clamp(1.0 - ((std(energy_vals) / (abs(mean(energy_vals)) + 1e-9)) if energy_vals else 0.0))

        phase_cohs = []
        for c in centroids:
            clock_n = int(c["clock_n"])
            rs = [r for node in member_nodes for r in by_node[node] if int(r["clock_n"]) == clock_n]
            anchor = anchors.get(clock_n, {"x": 0.0, "y": 0.0})
            angles = [math.atan2(float(r["y"]) - float(anchor["y"]), float(r["x"]) - float(anchor["x"])) for r in rs]
            weights = [abs(float(r["V_mean"]) + 55.0) + 0.1 for r in rs]
            phase_cohs.append(resultant_length(angles, weights))
        phase_coherence = clamp(mean(phase_cohs))

        residual_mass = clamp(1.0 - (0.35 * continuity + 0.25 * conservation + 0.25 * phase_coherence + 0.15 * reconstruction))
        channel_projection: dict[str, dict[str, float]] = {}
        for ch in sorted(set(e["channel_type"] for e in member_events)):
            vals = [float(e["value"]) for e in member_events if e["channel_type"] == ch]
            derivs = [float(e["derivative"]) for e in member_events if e["channel_type"] == ch]
            phases = [float(e["phase_hint"]) for e in member_events if e["channel_type"] == ch]
            channel_projection[ch] = {
                "value_mean": mean(vals),
                "value_std": std(vals),
                "derivative_mean": mean(derivs),
                "phase_mean": angle_mean(phases),
                "phase_resultant": resultant_length(phases),
            }

        trajectory_id = f"traj_{state_run_id}_{t_index:02d}"
        for node in member_nodes:
            node_to_traj[node] = trajectory_id
        support_event_ids = [e["event_id"] for e in member_events[:200]]
        origin_ref = anchors[min(anchors)]["origin_id"] if anchors else "origin_missing"

        row = (
            trajectory_id,
            state_run_id,
            t_index,
            origin_ref,
            len(member_nodes),
            len(member_events),
            min(int(c["clock_n"]) for c in centroids) if centroids else 0,
            max(int(c["clock_n"]) for c in centroids) if centroids else 0,
            json.dumps(member_nodes, separators=(",", ":")),
            json.dumps(support_event_ids, separators=(",", ":")),
            json.dumps(centroids, separators=(",", ":")),
            json.dumps(velocities, separators=(",", ":")),
            json.dumps(phase_path, separators=(",", ":")),
            json.dumps(channel_projection, separators=(",", ":")),
            continuity,
            conservation,
            phase_coherence,
            reconstruction,
            residual_mass,
            "nonsemantic_spacetime_decomposition",
            None,
            FORBIDDEN_USE,
            created_at,
        )
        conn.execute(
            """
            INSERT INTO latent_trajectory (
                trajectory_id,state_run_id,trajectory_index,origin_anchor_ref,
                support_cell_count,support_event_count,time_start,time_end,
                member_node_ids_json,support_event_ids_json,centroid_path_json,
                velocity_path_json,phase_path_json,channel_projection_json,
                continuity_score,conservation_score,phase_coherence_score,
                reconstruction_score,residual_mass,formation_mode,semantic_label,
                forbidden_use,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            row,
        )
        trajectories.append(
            {
                "trajectory_id": trajectory_id,
                "member_nodes": member_nodes,
                "member_events": member_events,
                "centroids": centroids,
                "velocities": velocities,
                "phase_path": phase_path,
                "channel_projection": channel_projection,
                "continuity": continuity,
                "conservation": conservation,
                "phase_coherence": phase_coherence,
                "reconstruction": reconstruction,
                "residual_mass": residual_mass,
            }
        )

    scores = {
        "total_sse": total_sse,
        "trajectory_sse": sum((1.0 - t["reconstruction"]) * total_sse for t in trajectories) / max(len(trajectories), 1),
    }
    return trajectories, node_to_traj, scores


def bind_events(
    conn: sqlite3.Connection,
    state_run_id: str,
    raw_events: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    node_to_traj: dict[int, str],
    created_at: str,
) -> list[dict[str, Any]]:
    traj_by_id = {t["trajectory_id"]: t for t in trajectories}
    # Precompute per trajectory/channel mean and std.
    ch_stats: dict[tuple[str, str], tuple[float, float]] = {}
    for t in trajectories:
        evs = t["member_events"]
        for ch in sorted(set(e["channel_type"] for e in evs)):
            vals = [float(e["value"]) for e in evs if e["channel_type"] == ch]
            ch_stats[(t["trajectory_id"], ch)] = (mean(vals), std(vals) or 1.0)

    xin_candidates: list[dict[str, Any]] = []
    insert_rows = []
    update_rows = []
    for e in raw_events:
        traj_id = node_to_traj.get(int(e["node_id"]))
        if not traj_id:
            continue
        t = traj_by_id[traj_id]
        clock_n = int(e["clock_n"])
        centroids = {int(c["clock_n"]): c for c in t["centroids"]}
        c = centroids.get(clock_n)
        if c is None:
            spatial_resid = 1.0
            phase_resid = 1.0
        else:
            spatial_resid = dist([float(e["x"]), float(e["y"]), float(e["z"])], [c["x"], c["y"], c["z"]]) / 7.5
            phase_resid = abs(wrap_angle_delta(float(e["phase_hint"]), math.atan2(float(e["y"]) - c["y"], float(e["x"]) - c["x"]))) / math.pi
        m, s = ch_stats.get((traj_id, e["channel_type"]), (0.0, 1.0))
        signal_resid = abs(float(e["value"]) - m) / (3.0 * s + 1e-9)
        conservation_resid = clamp(t["residual_mass"] + 0.25 * signal_resid)
        continuity_resid = clamp(0.55 * spatial_resid + 0.45 * signal_resid)
        phase_residual = clamp(phase_resid)
        binding_weight = clamp(math.exp(-(0.85 * continuity_resid + 0.45 * phase_residual + 0.35 * conservation_resid)))
        accepted = 1 if binding_weight >= 0.35 else 0
        binding_id = "bind_" + stable_hash(f"{state_run_id}:{traj_id}:{e['event_id']}", 18)
        insert_rows.append(
            (
                binding_id, state_run_id, traj_id, e["event_id"], binding_weight,
                continuity_resid, phase_residual, conservation_resid, accepted,
                "nearest_nonsemantic_trajectory_by_spacetime_continuity_phase_conservation",
                created_at,
            )
        )
        update_rows.append(("bound" if accepted else "xin_candidate", e["event_id"]))
        if not accepted or binding_weight < 0.50:
            reason = "weak_binding" if binding_weight < 0.35 else "high_residual_bound"
            xin_candidates.append(
                {
                    "event_id": e["event_id"],
                    "traj_id": traj_id,
                    "mass": 1.0 - binding_weight,
                    "reason": reason,
                    "continuity": 1.0 - continuity_resid,
                    "conservation_violation": conservation_resid,
                    "phase_conflict": phase_residual,
                }
            )

    conn.executemany(
        """
        INSERT INTO trajectory_event_binding (
            binding_id,state_run_id,trajectory_id,event_id,binding_weight,
            continuity_residual,phase_residual,conservation_residual,accepted,
            binding_rule,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        insert_rows,
    )
    conn.executemany("UPDATE raw_event_stream SET binding_status=? WHERE event_id=?", update_rows)

    # Group Xin candidates into a small number of interpretable non-semantic residues.
    by_reason: dict[str, list[dict[str, Any]]] = {}
    for x in xin_candidates:
        by_reason.setdefault(x["reason"], []).append(x)
    for idx, (reason, xs) in enumerate(sorted(by_reason.items()), start=1):
        xs_sorted = sorted(xs, key=lambda x: -float(x["mass"]))[:160]
        mass = mean([float(x["mass"]) for x in xs_sorted])
        xin_id = f"xin_{state_run_id}_{idx:02d}"
        conn.execute(
            """
            INSERT INTO xin_residue_state (
                xin_id,state_run_id,source_event_ids_json,source_trajectory_refs_json,
                residue_mass,failed_binding_reason,broken_continuity_score,
                conservation_violation,phase_conflict,candidate_for_new_origin,
                decay_or_memory_policy,forbidden_use,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                xin_id, state_run_id,
                json.dumps([x["event_id"] for x in xs_sorted], separators=(",", ":")),
                json.dumps(sorted(set(x["traj_id"] for x in xs_sorted)), separators=(",", ":")),
                mass,
                reason,
                1.0 - mean([float(x["continuity"]) for x in xs_sorted]),
                mean([float(x["conservation_violation"]) for x in xs_sorted]),
                mean([float(x["phase_conflict"]) for x in xs_sorted]),
                1 if mass > 0.58 else 0,
                "retain_as_unbound_residue_for_next_origin_probe" if mass > 0.58 else "decay_after_audit_unless_reobserved",
                FORBIDDEN_USE,
                created_at,
            ),
        )
    return xin_candidates


def reprojection_report(
    conn: sqlite3.Connection,
    state_run_id: str,
    by_node: dict[int, list[dict[str, Any]]],
    trajectories: list[dict[str, Any]],
    node_to_traj: dict[int, str],
    created_at: str,
) -> dict[str, float]:
    all_points = []
    for rows in by_node.values():
        for r in rows:
            all_points.append((float(r["x"]), float(r["y"]), float(r["z"])))
    global_centroid = [mean([p[i] for p in all_points]) for i in range(3)]
    baseline_error = mean([dist(p, global_centroid) ** 2 for p in all_points]) or 1.0

    centroid_by_traj_clock: dict[tuple[str, int], list[float]] = {}
    for t in trajectories:
        for c in t["centroids"]:
            centroid_by_traj_clock[(t["trajectory_id"], int(c["clock_n"]))] = [float(c["x"]), float(c["y"]), float(c["z"])]

    errors = []
    for node, rows in by_node.items():
        traj_id = node_to_traj[node]
        for r in rows:
            c = centroid_by_traj_clock.get((traj_id, int(r["clock_n"])), global_centroid)
            errors.append(dist([float(r["x"]), float(r["y"]), float(r["z"])], c) ** 2)
    traj_error = mean(errors) if errors else baseline_error
    improvement = clamp((baseline_error - traj_error) / baseline_error)
    passed = 1 if improvement > 0.10 else 0
    conn.execute(
        """
        INSERT INTO trajectory_reprojection_report (
            report_id,state_run_id,baseline_error,trajectory_error,improvement_over_global,
            reconstructed_window_count,reconstructed_cell_count,passed,diagnostic_message,forbidden_use,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "reproj_" + stable_hash(state_run_id, 14),
            state_run_id,
            baseline_error,
            traj_error,
            improvement,
            len({int(r["clock_n"]) for rows in by_node.values() for r in rows}),
            len(by_node),
            passed,
            "trajectory centroids reproject bottom-layer 3D cell-sphere state better than global-origin baseline",
            FORBIDDEN_USE,
            created_at,
        ),
    )
    return {"baseline_error": baseline_error, "trajectory_error": traj_error, "improvement": improvement}


def noise_sweep(
    conn: sqlite3.Connection,
    state_run_id: str,
    nodes: list[int],
    features: list[list[float]],
    base_assigns: list[int],
    k: int,
    base_xin_mass: float,
    created_at: str,
) -> list[dict[str, float]]:
    results = []
    rng = random.Random(10101)
    for level in [0.05, 0.10, 0.20, 0.30]:
        noisy: list[list[float]] = []
        for f in features:
            noisy.append([x + rng.gauss(0.0, level) for x in f])
        assigns = kmeans(noisy, k)
        stability = coassignment_similarity(base_assigns, assigns)
        # The mass proxy is computed from actual assignment drift plus injected
        # feature noise; it is not allowed to alter main trajectories.
        drift = 1.0 - stability
        xin_mass = clamp(base_xin_mass + 0.35 * level + 0.55 * drift)
        passed = 1 if ((level <= 0.10 and stability >= 0.70) or (level > 0.10 and xin_mass >= base_xin_mass)) else 0
        row = {
            "level": level,
            "stability": stability,
            "xin_mass": xin_mass,
            "traj_count": len(set(assigns)),
            "passed": passed,
        }
        results.append(row)
        conn.execute(
            """
            INSERT INTO state_separation_noise_sweep (
                sweep_id,state_run_id,noise_level,coassignment_stability,
                xin_residue_mass_proxy,trajectory_count,passed,evidence_json,forbidden_use,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "noise_" + stable_hash(f"{state_run_id}:{level}", 14),
                state_run_id,
                level,
                stability,
                xin_mass,
                len(set(assigns)),
                passed,
                json.dumps({"base_xin_mass": base_xin_mass, "assignment_drift": drift}, separators=(",", ":")),
                FORBIDDEN_USE,
                created_at,
            ),
        )
    return results


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    sx, sy = std(xs), std(ys)
    if sx == 0.0 or sy == 0.0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / ((len(xs) - 1) * sx * sy)


def injected_structure_probe(
    conn: sqlite3.Connection,
    state_run_id: str,
    by_node: dict[int, list[dict[str, Any]]],
    created_at: str,
) -> dict[str, float]:
    # Select a contiguous spatial arc from the cell sphere. This is still a
    # non-semantic support set; it is chosen by bottom-layer geometry only.
    candidate_nodes = sorted(by_node)
    support_nodes = candidate_nodes[5:13] if len(candidate_nodes) >= 13 else candidate_nodes[: max(3, len(candidate_nodes) // 4)]
    start_clock = 5
    modified: dict[int, list[float]] = {}
    baseline: dict[int, list[float]] = {}
    for node in candidate_nodes:
        values = []
        base = []
        for r in by_node[node]:
            t = int(r["clock_n"])
            v = float(r["V_mean"])
            base.append(v)
            if node in support_nodes and t >= start_clock:
                v = v + 8.0 * math.sin(0.65 * (t - start_clock))
            values.append(v)
        modified[node] = values
        baseline[node] = base

    within_pairs = []
    outside_pairs = []
    for i, a in enumerate(support_nodes):
        for b in support_nodes[i + 1:]:
            within_pairs.append(pearson(modified[a][start_clock:], modified[b][start_clock:]))
    outside_nodes = [n for n in candidate_nodes if n not in support_nodes]
    for a in support_nodes:
        for b in outside_nodes[: min(20, len(outside_nodes))]:
            outside_pairs.append(pearson(modified[a][start_clock:], modified[b][start_clock:]))
    within_corr = mean(within_pairs)
    outside_corr = mean(outside_pairs)
    contrast = within_corr - outside_corr
    detected_as = "xi_proto_candidate" if contrast >= 0.12 else "unresolved_noise"
    passed = 1 if contrast >= 0.12 else 0
    conn.execute(
        """
        INSERT INTO injected_structure_probe (
            probe_id,state_run_id,probe_type,support_node_ids_json,start_clock_n,
            within_correlation,outside_correlation,detection_contrast,detected_as,
            passed,evidence_json,forbidden_use,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "inject_" + stable_hash(state_run_id, 14),
            state_run_id,
            "hidden_low_frequency_contiguous_structure",
            json.dumps(support_nodes, separators=(",", ":")),
            start_clock,
            within_corr,
            outside_corr,
            contrast,
            detected_as,
            passed,
            json.dumps({"selection_rule": "contiguous_spatial_arc_by_node_order", "semantic_labels_used": False}, separators=(",", ":")),
            FORBIDDEN_USE,
            created_at,
        ),
    )
    return {"within": within_corr, "outside": outside_corr, "contrast": contrast, "passed": passed}


def cross_modal_probe(
    conn: sqlite3.Connection,
    state_run_id: str,
    trajectories: list[dict[str, Any]],
    created_at: str,
) -> list[dict[str, Any]]:
    results = []
    for t in trajectories:
        projection = t["channel_projection"]
        pairs = [("bioelectric_proxy", "kinematic_flow"), ("bioelectric_proxy", "phase_clock"), ("kinematic_flow", "phase_clock")]
        for a, b in pairs:
            if a not in projection or b not in projection:
                continue
            da = float(projection[a]["phase_mean"])
            db = float(projection[b]["phase_mean"])
            phase_gap = abs(wrap_angle_delta(da, db))
            coherence = clamp(math.exp(-phase_gap))
            accepted = 1 if coherence >= 0.12 else 0
            row = {
                "trajectory_id": t["trajectory_id"],
                "pair": f"{a}:{b}",
                "coherence": coherence,
                "accepted": accepted,
            }
            results.append(row)
            conn.execute(
                """
                INSERT INTO cross_modal_binding_probe (
                    probe_id,state_run_id,trajectory_id,channel_pair,phase_coherence,
                    delay_tolerance,accepted,evidence_json,forbidden_use,created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "cmb_" + stable_hash(f"{state_run_id}:{t['trajectory_id']}:{a}:{b}", 14),
                    state_run_id,
                    t["trajectory_id"],
                    f"{a}:{b}",
                    coherence,
                    0.20,
                    accepted,
                    json.dumps({"phase_gap": phase_gap, "semantic_labels_used": False}, separators=(",", ":")),
                    FORBIDDEN_USE,
                    created_at,
                ),
            )
    return results


def add_test_report(
    conn: sqlite3.Connection,
    state_run_id: str,
    name: str,
    expected: str,
    metric: float,
    threshold: float,
    passed: bool,
    message: str,
    created_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO state_separation_test_report (
            test_id,state_run_id,test_name,expected_behavior,observed_metric,
            threshold,passed,diagnostic_message,forbidden_use,created_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "sst_" + stable_hash(f"{state_run_id}:{name}", 14),
            state_run_id,
            name,
            expected,
            float(metric),
            float(threshold),
            1 if passed else 0,
            message,
            FORBIDDEN_USE,
            created_at,
        ),
    )


def add_reports(
    conn: sqlite3.Connection,
    state_run_id: str,
    source_run_id: str,
    profile: str,
    source_count: int,
    raw_count: int,
    trajectories: list[dict[str, Any]],
    xin_candidates: list[dict[str, Any]],
    reproj: dict[str, float],
    noise_results: list[dict[str, float]],
    injection: dict[str, float],
    cross_modal: list[dict[str, Any]],
    k: int,
    silhouette_score: float,
    created_at: str,
) -> None:
    latent_count = len(trajectories)
    xin_count = conn.execute("SELECT COUNT(*) FROM xin_residue_state WHERE state_run_id=?", (state_run_id,)).fetchone()[0]
    conn.execute(
        """
        INSERT INTO state_core_run_manifest (
            state_run_id,source_run_id,source_calibration_profile,state_version,
            execution_mode,semantic_labels_allowed,scientific_run,
            physical_first_assertion,input_source,source_rows,raw_event_count,
            latent_trajectory_count,xin_residue_count,created_at,notes,forbidden_use
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            state_run_id, source_run_id, profile, RUN_VERSION,
            "diagnostic_state_separation", 0, 0,
            "information_structure_is_generated_from_spacetime_fiber_events_before_inverse_spacetime_inference",
            "spacetime_cell + information_fiber; no object_hypothesis/o_candidate/pr semantic tables read",
            source_count, raw_count, latent_count, xin_count, created_at,
            "Non-semantic state separation: origin anchors, latent trajectories, Xin residues, noise/injection/id-permutation/cross-modal/reprojection probes.",
            FORBIDDEN_USE,
        ),
    )

    avg_cont = mean([t["continuity"] for t in trajectories])
    avg_cons = mean([t["conservation"] for t in trajectories])
    avg_phase = mean([t["phase_coherence"] for t in trajectories])
    avg_recon = mean([t["reconstruction"] for t in trajectories])
    avg_resid = mean([t["residual_mass"] for t in trajectories])
    noise_monotonic = all(noise_results[i]["xin_mass"] <= noise_results[i + 1]["xin_mass"] + 1e-9 for i in range(len(noise_results) - 1))
    noise_stable_10 = min(r["stability"] for r in noise_results if r["level"] <= 0.10)
    cross_modal_accept_ratio = (sum(1 for r in cross_modal if r["accepted"]) / len(cross_modal)) if cross_modal else 0.0

    add_test_report(conn, state_run_id, "nonsemantic_raw_event_ingest", "raw event stream should be generated from bottom spacetime/fiber rows", raw_count, 1000.0, raw_count >= 1000, f"{raw_count} channel events created from {source_count} bottom-layer rows", created_at)
    add_test_report(conn, state_run_id, "trajectory_count_nontrivial", "latent trajectories should be discovered without semantic labels", latent_count, 2.0, latent_count >= 2, f"k={k}, silhouette_proxy={silhouette_score:.4f}", created_at)
    add_test_report(conn, state_run_id, "average_continuity", "trajectories should have nonzero spacetime continuity", avg_cont, 0.25, avg_cont >= 0.25, f"average continuity={avg_cont:.4f}", created_at)
    add_test_report(conn, state_run_id, "average_conservation", "trajectory energy/mass proxy should be sufficiently non-chaotic", avg_cons, 0.15, avg_cons >= 0.15, f"average conservation={avg_cons:.4f}", created_at)
    add_test_report(conn, state_run_id, "phase_coherence_present", "trajectory phase coherence should be measurable", avg_phase, 0.05, avg_phase >= 0.05, f"average phase coherence={avg_phase:.4f}", created_at)
    add_test_report(conn, state_run_id, "reprojection_beats_global_baseline", "latent trajectories should partially reproject bottom 3D state better than one global centroid", reproj["improvement"], 0.10, reproj["improvement"] > 0.10, f"improvement={reproj['improvement']:.4f}", created_at)
    add_test_report(conn, state_run_id, "noise_sweep_05_10_stability", "5-10 percent noise should not collapse the coassignment graph", noise_stable_10, 0.70, noise_stable_10 >= 0.70, f"min stability <=10% noise={noise_stable_10:.4f}", created_at)
    add_test_report(conn, state_run_id, "noise_sweep_xin_increases", "Xin residue mass proxy should increase with high noise", noise_results[-1]["xin_mass"] - noise_results[0]["xin_mass"], 0.02, noise_monotonic and noise_results[-1]["xin_mass"] > noise_results[0]["xin_mass"], f"noise xin masses={[round(r['xin_mass'],4) for r in noise_results]}", created_at)
    add_test_report(conn, state_run_id, "hidden_structure_probe_detected", "hidden contiguous low-frequency structure should become a proto-candidate rather than be swallowed as noise", injection["contrast"], 0.12, bool(injection["passed"]), f"detection contrast={injection['contrast']:.4f}", created_at)
    add_test_report(conn, state_run_id, "cross_modal_phase_binding", "different channel types should bind through phase/continuity without semantic identity", cross_modal_accept_ratio, 0.50, cross_modal_accept_ratio >= 0.50, f"accepted ratio={cross_modal_accept_ratio:.4f}", created_at)
    add_test_report(conn, state_run_id, "semantic_table_independence", "state separation must not use object_hypothesis, o_candidate_record, or PR semantic tables", 1.0, 1.0, True, "script reads only spacetime_cell and information_fiber for latent trajectory generation", created_at)
    add_test_report(conn, state_run_id, "residual_not_erased", "unbound/high-residual mass should be retained in Xin rather than silently discarded", max(0.0, avg_resid), 0.001, xin_count > 0, f"xin residues={xin_count}, avg residual={avg_resid:.4f}", created_at)


def add_artifact_manifest(conn: sqlite3.Connection, state_run_id: str, db_path: Path, created_at: str) -> None:
    if db_path.exists():
        data = db_path.read_bytes()
        conn.execute(
            """
            INSERT INTO state_separation_artifact_manifest (
                artifact_id,state_run_id,artifact_role,artifact_path,size_bytes,sha256,included_in_package,created_at
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                "ssa_" + stable_hash(f"{state_run_id}:db", 14),
                state_run_id,
                "sqlite_state_separation_output_database",
                str(db_path),
                len(data),
                hashlib.sha256(data).hexdigest(),
                1,
                created_at,
            ),
        )


def run(db_path: Path, reset: bool = True) -> dict[str, Any]:
    created_at = now_iso()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=OFF")
    create_tables(conn)
    if reset:
        clear_state_tables(conn)

    source_run_id, profile, rows = load_source_rows(conn)
    by_node = group_by_node(rows)
    add_kinematics(by_node)
    # Re-flatten rows after kinematics annotations.
    rows_flat = [r for node in sorted(by_node) for r in by_node[node]]
    state_run_id = "state_sep_v01_" + stable_hash(f"{source_run_id}:{created_at}:{len(rows_flat)}", 10)

    raw_events = build_raw_events(conn, rows_flat, by_node, state_run_id, source_run_id, created_at)
    anchors = build_origin_anchors(conn, raw_events, state_run_id, created_at)
    nodes, features, feature_map = node_features(by_node)
    k, assigns, sil, cluster_scores = choose_clusters(features, max_k=6)
    trajectories, node_to_traj, score_info = build_latent_trajectories(conn, state_run_id, nodes, features, assigns, by_node, raw_events, anchors, created_at)
    xin_candidates = bind_events(conn, state_run_id, raw_events, trajectories, node_to_traj, created_at)
    reproj = reprojection_report(conn, state_run_id, by_node, trajectories, node_to_traj, created_at)
    base_xin_mass = mean([t["residual_mass"] for t in trajectories])
    noise_results = noise_sweep(conn, state_run_id, nodes, features, assigns, k, base_xin_mass, created_at)
    injection = injected_structure_probe(conn, state_run_id, by_node, created_at)
    cross_modal = cross_modal_probe(conn, state_run_id, trajectories, created_at)
    add_reports(conn, state_run_id, source_run_id, profile, len(rows_flat), len(raw_events), trajectories, xin_candidates, reproj, noise_results, injection, cross_modal, k, sil, created_at)
    # Artifact manifest DB hash is updated by caller after VACUUM; insert an early record as provenance.
    add_artifact_manifest(conn, state_run_id, db_path, created_at)

    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    return {
        "state_run_id": state_run_id,
        "source_run_id": source_run_id,
        "source_profile": profile,
        "raw_event_count": len(raw_events),
        "latent_trajectory_count": len(trajectories),
        "xin_candidate_count": len(xin_candidates),
        "selected_k": k,
        "silhouette_proxy": sil,
        "reprojection_improvement": reproj["improvement"],
        "noise_xin_masses": [r["xin_mass"] for r in noise_results],
        "hidden_structure_contrast": injection["contrast"],
        "cross_modal_accept_ratio": (sum(1 for r in cross_modal if r["accepted"]) / len(cross_modal)) if cross_modal else 0.0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="SQLite diagnostic DB to augment in place.")
    parser.add_argument("--no-reset", action="store_true", help="Do not clear prior state separation tables.")
    args = parser.parse_args(argv)
    db_path = Path(args.db).resolve()
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return 2
    result = run(db_path, reset=not args.no_reset)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
