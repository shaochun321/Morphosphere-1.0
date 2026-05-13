# Tags: [CORE_RUNTIME][DYNAMICS][FIVE_LAYER]
# Role: Five coupled dynamic layers (mech, MET, membrane, Ca/release, afferent).
# Must Not: Import semantic_readout or produce semantic labels.
# Producers: integrator.unified_step
# Consumers: cell_graph_state (mutates in-place)
"""Minimal dynamics skeleton for Stage-1 V2 (masterplan §6.2).

This module implements the five coupled dynamic layers:
  1. Mechanical: m_i d²r_i/dt² = F_contact + F_tissue + F_boundary + F_external + F_damp
  2. MET entry:  db/dt = (B(local_state) - b) / τ_b;  m_MET = sigmoid((b-b0-a)/k_b)
  3. Membrane:   C_h dV/dt = -I_leak - I_K - I_Ca + I_MET + I_ext  (+ I_h optional)
  4. Release:    dCa/dt = -Ca/τ_Ca + α·max(0,I_Ca);  dRel/dt = α_rel·φ(Ca)·(1-Rel) - β_rel·Rel
  5. Afferent:   AdEx/EIF model → event times, regularity, precision statistics

Design principle (masterplan §3):
  - Only physical ontology quantities and observation operators are explicit
  - No semantic labels (translation/rotation/family) enter this layer
"""

from __future__ import annotations

import numpy as np

from .v2_dataclass import CellGraphState
from .types import (
    Float64Array,
    METParams,
    HairCellMembraneParams,
    ReleaseParams,
    AfferentParams,
)


# ── Helper functions ──────────────────────────────────────────────────────────

def _sigmoid(x: Float64Array | float) -> Float64Array | float:
    """Numerically stable sigmoid."""
    return np.where(x >= 0,
                    1.0 / (1.0 + np.exp(-x)),
                    np.exp(x) / (1.0 + np.exp(x)))


def _boltzmann(v: Float64Array, v_half: float, k: float) -> Float64Array:
    """Boltzmann activation function for ion channel gating."""
    return _sigmoid((v - v_half) / k)


# ── Layer 1: Mechanical ──────────────────────────────────────────────────────

def compute_contact_forces(state: CellGraphState, k_contact: float = 900.0) -> Float64Array:
    """Hertz-like contact repulsion between overlapping cells.

    Operates on the contact graph topology in CellGraphState.
    """
    forces = np.zeros_like(state.positions)
    if state.contact_graph is None:
        return forces

    edges = state.contact_graph.edges
    pos = state.positions
    r = state.radii

    d_vec = pos[edges[:, 1]] - pos[edges[:, 0]]
    d_norm = np.linalg.norm(d_vec, axis=1)
    safe_d = np.maximum(d_norm, 1e-12)
    overlap = (r[edges[:, 0]] + r[edges[:, 1]]) - d_norm
    mask = overlap > 0
    if not np.any(mask):
        return forces

    direction = d_vec / safe_d[:, None]
    f_mag = k_contact * overlap
    f_mag[~mask] = 0.0

    np.add.at(forces, edges[:, 0], -direction * f_mag[:, None])
    np.add.at(forces, edges[:, 1],  direction * f_mag[:, None])
    return forces


def compute_spring_damper_forces(
    state: CellGraphState,
    k_bulk: float = 240.0,
    c_bulk: float = 2.5,
) -> Float64Array:
    """Spring-damper forces along neighbor graph edges."""
    forces = np.zeros_like(state.positions)
    if state.contact_graph is None:
        return forces

    edges = state.contact_graph.edges
    rest = state.contact_graph.rest_lengths
    pos = state.positions
    vel = state.velocities

    d_vec = pos[edges[:, 1]] - pos[edges[:, 0]]
    d_norm = np.linalg.norm(d_vec, axis=1)
    safe_d = np.maximum(d_norm, 1e-12)
    direction = d_vec / safe_d[:, None]

    # Spring: proportional to displacement from rest length
    stretch = d_norm - rest
    f_spring = k_bulk * stretch

    # Damper: proportional to relative velocity along the bond
    dv = vel[edges[:, 1]] - vel[edges[:, 0]]
    relative_v = np.sum(dv * direction, axis=1)
    f_damp = c_bulk * relative_v

    f_total = (f_spring + f_damp)[:, None] * direction
    np.add.at(forces, edges[:, 0],  f_total)
    np.add.at(forces, edges[:, 1], -f_total)
    return forces


