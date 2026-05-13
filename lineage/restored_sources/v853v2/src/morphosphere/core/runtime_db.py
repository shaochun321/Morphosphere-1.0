# Tags: [CORE_RUNTIME][VERSIONED][LEDGER_ONLY]
# Role: SQLite-based runtime database for persisting all v5 objects.
# Must Not: Import semantic_readout or legacy modules.
# Producers: pipeline.run_loop
# Consumers: ledger, replay_alignment, export
"""Runtime database — SQLite storage for v5 objects (v5 §5).

Provides:
  - Schema creation and migration
  - CRUD for all core objects
  - Schema version tracking
  - Manifest generation
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sqlite3
from datetime import datetime, timezone


SCHEMA_VERSION = "5.0.0a1"

# ── Schema SQL ──────────────────────────────────────────────────────────────

INITIAL_SCHEMA_SQL = """
-- Schema manifest
CREATE TABLE IF NOT EXISTS schema_manifest (
    schema_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    description TEXT DEFAULT ''
);

-- SystemClock state
CREATE TABLE IF NOT EXISTS system_clock (
    clock_n INTEGER PRIMARY KEY,
    dt_seconds REAL NOT NULL,
    run_id TEXT NOT NULL,
    wall_clock_created_at TEXT NOT NULL,
    tick_hash TEXT NOT NULL DEFAULT ''
);

-- Cell graph state snapshots
CREATE TABLE IF NOT EXISTS cell_graph_state (
    clock_n INTEGER NOT NULL,
    run_id TEXT NOT NULL,
    time_seconds REAL NOT NULL,
    num_cells INTEGER NOT NULL,
    state_hash TEXT NOT NULL DEFAULT '',
    snapshot_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (run_id, clock_n)
);

-- Geometry surface
CREATE TABLE IF NOT EXISTS geometry_surface (
    clock_n INTEGER NOT NULL,
    node_id TEXT NOT NULL,
    node_type TEXT NOT NULL DEFAULT 'cell_center',
    x REAL NOT NULL,
    y REAL NOT NULL,
    z REAL NOT NULL,
    normal_x REAL,
    normal_y REAL,
    normal_z REAL,
    support_radius REAL NOT NULL DEFAULT 0.004,
    boundary_distance REAL NOT NULL DEFAULT 0.0,
    source_cell_ids TEXT NOT NULL DEFAULT '[]',
    source_patch_ids TEXT NOT NULL DEFAULT '[]',
    neighbor_ids TEXT NOT NULL DEFAULT '[]',
    provenance_hash TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (clock_n, node_id)
);

-- Signal surface
CREATE TABLE IF NOT EXISTS signal_surface (
    window_id TEXT NOT NULL,
    clock_start INTEGER NOT NULL,
    clock_end INTEGER NOT NULL,
    node_id TEXT NOT NULL,
    V_mean REAL NOT NULL DEFAULT -65.0,
    V_slope REAL NOT NULL DEFAULT 0.0,
    release_proxy REAL NOT NULL DEFAULT 0.0,
    afferent_current REAL NOT NULL DEFAULT 0.0,
    spike_rate REAL NOT NULL DEFAULT 0.0,
    spike_regularity REAL NOT NULL DEFAULT 0.0,
    timing_precision REAL NOT NULL DEFAULT 0.0,
    adaptation_state REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (window_id, node_id)
);

-- Observable surface (O_k)
CREATE TABLE IF NOT EXISTS observable_surface (
    window_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    coherence REAL NOT NULL DEFAULT 0.0,
    bandwidth REAL NOT NULL DEFAULT 0.0,
    contradiction REAL NOT NULL DEFAULT 0.0,
    transport_score REAL NOT NULL DEFAULT 0.0,
    anchor_prior REAL NOT NULL DEFAULT 0.0,
    p_candidate_energy REAL NOT NULL DEFAULT 0.0,
    r_candidate_energy REAL NOT NULL DEFAULT 0.0,
    PRIMARY KEY (window_id, node_id)
);

-- Candidate clusters
CREATE TABLE IF NOT EXISTS candidate_clusters (
    cluster_id TEXT PRIMARY KEY,
    cluster_type TEXT NOT NULL DEFAULT '',
    window_id TEXT NOT NULL DEFAULT '',
    node_members TEXT NOT NULL DEFAULT '[]',
    window_members TEXT NOT NULL DEFAULT '[]',
    support_score REAL NOT NULL DEFAULT 0.0
);

-- P-band records
CREATE TABLE IF NOT EXISTS p_band_record (
    p_id TEXT PRIMARY KEY,
    clock_start INTEGER NOT NULL,
    clock_end INTEGER NOT NULL,
    member_node_ids TEXT NOT NULL DEFAULT '[]',
    member_time_pairs TEXT NOT NULL DEFAULT '[]',
    core_margin_type TEXT NOT NULL DEFAULT '',
    coherence_score REAL NOT NULL DEFAULT 0.0,
    bandwidth_score REAL NOT NULL DEFAULT 0.0,
    replay_support REAL NOT NULL DEFAULT 0.0,
    provenance_support REAL NOT NULL DEFAULT 0.0,
    origin_anchor_id TEXT NOT NULL DEFAULT ''
);

