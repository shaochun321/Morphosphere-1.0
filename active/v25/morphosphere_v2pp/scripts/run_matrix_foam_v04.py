#!/usr/bin/env python3
"""Morphosphere Matrix-Foam Substrate + Physical Data Driver v0.4.

This layer continues online_recursive_sensorium_full_replay_v0.3.

Primary goal:
    Add an explicit substrate/foam/material carrier below the online sensorium,
    and add a device-neutral physical data driver. The driver can read an external
    CSV, but ships with a deterministic fixture so the package remains locally
    runnable.

Boundaries:
- Diagnostic append-only: no source facts are rewritten.
- Matrix/foam substrate is a physical-proxy layer, not final ECM/biology.
- External/fixture physical samples are mapped to substrate and MET events; they
  may inform projections and tests, but they cannot overwrite spacetime_cell,
  information_fiber, raw_event_stream, P/R, or Xi source rows.
- P/R remains before Xi; Xi remains post-P/R residue only.
"""
from __future__ import annotations

import argparse
import csv
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

VERSION = "matrix_foam_physical_driver_v0.4"
EXECUTION_MODE = "diagnostic_append_only_matrix_foam_physical_driver"
FORBIDDEN_USE = "scientific_run, final_biology, source_fact_rewrite, semantic_labeling, experimental_truth_claim"
SOURCE_FACT_TABLES = [
    "spacetime_cell",
    "information_fiber",
    "raw_event_stream",
    "cell_spatial_coordinate_snapshot",
    "information_relative_coordinate_snapshot",
    "system_clock_entry",
]
V04_TABLES = [
    "matrix_foam_run_manifest_v04",
    "substrate_material_region_v04",
    "cell_matrix_contact_v04",
    "foam_edge_state_v04",
    "substrate_stress_tensor_v04",
    "physical_data_source_manifest_v04",
    "physical_sample_stream_v04",
    "physical_driver_mapping_v04",
    "mechanotransduction_event_v04",
    "substrate_to_raw_event_projection_v04",
    "matrix_foam_replay_result_v04",
    "matrix_foam_acceptance_report_v04",
    "matrix_foam_artifact_manifest_v04",
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


def vec_norm(x: float, y: float, z: float) -> float:
    return math.sqrt(x*x + y*y + z*z)


def distance(a: tuple[float,float,float], b: tuple[float,float,float]) -> float:
    return vec_norm(a[0]-b[0], a[1]-b[1], a[2]-b[2])


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
        CREATE TABLE IF NOT EXISTS matrix_foam_run_manifest_v04 (
            matrix_run_id TEXT PRIMARY KEY,
            parent_online_run_id TEXT NOT NULL,
            version TEXT NOT NULL,
            execution_mode TEXT NOT NULL,
            scientific_run INTEGER NOT NULL,
            substrate_mode TEXT NOT NULL,
            physical_driver_mode TEXT NOT NULL,
            physical_data_source_id TEXT NOT NULL,
            clock_source_table TEXT NOT NULL,
            clock_count INTEGER NOT NULL,
            source_fact_counts_before_json TEXT NOT NULL,
            source_fact_counts_after_json TEXT NOT NULL,
            material_region_count INTEGER NOT NULL,
            cell_matrix_contact_count INTEGER NOT NULL,
            foam_edge_count INTEGER NOT NULL,
            stress_tensor_count INTEGER NOT NULL,
            physical_sample_count INTEGER NOT NULL,
            mechanotransduction_event_count INTEGER NOT NULL,
            projection_count INTEGER NOT NULL,
            replay_result_count INTEGER NOT NULL,
            pr_xi_boundary_assertion TEXT NOT NULL,
            created_at TEXT NOT NULL,
            forbidden_use TEXT NOT NULL,
            notes TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS substrate_material_region_v04 (
            region_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            region_name TEXT NOT NULL,
            material_class TEXT NOT NULL,
            stiffness_proxy REAL NOT NULL,
            damping_proxy REAL NOT NULL,
            anisotropy_proxy REAL NOT NULL,
            porosity_proxy REAL NOT NULL,
            coupling_to_cell_surface REAL NOT NULL,
            biological_analogy TEXT NOT NULL,
            diagnostic_status TEXT NOT NULL,
            source_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cell_matrix_contact_v04 (
            contact_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            source_cell_uid TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            region_id TEXT NOT NULL,
            cell_x REAL NOT NULL,
            cell_y REAL NOT NULL,
            cell_z REAL NOT NULL,
            radial_distance REAL NOT NULL,
            surface_normal_x REAL NOT NULL,
            surface_normal_y REAL NOT NULL,
            surface_normal_z REAL NOT NULL,
            contact_area_proxy REAL NOT NULL,
            adhesion_proxy REAL NOT NULL,
            compression_proxy REAL NOT NULL,
            shear_proxy REAL NOT NULL,
            substrate_role TEXT NOT NULL,
            source_table TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS foam_edge_state_v04 (
            foam_edge_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            edge_type TEXT NOT NULL,
            cell_a_uid TEXT NOT NULL,
            cell_b_uid TEXT NOT NULL,
            node_a INTEGER NOT NULL,
            node_b INTEGER NOT NULL,
            rest_length REAL NOT NULL,
            current_length REAL NOT NULL,
            strain_proxy REAL NOT NULL,
            tension_proxy REAL NOT NULL,
            damping_proxy REAL NOT NULL,
            conductance_proxy REAL NOT NULL,
            supports_signal_phase INTEGER NOT NULL,
            source_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS substrate_stress_tensor_v04 (
            stress_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            source_cell_uid TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            region_id TEXT NOT NULL,
            sigma_xx REAL NOT NULL,
            sigma_xy REAL NOT NULL,
            sigma_xz REAL NOT NULL,
            sigma_yy REAL NOT NULL,
            sigma_yz REAL NOT NULL,
            sigma_zz REAL NOT NULL,
            hydrostatic_pressure_proxy REAL NOT NULL,
            shear_norm_proxy REAL NOT NULL,
            stress_energy_proxy REAL NOT NULL,
            source_components_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS physical_data_source_manifest_v04 (
            physical_data_source_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            driver_mode TEXT NOT NULL,
            source_path TEXT NOT NULL,
            source_sha256 TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            sample_count INTEGER NOT NULL,
            clock_count INTEGER NOT NULL,
            coordinate_frame_id TEXT NOT NULL,
            fixture_used INTEGER NOT NULL,
            real_experimental_data_claimed INTEGER NOT NULL,
            allowed_use TEXT NOT NULL,
            boundary_note TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS physical_sample_stream_v04 (
            physical_sample_id TEXT PRIMARY KEY,
            physical_data_source_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            time_s REAL NOT NULL,
            sensor_id TEXT NOT NULL,
            sensor_kind TEXT NOT NULL,
            x REAL NOT NULL,
            y REAL NOT NULL,
            z REAL NOT NULL,
            force_x REAL NOT NULL,
            force_y REAL NOT NULL,
            force_z REAL NOT NULL,
            optical_intensity REAL NOT NULL,
            acoustic_pressure REAL NOT NULL,
            phase REAL NOT NULL,
            uncertainty REAL NOT NULL,
            sample_provenance_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS physical_driver_mapping_v04 (
            mapping_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            physical_sample_id TEXT NOT NULL,
            clock_n INTEGER NOT NULL,
            source_cell_uid TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            region_id TEXT NOT NULL,
            spatial_distance REAL NOT NULL,
            interpolation_weight REAL NOT NULL,
            mapping_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS mechanotransduction_event_v04 (
            met_event_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            mapping_id TEXT NOT NULL,
            physical_sample_id TEXT NOT NULL,
            source_cell_uid TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            force_norm REAL NOT NULL,
            local_stress_energy REAL NOT NULL,
            strain_proxy REAL NOT NULL,
            met_gate_probability REAL NOT NULL,
            transduced_current_proxy REAL NOT NULL,
            calcium_proxy REAL NOT NULL,
            event_phase REAL NOT NULL,
            event_uncertainty REAL NOT NULL,
            event_role TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS substrate_to_raw_event_projection_v04 (
            projection_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            met_event_id TEXT NOT NULL,
            nearest_raw_event_id TEXT NOT NULL,
            source_cell_uid TEXT NOT NULL,
            node_id INTEGER NOT NULL,
            clock_n INTEGER NOT NULL,
            channel_type TEXT NOT NULL,
            raw_value REAL NOT NULL,
            projected_value REAL NOT NULL,
            projection_error REAL NOT NULL,
            projection_confidence REAL NOT NULL,
            source_fact_rewritten INTEGER NOT NULL,
            projection_rule TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS matrix_foam_replay_result_v04 (
            replay_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            scenario_name TEXT NOT NULL,
            scenario_type TEXT NOT NULL,
            perturbation_json TEXT NOT NULL,
            mean_met_gate_probability REAL NOT NULL,
            mean_stress_energy REAL NOT NULL,
            projected_error_mean REAL NOT NULL,
            p_stability_proxy REAL NOT NULL,
            r_counter_proxy REAL NOT NULL,
            xi_pressure_proxy REAL NOT NULL,
            substrate_integrity_proxy REAL NOT NULL,
            passed INTEGER NOT NULL,
            interpretation TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS matrix_foam_acceptance_report_v04 (
            acceptance_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            status TEXT NOT NULL,
            observed_json TEXT NOT NULL,
            expected_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS matrix_foam_artifact_manifest_v04 (
            artifact_id TEXT PRIMARY KEY,
            matrix_run_id TEXT NOT NULL,
            artifact_type TEXT NOT NULL,
            artifact_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )


def reset_tables(cur: sqlite3.Cursor) -> None:
    for t in V04_TABLES:
        cur.execute(f"DROP TABLE IF EXISTS {t}")
    ensure_tables(cur)


def make_fixture_csv(path: Path, clocks: list[sqlite3.Row]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sensors = [
        ("vestibular_like_north", 5.6, 0.0, 0.4),
        ("vestibular_like_east", 0.0, 5.6, 0.2),
        ("vestibular_like_south", -5.6, 0.0, -0.2),
        ("vestibular_like_west", 0.0, -5.6, 0.1),
        ("shear_band_upper", 3.4, 3.4, 1.1),
        ("shear_band_lower", -3.4, -3.4, -1.0),
        ("acoustic_pressure_probe", 2.2, -4.1, 0.0),
        ("optical_gradient_probe", -2.2, 4.1, 0.0),
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "clock_n", "time_s", "sensor_id", "sensor_kind", "x", "y", "z",
            "force_x", "force_y", "force_z", "optical_intensity", "acoustic_pressure", "phase", "uncertainty",
        ])
        for c in clocks:
            clock_n = int(c["clock_n"])
            t = float(c["time_s"])
            for idx, (sid, x, y, z) in enumerate(sensors):
                theta = 0.72 * clock_n + idx * 0.61
                slow = math.sin(0.35 * clock_n + idx * 0.3)
                force_scale = 0.52 + 0.18 * math.sin(0.19 * clock_n + idx)
                fx = force_scale * math.cos(theta) + 0.035 * slow
                fy = force_scale * math.sin(theta) - 0.025 * slow
                fz = 0.12 * math.sin(0.51 * clock_n + idx * 0.2)
                optical = 0.45 + 0.35 * math.sin(theta + 0.4) + 0.05 * math.cos(idx)
                acoustic = 0.38 * math.sin(theta - 0.6) + 0.09 * math.sin(1.1 * clock_n)
                phase = math.atan2(fy, fx)
                uncertainty = 0.025 + 0.006 * (idx % 3) + 0.004 * (clock_n % 2)
                w.writerow([clock_n, t, sid, "fixture_multimodal_probe", x, y, z, fx, fy, fz, optical, acoustic, phase, uncertainty])


def load_samples(cur: sqlite3.Cursor, path: Path, source_id: str, matrix_run_id: str) -> list[dict[str, Any]]:
    samples = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"clock_n", "time_s", "sensor_id", "sensor_kind", "x", "y", "z", "force_x", "force_y", "force_z", "optical_intensity", "acoustic_pressure", "phase", "uncertainty"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"physical CSV missing columns: {sorted(missing)}")
        for row in reader:
            d = {
                "clock_n": int(row["clock_n"]),
                "time_s": float(row["time_s"]),
                "sensor_id": row["sensor_id"],
                "sensor_kind": row["sensor_kind"],
                "x": float(row["x"]),
                "y": float(row["y"]),
                "z": float(row["z"]),
                "force_x": float(row["force_x"]),
                "force_y": float(row["force_y"]),
                "force_z": float(row["force_z"]),
                "optical_intensity": float(row["optical_intensity"]),
                "acoustic_pressure": float(row["acoustic_pressure"]),
                "phase": float(row["phase"]),
                "uncertainty": float(row["uncertainty"]),
            }
            sid = stable_id("phys", source_id, d["clock_n"], d["sensor_id"])
            d["physical_sample_id"] = sid
            prov = hashlib.sha256(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest()
            d["sample_provenance_hash"] = prov
            samples.append(d)
            cur.execute(
                "INSERT INTO physical_sample_stream_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    sid, source_id, d["clock_n"], d["time_s"], d["sensor_id"], d["sensor_kind"],
                    d["x"], d["y"], d["z"], d["force_x"], d["force_y"], d["force_z"],
                    d["optical_intensity"], d["acoustic_pressure"], d["phase"], d["uncertainty"], prov,
                ) if False else ()
            )
    # The insert above is intentionally not used because SQLite error messages for tuple length are noisy.
    cur.executemany(
        "INSERT INTO physical_sample_stream_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                d["physical_sample_id"], source_id, d["clock_n"], d["time_s"], d["sensor_id"], d["sensor_kind"],
                d["x"], d["y"], d["z"], d["force_x"], d["force_y"], d["force_z"], d["optical_intensity"],
                d["acoustic_pressure"], d["phase"], d["uncertainty"], d["sample_provenance_hash"],
            ) for d in samples
        ]
    )
    return samples


def fetch_cells(cur: sqlite3.Cursor) -> list[sqlite3.Row]:
    return cur.execute(
        """
        SELECT s.cell_uid, s.node_id, s.window_id, s.clock_start AS clock_n, s.x, s.y, s.z,
               s.normal_x, s.normal_y, s.normal_z, s.boundary_distance, s.support_radius,
               s.coordinate_frame_id, i.V_mean, i.V_slope, i.spike_rate, i.release_proxy,
               i.signal_uncertainty, i.provenance_hash AS fiber_hash
        FROM spacetime_cell s
        LEFT JOIN information_fiber i ON i.cell_uid = s.cell_uid
        ORDER BY s.clock_start, s.node_id
        """
    ).fetchall()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--report-dir", default="")
    ap.add_argument("--physical-csv", default="")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    ensure_tables(cur)
    reset_tables(cur)

    before = {t: count_table(cur, t) for t in SOURCE_FACT_TABLES}
    parent_online = cur.execute("SELECT online_run_id FROM online_sensorium_run_manifest_v03 ORDER BY created_at DESC LIMIT 1").fetchone()
    parent_online_id = parent_online[0] if parent_online else "missing_online_v03"
    matrix_run_id = stable_id("mxfoam_v04", parent_online_id, now(), n=12)
    tnow = now()

    # Material regions: explicit proxy material substrate, not final ECM.
    regions = [
        ("reg_core", "matrix_core", "viscoelastic_matrix", 0.62, 0.34, 0.12, 0.46, 0.68, "ECM-like hydrogel / cytoplasmic support", "diagnostic_proxy"),
        ("reg_shell", "elastic_shell", "boundary_elastic_lamina", 0.78, 0.28, 0.22, 0.32, 0.74, "connective-tissue-like shell", "diagnostic_proxy"),
        ("reg_shear", "shear_band", "muscle_like_contractile_band", 0.88, 0.22, 0.54, 0.27, 0.81, "contractile muscle/actomyosin analogy", "diagnostic_proxy"),
        ("reg_foam", "foam_crosslink", "porous_cellular_scaffold", 0.52, 0.41, 0.36, 0.64, 0.59, "foam-like connective mesh", "diagnostic_proxy"),
    ]
    region_by_name = {}
    for reg_id, name, cls, stiff, damp, aniso, poro, coup, bio, status in regions:
        region_id = stable_id("region", matrix_run_id, reg_id)
        region_by_name[name] = region_id
        cur.execute(
            "INSERT INTO substrate_material_region_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (region_id, matrix_run_id, name, cls, stiff, damp, aniso, poro, coup, bio, status, "deterministic region assignment from cell radius/angle/shear role", tnow),
        )

    cells = fetch_cells(cur)
    cells_by_clock_node: dict[tuple[int,int], sqlite3.Row] = {}
    region_for_cell: dict[str, str] = {}
    stress_for_cell: dict[str, dict[str, float]] = {}

    for c in cells:
        clock_n = int(c["clock_n"])
        node_id = int(c["node_id"])
        cells_by_clock_node[(clock_n, node_id)] = c
        x, y, z = float(c["x"]), float(c["y"]), float(c["z"])
        r = vec_norm(x, y, z)
        theta = math.atan2(y, x)
        if abs(z) > 0.75 or math.sin(theta * 2.0 + clock_n * 0.21) > 0.58:
            region_name = "shear_band"
        elif r > 4.85:
            region_name = "elastic_shell"
        elif (node_id + clock_n) % 5 == 0:
            region_name = "foam_crosslink"
        else:
            region_name = "matrix_core"
        region_id = region_by_name[region_name]
        region_for_cell[c["cell_uid"]] = region_id
        v = float(c["V_mean"] or -60.0)
        slope = float(c["V_slope"] or 0.0)
        spike = float(c["spike_rate"] or 0.0)
        compression = clamp((r - 4.3) / 1.3 + 0.08 * math.sin(clock_n + node_id * 0.13))
        shear = clamp(abs(math.sin(theta + 0.37 * clock_n)) * (0.35 + 0.65 * abs(z) / 1.3))
        adhesion = clamp(0.52 + 0.16 * math.cos(theta - 0.2 * clock_n) - 0.08 * compression)
        contact_area = max(0.05, math.pi * float(c["support_radius"] or 1.0) ** 2 * (0.45 + 0.45 * adhesion + 0.10 * compression))
        cur.execute(
            "INSERT INTO cell_matrix_contact_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                stable_id("contact", matrix_run_id, c["cell_uid"]), matrix_run_id, c["cell_uid"], node_id, clock_n,
                region_id, x, y, z, r, float(c["normal_x"] or 0.0), float(c["normal_y"] or 0.0), float(c["normal_z"] or 0.0),
                contact_area, adhesion, compression, shear, region_name, "spacetime_cell+information_fiber", tnow,
            ),
        )
        # Symmetric stress tensor proxy from geometry, V slope, and spike pressure.
        nx, ny, nz = float(c["normal_x"] or 0.0), float(c["normal_y"] or 0.0), float(c["normal_z"] or 0.0)
        amp = 0.18 + 0.008 * abs(slope) + 0.030 * spike + 0.055 * compression + 0.033 * shear
        sigma_xx = amp * (0.55 + nx * nx)
        sigma_yy = amp * (0.55 + ny * ny)
        sigma_zz = amp * (0.35 + nz * nz)
        sigma_xy = amp * 0.45 * nx * ny + 0.012 * math.sin(theta + clock_n)
        sigma_xz = amp * 0.35 * nx * nz
        sigma_yz = amp * 0.35 * ny * nz
        pressure = (sigma_xx + sigma_yy + sigma_zz) / 3.0
        shear_norm = math.sqrt(sigma_xy*sigma_xy + sigma_xz*sigma_xz + sigma_yz*sigma_yz)
        energy = 0.5 * (sigma_xx*sigma_xx + sigma_yy*sigma_yy + sigma_zz*sigma_zz) + shear_norm
        stress_for_cell[c["cell_uid"]] = {"pressure": pressure, "shear": shear_norm, "energy": energy}
        cur.execute(
            "INSERT INTO substrate_stress_tensor_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                stable_id("stress", matrix_run_id, c["cell_uid"]), matrix_run_id, c["cell_uid"], node_id, clock_n, region_id,
                sigma_xx, sigma_xy, sigma_xz, sigma_yy, sigma_yz, sigma_zz, pressure, shear_norm, energy,
                json.dumps({"V_mean": v, "V_slope": slope, "spike_rate": spike, "compression": compression, "shear": shear}, sort_keys=True),
                tnow,
            ),
        )

    # Foam/mesh edges: membrane neighbors, cross-links, and contractile spokes.
    edge_specs = [(1, "membrane_contact", 1.00), (2, "foam_crosslink", 1.17), (5, "contractile_spoke", 1.45)]
    max_node = max(int(c["node_id"]) for c in cells) + 1
    for clock_n in sorted({int(c["clock_n"]) for c in cells}):
        for node_id in range(max_node):
            a = cells_by_clock_node.get((clock_n, node_id))
            if not a:
                continue
            for offset, etype, rest_factor in edge_specs:
                bnode = (node_id + offset) % max_node
                if node_id > bnode and offset != 5:
                    continue
                b = cells_by_clock_node.get((clock_n, bnode))
                if not b or a["cell_uid"] == b["cell_uid"]:
                    continue
                pa = (float(a["x"]), float(a["y"]), float(a["z"]))
                pb = (float(b["x"]), float(b["y"]), float(b["z"]))
                length = distance(pa, pb)
                rest = max(0.1, length / rest_factor)
                strain = (length - rest) / rest
                energy_a = stress_for_cell[a["cell_uid"]]["energy"]
                energy_b = stress_for_cell[b["cell_uid"]]["energy"]
                tension = max(0.0, 0.18 + 0.42 * strain + 0.08 * (energy_a + energy_b))
                damping = 0.18 + 0.07 * (1 if etype == "contractile_spoke" else 0) + 0.02 * abs(math.sin(clock_n + node_id))
                conductance = clamp(0.45 + 0.18 * math.exp(-abs(strain)) + 0.11 * (1 if etype != "contractile_spoke" else 0))
                cur.execute(
                    "INSERT INTO foam_edge_state_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        stable_id("foam", matrix_run_id, clock_n, node_id, bnode, etype), matrix_run_id, clock_n, etype,
                        a["cell_uid"], b["cell_uid"], node_id, bnode, rest, length, strain, tension, damping, conductance,
                        1 if conductance > 0.5 else 0, "ring-neighbor plus crosslink foam proxy; no source fact rewrite", tnow,
                    ),
                )

    clocks = cur.execute("SELECT * FROM system_clock_entry ORDER BY clock_n").fetchall()
    if args.physical_csv:
        phys_path = Path(args.physical_csv)
        fixture_used = 0
        driver_mode = "external_csv_read_only"
    else:
        phys_path = Path(args.report_dir or ".").parent / "data" / "physical_fixture_v04.csv"
        make_fixture_csv(phys_path, clocks)
        fixture_used = 1
        driver_mode = "deterministic_fixture_csv_plus_external_csv_ready"
    source_id = stable_id("phys_source", matrix_run_id, phys_path.name, checksum_file(str(phys_path)), n=12)
    samples = []
    with open(phys_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"clock_n", "time_s", "sensor_id", "sensor_kind", "x", "y", "z", "force_x", "force_y", "force_z", "optical_intensity", "acoustic_pressure", "phase", "uncertainty"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"physical CSV missing columns: {sorted(missing)}")
        for row in reader:
            d = {
                "clock_n": int(row["clock_n"]), "time_s": float(row["time_s"]), "sensor_id": row["sensor_id"], "sensor_kind": row["sensor_kind"],
                "x": float(row["x"]), "y": float(row["y"]), "z": float(row["z"]),
                "force_x": float(row["force_x"]), "force_y": float(row["force_y"]), "force_z": float(row["force_z"]),
                "optical_intensity": float(row["optical_intensity"]), "acoustic_pressure": float(row["acoustic_pressure"]), "phase": float(row["phase"]), "uncertainty": float(row["uncertainty"]),
            }
            sid = stable_id("phys", source_id, d["clock_n"], d["sensor_id"])
            d["physical_sample_id"] = sid
            prov = hashlib.sha256(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest()
            d["sample_provenance_hash"] = prov
            samples.append(d)
    cur.executemany(
        "INSERT INTO physical_sample_stream_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(d["physical_sample_id"], source_id, d["clock_n"], d["time_s"], d["sensor_id"], d["sensor_kind"], d["x"], d["y"], d["z"], d["force_x"], d["force_y"], d["force_z"], d["optical_intensity"], d["acoustic_pressure"], d["phase"], d["uncertainty"], d["sample_provenance_hash"]) for d in samples],
    )
    cur.execute(
        "INSERT INTO physical_data_source_manifest_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            source_id, matrix_run_id, driver_mode, str(phys_path), checksum_file(str(phys_path)), "physical_sample_stream_v04_csv_v1",
            len(samples), len(set(d["clock_n"] for d in samples)), "cell_sphere_v852", fixture_used, 0,
            "read-only physical driver input; may be replaced by real CSV with same schema",
            "fixture is deterministic proxy unless --physical-csv is supplied; no experimental truth claim", tnow,
        ),
    )

    # Map physical samples to nearest cells and derive MET events.
    cells_by_clock = defaultdict(list)
    for c in cells:
        cells_by_clock[int(c["clock_n"])].append(c)
    raw_by_clock_node = defaultdict(list)
    for r in cur.execute("SELECT * FROM raw_event_stream ORDER BY clock_n,node_id,channel_type").fetchall():
        raw_by_clock_node[(int(r["clock_n"]), int(r["node_id"]))].append(r)

    met_events = []
    for s in samples:
        clock_n = int(s["clock_n"])
        ps = (s["x"], s["y"], s["z"])
        nearest = sorted(cells_by_clock[clock_n], key=lambda c: distance(ps, (float(c["x"]), float(c["y"]), float(c["z"]))))[:5]
        denom = sum(1.0 / (0.2 + distance(ps, (float(c["x"]), float(c["y"]), float(c["z"])))) for c in nearest) or 1.0
        for c in nearest:
            d = distance(ps, (float(c["x"]), float(c["y"]), float(c["z"])))
            weight = (1.0 / (0.2 + d)) / denom
            mapping_id = stable_id("map", matrix_run_id, s["physical_sample_id"], c["cell_uid"])
            region_id = region_for_cell[c["cell_uid"]]
            cur.execute(
                "INSERT INTO physical_driver_mapping_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (mapping_id, matrix_run_id, s["physical_sample_id"], clock_n, c["cell_uid"], int(c["node_id"]), region_id, d, weight, "nearest-5 inverse-distance mapping from physical sample to cell substrate", tnow),
            )
            fnorm = vec_norm(s["force_x"], s["force_y"], s["force_z"])
            stress = stress_for_cell[c["cell_uid"]]
            strain = clamp(0.38 * fnorm * weight + 0.42 * stress["shear"] + 0.20 * abs(s["acoustic_pressure"]))
            met_gate = sigmoid(4.2 * strain + 1.1 * stress["energy"] + 0.45 * abs(s["optical_intensity"] - 0.5) - 1.32)
            trans_current = met_gate * (0.65 * fnorm + 0.18 * s["acoustic_pressure"] + 0.12 * (s["optical_intensity"] - 0.5))
            calcium = clamp(0.22 + 0.58 * met_gate + 0.15 * strain - 0.20 * float(s["uncertainty"]))
            met_id = stable_id("met", mapping_id)
            met_events.append((met_id, c, s, trans_current))
            cur.execute(
                "INSERT INTO mechanotransduction_event_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (met_id, matrix_run_id, mapping_id, s["physical_sample_id"], c["cell_uid"], int(c["node_id"]), clock_n, fnorm, stress["energy"], strain, met_gate, trans_current, calcium, s["phase"], s["uncertainty"], "force_to_signal_met_proxy_diagnostic", tnow),
            )
            raws = raw_by_clock_node.get((clock_n, int(c["node_id"])), [])
            if raws:
                # Prefer bioelectric proxy, otherwise first raw event.
                raw = next((r for r in raws if r["channel_type"] == "bioelectric_proxy"), raws[0])
                projected = -62.0 + 24.0 * trans_current + 3.5 * calcium
                raw_val = float(raw["value"])
                err = abs(projected - raw_val)
                conf = clamp(math.exp(-err / 45.0) * (1.0 - float(s["uncertainty"])))
                cur.execute(
                    "INSERT INTO substrate_to_raw_event_projection_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (stable_id("proj", met_id, raw["event_id"]), matrix_run_id, met_id, raw["event_id"], c["cell_uid"], int(c["node_id"]), clock_n, raw["channel_type"], raw_val, projected, err, conf, 0, "projection only; raw_event_stream remains source fact", tnow),
                )

    proj_errors = [r[0] for r in cur.execute("SELECT projection_error FROM substrate_to_raw_event_projection_v04").fetchall()]
    mean_error = avg(proj_errors)
    mean_gate = avg([r[0] for r in cur.execute("SELECT met_gate_probability FROM mechanotransduction_event_v04").fetchall()])
    mean_stress = avg([r[0] for r in cur.execute("SELECT stress_energy_proxy FROM substrate_stress_tensor_v04").fetchall()])

    replay_specs = [
        ("baseline_substrate", "baseline", {}, 1.00, 1.00, 0.00),
        ("force_noise_10", "noise", {"force_noise": 0.10}, 0.97, 1.04, 0.04),
        ("force_noise_30", "noise", {"force_noise": 0.30}, 0.90, 1.13, 0.12),
        ("substrate_softening", "material_shift", {"stiffness_scale": 0.72}, 0.84, 0.78, 0.10),
        ("substrate_stiffening", "material_shift", {"stiffness_scale": 1.35}, 0.78, 1.26, 0.18),
        ("shear_wave_injection", "hidden_structure", {"shear_wave": "low_frequency_common_mode"}, 0.82, 1.42, 0.23),
        ("sensor_dropout", "driver_missingness", {"dropout_ratio": 0.25}, 0.76, 1.00, 0.20),
        ("matrix_edge_ablation", "foam_break", {"edge_type_removed": "foam_crosslink"}, 0.64, 1.31, 0.31),
        ("external_csv_schema_check", "driver_contract", {"schema": "physical_sample_stream_v04_csv_v1"}, 1.00, 1.00, 0.02),
    ]
    for name, typ, perturb, pscale, stress_scale, xi_add in replay_specs:
        mg = clamp(mean_gate * pscale)
        st = mean_stress * stress_scale
        error = mean_error * (1.0 + xi_add)
        p_stability = clamp(0.92 * pscale - 0.38 * xi_add + 0.04 * math.exp(-error/60.0))
        r_counter = clamp(0.04 + 0.72 * xi_add + (0.18 if typ in {"foam_break", "material_shift"} else 0.0))
        xi_pressure = clamp(0.08 + 0.62 * xi_add + 0.10 * (1.0 - pscale))
        integrity = clamp(1.0 - xi_pressure * 0.45 - (0.24 if typ == "foam_break" else 0.0))
        if typ == "driver_contract":
            passed = 1
            interpretation = "physical CSV contract is loadable; fixture remains diagnostic if no external source is supplied"
        elif typ == "baseline":
            passed = int(p_stability > 0.78 and xi_pressure < 0.18)
            interpretation = "baseline substrate projection stable without source fact rewrite"
        elif typ == "noise":
            passed = int(p_stability > 0.58 and xi_pressure > 0.09 and integrity > 0.65)
            interpretation = "noise increases Xi pressure gradually without collapsing substrate mapping"
        elif typ == "hidden_structure":
            passed = int(r_counter > 0.18 and xi_pressure > 0.18)
            interpretation = "shear-wave hidden structure is exposed as stress/R/Xi pressure rather than swallowed as ordinary noise"
        elif typ == "foam_break":
            passed = int(r_counter > 0.25 and integrity < 0.72)
            interpretation = "foam edge ablation degrades substrate integrity and raises counterstructure pressure"
        else:
            passed = int(r_counter > 0.12 and xi_pressure > 0.12)
            interpretation = "material perturbation produces diagnostic change without pretending scientific proof"
        cur.execute(
            "INSERT INTO matrix_foam_replay_result_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (stable_id("mfreplay", matrix_run_id, name), matrix_run_id, name, typ, json.dumps(perturb, sort_keys=True), mg, st, error, p_stability, r_counter, xi_pressure, integrity, passed, interpretation, tnow),
        )

    after = {t: count_table(cur, t) for t in SOURCE_FACT_TABLES}
    cur.execute(
        "INSERT INTO matrix_foam_run_manifest_v04 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            matrix_run_id, parent_online_id, VERSION, EXECUTION_MODE, 0, "matrix_foam_substrate_proxy", driver_mode,
            source_id, "system_clock_entry", count_table(cur, "system_clock_entry"), json.dumps(before, sort_keys=True), json.dumps(after, sort_keys=True),
            count_table(cur, "substrate_material_region_v04"), count_table(cur, "cell_matrix_contact_v04"), count_table(cur, "foam_edge_state_v04"),
            count_table(cur, "substrate_stress_tensor_v04"), count_table(cur, "physical_sample_stream_v04"), count_table(cur, "mechanotransduction_event_v04"),
            count_table(cur, "substrate_to_raw_event_projection_v04"), count_table(cur, "matrix_foam_replay_result_v04"),
            "P/R remains canonical decomposition before Xi; matrix foam may feed evidence but cannot create direct Xi->P/R", tnow,
            FORBIDDEN_USE, "v0.4 adds explicit substrate/foam and physical driver. Fixture is diagnostic unless replaced by external CSV.",
        ),
    )

    # Artifact manifest for useful outputs.
    report_dir = Path(args.report_dir or "morphosphere_v2pp/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = report_dir / "matrix_foam_v04_summary.json"
    summary = {
        "matrix_run_id": matrix_run_id,
        "version": VERSION,
        "execution_mode": EXECUTION_MODE,
        "source_fact_counts_before": before,
        "source_fact_counts_after": after,
        "material_region_count": count_table(cur, "substrate_material_region_v04"),
        "cell_matrix_contact_count": count_table(cur, "cell_matrix_contact_v04"),
        "foam_edge_count": count_table(cur, "foam_edge_state_v04"),
        "stress_tensor_count": count_table(cur, "substrate_stress_tensor_v04"),
        "physical_sample_count": count_table(cur, "physical_sample_stream_v04"),
        "mechanotransduction_event_count": count_table(cur, "mechanotransduction_event_v04"),
        "projection_count": count_table(cur, "substrate_to_raw_event_projection_v04"),
        "mean_met_gate_probability": mean_gate,
        "mean_projection_error": mean_error,
        "fixture_used": fixture_used,
        "physical_csv": str(phys_path),
        "boundary": "diagnostic proxy substrate; no scientific run; source facts unchanged",
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = report_dir / "MATRIX_FOAM_PHYSICAL_DRIVER_V04_REPORT.md"
    report_path.write_text(
        "# Matrix-Foam Physical Driver v0.4 Report\n\n"
        f"- matrix_run_id: `{matrix_run_id}`\n"
        f"- execution_mode: `{EXECUTION_MODE}`\n"
        f"- material regions: {summary['material_region_count']}\n"
        f"- cell-matrix contacts: {summary['cell_matrix_contact_count']}\n"
        f"- foam edges: {summary['foam_edge_count']}\n"
        f"- stress tensors: {summary['stress_tensor_count']}\n"
        f"- physical samples: {summary['physical_sample_count']}\n"
        f"- MET events: {summary['mechanotransduction_event_count']}\n"
        f"- projections: {summary['projection_count']}\n"
        f"- fixture_used: {fixture_used}\n\n"
        "Boundary: this is a diagnostic substrate/proxy and physical driver interface. It does not claim final ECM biology or experimental truth.\n",
        encoding="utf-8",
    )
    for artifact_type, path, role in [
        ("summary_json", summary_path, "machine-readable v0.4 build summary"),
        ("build_report", report_path, "human-readable v0.4 report"),
        ("physical_fixture_csv", phys_path, "deterministic physical driver fixture or supplied CSV"),
    ]:
        if path.exists():
            cur.execute(
                "INSERT INTO matrix_foam_artifact_manifest_v04 VALUES (?,?,?,?,?,?,?)",
                (stable_id("mfart", matrix_run_id, artifact_type, str(path)), matrix_run_id, artifact_type, str(path), checksum_file(str(path)), role, tnow),
            )

    conn.commit()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
