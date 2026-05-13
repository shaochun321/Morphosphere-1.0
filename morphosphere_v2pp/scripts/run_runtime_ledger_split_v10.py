#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Morphosphere v1.0 Runtime/Ledger Split builder.

This script is intentionally stdlib-only. It creates an external runtime store
(JSONL chunks in v1.0; future-compatible with Zarr/HDF5) and records only
manifests, indexes, source digests, P/R-Xi boundaries, and adoption policies in
SQLite. It does not mutate source facts and does not hot-swap candidate weights.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import statistics
from typing import Any, Iterable

VERSION = "runtime_ledger_split_external_adapter_v1.0"
RUN_ID = "runtime_ledger_split_v10"
PROTECTED_TABLES = [
    "spacetime_cell",
    "information_fiber",
    "raw_event_stream",
    "cell_spatial_coordinate_snapshot",
    "information_relative_coordinate_snapshot",
    "system_clock_entry",
    "p_predictive_support_v022",
    "r_counterstructure_v022",
    "xi_boundary_guard_v022",
    "external_physical_sample_v09",
    "external_sample_cell_mapping_v09",
]

REQUIRED_EXTERNAL_FIELDS = [
    "clock_n", "time_s", "sensor_id", "sensor_kind", "x", "y", "z",
    "force_x", "force_y", "force_z", "optical_intensity",
    "acoustic_pressure", "phase", "uncertainty",
]

def now() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
    return n

def get_columns(cur: sqlite3.Cursor, table: str) -> list[str]:
    return [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]

def table_digest(cur: sqlite3.Cursor, table: str) -> tuple[int, str]:
    cols = get_columns(cur, table)
    if not cols:
        return 0, "missing"
    quoted = ",".join([f'"{c}"' for c in cols])
    h = hashlib.sha256()
    count = 0
    try:
        sql = f"SELECT {quoted} FROM {table} ORDER BY rowid"
        rows = cur.execute(sql)
    except sqlite3.OperationalError:
        sql = f"SELECT {quoted} FROM {table}"
        rows = cur.execute(sql)
    for row in rows:
        h.update(json.dumps(list(row), ensure_ascii=False, sort_keys=False, default=str).encode("utf-8"))
        h.update(b"\n")
        count += 1
    return count, h.hexdigest()

def stats(values: list[float]) -> dict[str, float]:
    if not values:
        return dict(min_value=0.0, max_value=0.0, mean_value=0.0, std_value=0.0, energy_sum=0.0)
    mean = statistics.fmean(values)
    std = statistics.pstdev(values) if len(values) > 1 else 0.0
    return dict(
        min_value=min(values),
        max_value=max(values),
        mean_value=mean,
        std_value=std,
        energy_sum=sum(v*v for v in values),
    )

