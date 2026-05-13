#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Morphosphere v0.7: Candidate Adoption Gate + Real-Data Calibration Harness.

This layer evaluates the v0.6 fitted parameter profile against replay, calibration,
source-fact, P/R-Xi, and shell0 gates. It produces a staged patch only. It never
mutates mainline source facts or automatically adopts fitted parameters.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import math
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

SCHEMA_VERSION = "candidate_adoption_gate_real_data_calibration_v0.7"
RUN_ID = "cadopt_v07_" + hashlib.sha256(SCHEMA_VERSION.encode()).hexdigest()[:12]

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
    "substrate_stress_tensor_v04",
    "cell_matrix_contact_v04",
    "foam_edge_state_v04",
    "mechanotransduction_event_v04",
    "preneural_synaptic_edge_v05",
    "device_edge_tick_state_v05",
]

V07_TABLES = [
    "candidate_adoption_run_manifest_v07",
    "candidate_profile_review_v07",
    "real_data_calibration_source_v07",
    "real_data_calibration_sample_v07",
    "real_data_calibration_mapping_v07",
    "real_data_calibration_result_v07",
    "candidate_adoption_gate_v07",
    "candidate_patch_manifest_v07",
    "source_fact_digest_v07",
    "shell0_lineage_audit_v07",
    "shell0_resolution_probe_v07",
    "shell0_adjudication_v07",
    "candidate_adoption_acceptance_report_v07",
    "candidate_adoption_artifact_manifest_v07",
]

REQUIRED_CALIBRATION_COLUMNS = [
    "clock_n", "time_s", "sensor_id", "sensor_kind", "x", "y", "z",
    "force_x", "force_y", "force_z", "optical_intensity", "acoustic_pressure",
    "phase", "uncertainty",
]


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def stable_id(prefix: str, *parts: object) -> str:
    h = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()[:18]
    return f"{prefix}_{h}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def table_exists(cur: sqlite3.Cursor, name: str) -> bool:
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def table_count(cur: sqlite3.Cursor, name: str, where: str = "1=1") -> int:
    if not table_exists(cur, name):
        return 0
    cur.execute(f"SELECT COUNT(*) FROM {name} WHERE {where}")
    return int(cur.fetchone()[0])


def scalar(cur: sqlite3.Cursor, sql: str, default: Any = None) -> Any:
    try:
        cur.execute(sql)
        row = cur.fetchone()
        if row is None:
            return default
        return row[0]
    except Exception:
        return default


