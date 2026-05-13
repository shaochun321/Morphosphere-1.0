"""Legacy V2 state adapter entrypoints.

These functions are intentionally thin wrappers around the mainline physical
contract. They keep future V2 imports from leaking into the mainline package and
make all conversions explicit.
"""

from __future__ import annotations

from ..physical_cell_graph_state import (
    CellGraphStateRecord,
    PhysicalCellGraphState,
    from_cell_graph_state_record,
    to_cell_graph_state_record,
)


legacy_record_to_physical = from_cell_graph_state_record
physical_to_legacy_record = to_cell_graph_state_record


__all__ = [
    "CellGraphStateRecord",
    "PhysicalCellGraphState",
    "legacy_record_to_physical",
    "physical_to_legacy_record",
]
