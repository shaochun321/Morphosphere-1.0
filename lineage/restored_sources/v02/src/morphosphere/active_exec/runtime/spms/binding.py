"""V8.5 P3: Spacetime-Fiber Binding — interpretive constraint for SPMS.

V8.5 §8: SPMS can store spacetime and fiber separately, but they are
interpretively inseparable. spacetime_fiber_binding records the
co-generation relationship between spacetime coordinates and information fibers.

Hard rules (V8.5 §8.4):
  1. P/R/Xi candidates must reference at least one binding.
  2. transport_current must reference bindings on both endpoints.
  3. occupancy_measure must declare its (k, K) and binding scope.
  4. relation ledger records must declare subject/object binding scope.
  5. External research modules cannot write mainline bindings.
"""
import hashlib
import json
import uuid
from typing import Any, List, Optional

from pydantic import BaseModel, Field


BINDING_TYPES = [
    "direct",      # Direct measurement → cell + fiber
    "aggregated",  # Multiple sources aggregated
    "proxy",       # Proxy-filled binding
    "inferred",    # Inferred from indirect evidence
]


class SpacetimeFiberBinding(BaseModel):
    """V8.5 §8.2: Minimal spacetime-fiber binding record.

    Records the co-generation relationship between a spacetime cell
    and its information fiber. This is NOT just a join table — it is
    an interpretive constraint.
    """
    binding_id: str = Field(..., description="Unique binding ID")
    run_id: str = Field(...)
    clock_n: int = Field(default=0, description="Clock tick")
    window_id: str = Field(..., description="Analysis window ID")
    spacetime_cell_id: str = Field(..., description="Reference to spacetime_cell")
    information_fiber_id: str = Field(..., description="Reference to information_fiber")
    source_cell_ids_json: str = Field(default="[]", description="Source cell identifiers")
    source_patch_ids_json: str = Field(default="[]", description="Source patch identifiers")
    binding_type: str = Field(default="direct", description="direct/aggregated/proxy/inferred")
    proxy_provenance_id: Optional[str] = Field(default=None, description="Proxy provenance if type=proxy")
    calibration_profile: str = Field(default="default_v83")
    provenance_hash: str = Field(default="")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SpacetimeFiberBinding":
        return cls.model_validate(row)

    @staticmethod
    def generate_id(run_id: str, cell_uid: str, fiber_id: str) -> str:
        h = hashlib.sha256(f"{run_id}:{cell_uid}:{fiber_id}".encode()).hexdigest()[:12]
        return f"bind_{h}"


class SpacetimeFiberBindingPopulator:
    """Populates spacetime_fiber_binding from existing SPMS cells and fibers.

    V8.5 §8.3: Any SPMS query using information_fiber for structural
    interpretation MUST reference the corresponding spacetime_cell and binding.
    """

    @staticmethod
    def bind_cells_and_fibers(
        run_id: str,
        cells: list,
        fibers: list,
        clock_n: int = 0,
        window_id: str = "",
    ) -> list:
        """Generate bindings from parallel cell and fiber lists.

        Assumes cells[i] and fibers[i] are co-generated pairs.
        """
        bindings = []
        fiber_map = {f.cell_uid: f for f in fibers}

        for cell in cells:
            fiber = fiber_map.get(cell.cell_uid)
            if fiber is None:
                continue

            binding = SpacetimeFiberBinding(
                binding_id=SpacetimeFiberBinding.generate_id(
                    run_id, cell.cell_uid, fiber.fiber_id
                ),
                run_id=run_id,
                clock_n=clock_n,
                window_id=window_id or cell.window_id,
                spacetime_cell_id=cell.cell_uid,
                information_fiber_id=fiber.fiber_id,
                source_cell_ids_json=json.dumps([cell.cell_uid]),
                source_patch_ids_json=cell.source_patch_ids_json,
                binding_type="direct",
                calibration_profile=fiber.calibration_profile,
                provenance_hash=cell.provenance_hash,
            )
            bindings.append(binding)

        return bindings