def compute_external_forces(
    state: CellGraphState,
    gravity: Float64Array | None = None,
    stimulus_accel: Float64Array | None = None,
) -> Float64Array:
    """External forces: gravity + stimulus acceleration."""
    forces = np.zeros_like(state.positions)
    if gravity is not None:
        forces += state.masses[:, None] * gravity[None, :]
    if stimulus_accel is not None:
        forces += state.masses[:, None] * stimulus_accel[None, :]
    return forces


def compute_damping_forces(
    state: CellGraphState,
    c_global: float = 0.8,
) -> Float64Array:
    """Velocity-proportional global damping."""
    return -c_global * state.masses[:, None] * state.velocities


def compute_all_mechanical_forces(
    state: CellGraphState,
    *,
    k_contact: float = 900.0,
    k_bulk: float = 240.0,
    c_bulk: float = 2.5,
    c_global: float = 0.8,
    gravity: Float64Array | None = None,
    stimulus_accel: Float64Array | None = None,
) -> Float64Array:
    """Combine all mechanical forces. Updates state.total_forces."""
    f = (
        compute_contact_forces(state, k_contact)
        + compute_spring_damper_forces(state, k_bulk, c_bulk)
        + compute_external_forces(state, gravity, stimulus_accel)
        + compute_damping_forces(state, c_global)
    )
    state.total_forces = f
    return f


# ── Layer 2: MET entry ───────────────────────────────────────────────────────

def compute_local_bundle_drive(state: CellGraphState) -> Float64Array:
    """Compute the local mechanical drive B(local_state) on each cell's hair bundle.

    The drive depends on local strain (radial displacement from rest).
    This is a purely mechanical observable — no semantic labels.
    """
    center = np.mean(state.positions, axis=0)
    relative = state.positions - center
    radius = np.linalg.norm(relative, axis=1)
    safe_r = np.maximum(radius, 1e-12)
    radial_dir = relative / safe_r[:, None]

    # Radial velocity component
    v_radial = np.sum(state.velocities * radial_dir, axis=1)

    # Bundle drive proportional to radial velocity + strain
    drive = 0.7 * v_radial + 0.3 * state.local_strain
    return drive


def step_met_channel(
    state: CellGraphState,
    dt: float,
    params: METParams,
) -> None:
    """Advance the MET channel state by one time step.

    Masterplan §6.2 line 2:
        db/dt = (B(local_state) - b) / τ_b
        da/dt = adaptation_rate * (adaptation_strength * b - a)
        m_MET = sigmoid((b - b0 - a) / k_b)
    """
    n = state.num_cells
    if state.bundle_deflection.size != n:
        return

    B_drive = compute_local_bundle_drive(state)

    # Bundle deflection dynamics
    db = (B_drive - state.bundle_deflection) / params.tau_b
    state.bundle_deflection += dt * db

    # Adaptation dynamics
    da = params.adaptation_rate * (params.adaptation_strength * state.bundle_deflection - state.met_adaptation)
    state.met_adaptation += dt * da

    # Open probability
    x = (state.bundle_deflection - params.b0 - state.met_adaptation) / params.k_b
    state.met_open_probability = np.clip(_sigmoid(x), 0.0, 1.0)

    # MET current (stored for membrane layer)
    state.I_MET = params.g_met_max * state.met_open_probability * (params.e_met - state.V_hair_cell)