-- R-band records
CREATE TABLE IF NOT EXISTS r_band_record (
    r_id TEXT PRIMARY KEY,
    clock_start INTEGER NOT NULL,
    clock_end INTEGER NOT NULL,
    member_node_ids TEXT NOT NULL DEFAULT '[]',
    member_time_pairs TEXT NOT NULL DEFAULT '[]',
    margin_outer_type TEXT NOT NULL DEFAULT '',
    residual_reason TEXT NOT NULL DEFAULT '',
    routing_target TEXT NOT NULL DEFAULT '',
    upgrade_conditions TEXT NOT NULL DEFAULT '',
    boundary_score REAL NOT NULL DEFAULT 0.0,
    contradiction_score REAL NOT NULL DEFAULT 0.0
);

-- Origin anchor bundle
CREATE TABLE IF NOT EXISTS origin_anchor_bundle (
    origin_id TEXT PRIMARY KEY,
    supporting_p_ids TEXT NOT NULL DEFAULT '[]',
    provenance_rows TEXT NOT NULL DEFAULT '[]',
    temporal_window TEXT NOT NULL DEFAULT '',
    observability_score REAL NOT NULL DEFAULT 0.0,
    stability_score REAL NOT NULL DEFAULT 0.0
);

-- Recursive transition record
CREATE TABLE IF NOT EXISTS recursive_transition_record (
    transition_id TEXT PRIMARY KEY,
    from_stage_k INTEGER NOT NULL,
    to_stage_kplus1 INTEGER NOT NULL,
    t_to_o_summary TEXT NOT NULL DEFAULT '',
    o_to_p_summary TEXT NOT NULL DEFAULT '',
    o_to_r_summary TEXT NOT NULL DEFAULT '',
    p_to_tseed_summary TEXT NOT NULL DEFAULT '',
    triggering_r_ids TEXT NOT NULL DEFAULT '[]'
);

-- T-seed replay packet
CREATE TABLE IF NOT EXISTS t_seed_replay_packet (
    seed_id TEXT PRIMARY KEY,
    source_p_ids TEXT NOT NULL DEFAULT '[]',
    source_r_ids TEXT NOT NULL DEFAULT '[]',
    allowed_drive_envelope TEXT NOT NULL DEFAULT '',
    expected_region TEXT NOT NULL DEFAULT '',
    clock_window TEXT NOT NULL DEFAULT ''
);

