#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Morphosphere v0.6: Active-Inference / System-Identification External Lab.

This script is intentionally dependency-free and writes only v0.6 external-lab
diagnostic tables. It does not update source facts, P/R/Xi mainline tables, or
device/matrix facts. Candidate parameters are emitted as Decision Notes only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

SCHEMA_VERSION = "active_inference_system_identification_external_lab_v0.6"
RUN_ID = "ailab_v06_" + hashlib.sha256(SCHEMA_VERSION.encode()).hexdigest()[:12]
SOURCE_FACT_TABLES = [
    "spacetime_cell",
    "information_fiber",
    "raw_event_stream",
    "cell_spatial_coordinate_snapshot",
    "information_relative_coordinate_snapshot",
    "system_clock_entry",
    "p_predictive_support_v022",
    "r_counterstructure_v022",
    "xi_boundary_guard_v022",
    "device_pr_evidence_v05",
    "mechanotransduction_event_v04",
]
V06_TABLES = [
    "external_lab_run_manifest_v06",
    "source_fact_digest_v06",
    "system_id_feature_matrix_v06",
    "system_id_parameter_profile_v06",
    "system_id_iteration_trace_v06",
    "active_inference_free_energy_trace_v06",
    "parameter_sensitivity_report_v06",
    "decision_note_v06",
    "adoption_guard_v06",
    "external_lab_acceptance_report_v06",
    "external_lab_artifact_manifest_v06",
]

def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()

def sigmoid(x: float) -> float:
    if x >= 35:
        return 1.0
    if x <= -35:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

def stable_id(prefix: str, *parts: object) -> str:
    h = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()[:18]
    return f"{prefix}_{h}"

def table_exists(cur: sqlite3.Cursor, name: str) -> bool:
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

def table_count(cur: sqlite3.Cursor, name: str) -> int:
    if not table_exists(cur, name):
        return 0
    cur.execute(f"SELECT COUNT(*) FROM {name}")
    return int(cur.fetchone()[0])