# ── Layer 3: Hair cell membrane ──────────────────────────────────────────────

def step_hair_cell_membrane(
    state: CellGraphState,
    dt: float,
    params: HairCellMembraneParams,
) -> None:
    """Advance hair cell membrane potential by one time step.

    Masterplan §6.2 line 3:
        C_h dV/dt = -I_leak - I_K - I_Ca + I_MET + I_ext
    """
    n = state.num_cells
    if state.V_hair_cell.size != n:
        return

    V = state.V_hair_cell

    # Ion channel gating
    m_ca = _boltzmann(V, params.v_half_ca, params.k_slope_ca)
    m_k = _boltzmann(V, params.v_half_k, params.k_slope_k)

    # Update stored gate variables
    tau_gate = 0.005  # fast gating time constant
    state.m_gate_ca += dt * (m_ca - state.m_gate_ca) / tau_gate
    state.m_gate_k += dt * (m_k - state.m_gate_k) / tau_gate

    # Currents
    I_leak = params.g_leak * (V - params.e_leak)
    I_K = params.g_k * state.m_gate_k * (V - params.e_k)
    I_Ca = params.g_ca * state.m_gate_ca * (V - params.e_ca)

    # Optional I_h
    I_h = np.zeros(n) if params.g_h <= 0 else params.g_h * _boltzmann(-V, 60.0, 8.0) * (V - params.e_h)

    # Membrane dynamics
    dV = (-I_leak - I_K - I_Ca - I_h + state.I_MET) / params.capacitance
    state.V_hair_cell = np.clip(V + dt * dV, -90.0, 60.0)

    # Store Ca current for release layer (positive inward)
    # I_Ca is outward by convention (V - E_Ca), so inward Ca = -I_Ca when V < E_Ca
    state._last_I_Ca = -I_Ca  # store for release layer


# ── Layer 4: Ca²⁺ / Release ─────────────────────────────────────────────────

def step_calcium_release(
    state: CellGraphState,
    dt: float,
    params: ReleaseParams,
) -> None:
    """Advance Ca²⁺ concentration and vesicle release rate.

    Masterplan §6.2 line 4:
        dCa/dt = -Ca/τ_Ca + α·max(0, I_Ca)
        dRel/dt = α_rel·φ(Ca)·(1-Rel) - β_rel·Rel
    """
    n = state.num_cells
    if state.calcium.size != n:
        return

    # Get inward Ca current from membrane step
    I_Ca_inward = getattr(state, '_last_I_Ca', np.zeros(n))

    # Calcium dynamics
    dCa = -state.calcium / params.tau_ca + params.alpha_ca * np.maximum(0.0, I_Ca_inward)
    state.calcium = np.maximum(0.0, state.calcium + dt * dCa)

    # Release dynamics: φ(Ca) is a sigmoid
    phi_ca = _sigmoid((state.calcium - params.ca_half) / params.ca_slope)
    dRel = params.alpha_rel * phi_ca * (1.0 - state.release_rate) - params.beta_rel * state.release_rate
    state.release_rate = np.clip(state.release_rate + dt * dRel, 0.0, 1.0)


# ── Layer 5: Afferent neuron (AdEx/EIF) ──────────────────────────────────────

