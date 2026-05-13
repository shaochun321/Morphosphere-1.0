"""Mainline electromechanical integrator boundary.

This module ports the complete V2-style causal step into v2pp without changing
V8.5 diagnostic semantics. It is the explicit physical runtime path:

    forces -> semi-implicit mechanics -> local strain -> MET -> membrane ->
    calcium/release -> afferent

The diagnostic dynamic driver remains available in
``diagnostic_dynamic_driver.py`` and must not be described as a scientific
physical driver.
"""

from __future__ import annotations

import numpy as np

from .physical_cell_graph_state import PhysicalCellGraphState
from .types import Float64Array, SimulationConfig
from .dynamics import compute_all_mechanical_forces, step_all_dynamics


def semi_implicit_euler_mechanical(
    state: PhysicalCellGraphState,
    forces: Float64Array,
    dt: float,
) -> None:
    """Integrate physical positions and velocities with semi-implicit Euler."""
    if state.num_cells == 0:
        return
    safe_masses = np.maximum(state.masses, 1e-12)
    acceleration = forces / safe_masses[:, None]
    state.velocities = state.velocities + dt * acceleration
    state.positions = state.positions + dt * state.velocities


def compute_local_strain(state: PhysicalCellGraphState) -> None:
    """Update per-cell local strain from the physical contact graph."""
    n = state.num_cells
    state.local_strain = np.zeros(n, dtype=np.float64)
    if n == 0 or state.contact_graph is None or state.contact_graph.num_edges == 0:
        return

    edges = state.contact_graph.edges
    rest = state.contact_graph.rest_lengths
    pos = state.positions
    d_vec = pos[edges[:, 1]] - pos[edges[:, 0]]
    d_norm = np.linalg.norm(d_vec, axis=1)
    strain = (d_norm - rest) / np.maximum(rest, 1e-12)

    counts = np.zeros(n, dtype=np.float64)
    np.add.at(state.local_strain, edges[:, 0], np.abs(strain))
    np.add.at(state.local_strain, edges[:, 1], np.abs(strain))
    np.add.at(counts, edges[:, 0], 1.0)
    np.add.at(counts, edges[:, 1], 1.0)
    mask = counts > 0
    state.local_strain[mask] /= counts[mask]


def unified_electromechanical_step(
    state: PhysicalCellGraphState,
    dt: float,
    config: SimulationConfig,
    *,
    gravity: Float64Array | None = None,
    stimulus_accel: Float64Array | None = None,
) -> None:
    """Advance the authoritative physical state by one causal step."""
    forces = compute_all_mechanical_forces(
        state,
        k_contact=config.mechanical.k_contact,
        k_bulk=config.mechanical.k_tissue,
        c_bulk=config.mechanical.c_damping,
        c_global=config.mechanical.c_global_damping,
        gravity=gravity,
        stimulus_accel=stimulus_accel,
    )
    semi_implicit_euler_mechanical(state, forces, dt)
    compute_local_strain(state)
    step_all_dynamics(
        state,
        dt,
        met_params=config.met,
        hc_params=config.hair_cell,
        rel_params=config.release,
        aff_params=config.afferent,
    )
    state.clock_n += 1
    state.time += dt


# Compatibility alias for callers expecting the legacy V2 name.
unified_step = unified_electromechanical_step


__all__ = [
    "semi_implicit_euler_mechanical",
    "compute_local_strain",
    "unified_electromechanical_step",
    "unified_step",
]
