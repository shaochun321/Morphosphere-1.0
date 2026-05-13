"""Non-destructive mainline boundary declarations.

This module deliberately contains metadata only. It prevents checkpoint 01 from
changing runtime semantics before the physical and preneural contracts are
migrated in later checkpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class MainlineBoundary:
    """Declares which tree owns current runtime execution."""

    mainline_directory: str
    legacy_reference_directory: str
    mainline_package: str
    install_rule: str
    current_checkpoint: str
    deferred_convergence_items: Tuple[str, ...]


MAINLINE_IMPLEMENTATION = "morphosphere_v2pp"
LEGACY_REFERENCE = "morphosphere_v2"

BOUNDARY = MainlineBoundary(
    mainline_directory=MAINLINE_IMPLEMENTATION,
    legacy_reference_directory=LEGACY_REFERENCE,
    mainline_package="morphosphere",
    install_rule=(
        "Install morphosphere_v2pp for mainline work. Keep morphosphere_v2 in a "
        "separate virtual environment because both trees expose the package "
        "name 'morphosphere'."
    ),
    current_checkpoint="checkpoint_01_mainline_boundary",
    deferred_convergence_items=(
        "physical_cell_graph_source_of_truth",
        "electromechanical_integrator_adapter",
        "patch_afferent_transmission_graph_adapter",
        "preneural_slice_pointset_crosswalk",
        "run_manifest_physical_vs_spacetime_counts",
    ),
)