def digest_table(cur: sqlite3.Cursor, name: str, limit: int = 20000) -> str:
    if not table_exists(cur, name):
        return "MISSING"
    cur.execute(f"PRAGMA table_info({name})")
    cols = [r[1] for r in cur.fetchall()]
    if not cols:
        return "EMPTY_SCHEMA"
    order_cols = ", ".join(cols)
    # Deterministic row serialization. LIMIT is above current source table sizes.
    cur.execute(f"SELECT {order_cols} FROM {name} ORDER BY {', '.join(cols[:min(3, len(cols))])} LIMIT {int(limit)}")
    h = hashlib.sha256()
    h.update(name.encode("utf-8"))
    h.update("|".join(cols).encode("utf-8"))
    for row in cur.fetchall():
        h.update(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()

def create_schema(cur: sqlite3.Cursor) -> None:
    for t in V06_TABLES:
        cur.execute(f"DROP TABLE IF EXISTS {t}")
    cur.execute("""
    CREATE TABLE external_lab_run_manifest_v06 (
      run_id TEXT PRIMARY KEY,
      schema_version TEXT NOT NULL,
      source_db_path TEXT NOT NULL,
      source_db_sha256 TEXT NOT NULL,
      execution_mode TEXT NOT NULL,
      lab_role TEXT NOT NULL,
      source_fact_rewrite_allowed INTEGER NOT NULL,
      mainline_adoption_allowed INTEGER NOT NULL,
      optimizer_kind TEXT NOT NULL,
      feature_count INTEGER NOT NULL,
      sample_count INTEGER NOT NULL,
      train_count INTEGER NOT NULL,
      holdout_count INTEGER NOT NULL,
      baseline_train_loss REAL NOT NULL,
      fitted_train_loss REAL NOT NULL,
      baseline_holdout_loss REAL NOT NULL,
      fitted_holdout_loss REAL NOT NULL,
      best_profile_id TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE source_fact_digest_v06 (
      digest_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      table_name TEXT NOT NULL,
      row_count_before INTEGER NOT NULL,
      row_count_after INTEGER NOT NULL,
      digest_before TEXT NOT NULL,
      digest_after TEXT NOT NULL,
      status TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE system_id_feature_matrix_v06 (
      feature_row_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      split TEXT NOT NULL,
      source_p_support_id TEXT NOT NULL,
      source_o_bridge_id TEXT NOT NULL,
      trajectory_id TEXT NOT NULL,
      clock_n INTEGER NOT NULL,
      target_support_score REAL NOT NULL,
      target_support_status TEXT NOT NULL,
      prediction_error REAL NOT NULL,
      accuracy_inverse_error REAL NOT NULL,
      continuity_score REAL NOT NULL,
      conservation_score REAL NOT NULL,
      phase_coherence_score REAL NOT NULL,
      memory_coupling REAL NOT NULL,
      xin_pressure REAL NOT NULL,
      r_counter_score REAL NOT NULL,
      device_evidence_score REAL NOT NULL,
      memory_consistency_score REAL NOT NULL,
      phase_gate_score REAL NOT NULL,
      matrix_projection_confidence REAL NOT NULL,
      matrix_projection_error_norm REAL NOT NULL,
      met_gate_probability REAL NOT NULL,
      device_energy_dissipation_norm REAL NOT NULL,
      feature_vector_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE system_id_parameter_profile_v06 (
      profile_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      profile_role TEXT NOT NULL,
      parameter_json TEXT NOT NULL,
      train_loss REAL NOT NULL,
      holdout_loss REAL NOT NULL,
      regularization_loss REAL NOT NULL,
      free_energy_proxy REAL NOT NULL,
      source TEXT NOT NULL,
      adoption_status TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE system_id_iteration_trace_v06 (
      trace_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      iteration_n INTEGER NOT NULL,
      train_loss REAL NOT NULL,
      holdout_loss REAL NOT NULL,
      regularization_loss REAL NOT NULL,
      gradient_norm REAL NOT NULL,
      parameter_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE active_inference_free_energy_trace_v06 (
      free_energy_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      feature_row_id TEXT NOT NULL,
      profile_id TEXT NOT NULL,
      prediction_component REAL NOT NULL,
      complexity_component REAL NOT NULL,
      xi_component REAL NOT NULL,
      r_counter_component REAL NOT NULL,
      entropy_component REAL NOT NULL,
      device_noise_component REAL NOT NULL,
      free_energy_proxy REAL NOT NULL,
      interpretation TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE parameter_sensitivity_report_v06 (
      sensitivity_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      parameter_name TEXT NOT NULL,
      fitted_value REAL NOT NULL,
      perturbation_fraction REAL NOT NULL,
      loss_minus REAL NOT NULL,
      loss_plus REAL NOT NULL,
      local_sensitivity REAL NOT NULL,
      interpretation TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE decision_note_v06 (
      decision_note_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      best_profile_id TEXT NOT NULL,
      decision_type TEXT NOT NULL,
      recommendation TEXT NOT NULL,
      rationale_json TEXT NOT NULL,
      may_update_mainline INTEGER NOT NULL,
      requires_human_review INTEGER NOT NULL,
      required_next_validation TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE adoption_guard_v06 (
      guard_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      guard_name TEXT NOT NULL,
      assertion TEXT NOT NULL,
      status TEXT NOT NULL,
      enforcement_scope TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE external_lab_acceptance_report_v06 (
      acceptance_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      test_name TEXT NOT NULL,
      status TEXT NOT NULL,
      observed TEXT NOT NULL,
      expected TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE external_lab_artifact_manifest_v06 (
      artifact_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      artifact_path TEXT NOT NULL,
      artifact_role TEXT NOT NULL,
      sha256 TEXT NOT NULL,
      note TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)

def read_scalar(cur: sqlite3.Cursor, sql: str, params: Sequence[object] = (), default: float = 0.0) -> float:
    try:
        cur.execute(sql, params)
        row = cur.fetchone()
        if row is None or row[0] is None:
            return default
        return float(row[0])
    except Exception:
        return default

def load_feature_rows(cur: sqlite3.Cursor) -> Tuple[List[str], List[Dict[str, object]]]:
    if not table_exists(cur, "p_predictive_support_v022"):
        raise RuntimeError("p_predictive_support_v022 is required for v0.6 external lab.")
    # Global normalizers.
    avg_device_evidence_by_traj_clock: Dict[Tuple[str, int], Tuple[float, float, float]] = {}
    if table_exists(cur, "device_pr_evidence_v05"):
        cur.execute("""
            SELECT trajectory_id, clock_n,
                   AVG(device_evidence_score), AVG(memory_consistency_score), AVG(phase_gate_score)
            FROM device_pr_evidence_v05 GROUP BY trajectory_id, clock_n
        """)
        for traj, clock, dev, mem, phase in cur.fetchall():
            avg_device_evidence_by_traj_clock[(traj, int(clock))] = (
                float(dev or 0.5), float(mem or 0.5), float(phase or 0.5)
            )
    proj_by_clock: Dict[int, Tuple[float, float]] = {}
    if table_exists(cur, "substrate_to_raw_event_projection_v04"):
        cur.execute("""
            SELECT clock_n, AVG(projection_confidence), AVG(ABS(projection_error))
            FROM substrate_to_raw_event_projection_v04 GROUP BY clock_n
        """)
        err_vals = []
        tmp = []
        for clock, conf, err in cur.fetchall():
            err = float(err or 0.0)
            err_vals.append(err)
            tmp.append((int(clock), float(conf or 0.5), err))
        max_err = max(err_vals) if err_vals else 1.0
        for clock, conf, err in tmp:
            proj_by_clock[clock] = (clamp(conf), clamp(err / max(max_err, 1e-9)))
    met_by_clock: Dict[int, float] = {}
    if table_exists(cur, "mechanotransduction_event_v04"):
        cur.execute("SELECT clock_n, AVG(met_gate_probability) FROM mechanotransduction_event_v04 GROUP BY clock_n")
        for clock, val in cur.fetchall():
            met_by_clock[int(clock)] = clamp(float(val or 0.0))
    energy_by_clock: Dict[int, float] = {}
    if table_exists(cur, "device_edge_tick_state_v05"):
        cur.execute("SELECT clock_n, AVG(energy_dissipation_proxy) FROM device_edge_tick_state_v05 GROUP BY clock_n")
        vals = [(int(clock), float(v or 0.0)) for clock, v in cur.fetchall()]
        maxv = max([v for _, v in vals] or [1.0])
        for clock, v in vals:
            energy_by_clock[clock] = clamp(v / max(maxv, 1e-9))
    r_by_traj_clock: Dict[Tuple[str, int], float] = {}
    if table_exists(cur, "r_counterstructure_v022"):
        cur.execute("SELECT trajectory_id, clock_n, AVG(counter_score) FROM r_counterstructure_v022 GROUP BY trajectory_id, clock_n")
        for traj, clock, score in cur.fetchall():
            r_by_traj_clock[(traj, int(clock))] = clamp(float(score or 0.0))
    # Use p support rows as current gold diagnostic observations.
    cur.execute("""
        SELECT p_support_id, o_bridge_id, trajectory_id, clock_n,
               prediction_error, continuity_score, conservation_score,
               phase_coherence_score, memory_coupling, xin_mass_input,
               support_score, support_status
        FROM p_predictive_support_v022
        ORDER BY clock_n, trajectory_id
    """)
    rows = []
    for idx, row in enumerate(cur.fetchall()):
        (pid, obid, traj, clock, pred_err, cont, cons, phase, memory, xin, support, status) = row
        clock = int(clock)
        pred_err = float(pred_err or 0.0)
        cont = clamp(float(cont or 0.0))
        cons = clamp(float(cons or 0.0))
        phase = clamp(float(phase or 0.0))
        memory = clamp(float(memory or 0.0))
        xin = clamp(float(xin or 0.0))
        support = clamp(float(support or 0.0))
        dev, mem_cons, phase_gate = avg_device_evidence_by_traj_clock.get((traj, clock), (0.5, 0.5, phase))
        proj_conf, proj_err = proj_by_clock.get(clock, (0.5, 0.5))
        met_gate = met_by_clock.get(clock, 0.5)
        energy = energy_by_clock.get(clock, 0.3)
        r_score = r_by_traj_clock.get((traj, clock), 0.0)
        # Deterministic split: hold out every fifth row.
        split = "holdout" if idx % 5 == 0 else "train"
        feature_values = {
            "bias": 1.0,
            "accuracy_inverse_error": clamp(1.0 - pred_err),
            "continuity_score": cont,
            "conservation_score": cons,
            "phase_coherence_score": phase,
            "memory_coupling": memory,
            "device_evidence_score": clamp(dev),
            "memory_consistency_score": clamp(mem_cons),
            "phase_gate_score": clamp(phase_gate),
            "matrix_projection_confidence": clamp(proj_conf),
            "met_gate_probability": clamp(met_gate),
            "r_counter_score_neg": -clamp(r_score),
            "xin_pressure_neg": -xin,
            "matrix_projection_error_neg": -clamp(proj_err),
            "device_energy_dissipation_neg": -clamp(energy),
        }
        rows.append({
            "feature_row_id": stable_id("featv06", pid, traj, clock),
            "source_p_support_id": pid,
            "source_o_bridge_id": obid,
            "trajectory_id": traj,
            "clock_n": clock,
            "target_support_score": support,
            "target_support_status": status,
            "prediction_error": pred_err,
            "accuracy_inverse_error": feature_values["accuracy_inverse_error"],
            "continuity_score": cont,
            "conservation_score": cons,
            "phase_coherence_score": phase,
            "memory_coupling": memory,
            "xin_pressure": xin,
            "r_counter_score": clamp(r_score),
            "device_evidence_score": clamp(dev),
            "memory_consistency_score": clamp(mem_cons),
            "phase_gate_score": clamp(phase_gate),
            "matrix_projection_confidence": clamp(proj_conf),
            "matrix_projection_error_norm": clamp(proj_err),
            "met_gate_probability": clamp(met_gate),
            "device_energy_dissipation_norm": clamp(energy),
            "split": split,
            "feature_values": feature_values,
        })
    feature_names = list(rows[0]["feature_values"].keys()) if rows else []
    return feature_names, rows

def predict(weights: Sequence[float], xs: Sequence[float]) -> float:
    return sigmoid(sum(w * x for w, x in zip(weights, xs)))

def loss_for(weights: Sequence[float], xys: Sequence[Tuple[List[float], float]], l2: float = 0.002) -> float:
    if not xys:
        return 0.0
    mse = sum((predict(weights, x) - y) ** 2 for x, y in xys) / len(xys)
    reg = l2 * sum(w * w for w in weights[1:]) / max(1, len(weights) - 1)
    return mse + reg

def optimize(feature_names: List[str], rows: List[Dict[str, object]]) -> Tuple[List[float], List[Dict[str, object]], Dict[str, float]]:
    train = []
    hold = []
    for r in rows:
        x = [float(r["feature_values"][n]) for n in feature_names]  # type: ignore[index]
        y = float(r["target_support_score"])
        (hold if r["split"] == "holdout" else train).append((x, y))
    # Baseline is the explicit "phenomenological hack" proxy: strong positive support terms,
    # negative R/Xi/error/energy terms. It is not adopted here; only used as a comparison.
    baseline = []
    base_map = {
        "bias": -0.50,
        "accuracy_inverse_error": 0.65,
        "continuity_score": 1.50,
        "conservation_score": 0.95,
        "phase_coherence_score": 1.20,
        "memory_coupling": 0.55,
        "device_evidence_score": 0.35,
        "memory_consistency_score": 0.25,
        "phase_gate_score": 0.25,
        "matrix_projection_confidence": 0.30,
        "met_gate_probability": 0.25,
        "r_counter_score_neg": 0.70,
        "xin_pressure_neg": 0.80,
        "matrix_projection_error_neg": 0.55,
        "device_energy_dissipation_neg": 0.30,
    }
    for n in feature_names:
        baseline.append(base_map.get(n, 0.0))
    weights = baseline[:]
    traces = []
    lr0 = 0.20
    l2 = 0.002
    for it in range(550):
        grads = [0.0] * len(weights)
        if train:
            for x, y in train:
                p = predict(weights, x)
                # MSE + sigmoid derivative gradient.
                coeff = 2.0 * (p - y) * p * (1 - p) / len(train)
                for j, val in enumerate(x):
                    grads[j] += coeff * val
            for j in range(1, len(weights)):
                grads[j] += 2 * l2 * weights[j] / max(1, len(weights) - 1)
        gnorm = math.sqrt(sum(g * g for g in grads))
        lr = lr0 / (1.0 + it / 160.0)
        for j in range(len(weights)):
            weights[j] -= lr * grads[j]
            # Keep proxies interpretable; do not allow giant optimizer hacks.
            weights[j] = max(-4.0, min(4.0, weights[j]))
        if it % 25 == 0 or it == 549:
            traces.append({
                "iteration_n": it,
                "train_loss": loss_for(weights, train, l2),
                "holdout_loss": loss_for(weights, hold, l2),
                "regularization_loss": l2 * sum(w * w for w in weights[1:]) / max(1, len(weights) - 1),
                "gradient_norm": gnorm,
                "weights": dict(zip(feature_names, weights)),
            })
    metrics = {
        "baseline_train_loss": loss_for(baseline, train, l2),
        "baseline_holdout_loss": loss_for(baseline, hold, l2),
        "fitted_train_loss": loss_for(weights, train, l2),
        "fitted_holdout_loss": loss_for(weights, hold, l2),
    }
    return weights, traces, metrics | {"baseline_weights": dict(zip(feature_names, baseline))}

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

def run(db_path: Path, report_dir: Path) -> Dict[str, object]:
    source_db_sha = file_sha256(db_path)
    created = now()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=OFF")
    cur = conn.cursor()
    # Capture source digests before v0.6 writes.
    before = {t: (table_count(cur, t), digest_table(cur, t)) for t in SOURCE_FACT_TABLES}
    create_schema(cur)
    feature_names, rows = load_feature_rows(cur)
    weights, traces, metrics = optimize(feature_names, rows)
    train_count = sum(1 for r in rows if r["split"] == "train")
    hold_count = sum(1 for r in rows if r["split"] == "holdout")
    best_profile_id = stable_id("profilev06", RUN_ID, "fitted", metrics["fitted_train_loss"], metrics["fitted_holdout_loss"])
    baseline_profile_id = stable_id("profilev06", RUN_ID, "baseline")
    # Insert feature rows.
    for r in rows:
        fv = {n: float(r["feature_values"][n]) for n in feature_names}  # type: ignore[index]
        cur.execute("""
          INSERT INTO system_id_feature_matrix_v06 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r["feature_row_id"], RUN_ID, r["split"], r["source_p_support_id"], r["source_o_bridge_id"],
            r["trajectory_id"], int(r["clock_n"]), float(r["target_support_score"]),
            r["target_support_status"], float(r["prediction_error"]), float(r["accuracy_inverse_error"]),
            float(r["continuity_score"]), float(r["conservation_score"]), float(r["phase_coherence_score"]),
            float(r["memory_coupling"]), float(r["xin_pressure"]), float(r["r_counter_score"]),
            float(r["device_evidence_score"]), float(r["memory_consistency_score"]), float(r["phase_gate_score"]),
            float(r["matrix_projection_confidence"]), float(r["matrix_projection_error_norm"]),
            float(r["met_gate_probability"]), float(r["device_energy_dissipation_norm"]),
            json.dumps(fv, sort_keys=True), created
        ))
    # Profiles.
    def free_energy_summary(profile_weights: Dict[str, float]) -> float:
        if not rows:
            return 0.0
        xys = [([float(r["feature_values"][n]) for n in feature_names], float(r["target_support_score"])) for r in rows]  # type: ignore[index]
        return loss_for([profile_weights[n] for n in feature_names], xys, 0.002)
    baseline_weights = metrics["baseline_weights"]  # type: ignore[assignment]
    fitted_weights = dict(zip(feature_names, weights))
    cur.execute("INSERT INTO system_id_parameter_profile_v06 VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
        baseline_profile_id, RUN_ID, "legacy_like_comparison", json.dumps(baseline_weights, sort_keys=True),
        metrics["baseline_train_loss"], metrics["baseline_holdout_loss"],
        0.002 * sum(float(v) * float(v) for k, v in baseline_weights.items() if k != "bias") / max(1, len(feature_names)-1),
        free_energy_summary(baseline_weights), "handcrafted comparison; not adopted", "comparison_only", created
    ))
    cur.execute("INSERT INTO system_id_parameter_profile_v06 VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
        best_profile_id, RUN_ID, "fitted_candidate", json.dumps(fitted_weights, sort_keys=True),
        metrics["fitted_train_loss"], metrics["fitted_holdout_loss"],
        0.002 * sum(w * w for w in weights[1:]) / max(1, len(weights)-1),
        free_energy_summary(fitted_weights), "external-lab pure-python gradient descent over diagnostic P/R observations", "candidate_not_adopted", created
    ))
    # Iteration traces.
    for tr in traces:
        cur.execute("INSERT INTO system_id_iteration_trace_v06 VALUES (?,?,?,?,?,?,?,?,?)", (
            stable_id("iterv06", RUN_ID, tr["iteration_n"]), RUN_ID, int(tr["iteration_n"]),
            float(tr["train_loss"]), float(tr["holdout_loss"]), float(tr["regularization_loss"]),
            float(tr["gradient_norm"]), json.dumps(tr["weights"], sort_keys=True), created
        ))
    # Free energy row-level traces using fitted weights.
    max_entropy = 1.0
    for r in rows:
        fv = {n: float(r["feature_values"][n]) for n in feature_names}  # type: ignore[index]
        x = [fv[n] for n in feature_names]
        pred = predict(weights, x)
        target = float(r["target_support_score"])
        pred_component = (pred - target) ** 2
        complexity_component = 0.01 * sum(abs(weights[i]) * abs(x[i]) for i in range(1, len(weights))) / max(1, len(weights)-1)
        xi_component = float(r["xin_pressure"]) * max(0.01, abs(fitted_weights.get("xin_pressure_neg", 0.0)))
        r_component = float(r["r_counter_score"]) * max(0.01, abs(fitted_weights.get("r_counter_score_neg", 0.0)))
        entropy_component = abs(float(r["phase_coherence_score"]) - float(r["continuity_score"])) * 0.10
        noise_component = float(r["device_energy_dissipation_norm"]) * 0.03
        fe = pred_component + complexity_component + xi_component + r_component + entropy_component + noise_component
        cur.execute("INSERT INTO active_inference_free_energy_trace_v06 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            stable_id("fev06", RUN_ID, r["feature_row_id"]),
            RUN_ID, r["feature_row_id"], best_profile_id,
            pred_component, complexity_component, xi_component, r_component,
            entropy_component, noise_component, fe,
            "diagnostic expected-free-energy proxy: prediction error + complexity + Xi/R/noise terms; not a scientific FEP proof",
            created
        ))
    # Sensitivity.
    train_rows = [r for r in rows if r["split"] == "train"]
    xys_train = [([float(r["feature_values"][n]) for n in feature_names], float(r["target_support_score"])) for r in train_rows]  # type: ignore[index]
    for j, pname in enumerate(feature_names):
        if pname == "bias":
            frac = 0.10
        else:
            frac = 0.10
        wminus = weights[:]; wplus = weights[:]
        delta = max(0.025, abs(weights[j]) * frac)
        wminus[j] -= delta; wplus[j] += delta
        lm = loss_for(wminus, xys_train, 0.002)
        lp = loss_for(wplus, xys_train, 0.002)
        sens = abs(lp - lm) / (2 * delta)
        cur.execute("INSERT INTO parameter_sensitivity_report_v06 VALUES (?,?,?,?,?,?,?,?,?,?)", (
            stable_id("sensv06", RUN_ID, pname), RUN_ID, pname, float(weights[j]), frac, lm, lp, sens,
            "local loss response; use for review before any mainline adoption", created
        ))
    # Decision note.
    rationale = {
        "baseline_train_loss": metrics["baseline_train_loss"],
        "fitted_train_loss": metrics["fitted_train_loss"],
        "baseline_holdout_loss": metrics["baseline_holdout_loss"],
        "fitted_holdout_loss": metrics["fitted_holdout_loss"],
        "improvement_train": metrics["baseline_train_loss"] - metrics["fitted_train_loss"],
        "improvement_holdout": metrics["baseline_holdout_loss"] - metrics["fitted_holdout_loss"],
        "feature_count": len(feature_names),
        "sample_count": len(rows),
        "p_r_xi_boundary": "P/R mainline remains authoritative; Xi is post-P/R residue; v0.6 cannot adopt itself.",
    }
    cur.execute("INSERT INTO decision_note_v06 VALUES (?,?,?,?,?,?,?,?,?,?)", (
        stable_id("dnotev06", RUN_ID, best_profile_id), RUN_ID, best_profile_id,
        "candidate_parameter_profile", "HOLD_FOR_HUMAN_REVIEW",
        json.dumps(rationale, sort_keys=True), 0, 1,
        "Run full replay harness and real physical-data driver before adoption; never write weights directly from external lab.",
        created
    ))
    guards = [
        ("read_only_external_lab", "External lab may read source facts and append v0.6 diagnostic tables only."),
        ("no_mainline_mutation", "External lab must not update P/R, Xi, transport, raw_event, matrix, or device source rows."),
        ("candidate_not_adopted", "Fitted parameters are candidates; mainline config remains unchanged."),
        ("p_r_before_xi", "P/R remains the decomposition layer before Xi; lab weights cannot make Xi replace P/R."),
        ("no_semantic_labels", "Fitter uses diagnostic numeric features only; no semantic labels are introduced."),
        ("human_review_required", "A Decision Note is required before any candidate adoption."),
    ]
    for name, assertion in guards:
        cur.execute("INSERT INTO adoption_guard_v06 VALUES (?,?,?,?,?,?,?)", (
            stable_id("guardv06", RUN_ID, name), RUN_ID, name, assertion, "active", "external_lab_v06", created
        ))
    # Capture source digests after v0.6 writes.
    after = {t: (table_count(cur, t), digest_table(cur, t)) for t in SOURCE_FACT_TABLES}
    for t in SOURCE_FACT_TABLES:
        status = "PASS" if before[t] == after[t] else "FAIL"
        cur.execute("INSERT INTO source_fact_digest_v06 VALUES (?,?,?,?,?,?,?,?,?)", (
            stable_id("digestv06", RUN_ID, t), RUN_ID, t, before[t][0], after[t][0], before[t][1], after[t][1], status, created
        ))
    # Manifest.
    cur.execute("INSERT INTO external_lab_run_manifest_v06 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
        RUN_ID, SCHEMA_VERSION, str(db_path), source_db_sha,
        "external_read_only_parameter_identification_append_only",
        "diagnostic_external_lab_not_mainline", 0, 0,
        "pure_python_gradient_descent_logistic_free_energy_proxy",
        len(feature_names), len(rows), train_count, hold_count,
        metrics["baseline_train_loss"], metrics["fitted_train_loss"],
        metrics["baseline_holdout_loss"], metrics["fitted_holdout_loss"],
        best_profile_id, created
    ))
    conn.commit()
    # Reports / artifacts.
    summary = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "sample_count": len(rows),
        "feature_count": len(feature_names),
        "train_count": train_count,
        "holdout_count": hold_count,
        "best_profile_id": best_profile_id,
        "baseline_train_loss": metrics["baseline_train_loss"],
        "fitted_train_loss": metrics["fitted_train_loss"],
        "baseline_holdout_loss": metrics["baseline_holdout_loss"],
        "fitted_holdout_loss": metrics["fitted_holdout_loss"],
        "train_improvement": metrics["baseline_train_loss"] - metrics["fitted_train_loss"],
        "holdout_improvement": metrics["baseline_holdout_loss"] - metrics["fitted_holdout_loss"],
        "adoption_status": "candidate_not_adopted",
        "source_fact_rewrite_allowed": False,
        "mainline_adoption_allowed": False,
        "source_digest_status": all(before[t] == after[t] for t in SOURCE_FACT_TABLES),
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = report_dir / "active_inference_lab_v06_summary.json"
    write_json(summary_path, summary)
    md_path = report_dir / "ACTIVE_INFERENCE_LAB_V06_REPORT.md"
    md_path.write_text(
        "# Active-Inference / System-Identification External Lab v0.6\n\n"
        "This report is an external diagnostic Decision Note, not a mainline adoption.\n\n"
        f"- run_id: `{RUN_ID}`\n"
        f"- samples: `{len(rows)}`\n"
        f"- features: `{len(feature_names)}`\n"
        f"- baseline_train_loss: `{metrics['baseline_train_loss']:.8f}`\n"
        f"- fitted_train_loss: `{metrics['fitted_train_loss']:.8f}`\n"
        f"- baseline_holdout_loss: `{metrics['baseline_holdout_loss']:.8f}`\n"
        f"- fitted_holdout_loss: `{metrics['fitted_holdout_loss']:.8f}`\n"
        f"- source facts unchanged: `{summary['source_digest_status']}`\n\n"
        "Boundary: the fitted weights are `candidate_not_adopted`. They cannot rewrite source facts, "
        "cannot bypass P/R, and cannot make Xi/Xin replace P/R.\n",
        encoding="utf-8",
    )
    for art_path, role in [(summary_path, "summary_json"), (md_path, "human_report")]:
        cur.execute("INSERT INTO external_lab_artifact_manifest_v06 VALUES (?,?,?,?,?,?,?)", (
            stable_id("artv06", RUN_ID, art_path.name), RUN_ID, str(art_path),
            role, file_sha256(art_path), "generated by v0.6 external lab", created
        ))
    conn.commit()
    # Store acceptance inside DB.
    insert_acceptance(cur, RUN_ID, summary, feature_names, rows, metrics, before, after, created)
    conn.commit()
    conn.close()
    return summary

