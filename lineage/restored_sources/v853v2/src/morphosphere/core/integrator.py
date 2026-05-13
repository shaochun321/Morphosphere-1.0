# Tags: [CORE_RUNTIME][TEMPORAL][INTEGRATOR]
# Role: Time integration for all coupled dynamics layers.
# Must Not: Import semantic_readout or produce semantic labels.
# Producers: pipeline
# Consumers: cell_graph_state (mutates in-place)
"""Time integration for the Morphosphere V2 system.

Provides the semi-implicit Euler integrator for the mechanical layer,
and a unified stepper that advances all coupled dynamics.
"""

from __future__ import annotations

import numpy as np

from .cell_graph_state import CellGraphState
from .types import (
    Float64Array,
    SimulationConfig,
    METParams,
    HairCellMembraneParams,
    ReleaseParams,
    AfferentParams,
)
from .dynamics import (
    compute_all_mechanical_forces,
    step_all_dynamics,
)


def semi_implicit_euler_mechanical(
    state: CellGraphState,
    forces: Float64Array,
    dt: float,
) -> None:
    """Semi-implicit Euler integration for positions and velocities.

    v(t+dt) = v(t) + dt * F/m
    x(t+dt) = x(t) + dt * v(t+dt)

    This is the same scheme as v1 but operates on CellGraphState.
    """
    acc = forces / state.masses[:, None]
    state.velocities += dt * acc
    state.positions += dt * state.velocities


def compute_local_strain(state: CellGraphState) -> None:
    """Update local strain estimates from the contact graph.

    Strain is measured as the fractional deviation of neighbor distances
    from their rest lengths. This provides the mechanical input for MET.
    """
    n = state.num_cells
    state.local_strain = np.zeros(n, dtype=np.float64)

    if state.contact_graph is None:
        return

    edges = state.contact_graph.edges
    rest = state.contact_graph.rest_lengths
    pos = state.positions

    d_vec = pos[edges[:, 1]] - pos[edges[:, 0]]
    d_norm = np.linalg.norm(d_vec, axis=1)
    strain = (d_norm - rest) / np.maximum(rest, 1e-12)

    # Accumulate mean strain per cell
    counts = np.zeros(n, dtype=np.float64)
    np.add.at(state.local_strain, edges[:, 0], np.abs(strain))
    np.add.at(state.local_strain, edges[:, 1], np.abs(strain))
    np.add.at(counts, edges[:, 0], 1.0)
    np.add.at(counts, edges[:, 1], 1.0)
    mask = counts > 0
    state.local_strain[mask] /= counts[mask]


def unified_step(
    state: CellGraphState,
    dt: float,
    config: SimulationConfig,
    *,
    gravity: Float64Array | None = None,
    stimulus_accel: Float64Array | None = None,
) -> None:
    """Advance the entire system by one time step.

    Execution order follows causal chain:
        1. Compute mechanical forces
        2. Integrate positions/velocities
        3. Update local strain (mechanical observable)
        4. Step electrophysiology chain: MET → HC → Ca/Rel → Aff

    This ensures that mechanical state is fully updated before
    being used as input to the electrophysiology chain.
    """
    # 1. Mechanical forces
    forces = compute_all_mechanical_forces(
        state,
        k_contact=config.mechanical.k_contact,
        k_bulk=config.mechanical.k_tissue,
        c_bulk=config.mechanical.c_damping,
        c_global=config.mechanical.c_global_damping,
        gravity=gravity,
        stimulus_accel=stimulus_accel,
    )

    # 2. Integrate mechanics
    semi_implicit_euler_mechanical(state, forces, dt)

    # 3. Update strain observable
    compute_local_strain(state)

    # 4. Electrophysiology chain
    step_all_dynamics(
        state, dt,
        met_params=config.met,
        hc_params=config.hair_cell,
        rel_params=config.release,
        aff_params=config.afferent,
    )

    # Update time (v5 §3.1: clock_n is canonical time index)
    state.clock_n += 1
    state.time += dt
