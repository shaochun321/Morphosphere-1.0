"""Physical cell graph source-of-truth contract for mainline stage-1.

This module makes the stage-1 boundary explicit after mainline convergence:

* :class:`PhysicalCellGraphState` is the authoritative physical state used by
  mechanical and electrophysiology dynamics.
* :class:`CellGraphStateRecord` is the pydantic/JSON-facing record imported
  from ``cell_graph_state.py``. It is a serialization/interface view, not the
  mutable physical source-of-truth for dynamics.
* ``SpacetimeCell`` rows in the V8.5 diagnostic database are downstream
  runtime records, not physical cells.

The implementation intentionally aliases the existing V2-derived dataclass so
existing dynamics remain stable while downstream code gets an unambiguous name.
"""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from .v2_dataclass import CellGraphState as PhysicalCellGraphState
from .cell_graph_state import CellGraphState as CellGraphStateRecord
from .types import ContactGraph


MAINLINE_PHYSICAL_SOURCE_OF_TRUTH = "PhysicalCellGraphState"
DERIVED_RUNTIME_CELL_KIND = "spacetime_cell"


def physical_cell_count(state: PhysicalCellGraphState | CellGraphStateRecord | Any) -> int:
    """Return the count of physical cells represented by a stage-1 state."""
    if hasattr(state, "num_cells"):
        value = getattr(state, "num_cells")
        return int(value() if callable(value) else value)
    positions = getattr(state, "positions", None)
    if positions is None:
        return 0
    return int(np.asarray(positions).shape[0])


def spacetime_cell_count(*, physical_cells: int, window_count: int) -> int:
    """Return derived diagnostic spacetime-cell count.

    This helper exists to prevent code from reusing ``cell_count`` ambiguously
    in manifests and reports.
    """
    return int(physical_cells) * int(window_count)


def to_cell_graph_state_record(
    state: PhysicalCellGraphState,
    *,
    run_id: str | None = None,
) -> CellGraphStateRecord:
    """Convert the physical dataclass into the existing pydantic row model.

    The record is suitable for importers, patch builders, JSON rows, and the
    diagnostic runner. It deliberately carries only the row-facing fields.
    """
    return CellGraphStateRecord(
        clock_n=int(state.clock_n),
        run_id=run_id if run_id is not None else state.run_id,
        num_cells=state.num_cells,
        positions=state.positions.tolist(),
        velocities=state.velocities.tolist(),
        radii=state.radii.tolist(),
        active_flags=np.ones(state.num_cells, dtype=bool).tolist(),
        v_hair_cell=state.V_hair_cell.tolist() if state.V_hair_cell.size else [],
        calcium_concentration=state.calcium.tolist() if state.calcium.size else [],
        v_afferent=state.V_afferent.tolist() if state.V_afferent.size else [],
        met_open_probability=(
            state.met_open_probability.tolist() if state.met_open_probability.size else []
        ),
        neurotransmitter_release_rate=(
            state.release_rate.tolist() if state.release_rate.size else []
        ),
        provenance_hash=state.provenance_hash(),
    )


def from_cell_graph_state_record(record: CellGraphStateRecord) -> PhysicalCellGraphState:
    """Create a physical source-of-truth dataclass from a row/interface record.

    Missing physical fields are initialized conservatively so dynamics can be
    run after callers add or compute topology/masses as needed.
    """
    positions = np.asarray(record.positions if record.positions is not None else [], dtype=float)
    if positions.size == 0:
        positions = np.empty((0, 3), dtype=float)
    positions = positions.reshape((-1, 3))
    n = positions.shape[0]

    velocities = np.asarray(
        record.velocities if record.velocities is not None else np.zeros((n, 3)),
        dtype=float,
    ).reshape((n, 3))
    radii = np.asarray(record.radii if record.radii is not None else np.ones(n), dtype=float)
    masses = np.ones(n, dtype=float)
    active = np.asarray(
        record.active_flags if record.active_flags is not None else np.ones(n, dtype=bool),
        dtype=bool,
    )

    state = PhysicalCellGraphState(
        clock_n=int(record.clock_n),
        time=0.0,
        run_id=record.run_id,
        positions=positions,
        velocities=velocities,
        radii=radii,
        masses=masses,
        is_surface=active,
        radial_band_index=np.zeros(n, dtype=np.int64),
        contact_graph=ContactGraph(
            edges=np.empty((0, 2), dtype=np.int64),
            rest_lengths=np.empty(0, dtype=float),
            edge_types=np.empty(0, dtype=np.int64),
        ),
    )
    state.initialize_electrophysiology()

    def _assign(name: str, values: list[float]) -> None:
        if values:
            arr = np.asarray(values, dtype=float)
            if arr.shape == (n,):
                setattr(state, name, arr)

    _assign("V_hair_cell", record.v_hair_cell)
    _assign("calcium", record.calcium_concentration)
    _assign("V_afferent", record.v_afferent)
    _assign("met_open_probability", record.met_open_probability)
    _assign("release_rate", record.neurotransmitter_release_rate)
    return state


def manifest_count_fields(*, physical_cells: int, window_count: int) -> dict[str, int]:
    """Canonical manifest count fields for diagnostic and mainline reports."""
    return {
        "physical_cell_count": int(physical_cells),
        "window_count": int(window_count),
        "spacetime_cell_count": spacetime_cell_count(
            physical_cells=physical_cells,
            window_count=window_count,
        ),
    }


__all__ = [
    "CellGraphStateRecord",
    "PhysicalCellGraphState",
    "MAINLINE_PHYSICAL_SOURCE_OF_TRUTH",
    "DERIVED_RUNTIME_CELL_KIND",
    "physical_cell_count",
    "spacetime_cell_count",
    "manifest_count_fields",
    "to_cell_graph_state_record",
    "from_cell_graph_state_record",
]
