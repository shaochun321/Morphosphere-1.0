# Tags: [CORE_RUNTIME][SOURCE_OF_TRUTH][VERSIONED]
# Role: Sole physical source of truth for the entire system.
# Must Not: Import semantic_readout, archive_access, or semantic_assets.
# Producers: pipeline, integrator
# Consumers: ALL downstream modules (patch_graph, preneural, trajectory, ledger)
"""CellGraphState — the sole source of truth (masterplan §5.1).

CellGraphState X(t) encodes the complete physical state of the cell
aggregate at time t. All downstream representations (PatchAfferentTransmission
Graph, PreNeuralSlice, WindowedTrajectoryField) are derived from or
can be traced back to this state.

Included state variables (masterplan §5.1):
  - Cell/particle geometric state (positions, velocities, radii, masses)
  - Local mechanical state (contact forces, strains)
  - Hair bundle mechano-transduction entry (deflection, adaptation, open prob.)
  - Hair cell continuous membrane state (V_h, gating variables)
  - Ca²⁺ / release state (calcium concentration, vesicle release rate)
  - Afferent excitability state (V_aff, adaptation current, spike history)
  - Contact graph / neighbor graph topology
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import json

import numpy as np

from .types import (
    Float64Array,
    Int64Array,
    BoolArray,
    ContactGraph,
)


@dataclass
class CellGraphState:
    """Complete physical state of the cell aggregate at time t.

    This is the ONLY source of truth in the system.
    All other data structures are views or derivations.

    Attributes marked [GEO] are geometric, [MECH] mechanical,
    [MET] mechanotransduction, [HC] hair cell membrane,
    [REL] release, [AFF] afferent, [TOPO] topological.
    """

    # ── Time (v5 §3.1: clock_n is the canonical time index) ────────────────
    clock_n: int = 0
    time: float = 0.0
    run_id: str = ""

    # ── [GEO] Geometric state ─────────────────────────────────────────────
    positions: Float64Array = field(default_factory=lambda: np.empty((0, 3)))
    velocities: Float64Array = field(default_factory=lambda: np.empty((0, 3)))
    radii: Float64Array = field(default_factory=lambda: np.empty(0))
    masses: Float64Array = field(default_factory=lambda: np.empty(0))
    is_surface: BoolArray = field(default_factory=lambda: np.empty(0, dtype=bool))
    radial_band_index: Int64Array = field(default_factory=lambda: np.empty(0, dtype=np.int64))

    # ── [TOPO] Topology ───────────────────────────────────────────────────
    contact_graph: ContactGraph | None = None
    neighbor_list: list[list[int]] = field(default_factory=list)
    num_radial_bands: int = 4

    # ── [MECH] Mechanical state ───────────────────────────────────────────
    total_forces: Float64Array = field(default_factory=lambda: np.empty((0, 3)))
    local_strain: Float64Array = field(default_factory=lambda: np.empty(0))

    # ── [MET] Mechano-electrical transduction ─────────────────────────────
    bundle_deflection: Float64Array = field(default_factory=lambda: np.empty(0))
    met_adaptation: Float64Array = field(default_factory=lambda: np.empty(0))
    met_open_probability: Float64Array = field(default_factory=lambda: np.empty(0))

    # ── [HC] Hair cell membrane ───────────────────────────────────────────
    V_hair_cell: Float64Array = field(default_factory=lambda: np.empty(0))
    m_gate_ca: Float64Array = field(default_factory=lambda: np.empty(0))
    m_gate_k: Float64Array = field(default_factory=lambda: np.empty(0))
    I_MET: Float64Array = field(default_factory=lambda: np.empty(0))

    # ── [REL] Ca²⁺ / vesicle release ─────────────────────────────────────
    calcium: Float64Array = field(default_factory=lambda: np.empty(0))
    release_rate: Float64Array = field(default_factory=lambda: np.empty(0))

    # ── [AFF] Afferent neuron ─────────────────────────────────────────────
    V_afferent: Float64Array = field(default_factory=lambda: np.empty(0))
    w_adaptation: Float64Array = field(default_factory=lambda: np.empty(0))
    synaptic_conductance: Float64Array = field(default_factory=lambda: np.empty(0))
    spike_times: list[list[float]] = field(default_factory=list)

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def num_cells(self) -> int:
        return self.positions.shape[0]

    @property
    def num_surface_cells(self) -> int:
        return int(np.sum(self.is_surface))

    def validate(self) -> list[str]:
        """Check internal consistency. Returns list of error messages."""
        errors: list[str] = []
        n = self.num_cells
        if n == 0:
            return errors

        def _check(name: str, arr: np.ndarray, expected_shape: tuple[int, ...]) -> None:
            if arr.shape != expected_shape:
                errors.append(f"{name}: expected shape {expected_shape}, got {arr.shape}")

        _check("velocities", self.velocities, (n, 3))
        _check("radii", self.radii, (n,))
        _check("masses", self.masses, (n,))
        _check("is_surface", self.is_surface, (n,))
        _check("radial_band_index", self.radial_band_index, (n,))

        # Electrophysiology arrays may be empty if not yet initialized
        for name, arr in [
            ("bundle_deflection", self.bundle_deflection),
            ("met_adaptation", self.met_adaptation),
            ("met_open_probability", self.met_open_probability),
            ("V_hair_cell", self.V_hair_cell),
            ("calcium", self.calcium),
            ("release_rate", self.release_rate),
            ("V_afferent", self.V_afferent),
        ]:
            if arr.size > 0 and arr.shape != (n,):
                errors.append(f"{name}: expected shape ({n},), got {arr.shape}")

        return errors

    # ── Initialization helpers ────────────────────────────────────────────

    def initialize_electrophysiology(self) -> None:
        """Initialize all electrophysiology arrays to resting state."""
        n = self.num_cells
        self.bundle_deflection = np.zeros(n, dtype=np.float64)
        self.met_adaptation = np.zeros(n, dtype=np.float64)
        self.met_open_probability = np.full(n, 0.05, dtype=np.float64)
        self.V_hair_cell = np.full(n, -65.0, dtype=np.float64)
        self.m_gate_ca = np.zeros(n, dtype=np.float64)
        self.m_gate_k = np.zeros(n, dtype=np.float64)
        self.I_MET = np.zeros(n, dtype=np.float64)
        self.calcium = np.zeros(n, dtype=np.float64)
        self.release_rate = np.zeros(n, dtype=np.float64)
        self.V_afferent = np.full(n, -70.0, dtype=np.float64)
        self.w_adaptation = np.zeros(n, dtype=np.float64)
        self.synaptic_conductance = np.zeros(n, dtype=np.float64)
        self.spike_times = [[] for _ in range(n)]
        self.total_forces = np.zeros((n, 3), dtype=np.float64)
        self.local_strain = np.zeros(n, dtype=np.float64)

    # ── Serialization ────────────────────────────────────────────────────

    def to_snapshot(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible snapshot for ledger storage."""
        return {
            "clock_n": self.clock_n,
            "run_id": self.run_id,
            "time": float(self.time),
            "num_cells": self.num_cells,
            "positions": self.positions.tolist(),
            "velocities": self.velocities.tolist(),
            "V_hair_cell": self.V_hair_cell.tolist() if self.V_hair_cell.size > 0 else [],
            "calcium": self.calcium.tolist() if self.calcium.size > 0 else [],
            "release_rate": self.release_rate.tolist() if self.release_rate.size > 0 else [],
            "V_afferent": self.V_afferent.tolist() if self.V_afferent.size > 0 else [],
            "met_open_probability": self.met_open_probability.tolist() if self.met_open_probability.size > 0 else [],
            "bundle_deflection": self.bundle_deflection.tolist() if self.bundle_deflection.size > 0 else [],
        }

    def provenance_hash(self) -> str:
        """Compute a provenance hash for replay alignment (masterplan §5.2)."""
        h = hashlib.sha256()
        h.update(f"run={self.run_id}".encode())
        h.update(f"n={self.clock_n}".encode())
        h.update(f"t={self.time:.8f}".encode())
        h.update(self.positions.tobytes())
        h.update(self.velocities.tobytes())
        if self.V_hair_cell.size > 0:
            h.update(self.V_hair_cell.tobytes())
        return h.hexdigest()[:16]

    # ── Extraction for downstream layers ──────────────────────────────────

    def extract_mechanical_state(self) -> dict[str, Float64Array]:
        """Extract pure mechanical state for force computation.

        Returns arrays aligned by cell index — no semantic labels.
        """
        center = np.mean(self.positions, axis=0)
        relative_pos = self.positions - center
        radius = np.linalg.norm(relative_pos, axis=1)
        safe_r = np.maximum(radius, 1e-12)
        radial_dir = relative_pos / safe_r[:, None]
        v_radial = np.sum(self.velocities * radial_dir, axis=1)
        v_tangential = self.velocities - radial_dir * v_radial[:, None]
        v_tangential_speed = np.linalg.norm(v_tangential, axis=1)

        return {
            "positions": self.positions,
            "velocities": self.velocities,
            "radii": self.radii,
            "masses": self.masses,
            "relative_positions": relative_pos,
            "radius": radius,
            "radial_direction": radial_dir,
            "radial_velocity": v_radial,
            "tangential_speed": v_tangential_speed,
        }

    def extract_electrophysiology_state(self) -> dict[str, Float64Array]:
        """Extract all electrophysiology variables for analysis.

        No semantic labels — just raw physical quantities.
        """
        return {
            "V_hair_cell": self.V_hair_cell.copy(),
            "met_open_probability": self.met_open_probability.copy(),
            "calcium": self.calcium.copy(),
            "release_rate": self.release_rate.copy(),
            "V_afferent": self.V_afferent.copy(),
            "bundle_deflection": self.bundle_deflection.copy(),
        }