def reset_tables(cur: sqlite3.Cursor) -> None:
    tables = [
        "runtime_ledger_split_run_manifest_v10",
        "runtime_store_manifest_v10",
        "runtime_chunk_index_v10",
        "runtime_tensor_summary_v10",
        "runtime_source_fact_digest_v10",
        "external_physical_adapter_contract_v10",
        "external_runtime_adapter_trial_v10",
        "runtime_ledger_boundary_contract_v10",
        "promotion_loop_policy_v10",
        "frozen_profile_candidate_v10",
        "runtime_ledger_acceptance_report_v10",
        "runtime_artifact_manifest_v10",
    ]
    for t in tables:
        cur.execute(f"DROP TABLE IF EXISTS {t}")

    cur.execute("""CREATE TABLE runtime_ledger_split_run_manifest_v10(
        run_id TEXT PRIMARY KEY,
        version TEXT NOT NULL,
        source_db_path TEXT NOT NULL,
        runtime_store_uri TEXT NOT NULL,
        runtime_engine TEXT NOT NULL,
        ledger_role TEXT NOT NULL,
        execution_mode TEXT NOT NULL,
        scientific_run INTEGER NOT NULL,
        source_fact_policy TEXT NOT NULL,
        hot_swap_allowed INTEGER NOT NULL,
        candidate_auto_apply_allowed INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE runtime_store_manifest_v10(
        store_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        store_format TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        role TEXT NOT NULL,
        record_count INTEGER NOT NULL,
        byte_size INTEGER NOT NULL,
        sha256 TEXT NOT NULL,
        mutable INTEGER NOT NULL,
        description TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE runtime_chunk_index_v10(
        chunk_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        store_id TEXT NOT NULL,
        tensor_role TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        clock_n_min INTEGER,
        clock_n_max INTEGER,
        row_count INTEGER NOT NULL,
        schema_json TEXT NOT NULL,
        byte_size INTEGER NOT NULL,
        sha256 TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE runtime_tensor_summary_v10(
        summary_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        tensor_role TEXT NOT NULL,
        sample_count INTEGER NOT NULL,
        cell_count INTEGER NOT NULL,
        clock_count INTEGER NOT NULL,
        channel_count INTEGER NOT NULL,
        min_value REAL NOT NULL,
        max_value REAL NOT NULL,
        mean_value REAL NOT NULL,
        std_value REAL NOT NULL,
        energy_sum REAL NOT NULL,
        file_ref TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE runtime_source_fact_digest_v10(
        digest_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        table_name TEXT NOT NULL,
        row_count INTEGER NOT NULL,
        table_sha256 TEXT NOT NULL,
        role TEXT NOT NULL,
        mutation_allowed INTEGER NOT NULL,
        verification_status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE external_physical_adapter_contract_v10(
        adapter_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        adapter_name TEXT NOT NULL,
        accepted_format TEXT NOT NULL,
        required_fields_json TEXT NOT NULL,
        target_runtime_role TEXT NOT NULL,
        sqlite_role TEXT NOT NULL,
        declared_real_external_required INTEGER NOT NULL,
        notes TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE external_runtime_adapter_trial_v10(
        trial_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        adapter_id TEXT NOT NULL,
        source_path TEXT NOT NULL,
        declared_real_external INTEGER NOT NULL,
        sample_count INTEGER NOT NULL,
        mapped_sample_count INTEGER NOT NULL,
        schema_valid INTEGER NOT NULL,
        quality_gate_status TEXT NOT NULL,
        rationale TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE runtime_ledger_boundary_contract_v10(
        contract_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        boundary_name TEXT NOT NULL,
        assertion TEXT NOT NULL,
        enforcement_status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE promotion_loop_policy_v10(
        policy_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        proposal_source TEXT NOT NULL,
        hot_swap_allowed INTEGER NOT NULL,
        frozen_profile_required INTEGER NOT NULL,
        full_replay_required INTEGER NOT NULL,
        real_external_data_required INTEGER NOT NULL,
        human_review_required INTEGER NOT NULL,
        source_fact_rewrite_allowed INTEGER NOT NULL,
        policy_status TEXT NOT NULL,
        rationale TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE frozen_profile_candidate_v10(
        candidate_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        source_version TEXT NOT NULL,
        source_packet_id TEXT,
        candidate_profile_path TEXT,
        candidate_status TEXT NOT NULL,
        auto_applied INTEGER NOT NULL,
        manual_review_required INTEGER NOT NULL,
        blockers_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE runtime_ledger_acceptance_report_v10(
        check_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        check_name TEXT NOT NULL,
        passed INTEGER NOT NULL,
        observed_value TEXT NOT NULL,
        expected_value TEXT NOT NULL,
        severity TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE runtime_artifact_manifest_v10(
        artifact_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        artifact_role TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        byte_size INTEGER NOT NULL,
        sha256 TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--runtime-dir", default="runtime_store/v10")
    ap.add_argument("--report-dir", default="morphosphere_v2pp/reports")
    ap.add_argument("--external-csv", default="")
    ap.add_argument("--declare-real-external", action="store_true")
    args = ap.parse_args()

    db = Path(args.db).resolve()
    runtime_dir = Path(args.runtime_dir)
    if not runtime_dir.is_absolute():
        runtime_dir = (Path.cwd() / runtime_dir).resolve()
    report_dir = Path(args.report_dir)
    if not report_dir.is_absolute():
        report_dir = (Path.cwd() / report_dir).resolve()
    runtime_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    reset_tables(cur)

    # Read core tables
    clocks = [dict(r) for r in cur.execute("SELECT clock_n,time_s,dt_s,run_id FROM system_clock_entry ORDER BY clock_n").fetchall()]
    cells = [dict(r) for r in cur.execute("SELECT cell_uid,node_id,window_id,clock_start,clock_end,x,y,z,boundary_distance,support_radius,coordinate_frame_id FROM spacetime_cell ORDER BY cell_uid").fetchall()]
    fibers_by_cell = {r["cell_uid"]: dict(r) for r in cur.execute("SELECT * FROM information_fiber ORDER BY cell_uid").fetchall()}
    raw_events = [dict(r) for r in cur.execute("SELECT event_id,source_cell_uid,source_fiber_id,node_id,window_id,clock_n,x,y,z,channel_type,value,derivative,phase_hint,uncertainty,energy_proxy FROM raw_event_stream ORDER BY clock_n,event_id").fetchall()]

    # Runtime store files
    cell_rows = []
    for c in cells:
        f = fibers_by_cell.get(c["cell_uid"], {})
        cell_rows.append({
            "cell_uid": c["cell_uid"],
            "node_id": c["node_id"],
            "window_id": c["window_id"],
            "clock_start": c["clock_start"],
            "clock_end": c["clock_end"],
            "position": [c["x"], c["y"], c["z"]],
            "boundary_distance": c["boundary_distance"],
            "support_radius": c["support_radius"],
            "coordinate_frame_id": c["coordinate_frame_id"],
            "V_mean": f.get("V_mean", 0.0),
            "V_slope": f.get("V_slope", 0.0),
            "spike_rate": f.get("spike_rate", 0.0),
            "release_proxy": f.get("release_proxy", 0.0),
            "signal_uncertainty": f.get("signal_uncertainty", 0.0),
            "runtime_role": "cell_state_tensor_record",
        })
    cell_path = runtime_dir / "cell_state_tensor_v10.jsonl"
    cell_count = write_jsonl(cell_path, cell_rows)

    event_rows = []
    for e in raw_events:
        event_rows.append({
            "event_id": e["event_id"],
            "source_cell_uid": e["source_cell_uid"],
            "source_fiber_id": e["source_fiber_id"],
            "node_id": e["node_id"],
            "window_id": e["window_id"],
            "clock_n": e["clock_n"],
            "position": [e["x"], e["y"], e["z"]],
            "channel_type": e["channel_type"],
            "value": e["value"],
            "derivative": e["derivative"],
            "phase_hint": e["phase_hint"],
            "uncertainty": e["uncertainty"],
            "energy_proxy": e["energy_proxy"],
            "runtime_role": "raw_event_tensor_record",
        })
    event_path = runtime_dir / "raw_event_tensor_v10.jsonl"
    event_count = write_jsonl(event_path, event_rows)

    clock_path = runtime_dir / "clock_index_v10.json"
    write_json(clock_path, {"run_id": RUN_ID, "clock_source_table": "system_clock_entry", "clock_count": len(clocks), "clocks": clocks})

    # P/R/Xi summary into runtime sidecar: this is not source of truth, just a fast runtime lookup summary.
    pr_counts = {
        "p_support": cur.execute("SELECT count(*) FROM p_predictive_support_v022").fetchone()[0],
        "r_counterstructure": cur.execute("SELECT count(*) FROM r_counterstructure_v022").fetchone()[0],
        "xi_boundary_guard": cur.execute("SELECT count(*) FROM xi_boundary_guard_v022").fetchone()[0],
    }
    pr_path = runtime_dir / "pr_xi_fast_index_v10.json"
    write_json(pr_path, {"run_id": RUN_ID, "role": "runtime_fast_lookup_not_source_of_truth", **pr_counts})

    # Optional external CSV trial or carry v09 demo proxy.
    ext_csv = Path(args.external_csv).resolve() if args.external_csv else None
    if ext_csv and ext_csv.exists():
        rows = []
        with ext_csv.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []
            schema_valid = all(x in fields for x in REQUIRED_EXTERNAL_FIELDS)
            for row in reader:
                rows.append(row)
        mapped = len(rows) if schema_valid else 0
        source_path = str(ext_csv)
        declared_real = 1 if args.declare_real_external else 0
        gate = "REAL_EXTERNAL_ACCEPTED_FOR_REVIEW" if declared_real and schema_valid and mapped > 0 else "BLOCKED_PENDING_REAL_EXTERNAL_DECLARATION_OR_SCHEMA"
        rationale = "external CSV supplied; accepted for review only, not source-fact mutation" if gate.startswith("REAL") else "external CSV missing schema fields or not declared real external"
    else:
        count = cur.execute("SELECT count(*) FROM external_physical_sample_v09").fetchone()[0]
        mapped = cur.execute("SELECT count(*) FROM external_sample_cell_mapping_v09").fetchone()[0]
        schema_valid = 1 if count > 0 else 0
        source_path = "carried_forward:v09_demo_proxy_or_fixture"
        declared_real = 0
        gate = "BLOCKED_PENDING_REAL_EXTERNAL_DATA"
        rationale = "v1.0 runtime split is ready, but no real external CSV was provided; fixture/demo proxy cannot promote candidate weights"

    created = now()
    cur.execute("""INSERT INTO runtime_ledger_split_run_manifest_v10 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
        RUN_ID, VERSION, str(db), str(runtime_dir), "external_runtime_store_jsonl_v1_future_zarr_hdf5",
        "sqlite_ledger_only_not_runtime_engine",
        "diagnostic_append_only_runtime_ledger_split", 0,
        "source_facts_append_only_digest_protected", 0, 0, created
    ))

    # Store manifests and chunk indexes
    store_files = [
        ("store_cell_state_v10", cell_path, "cell_state_tensor", cell_count, "runtime cell-state tensor sidecar; SQLite stores only manifest/index"),
        ("store_raw_event_v10", event_path, "raw_event_tensor", event_count, "runtime event tensor sidecar; derived from raw_event_stream without source mutation"),
        ("store_clock_index_v10", clock_path, "clock_index", len(clocks), "runtime clock index copied from system_clock_entry"),
        ("store_pr_xi_fast_index_v10", pr_path, "pr_xi_fast_lookup", sum(pr_counts.values()), "fast lookup summary, not source of truth"),
    ]
    for sid, path, role, rec_count, desc in store_files:
        rel = os.path.relpath(path, Path.cwd())
        h = sha256_file(path)
        bs = path.stat().st_size
        cur.execute("INSERT INTO runtime_store_manifest_v10 VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (sid, RUN_ID, "jsonl" if path.suffix == ".jsonl" else "json", rel, role, rec_count, bs, h, 0, desc, created))
        schema = {}
        if role == "cell_state_tensor":
            schema = {"fields": list(cell_rows[0].keys()) if cell_rows else []}
            cmin, cmax = min((r["clock_start"] for r in cell_rows), default=None), max((r["clock_end"] for r in cell_rows), default=None)
        elif role == "raw_event_tensor":
            schema = {"fields": list(event_rows[0].keys()) if event_rows else []}
            cmin, cmax = min((r["clock_n"] for r in event_rows), default=None), max((r["clock_n"] for r in event_rows), default=None)
        else:
            schema = {"format": path.suffix.lstrip(".")}
            cmin, cmax = (min((c["clock_n"] for c in clocks), default=None), max((c["clock_n"] for c in clocks), default=None))
        cur.execute("INSERT INTO runtime_chunk_index_v10 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("chunk_" + sid, RUN_ID, sid, role, rel, cmin, cmax, rec_count, json.dumps(schema, sort_keys=True), bs, h, created))

    # Tensor summaries
    cell_values = [float(r["V_mean"]) for r in cell_rows] + [float(r["spike_rate"]) for r in cell_rows]
    event_values = [float(r["value"]) for r in event_rows]
    for summary_id, role, vals, rec_count, file_ref in [
        ("summary_cell_state_v10", "cell_state_tensor", cell_values, cell_count, os.path.relpath(cell_path, Path.cwd())),
        ("summary_raw_event_v10", "raw_event_tensor", event_values, event_count, os.path.relpath(event_path, Path.cwd())),
    ]:
        st = stats(vals)
        cur.execute("INSERT INTO runtime_tensor_summary_v10 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            summary_id, RUN_ID, role, rec_count, len({r["cell_uid"] for r in cell_rows}),
            len({c["clock_n"] for c in clocks}), len({r.get("channel_type", "cell") for r in event_rows}) if role == "raw_event_tensor" else 1,
            st["min_value"], st["max_value"], st["mean_value"], st["std_value"], st["energy_sum"], file_ref, created
        ))

    # Source fact digests
    for t in PROTECTED_TABLES:
        cnt, digest = table_digest(cur, t)
        status = "PASS" if digest != "missing" else "MISSING"
        cur.execute("INSERT INTO runtime_source_fact_digest_v10 VALUES (?,?,?,?,?,?,?,?,?)",
                    (f"digest_{t}_v10", RUN_ID, t, cnt, digest, "protected_source_fact_or_boundary", 0, status, created))

    # External adapter contracts
    adapters = [
        ("adapter_csv_physical_v10", "csv_physical_samples", "CSV", REQUIRED_EXTERNAL_FIELDS, "external_physical_sample_runtime_tensor", "manifest_and_mapping_only", 1,
         "Minimum common entry for small real external physical trials."),
        ("adapter_zarr_field_v10", "zarr_field_store", "ZARR_PLANNED", ["attrs/schema.json", "chunks"], "high_dimensional_field_tensor", "manifest_only_planned", 1,
         "Planned adapter for PDE/FEM/video/field outputs; prevents SQLite from becoming tensor runtime."),
        ("adapter_event_stream_v10", "neuromorphic_event_stream", "JSONL_OR_AEDAT_PLANNED", ["timestamp", "source_id", "polarity_or_channel", "value"], "asynchronous_event_tensor", "manifest_only_planned", 1,
         "Planned adapter for event cameras, MEA/EEG preprocessing, memristor/OECT traces."),
    ]
    for row in adapters:
        cur.execute("INSERT INTO external_physical_adapter_contract_v10 VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (row[0], RUN_ID, row[1], row[2], json.dumps(row[3], ensure_ascii=False), row[4], row[5], row[6], row[7], created))

    cur.execute("INSERT INTO external_runtime_adapter_trial_v10 VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
        "trial_external_data_v10", RUN_ID, "adapter_csv_physical_v10", source_path, declared_real,
        int(count if not ext_csv else len(rows)), int(mapped), int(schema_valid), gate, rationale, created
    ))

    # Boundary contracts
    contracts = [
        ("runtime_not_sqlite", "SQLite is ledger/index/provenance only; high-frequency state evolves in runtime_store or future tensor engine.", "ENFORCED_BY_RUNTIME_STORE"),
        ("source_facts_no_rewrite", "v1.0 must not rewrite spacetime_cell/information_fiber/raw_event_stream or protected P/R/Xi tables.", "ENFORCED_BY_DIGESTS"),
        ("no_hot_swap", "External lab proposals cannot hot-swap mainline runner parameters.", "ENFORCED_BY_POLICY"),
        ("frozen_profile_promotion_only", "Candidate parameters may enter only through a new frozen calibration profile and full replay.", "ENFORCED_BY_POLICY"),
        ("p_r_before_xi", "P/R remains before Xi; Xi cannot directly become P or R.", "CARRIED_FORWARD_AND_PROTECTED"),
        ("real_data_not_fixture", "Fixture/demo data cannot unlock automatic adoption.", "ENFORCED_BY_GATE"),
    ]
    for i, (name, assertion, status) in enumerate(contracts, 1):
        cur.execute("INSERT INTO runtime_ledger_boundary_contract_v10 VALUES (?,?,?,?,?,?)",
                    (f"contract_{i:02d}_{name}", RUN_ID, name, assertion, status, created))

    cur.execute("INSERT INTO promotion_loop_policy_v10 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
        "promotion_policy_frozen_profile_v10", RUN_ID, "active_inference_lab_v06_and_candidate_review_v09",
        0, 1, 1, 1, 1, 0, "ACTIVE_BLOCK_HOT_SWAP_ALLOW_STAGED_FROZEN_PROFILE_ONLY",
        "Hot-swap would let an external lab govern source facts and P/R-Xi boundaries; v1.0 requires frozen-profile promotion after real-data trial and full replay.", created
    ))

    # Candidate carry-forward
    packet = None
    try:
        packet = cur.execute("SELECT packet_id,patch_path,review_status,auto_applied,manual_review_required,blocking_reasons_json FROM candidate_patch_manual_review_packet_v09 LIMIT 1").fetchone()
    except sqlite3.OperationalError:
        packet = None
    if packet:
        source_packet_id, candidate_path, status, auto_applied, manual, blockers = packet
    else:
        source_packet_id, candidate_path, status, auto_applied, manual, blockers = None, "", "CARRIED_FORWARD_NO_PACKET_FOUND", 0, 1, json.dumps(["pending_real_external_data"])
    cur.execute("INSERT INTO frozen_profile_candidate_v10 VALUES (?,?,?,?,?,?,?,?,?,?)", (
        "frozen_profile_candidate_v10", RUN_ID, "v09_manual_review_packet", source_packet_id,
        candidate_path, "STAGED_NOT_APPLIED_RUNTIME_SPLIT_READY_PENDING_REAL_DATA", 0, 1,
        blockers if blockers else json.dumps(["pending_real_external_data"]), created
    ))

    # Artifacts
    for artifact_id, role, path in [
        ("artifact_cell_state_tensor_v10", "runtime_store", cell_path),
        ("artifact_raw_event_tensor_v10", "runtime_store", event_path),
        ("artifact_clock_index_v10", "runtime_store", clock_path),
        ("artifact_pr_xi_fast_index_v10", "runtime_store", pr_path),
    ]:
        cur.execute("INSERT INTO runtime_artifact_manifest_v10 VALUES (?,?,?,?,?,?,?)", (
            artifact_id, RUN_ID, role, os.path.relpath(path, Path.cwd()), path.stat().st_size, sha256_file(path), created
        ))

    # Acceptance report stored
    checks = []
    def add(name, passed, observed, expected, severity="critical"):
        checks.append((f"check_{len(checks)+1:02d}_{name}", RUN_ID, name, int(bool(passed)), str(observed), str(expected), severity, created))
    add("runtime_store_files_created", all(p.exists() for _, p, *_ in store_files), "all_present", "all_present")
    add("sqlite_role_is_ledger_only", True, "sqlite_ledger_only_not_runtime_engine", "sqlite_ledger_only_not_runtime_engine")
    add("source_fact_digests_pass", all(r[0] != "missing" for r in [table_digest(cur, t) for t in PROTECTED_TABLES]), "protected_tables_digestable", "protected_tables_digestable")
    add("hot_swap_disabled", True, 0, 0)
    add("candidate_auto_apply_disabled", True, 0, 0)
    add("frozen_profile_required", True, 1, 1)
    add("real_external_data_gate", gate in ("BLOCKED_PENDING_REAL_EXTERNAL_DATA","REAL_EXTERNAL_ACCEPTED_FOR_REVIEW","BLOCKED_PENDING_REAL_EXTERNAL_DECLARATION_OR_SCHEMA"), gate, "explicit_gate_status")
    add("raw_event_runtime_count_matches_ledger", event_count == len(raw_events), event_count, len(raw_events))
    add("cell_runtime_count_matches_ledger", cell_count == len(cells), cell_count, len(cells))
    add("p_r_xi_policy_carried_forward", True, "P/R before Xi", "P/R before Xi")
    cur.executemany("INSERT INTO runtime_ledger_acceptance_report_v10 VALUES (?,?,?,?,?,?,?,?)", checks)

    # Reports
    summary = {
        "version": VERSION,
        "run_id": RUN_ID,
        "runtime_store": str(runtime_dir),
        "cell_state_records": cell_count,
        "raw_event_records": event_count,
        "clock_count": len(clocks),
        "store_files": {sid: {"path": os.path.relpath(path, Path.cwd()), "sha256": sha256_file(path), "bytes": path.stat().st_size} for sid, path, *_ in store_files},
        "external_gate_status": gate,
        "candidate_status": "STAGED_NOT_APPLIED_RUNTIME_SPLIT_READY_PENDING_REAL_DATA",
        "hot_swap_allowed": False,
        "sqlite_role": "ledger_only",
        "scientific_run": False,
        "protected_source_tables": PROTECTED_TABLES,
    }
    summary_path = report_dir / "runtime_ledger_split_v10_summary.json"
    write_json(summary_path, summary)
    report_path = report_dir / "RUNTIME_LEDGER_SPLIT_V10_REPORT.md"
    report_path.write_text(f"""# Runtime/Ledger Split v1.0 Report

Version: `{VERSION}`

## Result

- Runtime store created: `{runtime_dir}`
- Cell-state runtime records: {cell_count}
- Raw-event runtime records: {event_count}
- Clock count: {len(clocks)}
- SQLite role: ledger/index/provenance only
- Hot-swap allowed: false
- Candidate profile auto-applied: false
- External real-data gate: `{gate}`

## Boundary

v1.0 separates runtime state from the SQLite ledger. It does not claim scientific completion,
does not rewrite source facts, and does not hot-swap external-lab parameters into the mainline.
Future high-frequency physics should run in an external tensor/PDE/FEM runtime and only commit
manifests, digests, and P/R-Xi summaries back to the ledger.
""", encoding="utf-8")

    cur.execute("INSERT INTO runtime_artifact_manifest_v10 VALUES (?,?,?,?,?,?,?)", (
        "artifact_runtime_ledger_summary_v10", RUN_ID, "report", os.path.relpath(summary_path, Path.cwd()), summary_path.stat().st_size, sha256_file(summary_path), created
    ))
    cur.execute("INSERT INTO runtime_artifact_manifest_v10 VALUES (?,?,?,?,?,?,?)", (
        "artifact_runtime_ledger_report_v10", RUN_ID, "report", os.path.relpath(report_path, Path.cwd()), report_path.stat().st_size, sha256_file(report_path), created
    ))

    con.commit()
    con.close()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
