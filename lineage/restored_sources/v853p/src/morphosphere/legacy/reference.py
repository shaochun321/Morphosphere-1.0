"""Metadata for V2 reference modules selected for future convergence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class LegacyReferenceModule:
    path: str
    planned_role: str
    convergence_status: str = "reference_only"


LEGACY_V2_REFERENCE_MODULES: Tuple[LegacyReferenceModule, ...] = (
    LegacyReferenceModule(
        "morphosphere_v2/src/morphosphere/core/cell_graph_state.py",
        "physical cell graph state source-of-truth candidate",
    ),
    LegacyReferenceModule(
        "morphosphere_v2/src/morphosphere/core/integrator.py",
        "electromechanical unified-step reference",
    ),
    LegacyReferenceModule(
        "morphosphere_v2/src/morphosphere/preneural/patch_graph.py",
        "PatchAfferentTransmissionGraph reference",
    ),
    LegacyReferenceModule(
        "morphosphere_v2/src/morphosphere/preneural/preneural_slice.py",
        "PreNeuralSlice reference for pointset crosswalk",
    ),
    LegacyReferenceModule(
        "morphosphere_v2/src/morphosphere/trajectory/transport.py",
        "legacy transport reference",
    ),
    LegacyReferenceModule(
        "morphosphere_v2/src/morphosphere/trajectory/decomposition.py",
        "legacy P/R decomposition reference",
    ),
)