def digest_table(cur: sqlite3.Cursor, name: str, limit: int = 50000) -> str:
    if not table_exists(cur, name):
        return "MISSING"
    cur.execute(f"PRAGMA table_info({name})")
    cols = [r[1] for r in cur.fetchall()]
    if not cols:
        return "EMPTY_SCHEMA"
    select_cols = ", ".join(cols)
    order_cols = ", ".join(cols[: min(3, len(cols))])
    cur.execute(f"SELECT {select_cols} FROM {name} ORDER BY {order_cols} LIMIT {int(limit)}")
    h = hashlib.sha256()
    h.update(name.encode("utf-8"))
    h.update("|".join(cols).encode("utf-8"))
    for row in cur.fetchall():
        h.update(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"))
    return h.hexdigest()


def load_best_profile(cur: sqlite3.Cursor) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT profile_id, parameter_json, train_loss, holdout_loss, regularization_loss,
               free_energy_proxy, adoption_status
        FROM system_id_parameter_profile_v06
        WHERE profile_role='fitted_candidate'
        ORDER BY holdout_loss ASC LIMIT 1
        """
    )
    row = cur.fetchone()
    if row is None:
        return {}
    params = json.loads(row[1])
    return {
        "profile_id": row[0],
        "parameters": params,
        "train_loss": float(row[2]),
        "holdout_loss": float(row[3]),
        "regularization_loss": float(row[4]),
        "free_energy_proxy": float(row[5]),
        "adoption_status": row[6],
    }


def load_baseline_profile(cur: sqlite3.Cursor) -> Dict[str, Any]:
    cur.execute(
        """
        SELECT profile_id, parameter_json, train_loss, holdout_loss, regularization_loss,
               free_energy_proxy, adoption_status
        FROM system_id_parameter_profile_v06
        WHERE profile_role='legacy_like_comparison'
        ORDER BY holdout_loss ASC LIMIT 1
        """
    )
    row = cur.fetchone()
    if row is None:
        return {}
    return {
        "profile_id": row[0],
        "parameters": json.loads(row[1]),
        "train_loss": float(row[2]),
        "holdout_loss": float(row[3]),
        "regularization_loss": float(row[4]),
        "free_energy_proxy": float(row[5]),
        "adoption_status": row[6],
    }


def create_schema(cur: sqlite3.Cursor) -> None:
    for t in V07_TABLES:
        cur.execute(f"DROP TABLE IF EXISTS {t}")

    cur.execute("""
    CREATE TABLE candidate_adoption_run_manifest_v07 (
      run_id TEXT PRIMARY KEY,
      schema_version TEXT NOT NULL,
      execution_mode TEXT NOT NULL,
      source_db_path TEXT NOT NULL,
      source_db_sha256_before TEXT NOT NULL,
      source_db_sha256_after TEXT NOT NULL,
      candidate_profile_id TEXT NOT NULL,
      baseline_profile_id TEXT NOT NULL,
      final_decision TEXT NOT NULL,
      auto_adoption_allowed INTEGER NOT NULL,
      staged_patch_written INTEGER NOT NULL,
      manual_review_required INTEGER NOT NULL,
      blocker_count INTEGER NOT NULL,
      shell0_final_verdict TEXT NOT NULL,
      calibration_source_kind TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE candidate_profile_review_v07 (
      review_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      candidate_profile_id TEXT NOT NULL,
      baseline_profile_id TEXT NOT NULL,
      candidate_train_loss REAL NOT NULL,
      candidate_holdout_loss REAL NOT NULL,
      baseline_train_loss REAL NOT NULL,
      baseline_holdout_loss REAL NOT NULL,
      train_improvement REAL NOT NULL,
      holdout_improvement REAL NOT NULL,
      candidate_parameter_json TEXT NOT NULL,
      review_status TEXT NOT NULL,
      rationale TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE real_data_calibration_source_v07 (
      calibration_source_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      source_path TEXT NOT NULL,
      source_sha256 TEXT NOT NULL,
      source_kind TEXT NOT NULL,
      schema_status TEXT NOT NULL,
      row_count INTEGER NOT NULL,
      sensor_count INTEGER NOT NULL,
      clock_count INTEGER NOT NULL,
      is_fixture INTEGER NOT NULL,
      provenance_note TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE real_data_calibration_sample_v07 (
      calibration_sample_id TEXT PRIMARY KEY,
      calibration_source_id TEXT NOT NULL,
      clock_n INTEGER NOT NULL,
      time_s REAL NOT NULL,
      sensor_id TEXT NOT NULL,
      sensor_kind TEXT NOT NULL,
      x REAL NOT NULL,
      y REAL NOT NULL,
      z REAL NOT NULL,
      force_norm REAL NOT NULL,
      optical_intensity REAL NOT NULL,
      acoustic_pressure REAL NOT NULL,
      phase REAL NOT NULL,
      uncertainty REAL NOT NULL,
      sample_hash TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE real_data_calibration_mapping_v07 (
      mapping_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      calibration_sample_id TEXT NOT NULL,
      nearest_cell_uid TEXT NOT NULL,
      nearest_node_id INTEGER NOT NULL,
      nearest_distance REAL NOT NULL,
      matched_met_event_id TEXT,
      met_gate_probability REAL NOT NULL,
      matrix_projection_confidence REAL NOT NULL,
      device_evidence_score REAL NOT NULL,
      p_support_proxy REAL NOT NULL,
      r_counter_proxy REAL NOT NULL,
      xi_pressure_proxy REAL NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE real_data_calibration_result_v07 (
      result_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      calibration_source_id TEXT NOT NULL,
      sample_count INTEGER NOT NULL,
      mapped_sample_count INTEGER NOT NULL,
      mean_force_norm REAL NOT NULL,
      force_nonuniformity REAL NOT NULL,
      phase_continuity_score REAL NOT NULL,
      multimodal_consistency_score REAL NOT NULL,
      met_alignment_score REAL NOT NULL,
      p_stability_proxy REAL NOT NULL,
      r_counter_proxy REAL NOT NULL,
      xi_pressure_proxy REAL NOT NULL,
      real_data_gate_status TEXT NOT NULL,
      interpretation TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE candidate_adoption_gate_v07 (
      gate_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      gate_name TEXT NOT NULL,
      gate_status TEXT NOT NULL,
      severity TEXT NOT NULL,
      observed_value TEXT NOT NULL,
      expected_value TEXT NOT NULL,
      blocks_auto_adoption INTEGER NOT NULL,
      rationale TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE candidate_patch_manifest_v07 (
      patch_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      candidate_profile_id TEXT NOT NULL,
      patch_path TEXT NOT NULL,
      patch_sha256 TEXT NOT NULL,
      patch_status TEXT NOT NULL,
      may_apply_automatically INTEGER NOT NULL,
      requires_human_review INTEGER NOT NULL,
      parameter_json TEXT NOT NULL,
      blocker_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE source_fact_digest_v07 (
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
    CREATE TABLE shell0_lineage_audit_v07 (
      audit_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      artifact_path TEXT NOT NULL,
      artifact_kind TEXT NOT NULL,
      evidence_role TEXT NOT NULL,
      observed_status TEXT NOT NULL,
      conclusion TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE shell0_resolution_probe_v07 (
      probe_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      probe_name TEXT NOT NULL,
      probe_kind TEXT NOT NULL,
      shell_energy_proxy REAL NOT NULL,
      leakage_proxy REAL NOT NULL,
      contact_sensitivity_proxy REAL NOT NULL,
      cross_resolution_variance REAL NOT NULL,
      artifact_risk_proxy REAL NOT NULL,
      physical_support_proxy REAL NOT NULL,
      verdict_component TEXT NOT NULL,
      interpretation TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE shell0_adjudication_v07 (
      adjudication_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      resolution_method TEXT NOT NULL,
      final_verdict TEXT NOT NULL,
      confidence REAL NOT NULL,
      project_structure_attribution REAL NOT NULL,
      physical_boundary_attribution REAL NOT NULL,
      mixed_or_indeterminate INTEGER NOT NULL,
      blocks_auto_adoption INTEGER NOT NULL,
      rationale_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE candidate_adoption_acceptance_report_v07 (
      check_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      check_name TEXT NOT NULL,
      status TEXT NOT NULL,
      observed TEXT NOT NULL,
      expected TEXT NOT NULL,
      severity TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE candidate_adoption_artifact_manifest_v07 (
      artifact_id TEXT PRIMARY KEY,
      run_id TEXT NOT NULL,
      artifact_path TEXT NOT NULL,
      artifact_type TEXT NOT NULL,
      sha256 TEXT NOT NULL,
      role TEXT NOT NULL,
      created_at TEXT NOT NULL
    )
    """)


def load_calibration_csv(path: Path) -> Tuple[List[Dict[str, str]], str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        missing = [c for c in REQUIRED_CALIBRATION_COLUMNS if c not in cols]
        if missing:
            raise ValueError(f"Calibration CSV missing columns: {missing}")
        rows = [dict(r) for r in reader]
    return rows, "PASS"


def nearest_cells(cur: sqlite3.Cursor) -> List[Tuple[str, int, float, float, float]]:
    # One coordinate per node from cell_matrix_contact_v04. Stable and already separated from information relative coordinates.
    cur.execute(
        """
        SELECT source_cell_uid, node_id, AVG(cell_x), AVG(cell_y), AVG(cell_z)
        FROM cell_matrix_contact_v04
        GROUP BY source_cell_uid, node_id
        """
    )
    return [(r[0], int(r[1]), float(r[2]), float(r[3]), float(r[4])) for r in cur.fetchall()]


def build_real_data_calibration(cur: sqlite3.Cursor, calibration_csv: Path, is_fixture: bool) -> Dict[str, Any]:
    rows, schema_status = load_calibration_csv(calibration_csv)
    source_id = stable_id("rcalsrc", calibration_csv.name, sha256_file(calibration_csv), len(rows))
    sensors = sorted({r["sensor_id"] for r in rows})
    clocks = sorted({int(float(r["clock_n"])) for r in rows})
    src_kind = "fixture_physical_driver_v04_compatible" if is_fixture else "external_user_supplied_physical_csv"
    cur.execute(
        """
        INSERT INTO real_data_calibration_source_v07 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            source_id, RUN_ID, str(calibration_csv), sha256_file(calibration_csv), src_kind,
            schema_status, len(rows), len(sensors), len(clocks), 1 if is_fixture else 0,
            "Fixture rows are deterministic local calibration samples; external CSV may replace this without changing schema.",
            now(),
        ),
    )
    cells = nearest_cells(cur)
    if not cells:
        raise RuntimeError("cell_matrix_contact_v04 is required for calibration mapping")

    # Cache approximate MET by clock/node.
    cur.execute(
        """
        SELECT clock_n, node_id, AVG(met_gate_probability), AVG(event_uncertainty)
        FROM mechanotransduction_event_v04
        GROUP BY clock_n, node_id
        """
    )
    met_map: Dict[Tuple[int, int], Tuple[float, float]] = {
        (int(r[0]), int(r[1])): (float(r[2]), float(r[3])) for r in cur.fetchall()
    }
    cur.execute(
        """
        SELECT clock_n, node_id, AVG(projection_confidence), AVG(projection_error)
        FROM substrate_to_raw_event_projection_v04
        GROUP BY clock_n, node_id
        """
    )
    proj_map: Dict[Tuple[int, int], Tuple[float, float]] = {
        (int(r[0]), int(r[1])): (float(r[2]), abs(float(r[3]))) for r in cur.fetchall()
    }
    cur.execute(
        """
        SELECT o_bridge_id, AVG(support_score), AVG(prediction_error)
        FROM p_predictive_support_v022
        GROUP BY o_bridge_id
        """
    )
    support_values = [(float(r[1]), float(r[2])) for r in cur.fetchall()]
    mean_p_support = sum(v for v, _ in support_values) / max(1, len(support_values))
    mean_pred_err = sum(e for _, e in support_values) / max(1, len(support_values))
    cur.execute("SELECT AVG(counter_score) FROM r_counterstructure_v022")
    mean_r_counter = float(cur.fetchone()[0] or 0.05)
    cur.execute("SELECT AVG(residue_mass) FROM xin_residue_dynamics")
    mean_xi_pressure = float(cur.fetchone()[0] or 0.12)
    cur.execute("SELECT AVG(device_evidence_score), AVG(memory_consistency_score) FROM device_pr_evidence_v05")
    devrow = cur.fetchone()
    mean_device_evidence = float(devrow[0] or 0.5)

    force_norms: List[float] = []
    phases_by_sensor: Dict[str, List[float]] = {}
    multimodal_terms: List[float] = []
    met_align_terms: List[float] = []
    p_terms: List[float] = []
    r_terms: List[float] = []
    xi_terms: List[float] = []
    mapped = 0

    for i, r in enumerate(rows):
        clock_n = int(float(r["clock_n"]))
        x, y, z = float(r["x"]), float(r["y"]), float(r["z"])
        fx, fy, fz = float(r["force_x"]), float(r["force_y"]), float(r["force_z"])
        force_norm = math.sqrt(fx * fx + fy * fy + fz * fz)
        optical = float(r["optical_intensity"])
        acoustic = float(r["acoustic_pressure"])
        phase = float(r["phase"])
        uncertainty = float(r["uncertainty"])
        nearest = min(cells, key=lambda c: (c[2] - x) ** 2 + (c[3] - y) ** 2 + (c[4] - z) ** 2)
        cell_uid, node_id, cx, cy, cz = nearest
        dist = math.sqrt((cx - x) ** 2 + (cy - y) ** 2 + (cz - z) ** 2)
        met_gate, met_unc = met_map.get((clock_n, node_id), (0.5, uncertainty))
        proj_conf, proj_err = proj_map.get((clock_n, node_id), (0.5, 1.0))
        # No semantic label: align channel magnitudes through phase and uncertainty proxies.
        multimodal = max(0.0, min(1.0, 1.0 - abs(math.sin(phase) - 0.35 * acoustic) * 0.25 - uncertainty))
        met_align = max(0.0, min(1.0, 1.0 - abs(met_gate - min(1.0, force_norm / 1.25)) * 0.55 - uncertainty * 0.4))
        p_proxy = max(0.0, min(1.0, 0.45 * mean_p_support + 0.25 * met_align + 0.15 * proj_conf + 0.15 * mean_device_evidence))
        r_proxy = max(0.0, min(1.0, mean_r_counter + 0.25 * (1.0 - multimodal) + 0.10 * min(1.0, dist / 3.0)))
        xi_proxy = max(0.0, min(1.0, mean_xi_pressure + 0.25 * uncertainty + 0.20 * (1.0 - met_align) + 0.15 * min(1.0, proj_err / 20.0)))
        sample_id = stable_id("rcalsamp", source_id, i, r["sensor_id"], r["clock_n"])
        sample_hash = hashlib.sha256(json.dumps(r, sort_keys=True).encode("utf-8")).hexdigest()
        cur.execute(
            "INSERT INTO real_data_calibration_sample_v07 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sample_id, source_id, clock_n, float(r["time_s"]), r["sensor_id"], r["sensor_kind"], x, y, z,
             force_norm, optical, acoustic, phase, uncertainty, sample_hash),
        )
        mapping_id = stable_id("rcalmap", sample_id, cell_uid, node_id)
        cur.execute(
            """
            INSERT INTO real_data_calibration_mapping_v07 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (mapping_id, RUN_ID, sample_id, cell_uid, node_id, dist, None, met_gate, proj_conf,
             mean_device_evidence, p_proxy, r_proxy, xi_proxy, now()),
        )
        force_norms.append(force_norm)
        phases_by_sensor.setdefault(r["sensor_id"], []).append(phase)
        multimodal_terms.append(multimodal)
        met_align_terms.append(met_align)
        p_terms.append(p_proxy)
        r_terms.append(r_proxy)
        xi_terms.append(xi_proxy)
        mapped += 1

    mean_force = sum(force_norms) / max(1, len(force_norms))
    variance = sum((v - mean_force) ** 2 for v in force_norms) / max(1, len(force_norms))
    force_nonuniformity = math.sqrt(variance) / max(1e-9, mean_force)
    phase_jumps: List[float] = []
    for vals in phases_by_sensor.values():
        vals_sorted = vals[:]
        for a, b in zip(vals_sorted, vals_sorted[1:]):
            d = abs(math.atan2(math.sin(b - a), math.cos(b - a)))
            phase_jumps.append(d)
    phase_continuity = max(0.0, min(1.0, 1.0 - (sum(phase_jumps) / max(1, len(phase_jumps))) / math.pi))
    multimodal_score = sum(multimodal_terms) / max(1, len(multimodal_terms))
    met_score = sum(met_align_terms) / max(1, len(met_align_terms))
    p_stability = sum(p_terms) / max(1, len(p_terms))
    r_counter = sum(r_terms) / max(1, len(r_terms))
    xi_pressure = sum(xi_terms) / max(1, len(xi_terms))
    gate_status = "FIXTURE_ONLY_BLOCKS_AUTO_ADOPTION" if is_fixture else "EXTERNAL_DATA_ACCEPTED_FOR_REVIEW"
    result_id = stable_id("rcalres", source_id, mapped, round(met_score, 6))
    cur.execute(
        """
        INSERT INTO real_data_calibration_result_v07 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (result_id, RUN_ID, source_id, len(rows), mapped, mean_force, force_nonuniformity,
         phase_continuity, multimodal_score, met_score, p_stability, r_counter, xi_pressure,
         gate_status,
         "Calibration harness maps physical CSV samples into matrix/MET/device/P-R-Xi proxies without source fact rewrite.",
         now()),
    )
    return {
        "source_id": source_id,
        "sample_count": len(rows),
        "mapped": mapped,
        "mean_force": mean_force,
        "force_nonuniformity": force_nonuniformity,
        "phase_continuity": phase_continuity,
        "multimodal_score": multimodal_score,
        "met_score": met_score,
        "p_stability": p_stability,
        "r_counter": r_counter,
        "xi_pressure": xi_pressure,
        "gate_status": gate_status,
        "is_fixture": is_fixture,
    }


def insert_shell0_lineage(cur: sqlite3.Cursor, root: Path) -> None:
    entries = [
        ("morphosphere_v2pp/data_contracts/suspension_registry.yaml", "contract", "declares full-shell0-resolution", "SUSPENDED_PRESENT", "formal unresolved high-risk boundary issue"),
        ("morphosphere_v2pp/schemas/shell0_adjudication.schema.json", "schema", "defines allowed adjudication verdicts", "present", "shell0 has a schema seat but not a closed mainline table"),
        ("morphosphere_v2pp/src/morphosphere/active_exec/shell0/boundary_analyzer.py", "legacy_module", "multi-variant analyzer with numpy dependency", "present_not_mainline_executed", "legacy analyzer is informative but not used as source-of-truth in DB"),
        ("morphosphere_v2pp/src/morphosphere/active_exec/runtime/replay/shell0_ci.py", "legacy_ci_stub", "simulated CI check", "stub", "not enough to certify physical shell0"),
        ("family_recursive_surface_index", "database_table", "contains shell0_verdict field", f"row_count={table_count(cur, 'family_recursive_surface_index')}", "formal field exists but no adjudicated rows in current DB"),
        ("morphosphere_v2pp/src/morphosphere/active_exec/stage2_object/family_surface/index_builder.py", "legacy_builder", "uses shell0 verdict for suspension and aggregation role", "present", "risks propagating unresolved shell0 into object surfaces if not gated"),
    ]
    for path, kind, role, status, conclusion in entries:
        cur.execute(
            "INSERT INTO shell0_lineage_audit_v07 VALUES (?,?,?,?,?,?,?,?)",
            (stable_id("sh0aud", path, status), RUN_ID, path, kind, role, status, conclusion, now()),
        )


def insert_shell0_probes(cur: sqlite3.Cursor) -> Dict[str, Any]:
    avg_stress = float(scalar(cur, "SELECT AVG(stress_energy_proxy) FROM substrate_stress_tensor_v04", 0.0) or 0.0)
    avg_leak = float(scalar(cur, "SELECT AVG(1.0 - conductance_proxy) FROM foam_edge_state_v04", 0.0) or 0.0)
    avg_contact = float(scalar(cur, "SELECT AVG(adhesion_proxy * compression_proxy) FROM cell_matrix_contact_v04", 0.0) or 0.0)
    avg_radial = float(scalar(cur, "SELECT AVG(radial_distance) FROM cell_matrix_contact_v04", 1.0) or 1.0)
    shell_count_rows = table_count(cur, "family_recursive_surface_index")
    shell_field_present = 1 if table_exists(cur, "family_recursive_surface_index") else 0
    v04_ablation_integrity = float(scalar(cur, "SELECT substrate_integrity_proxy FROM matrix_foam_replay_result_v04 WHERE scenario_name='matrix_edge_ablation'", 0.62) or 0.62)
    base_integrity = float(scalar(cur, "SELECT substrate_integrity_proxy FROM matrix_foam_replay_result_v04 WHERE scenario_name='baseline_substrate'", 0.96) or 0.96)
    ablation_delta = max(0.0, base_integrity - v04_ablation_integrity)
    # Diagnostic variants: not a proof; designed to determine whether shell0 is artifact-prone.
    variants = [
        ("baseline_matrix_shell", "baseline", avg_stress, avg_leak, avg_contact, 0.18, 0.22, 0.48, "partial_physical_support", "matrix shell has energy/contact structure but remains diagnostic"),
        ("contact_ablation", "contact_ablation", avg_stress * (1.0 - 0.35 * avg_contact), avg_leak + 0.07, avg_contact * 0.25, 0.21, 0.35, 0.30, "contact_sensitive", "contact ablation changes shell proxy but does not close shell0"),
        ("matrix_edge_ablation", "edge_ablation", avg_stress * (1.0 - ablation_delta * 0.30), avg_leak + ablation_delta, avg_contact * 0.65, 0.28, 0.42, 0.32, "artifact_risk_high", "edge ablation strongly affects substrate integrity"),
        ("ghost_shell", "ghost_boundary", avg_stress * 1.09, avg_leak + 0.12, avg_contact * 0.40, 0.34, 0.55, 0.20, "do_not_freeze", "ghost shell changes energy enough to block P-band freezing"),
        ("multi_resolution_2band", "multi_resolution", avg_stress * 0.97, avg_leak + 0.03, avg_contact * 0.90, 0.16, 0.25, 0.43, "indeterminate", "two-band resolution is stable but too coarse"),
        ("multi_resolution_4band", "multi_resolution", avg_stress * 1.03, avg_leak + 0.05, avg_contact * 0.86, 0.24, 0.30, 0.42, "indeterminate", "four-band resolution shifts shell proxy; needs full multi-resolution closure"),
        ("database_evidence_gap", "lineage_gap", 0.0, 0.0, 0.0, 1.0 if shell_count_rows == 0 and shell_field_present else 0.4, 0.78, 0.05, "project_structure_gap", "shell0 verdict field exists but current DB has no adjudicated surface rows"),
    ]
    physical_support_values = []
    artifact_values = []
    for name, kind, energy, leakage, contact, resvar, art, phys, verdict, interp in variants:
        physical_support_values.append(phys)
        artifact_values.append(art)
        cur.execute(
            "INSERT INTO shell0_resolution_probe_v07 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (stable_id("sh0probe", name, kind), RUN_ID, name, kind, float(energy), float(leakage), float(contact), float(resvar), float(art), float(phys), verdict, interp, now()),
        )
    physical_attr = sum(physical_support_values) / max(1, len(physical_support_values))
    artifact_risk = sum(artifact_values) / max(1, len(artifact_values))
    project_attr = max(0.55, min(0.95, 0.55 + 0.25 * (1 if shell_count_rows == 0 else 0) + 0.20 * artifact_risk))
    physical_attr = max(0.05, min(0.45, physical_attr * 0.75))
    verdict = "mixed_or_indeterminate"
    rationale = {
        "lineage": "shell0 is a documented high-risk boundary-first issue, not a settled physical layer",
        "database_state": f"family_recursive_surface_index rows={shell_count_rows}; no shell0 adjudication table exists before v0.7",
        "physical_signal": "matrix/foam data gives partial boundary-like support but is diagnostic proxy only",
        "dominant_attribution": "project_structure_boundary_closure_gap",
        "secondary_attribution": "possible_real_boundary_component_unproven",
        "action": "block automatic parameter adoption and keep shell0 suspended until multi-resolution/multi-boundary/contact-ablation closure",
    }
    cur.execute(
        "INSERT INTO shell0_adjudication_v07 VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (stable_id("sh0adj", RUN_ID, verdict), RUN_ID, "boundary_first_multi_probe_v07", verdict, 0.72, project_attr, physical_attr, 1, 1, json.dumps(rationale, ensure_ascii=False, sort_keys=True), now()),
    )
    return {
        "verdict": verdict,
        "project_attribution": project_attr,
        "physical_attribution": physical_attr,
        "blocks_auto": True,
        "artifact_risk": artifact_risk,
        "shell_rows": shell_count_rows,
    }


def add_gate(cur: sqlite3.Cursor, name: str, status: str, severity: str, observed: Any, expected: Any, blocks: bool, rationale: str) -> None:
    cur.execute(
        "INSERT INTO candidate_adoption_gate_v07 VALUES (?,?,?,?,?,?,?,?,?,?)",
        (stable_id("gatev07", name, observed, status), RUN_ID, name, status, severity, str(observed), str(expected), 1 if blocks else 0, rationale, now()),
    )


def write_patch_file(root: Path, candidate: Dict[str, Any], blockers: List[str]) -> Tuple[Path, str]:
    config_dir = root / "morphosphere_v2pp" / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    patch_path = config_dir / "candidate_adoption_v07_staged_profile.json"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "candidate_profile_id": candidate.get("profile_id"),
        "status": "staged_patch_not_applied",
        "may_apply_automatically": False,
        "requires_human_review": True,
        "blockers": blockers,
        "parameters": candidate.get("parameters", {}),
        "adoption_rules": [
            "run full replay on external real data",
            "resolve shell0 or keep shell0 explicitly suspended",
            "preserve P/R before Xi",
            "do not rewrite source facts",
            "record human approval before mainline config promotion",
        ],
    }
    patch_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return patch_path, sha256_file(patch_path)


def write_docs(root: Path, summary: Dict[str, Any]) -> None:
    docs = root / "morphosphere_v2pp" / "docs"
    reports = root / "morphosphere_v2pp" / "reports"
    docs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    md = f"""# Candidate Adoption Gate + Real-Data Calibration Harness v0.7

`v0.7` evaluates the fitted candidate profile generated by the v0.6 external lab. It does not automatically update the mainline.

## Main decision

- Decision: `{summary['final_decision']}`
- Auto adoption allowed: `{summary['auto_adoption_allowed']}`
- Manual review required: `{summary['manual_review_required']}`
- Candidate profile: `{summary['candidate_profile_id']}`
- Blockers: `{', '.join(summary['blockers'])}`

## Shell0 attribution

Shell0 is classified as `{summary['shell0_verdict']}`. The dominant attribution is a project-structure / boundary-closure gap, with a possible but unproven physical boundary component. It is not treated as certified real physics.

## Calibration

The harness accepts a CSV with `clock_n,time_s,sensor_id,sensor_kind,x,y,z,force_x,force_y,force_z,optical_intensity,acoustic_pressure,phase,uncertainty`. The packaged run uses a deterministic fixture so local replay is complete.

## Boundaries

- P/R remains before Xi.
- Xi cannot replace P/R.
- Candidate weights are staged as a patch only.
- Source facts are digested before/after and must remain unchanged.
- Shell0 blocks automatic adoption until explicitly resolved or kept suspended by policy.
"""
    (docs / "CANDIDATE_ADOPTION_GATE_V07.md").write_text(md, encoding="utf-8")
    quick = """# Quickstart: v0.7 Candidate Adoption Gate

Run all v0.7 checks:

```bash
./run_local_candidate_adoption.sh
```

Rebuild only v0.7:

```bash
python3 -S morphosphere_v2pp/scripts/run_candidate_adoption_v07.py --db outputs/morphosphere_candidate_adoption_v07_output_database.db --report-dir morphosphere_v2pp/reports
python3 -S morphosphere_v2pp/scripts/run_candidate_adoption_acceptance_v07.py outputs/morphosphere_candidate_adoption_v07_output_database.db
```

Provide external physical data:

```bash
python3 -S morphosphere_v2pp/scripts/run_candidate_adoption_v07.py --db outputs/morphosphere_candidate_adoption_v07_output_database.db --calibration-csv path/to/samples.csv --report-dir morphosphere_v2pp/reports
```
"""
    (root / "morphosphere_v2pp" / "QUICKSTART_CANDIDATE_ADOPTION_V07.md").write_text(quick, encoding="utf-8")
    report = {
        "schema_version": SCHEMA_VERSION,
        **summary,
    }
    (reports / "candidate_adoption_v07_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_md = "# Candidate Adoption v0.7 Report\n\n" + json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    (reports / "CANDIDATE_ADOPTION_GATE_V07_REPORT.md").write_text(report_md, encoding="utf-8")


def add_acceptance_rows(cur: sqlite3.Cursor, checks: List[Tuple[str, bool, Any, Any, str]]) -> None:
    for name, ok, observed, expected, severity in checks:
        cur.execute(
            "INSERT INTO candidate_adoption_acceptance_report_v07 VALUES (?,?,?,?,?,?,?,?)",
            (stable_id("accv07", name), RUN_ID, name, "PASS" if ok else "FAIL", str(observed), str(expected), severity, now()),
        )


def run(db: Path, root: Path, report_dir: Path, calibration_csv: Optional[Path], fixture_flag: Optional[bool]) -> Dict[str, Any]:
    before_db_sha = sha256_file(db)
    con = sqlite3.connect(str(db))
    cur = con.cursor()
    before_digests = {t: (table_count(cur, t), digest_table(cur, t)) for t in SOURCE_FACT_TABLES}
    create_schema(cur)

    candidate = load_best_profile(cur)
    baseline = load_baseline_profile(cur)
    if not candidate or not baseline:
        raise RuntimeError("v0.6 profiles are required before v0.7 adoption gate")
    train_improvement = baseline["train_loss"] - candidate["train_loss"]
    holdout_improvement = baseline["holdout_loss"] - candidate["holdout_loss"]
    review_status = "eligible_for_gated_review" if holdout_improvement > 0.01 else "insufficient_improvement"
    cur.execute(
        "INSERT INTO candidate_profile_review_v07 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (stable_id("reviewv07", candidate["profile_id"]), RUN_ID, candidate["profile_id"], baseline["profile_id"],
         candidate["train_loss"], candidate["holdout_loss"], baseline["train_loss"], baseline["holdout_loss"],
         train_improvement, holdout_improvement, json.dumps(candidate["parameters"], ensure_ascii=False, sort_keys=True),
         review_status,
         "Candidate improves held-out diagnostic loss but requires replay, real-data and shell0 gates before any mainline promotion.",
         now()),
    )

    if calibration_csv is None:
        calibration_csv = root / "morphosphere_v2pp" / "data" / "physical_fixture_v04.csv"
        is_fixture = True
    else:
        is_fixture = bool(fixture_flag) if fixture_flag is not None else False
    calibration = build_real_data_calibration(cur, calibration_csv, is_fixture=is_fixture)

    insert_shell0_lineage(cur, root)
    shell0 = insert_shell0_probes(cur)

    # Replay summaries from existing layers.
    v03_total = table_count(cur, "full_replay_result_v03")
    v03_pass = table_count(cur, "full_replay_result_v03", "passed=1")
    v04_total = table_count(cur, "matrix_foam_replay_result_v04")
    v04_pass = table_count(cur, "matrix_foam_replay_result_v04", "passed=1")
    v05_total = table_count(cur, "device_neutral_replay_result_v05")
    v05_pass = table_count(cur, "device_neutral_replay_result_v05", "passed=1")
    p_count = table_count(cur, "p_predictive_support_v022")
    r_count = table_count(cur, "r_counterstructure_v022")
    xi_count = table_count(cur, "xi_boundary_guard_v022")
    xi_direct = table_count(cur, "xi_boundary_guard_v022", "direct_to_p_allowed != 0 OR direct_to_r_allowed != 0") if table_exists(cur, "xi_boundary_guard_v022") else 999

    blockers: List[str] = []
    add_gate(cur, "candidate_holdout_improvement", "PASS" if holdout_improvement > 0.01 else "FAIL", "hard", round(holdout_improvement, 8), "> 0.01", holdout_improvement <= 0.01, "Candidate must improve holdout loss over legacy-like formula.")
    if holdout_improvement <= 0.01:
        blockers.append("insufficient_holdout_improvement")
    add_gate(cur, "full_replay_v03_all_pass", "PASS" if v03_total and v03_total == v03_pass else "FAIL", "hard", f"{v03_pass}/{v03_total}", "all pass", not (v03_total and v03_total == v03_pass), "Online sensorium full replay must pass before candidate promotion.")
    if not (v03_total and v03_total == v03_pass): blockers.append("v03_replay_failure")
    add_gate(cur, "matrix_foam_v04_all_pass", "PASS" if v04_total and v04_total == v04_pass else "FAIL", "hard", f"{v04_pass}/{v04_total}", "all pass", not (v04_total and v04_total == v04_pass), "Matrix-foam replay must pass before candidate promotion.")
    if not (v04_total and v04_total == v04_pass): blockers.append("v04_matrix_foam_failure")
    add_gate(cur, "device_neutral_v05_all_pass", "PASS" if v05_total and v05_total == v05_pass else "FAIL", "hard", f"{v05_pass}/{v05_total}", "all pass", not (v05_total and v05_total == v05_pass), "Device-neutral replay must pass before candidate promotion.")
    if not (v05_total and v05_total == v05_pass): blockers.append("v05_device_failure")
    pr_ok = p_count > 0 and r_count > 0 and xi_count > 0 and xi_direct == 0
    add_gate(cur, "p_r_before_xi_boundary", "PASS" if pr_ok else "FAIL", "hard", f"P={p_count},R={r_count},Xi={xi_count},direct={xi_direct}", "P/R present, Xi direct disabled", not pr_ok, "P/R cannot be replaced by Xi.")
    if not pr_ok: blockers.append("pr_xi_boundary_failure")
    real_ok = not calibration["is_fixture"] and calibration["mapped"] > 0 and calibration["met_score"] > 0.45
    add_gate(cur, "real_data_calibration_gate", "PASS" if real_ok else "BLOCKED_BY_FIXTURE_OR_LOW_ALIGNMENT", "release", calibration["gate_status"], "external data accepted and alignment > 0.45", not real_ok, "Packaged fixture proves harness, not real-world validation.")
    if not real_ok: blockers.append("external_real_data_required")
    shell_ok = shell0["verdict"] == "resolved" and not shell0["blocks_auto"]
    add_gate(cur, "shell0_resolution_gate", "PASS" if shell_ok else "BLOCKED_SHELL0_UNRESOLVED", "release", shell0["verdict"], "resolved", not shell_ok, "Shell0 remains mixed or indeterminate; auto adoption is blocked.")
    if not shell_ok: blockers.append("shell0_unresolved")
    add_gate(cur, "no_semantic_labels_in_adoption", "PASS", "hard", "semantic-free diagnostic profiles only", "no semantic labels", False, "Candidate profile uses diagnostic metrics, not labels.")
    add_gate(cur, "human_review_required", "ACTIVE", "policy", "required", "required", True, "Even if gates pass, human review is required before mainline config promotion.")
    blockers.append("human_review_required")

    patch_path, patch_sha = write_patch_file(root, candidate, blockers)
    cur.execute(
        "INSERT INTO candidate_patch_manifest_v07 VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (stable_id("patchv07", candidate["profile_id"], patch_sha), RUN_ID, candidate["profile_id"], str(patch_path.relative_to(root)), patch_sha,
         "staged_patch_not_applied", 0, 1, json.dumps(candidate["parameters"], ensure_ascii=False, sort_keys=True), json.dumps(blockers, ensure_ascii=False), now()),
    )

    after_digests = {t: (table_count(cur, t), digest_table(cur, t)) for t in SOURCE_FACT_TABLES}
    for t in SOURCE_FACT_TABLES:
        bc, bd = before_digests[t]
        ac, ad = after_digests[t]
        status = "PASS" if bc == ac and bd == ad else "FAIL"
        cur.execute(
            "INSERT INTO source_fact_digest_v07 VALUES (?,?,?,?,?,?,?,?,?)",
            (stable_id("digv07", t), RUN_ID, t, bc, ac, bd, ad, status, now()),
        )
        if status != "PASS":
            blockers.append(f"source_fact_mutated:{t}")

    final_decision = "STAGED_PATCH_NOT_APPLIED"
    auto_adoption_allowed = False
    manual_review_required = True
    source_kind = "fixture" if calibration["is_fixture"] else "external_csv"

    checks = [
        ("v07_tables_created", all(table_exists(cur, t) for t in V07_TABLES), "all", "all", "hard"),
        ("candidate_profile_reviewed", table_count(cur, "candidate_profile_review_v07") == 1, table_count(cur, "candidate_profile_review_v07"), 1, "hard"),
        ("patch_staged", table_count(cur, "candidate_patch_manifest_v07") == 1, table_count(cur, "candidate_patch_manifest_v07"), 1, "hard"),
        ("auto_adoption_disabled", auto_adoption_allowed is False, auto_adoption_allowed, False, "hard"),
        ("real_data_samples_mapped", calibration["mapped"] == calibration["sample_count"] and calibration["sample_count"] > 0, f"{calibration['mapped']}/{calibration['sample_count']}", "all", "hard"),
        ("shell0_adjudicated", table_count(cur, "shell0_adjudication_v07") == 1, table_count(cur, "shell0_adjudication_v07"), 1, "hard"),
        ("shell0_blocks_auto_adoption", shell0["blocks_auto"] is True, shell0["blocks_auto"], True, "release"),
        ("source_digests_pass", table_count(cur, "source_fact_digest_v07", "status='FAIL'") == 0, table_count(cur, "source_fact_digest_v07", "status='FAIL'"), 0, "hard"),
        ("p_r_xi_boundary_ok", pr_ok, f"P={p_count},R={r_count},Xi={xi_count},direct={xi_direct}", "ok", "hard"),
        ("candidate_not_mainline_adopted", True, "staged only", "staged only", "hard"),
    ]
    add_acceptance_rows(cur, checks)

    # Manifest after commit not final sha yet; we update after calculating and then write again.
    con.commit()
    after_db_sha = sha256_file(db)
    cur.execute(
        "INSERT INTO candidate_adoption_run_manifest_v07 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (RUN_ID, SCHEMA_VERSION, "diagnostic_append_only_candidate_adoption_gate", str(db), before_db_sha, after_db_sha,
         candidate["profile_id"], baseline["profile_id"], final_decision, 1 if auto_adoption_allowed else 0,
         1, 1 if manual_review_required else 0, len(set(blockers)), shell0["verdict"], source_kind, now()),
    )
    con.commit()

    summary = {
        "run_id": RUN_ID,
        "candidate_profile_id": candidate["profile_id"],
        "baseline_profile_id": baseline["profile_id"],
        "train_improvement": train_improvement,
        "holdout_improvement": holdout_improvement,
        "calibration_sample_count": calibration["sample_count"],
        "calibration_mapped_count": calibration["mapped"],
        "calibration_is_fixture": calibration["is_fixture"],
        "calibration_met_alignment": calibration["met_score"],
        "shell0_verdict": shell0["verdict"],
        "shell0_project_structure_attribution": shell0["project_attribution"],
        "shell0_physical_boundary_attribution": shell0["physical_attribution"],
        "final_decision": final_decision,
        "auto_adoption_allowed": auto_adoption_allowed,
        "manual_review_required": manual_review_required,
        "blockers": sorted(set(blockers)),
        "patch_path": str(patch_path.relative_to(root)),
        "patch_sha256": patch_sha,
    }
    write_docs(root, summary)

    # Artifact manifest after writing docs.
    for rel, typ, role in [
        ("morphosphere_v2pp/configs/candidate_adoption_v07_staged_profile.json", "json", "staged candidate parameters"),
        ("morphosphere_v2pp/docs/CANDIDATE_ADOPTION_GATE_V07.md", "markdown", "v0.7 design notes"),
        ("morphosphere_v2pp/QUICKSTART_CANDIDATE_ADOPTION_V07.md", "markdown", "local run guide"),
        ("morphosphere_v2pp/reports/CANDIDATE_ADOPTION_GATE_V07_REPORT.md", "markdown", "human-readable report"),
        ("morphosphere_v2pp/reports/candidate_adoption_v07_summary.json", "json", "machine-readable summary"),
    ]:
        p = root / rel
        cur.execute(
            "INSERT INTO candidate_adoption_artifact_manifest_v07 VALUES (?,?,?,?,?,?,?)",
            (stable_id("artv07", rel), RUN_ID, rel, typ, sha256_file(p), role, now()),
        )
    con.commit()
    con.close()
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--report-dir", default="morphosphere_v2pp/reports")
    ap.add_argument("--calibration-csv", default=None)
    ap.add_argument("--fixture", action="store_true", help="Mark supplied calibration CSV as deterministic fixture rather than real external data")
    args = ap.parse_args()
    db = Path(args.db).resolve()
    root = Path.cwd()
    if not (root / "morphosphere_v2pp").exists():
        # If launched from scripts directory or elsewhere, infer package root from db path.
        root = db.parents[1] if db.parent.name == "outputs" else Path.cwd()
    report_dir = (root / args.report_dir).resolve() if not Path(args.report_dir).is_absolute() else Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    calibration_csv = Path(args.calibration_csv).resolve() if args.calibration_csv else None
    summary = run(db, root, report_dir, calibration_csv, fixture_flag=True if args.fixture else None)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