def step_afferent_neuron(
    state: CellGraphState,
    dt: float,
    params: AfferentParams,
) -> None:
    """Advance afferent neuron state using AdEx/EIF model.

    Masterplan §6.2 line 5:
        C dV/dt = -g_L(V-E_L) + g_L·Δ_T·exp((V-V_T)/Δ_T) - w + I_syn
        τ_w dw/dt = a(V - E_L) - w
        if V > V_peak: V ← V_reset, w ← w + b

    Outputs: event times, regularity, and precision statistics
    (not fixed-length spike packets).
    """
    n = state.num_cells
    if state.V_afferent.size != n:
        return

    V = state.V_afferent
    w = state.w_adaptation

    # Synaptic drive from hair cell release
    # Steady-state: g_syn → g_syn_max * release_rate
    dsyn = (-state.synaptic_conductance + params.g_syn_max * state.release_rate) / params.tau_syn
    state.synaptic_conductance = np.maximum(0.0, state.synaptic_conductance + dt * dsyn)

    # Synaptic current
    I_syn = state.synaptic_conductance * (params.e_syn - V)

    # EIF exponential term (with clamp to prevent overflow)
    exp_arg = np.clip((V - params.v_threshold) / params.delta_t, -20.0, 20.0)
    I_exp = params.g_leak * params.delta_t * np.exp(exp_arg)

    # Membrane dynamics
    dV = (-params.g_leak * (V - params.e_leak) + I_exp - w + I_syn) / params.capacitance
    V_new = V + dt * dV

    # Adaptation dynamics
    dw = (params.a_adapt * (V - params.e_leak) - w) / params.tau_w
    w_new = w + dt * dw

    # Spike detection and reset
    v_peak = 20.0  # mV, spike cutoff
    spiked = V_new > v_peak
    V_new[spiked] = params.v_reset
    w_new[spiked] += params.b_adapt

    # Record spike times
    for i in np.where(spiked)[0]:
        state.spike_times[i].append(float(state.time))

    state.V_afferent = np.clip(V_new, -90.0, v_peak)
    state.w_adaptation = w_new


# ── Unified step function ────────────────────────────────────────────────────

def step_all_dynamics(
    state: CellGraphState,
    dt: float,
    *,
    met_params: METParams | None = None,
    hc_params: HairCellMembraneParams | None = None,
    rel_params: ReleaseParams | None = None,
    aff_params: AfferentParams | None = None,
) -> None:
    """Advance all five dynamic layers by one time step.

    Call this after mechanical forces have been computed and applied.
    The layers are stepped in causal order:
        MET → hair cell membrane → Ca/release → afferent
    """
    if met_params is not None:
        step_met_channel(state, dt, met_params)
    if hc_params is not None:
        step_hair_cell_membrane(state, dt, hc_params)
    if rel_params is not None:
        step_calcium_release(state, dt, rel_params)
    if aff_params is not None:
        step_afferent_neuron(state, dt, aff_params)


# ── Afferent statistics (output contract) ────────────────────────────────────

def compute_afferent_statistics(
    spike_times: list[list[float]],
    window_start: float,
    window_end: float,
) -> dict[str, Float64Array]:
    """Compute afferent output statistics: rate, regularity, timing_precision.

    Masterplan §6.2: "输出事件时间、规则性与精度统计，而不是固定长度 spike 包"
    """
    n = len(spike_times)
    rates = np.zeros(n, dtype=np.float64)
    regularities = np.zeros(n, dtype=np.float64)
    timing_precisions = np.zeros(n, dtype=np.float64)

    window = window_end - window_start
    if window <= 0:
        return {"rate": rates, "regularity": regularities, "timing_precision": timing_precisions}

    for i, times in enumerate(spike_times):
        # Filter spikes in window
        spikes = [t for t in times if window_start <= t <= window_end]
        n_spikes = len(spikes)
        rates[i] = n_spikes / window

        if n_spikes >= 2:
            isis = np.diff(spikes)
            mean_isi = np.mean(isis)
            std_isi = np.std(isis)
            # Regularity = 1 / CV (coefficient of variation inverse)
            if std_isi > 1e-12:
                regularities[i] = mean_isi / std_isi
            else:
                regularities[i] = 100.0  # perfectly regular

            # Timing precision = 1 / std_isi (Hz)
            timing_precisions[i] = 1.0 / max(std_isi, 1e-6)

    return {
        "rate": rates,
        "regularity": regularities,
        "timing_precision": timing_precisions,
    }