-- Ledger entries
CREATE TABLE IF NOT EXISTS ledger_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_index INTEGER NOT NULL,
    clock_n INTEGER NOT NULL,
    time_seconds REAL NOT NULL,
    run_id TEXT NOT NULL DEFAULT '',
    state_hash TEXT NOT NULL DEFAULT '',
    slice_hash TEXT NOT NULL DEFAULT '',
    coherence_score REAL NOT NULL DEFAULT 0.0,
    sparsity_score REAL NOT NULL DEFAULT 0.0,
    p_energy_fraction REAL NOT NULL DEFAULT 0.0,
    r_energy_fraction REAL NOT NULL DEFAULT 0.0,
    shell0_status TEXT NOT NULL DEFAULT 'untested',
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cgs_run_clock ON cell_graph_state(run_id, clock_n);
CREATE INDEX IF NOT EXISTS idx_geo_clock ON geometry_surface(clock_n);
CREATE INDEX IF NOT EXISTS idx_sig_window ON signal_surface(window_id);
CREATE INDEX IF NOT EXISTS idx_ledger_clock ON ledger_entries(clock_n);
CREATE INDEX IF NOT EXISTS idx_ledger_run ON ledger_entries(run_id);
"""


class RuntimeDB:
    """SQLite runtime database for v5 objects.

    Usage:
        db = RuntimeDB.create("path/to/run.db")
        db.insert_clock_tick(clock)
        db.insert_ledger_entry(entry_dict)
        db.close()
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")

    @classmethod
    def create(cls, path: str | Path) -> "RuntimeDB":
        """Create a new runtime database at the given path."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        db = cls(conn)
        db._initialize_schema()
        return db

    @classmethod
    def open(cls, path: str | Path) -> "RuntimeDB":
        """Open an existing runtime database."""
        conn = sqlite3.connect(str(path))
        return cls(conn)

    def _initialize_schema(self) -> None:
        """Create all tables and indexes."""
        self._conn.executescript(INITIAL_SCHEMA_SQL)
        # Record schema version
        self._conn.execute(
            "INSERT INTO schema_manifest (schema_version, created_at, description) VALUES (?, ?, ?)",
            (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat(), "initial schema"),
        )
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    # ── Insert operations ───────────────────────────────────────────────

    def insert_clock_tick(self, clock_dict: dict[str, Any]) -> None:
        """Insert a clock tick record."""
        self._conn.execute(
            "INSERT OR REPLACE INTO system_clock (clock_n, dt_seconds, run_id, wall_clock_created_at, tick_hash) VALUES (?, ?, ?, ?, ?)",
            (clock_dict["clock_n"], clock_dict["dt_seconds"],
             clock_dict["run_id"], clock_dict["wall_clock_created_at"],
             clock_dict.get("tick_hash", "")),
        )
        self._conn.commit()

    def insert_state_snapshot(self, run_id: str, clock_n: int,
                               time_seconds: float, num_cells: int,
                               state_hash: str, snapshot: dict) -> None:
        """Insert a cell graph state snapshot."""
        self._conn.execute(
            "INSERT OR REPLACE INTO cell_graph_state (clock_n, run_id, time_seconds, num_cells, state_hash, snapshot_json) VALUES (?, ?, ?, ?, ?, ?)",
            (clock_n, run_id, time_seconds, num_cells, state_hash,
             json.dumps(snapshot, ensure_ascii=False)),
        )
        self._conn.commit()

    def insert_ledger_entry(self, entry: dict[str, Any]) -> None:
        """Insert a ledger entry."""
        self._conn.execute(
            """INSERT INTO ledger_entries
               (step_index, clock_n, time_seconds, run_id, state_hash, slice_hash,
                coherence_score, sparsity_score, p_energy_fraction, r_energy_fraction,
                shell0_status, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (entry.get("step_index", 0), entry.get("clock_n", 0),
             entry.get("time", 0.0), entry.get("run_id", ""),
             entry.get("state_hash", ""), entry.get("slice_hash", ""),
             entry.get("coherence_score", 0.0), entry.get("sparsity_score", 0.0),
             entry.get("p_energy_fraction", 0.0), entry.get("r_energy_fraction", 0.0),
             entry.get("shell0_status", "untested"),
             json.dumps(entry.get("metadata", {}), ensure_ascii=False)),
        )
        self._conn.commit()

    def insert_geometry_node(self, clock_n: int, node: dict[str, Any]) -> None:
        """Insert a geometry node."""
        xyz = node.get("xyz", [0, 0, 0])
        normal = node.get("local_normal")
        self._conn.execute(
            """INSERT OR REPLACE INTO geometry_surface
               (clock_n, node_id, node_type, x, y, z, normal_x, normal_y, normal_z,
                support_radius, boundary_distance, source_cell_ids, source_patch_ids,
                neighbor_ids, provenance_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (clock_n, node.get("node_id", ""), node.get("node_type", "cell_center"),
             xyz[0], xyz[1], xyz[2],
             normal[0] if normal else None,
             normal[1] if normal else None,
             normal[2] if normal else None,
             node.get("support_radius", 0.004),
             node.get("boundary_distance", 0.0),
             json.dumps(node.get("source_cell_ids", [])),
             json.dumps(node.get("source_patch_ids", [])),
             json.dumps(node.get("neighbor_node_ids", [])),
             node.get("provenance_hash", "")),
        )
        self._conn.commit()

    # ── Query operations ────────────────────────────────────────────────

    def get_schema_version(self) -> str:
        """Get the current schema version."""
        row = self._conn.execute(
            "SELECT schema_version FROM schema_manifest ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else "unknown"

    def get_ledger_entries(self, run_id: str = "") -> list[dict[str, Any]]:
        """Get all ledger entries, optionally filtered by run_id."""
        if run_id:
            rows = self._conn.execute(
                "SELECT * FROM ledger_entries WHERE run_id=? ORDER BY clock_n",
                (run_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM ledger_entries ORDER BY clock_n"
            ).fetchall()
        cols = [desc[0] for desc in self._conn.execute("SELECT * FROM ledger_entries LIMIT 0").description]
        return [dict(zip(cols, row)) for row in rows]

    def get_state_snapshot(self, run_id: str, clock_n: int) -> dict[str, Any] | None:
        """Get a specific state snapshot."""
        row = self._conn.execute(
            "SELECT snapshot_json FROM cell_graph_state WHERE run_id=? AND clock_n=?",
            (run_id, clock_n),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def get_geometry_at_tick(self, clock_n: int) -> list[dict[str, Any]]:
        """Get all geometry nodes at a given tick."""
        rows = self._conn.execute(
            "SELECT * FROM geometry_surface WHERE clock_n=?", (clock_n,)
        ).fetchall()
        cols = [desc[0] for desc in self._conn.execute("SELECT * FROM geometry_surface LIMIT 0").description]
        return [dict(zip(cols, row)) for row in rows]

    def manifest(self) -> dict[str, Any]:
        """Generate a storage manifest."""
        counts = {}
        for table in ["system_clock", "cell_graph_state", "geometry_surface",
                       "signal_surface", "observable_surface", "candidate_clusters",
                       "p_band_record", "r_band_record", "origin_anchor_bundle",
                       "recursive_transition_record", "t_seed_replay_packet",
                       "ledger_entries"]:
            row = self._conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = row[0] if row else 0
        return {
            "schema_version": self.get_schema_version(),
            "table_counts": counts,
        }
