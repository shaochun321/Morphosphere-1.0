"""Shell0 Boundary Hypothesis — front-loaded determination (masterplan §10).

Shell0 is redefined as a "hypothesis to be tested", not a long-term semantic
object. It must be determined within Stage-1 boundary solving, contact
perturbation, and multi-observation-basis verification.

Masterplan §10.1 determination tiers:
  CI tier: resolution coarse/nominal/fine, contact ablation/restoration,
           boundary replacement (baseline / ghost-image / pde_fvm_shell)
  Research tier: observation-basis invariance, energy budget closure,
                 topological persistence

Masterplan §10.2 determination rule:
  Only when a boundary layer remains stable under resolution, boundary
  implementation, and contact perturbation changes, AND can find a closed
  budget in mechanical work / current / release power / boundary exchange,
  is it promoted to a real physical boundary layer object. Otherwise it is
  judged as construction_issue or mixed_or_indeterminate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from morphosphere.core.types import Shell0Verdict, Float64Array
from morphosphere.core.cell_graph_state import CellGraphState


@dataclass
class ResolutionProbe:
    """Result of a resolution variation test."""
    resolution_label: str   # coarse / nominal / fine
    num_cells: int
    boundary_present: bool
    boundary_energy_ratio: float = 0.0
    boundary_force_mean: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolution": self.resolution_label,
            "num_cells": self.num_cells,
            "boundary_present": self.boundary_present,
            "boundary_energy_ratio": self.boundary_energy_ratio,
            "boundary_force_mean": self.boundary_force_mean,
        }


@dataclass
class ContactProbe:
    """Result of a contact perturbation test."""
    perturbation_type: str  # ablation / restoration
    boundary_stable: bool
    delta_energy: float = 0.0
    delta_force: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "perturbation_type": self.perturbation_type,
            "boundary_stable": self.boundary_stable,
            "delta_energy": self.delta_energy,
            "delta_force": self.delta_force,
        }


@dataclass
class BoundaryReplacementProbe:
    """Result of a boundary implementation replacement test."""
    method: str  # baseline / ghost_image / pde_fvm_shell
    boundary_stable: bool
    energy_ratio: float = 0.0
    force_reduction: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "boundary_stable": self.boundary_stable,
            "energy_ratio": self.energy_ratio,
            "force_reduction": self.force_reduction,
        }


@dataclass
class EnergyBudget:
    """Energy budget closure check for shell0."""
    mechanical_work: float = 0.0
    electrical_current: float = 0.0
    release_power: float = 0.0
    boundary_exchange: float = 0.0
    budget_residual: float = 0.0
    is_closed: bool = False

    @property
    def total_input(self) -> float:
        return self.mechanical_work + self.boundary_exchange

    @property
    def total_output(self) -> float:
        return self.electrical_current + self.release_power

    def to_dict(self) -> dict[str, Any]:
        return {
            "mechanical_work": self.mechanical_work,
            "electrical_current": self.electrical_current,
            "release_power": self.release_power,
            "boundary_exchange": self.boundary_exchange,
            "budget_residual": self.budget_residual,
            "is_closed": self.is_closed,
        }


@dataclass
class Shell0Determination:
    """Complete shell0 boundary hypothesis determination result.

    Masterplan §10.2: Only when stable under resolution/boundary/contact
    AND energy budget is closed → real boundary layer.
    Otherwise → construction_issue or mixed_or_indeterminate.
    """
    verdict: Shell0Verdict
    confidence: float = 0.0

    # CI tier probes
    resolution_probes: list[ResolutionProbe] = field(default_factory=list)
    contact_probes: list[ContactProbe] = field(default_factory=list)
    boundary_probes: list[BoundaryReplacementProbe] = field(default_factory=list)

    # Research tier
    energy_budget: EnergyBudget | None = None
    observation_invariant: bool = False
    topological_persistent: bool = False

    # Triad consistency (from masterplan §14)
    triad_consistent: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.name,
            "confidence": self.confidence,
            "triad_consistent": self.triad_consistent,
            "resolution_probes": [p.to_dict() for p in self.resolution_probes],
            "contact_probes": [p.to_dict() for p in self.contact_probes],
            "boundary_probes": [p.to_dict() for p in self.boundary_probes],
            "energy_budget": self.energy_budget.to_dict() if self.energy_budget else None,
            "observation_invariant": self.observation_invariant,
            "topological_persistent": self.topological_persistent,
        }


def determine_shell0(
    state: CellGraphState,
    *,
    resolution_probes: list[ResolutionProbe] | None = None,
    contact_probes: list[ContactProbe] | None = None,
    boundary_probes: list[BoundaryReplacementProbe] | None = None,
    energy_budget: EnergyBudget | None = None,
) -> Shell0Determination:
    """Run shell0 boundary hypothesis determination.

    Masterplan §10.2 decision rule:
      1. All resolution probes show boundary present → resolution_stable
      2. All contact probes show boundary stable → contact_stable
      3. All boundary replacement probes show stable → boundary_stable
      4. Energy budget is closed → energy_closed
      5. All four → REAL_BOUNDARY_LAYER
      6. None → CONSTRUCTION_ISSUE
      7. Otherwise → MIXED_OR_INDETERMINATE
    """
    if resolution_probes is None:
        resolution_probes = []
    if contact_probes is None:
        contact_probes = []
    if boundary_probes is None:
        boundary_probes = []

    # CI tier checks
    resolution_stable = (
        len(resolution_probes) >= 2 and
        all(p.boundary_present for p in resolution_probes)
    )
    contact_stable = (
        len(contact_probes) >= 1 and
        all(p.boundary_stable for p in contact_probes)
    )
    boundary_stable = (
        len(boundary_probes) >= 2 and
        all(p.boundary_stable for p in boundary_probes)
    )
    energy_closed = (
        energy_budget is not None and
        energy_budget.is_closed
    )

    # Count passing criteria
    criteria = [resolution_stable, contact_stable, boundary_stable, energy_closed]
    passing = sum(criteria)

    # Determine verdict
    if passing == 4:
        verdict = Shell0Verdict.REAL_BOUNDARY_LAYER
        confidence = 0.9
    elif passing == 0:
        verdict = Shell0Verdict.CONSTRUCTION_ISSUE
        confidence = 0.8
    else:
        verdict = Shell0Verdict.MIXED_OR_INDETERMINATE
        confidence = 0.3 + 0.15 * passing

    # Triad consistency check
    triad_consistent = resolution_stable and contact_stable and boundary_stable

    return Shell0Determination(
        verdict=verdict,
        confidence=confidence,
        resolution_probes=resolution_probes,
        contact_probes=contact_probes,
        boundary_probes=boundary_probes,
        energy_budget=energy_budget,
        triad_consistent=triad_consistent,
    )


def quick_shell0_check(state: CellGraphState) -> Shell0Determination:
    """Quick shell0 check based on current state only.

    This is a simplified version for runtime use. Full determination
    requires multiple simulation runs at different resolutions.
    """
    n = state.num_cells
    if n == 0:
        return Shell0Determination(verdict=Shell0Verdict.MIXED_OR_INDETERMINATE)

    # Check if outermost band has distinct mechanical behavior
    outer_band = state.num_radial_bands - 1
    outer_mask = state.radial_band_index == outer_band
    inner_mask = state.radial_band_index == 0

    if not np.any(outer_mask) or not np.any(inner_mask):
        return Shell0Determination(verdict=Shell0Verdict.MIXED_OR_INDETERMINATE)

    # Compare force densities
    if state.total_forces.size == 0:
        return Shell0Determination(verdict=Shell0Verdict.MIXED_OR_INDETERMINATE)

    force_density = np.linalg.norm(state.total_forces, axis=1)
    outer_force = float(np.mean(force_density[outer_mask]))
    inner_force = float(np.mean(force_density[inner_mask]))

    # If outer shell has significantly different force profile, it might be a boundary
    ratio = outer_force / max(inner_force, 1e-12)
    if ratio > 2.0:
        return Shell0Determination(
            verdict=Shell0Verdict.MIXED_OR_INDETERMINATE,
            confidence=0.5,
            resolution_probes=[ResolutionProbe(
                resolution_label="nominal",
                num_cells=n,
                boundary_present=True,
                boundary_energy_ratio=ratio,
                boundary_force_mean=outer_force,
            )],
        )

    return Shell0Determination(
        verdict=Shell0Verdict.MIXED_OR_INDETERMINATE,
        confidence=0.3,
    )