def insert_acceptance(cur: sqlite3.Cursor, run_id: str, summary: Dict[str, object],
                      feature_names: List[str], rows: List[Dict[str, object]],
                      metrics: Dict[str, float], before: Dict[str, Tuple[int, str]],
                      after: Dict[str, Tuple[int, str]], created: str) -> None:
    tests: List[Tuple[str, bool, object, object]] = []
    for t in V06_TABLES:
        tests.append((f"table_exists_{t}", table_exists(cur, t), "exists", True))
    tests.extend([
        ("feature_rows_nonzero", len(rows) > 0, len(rows), ">0"),
        ("feature_count_minimum", len(feature_names) >= 10, len(feature_names), ">=10"),
        ("holdout_rows_present", summary["holdout_count"] > 0, summary["holdout_count"], ">0"),
        ("fitted_train_loss_below_baseline", metrics["fitted_train_loss"] < metrics["baseline_train_loss"], {
            "fitted": metrics["fitted_train_loss"], "baseline": metrics["baseline_train_loss"]}, "fitted < baseline"),
        ("fitted_holdout_loss_not_worse_than_baseline_by_large_margin", metrics["fitted_holdout_loss"] <= metrics["baseline_holdout_loss"] + 0.02, {
            "fitted": metrics["fitted_holdout_loss"], "baseline": metrics["baseline_holdout_loss"]}, "fitted <= baseline + 0.02"),
        ("source_fact_digests_unchanged", all(before[t] == after[t] for t in SOURCE_FACT_TABLES), "all source digests", "unchanged"),
        ("decision_note_not_adopted", read_scalar(cur, "SELECT COUNT(*) FROM decision_note_v06 WHERE may_update_mainline=0 AND requires_human_review=1") >= 1, "decision note", "candidate only"),
        ("adoption_guards_active", read_scalar(cur, "SELECT COUNT(*) FROM adoption_guard_v06 WHERE status='active'") >= 6, "guards", ">=6"),
        ("p_r_xi_boundary_guard_present", read_scalar(cur, "SELECT COUNT(*) FROM adoption_guard_v06 WHERE guard_name='p_r_before_xi' AND status='active'") == 1, "p_r_before_xi", "active"),
        ("profiles_include_baseline_and_fitted", read_scalar(cur, "SELECT COUNT(*) FROM system_id_parameter_profile_v06") >= 2, "profile_count", ">=2"),
        ("iteration_trace_recorded", read_scalar(cur, "SELECT COUNT(*) FROM system_id_iteration_trace_v06") >= 10, "iteration_count", ">=10"),
        ("free_energy_trace_recorded", read_scalar(cur, "SELECT COUNT(*) FROM active_inference_free_energy_trace_v06") == len(rows), "free_energy_rows", "feature_row_count"),
        ("sensitivity_report_recorded", read_scalar(cur, "SELECT COUNT(*) FROM parameter_sensitivity_report_v06") == len(feature_names), "sensitivity_rows", "feature_count"),
    ])
    for name, passed, obs, exp in tests:
        cur.execute("INSERT INTO external_lab_acceptance_report_v06 VALUES (?,?,?,?,?,?,?)", (
            stable_id("accv06", run_id, name), run_id, name, "PASS" if passed else "FAIL",
            json.dumps(obs, ensure_ascii=False, sort_keys=True, default=str),
            json.dumps(exp, ensure_ascii=False, sort_keys=True, default=str),
            created
        ))

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="SQLite database path")
    ap.add_argument("--report-dir", default=None, help="Report directory")
    args = ap.parse_args()
    db_path = Path(args.db).resolve()
    report_dir = Path(args.report_dir).resolve() if args.report_dir else db_path.parent.parent / "morphosphere_v2pp" / "reports"
    summary = run(db_path, report_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
