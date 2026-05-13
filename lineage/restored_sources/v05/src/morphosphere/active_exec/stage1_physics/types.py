"""Core type definitions for the Morphosphere V2 system.

Follows the masterplan principle: multiple representations, single ontology.
All types here are pure data containers; dynamics live in dynamics.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import numpy as np
from numpy.typing import NDArray

# ── Array type aliases ────────────────────────────────────────────────────────

Float64Array = NDArray[np.float64]
Int64Array = NDArray[np.int64]
BoolArray = NDArray[np.bool_]


# ── Enumerations ──────────────────────────────────────────────────────────────

class NodeType(Enum):
    """Node types in the PatchAfferentTransmissionGraph."""
    CELL_CENTER = auto()
    MEMBRANE_PATCH = auto()
    SYNAPSE_PATCH = auto()
    AFFERENT_TERMINAL = auto()


class EdgeType(Enum):
    """Edge types in the PatchAfferentTransmissionGraph."""
    CONTACT = auto()
    SYNAPTIC = auto()
    FUNCTIONAL_COUPLING = auto()
    SPATIAL_PROXIMITY = auto()


class Shell0Verdict(Enum):
    """Possible outcomes of shell0 boundary hypothesis testing."""
    REAL_BOUNDARY_LAYER = auto()
    CONSTRUCTION_ISSUE = auto()
    MIXED_OR_INDETERMINATE = auto()


# ── Geometry & Topology ───────────────────────────────────────────────────────

@dataclass
class ContactGraph:
    """Sparse contact/neighbor graph for the cell aggregate.

    edges: (E, 2) array of node index pairs
    rest_lengths: (E,) equilibrium distances
    edge_types: (E,) integer edge type classification
    """
    edges: Int64Array
    rest_lengths: Float64Array
    edge_types: Int64Array

    @property
    def num_edges(self) -> int:
        return self.edges.shape[0]


@dataclass
class SpatialAnchor:
    """Spatial anchor for provenance tracking (masterplan §5.2).

    Every patch, synapse patch, or afferent terminal must carry
    source weights, spatial anchors, and a provenance hash.
    """
    position: Float64Array            # (3,) xyz in lab frame
    normal: Float64Array              # (3,) outward normal
    scale: float                      # characteristic length
    source_cell_ids: list[int]        # originating cell indices
    weights_to_cells: Float64Array    # (len(source_cell_ids),) weights
    provenance_hash: str = ""         # for replay alignment


# ── Physical parameters ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class MechanicalParams:
    """Parameters for the mechanical layer (masterplan §6.2 line 1)."""
    k_contact: float = 900.0
    k_tissue: float = 240.0
    c_damping: float = 2.5
    c_global_damping: float = 0.8


@dataclass(frozen=True)
class METParams:
    """Parameters for the mechano-electrical transduction channel.

    Masterplan §6.2 line 2:
        db/dt = (B(local_state) - b) / τ_b
        m_MET = sigmoid((b - b0 - a) / k_b)
    """
    tau_b: float = 0.005              # bundle relaxation time constant (s)
    b0: float = 0.0                   # resting deflection
    k_b: float = 0.02                 # sigmoid slope parameter
    g_met_max: float = 1.5            # maximum MET conductance (nS)
    e_met: float = 0.0                # MET reversal potential (mV)
    adaptation_rate: float = 50.0     # adaptation speed (1/s)
    adaptation_strength: float = 0.5  # fraction of deflection adapted out


@dataclass(frozen=True)
class HairCellMembraneParams:
    """Parameters for the hair cell membrane (masterplan §6.2 line 3).

    C_h dV/dt = -I_leak - I_K - I_Ca (+ I_h optional) + I_MET + I_ext
    """
    capacitance: float = 10.0         # pF
    g_leak: float = 1.0               # nS
    e_leak: float = -65.0             # mV
    g_k: float = 8.0                  # nS
    e_k: float = -80.0                # mV
    g_ca: float = 2.5                 # nS
    e_ca: float = 50.0                # mV
    v_half_k: float = -30.0           # mV, K activation midpoint
    k_slope_k: float = 5.0            # mV, K activation slope
    v_half_ca: float = -25.0          # mV, Ca activation midpoint
    k_slope_ca: float = 4.0           # mV, Ca activation slope
    # Optional I_h (hyperpolarization-activated)
    g_h: float = 0.0                  # nS, 0 = disabled
    e_h: float = -40.0                # mV


@dataclass(frozen=True)
class ReleaseParams:
    """Parameters for the Ca²⁺ / release layer (masterplan §6.2 line 4).

    dCa/dt = -Ca/τ_Ca + α·max(0, I_Ca)
    dRel/dt = α_rel·φ(Ca)·(1-Rel) - β_rel·Rel
    """
    tau_ca: float = 0.050             # Ca clearance time constant (s)
    alpha_ca: float = 0.1             # I_Ca → Ca conversion factor
    alpha_rel: float = 20.0           # release onset rate
    beta_rel: float = 5.0             # release recovery rate
    ca_half: float = 0.5              # Ca midpoint for φ(Ca) sigmoid
    ca_slope: float = 0.1             # Ca slope for φ(Ca) sigmoid


@dataclass(frozen=True)
class AfferentParams:
    """Parameters for the afferent neuron (masterplan §6.2 line 5).

    AdEx/EIF model scaled for vestibular afferent terminal.
    Outputs event times, regularity, and precision statistics.
    """
    capacitance: float = 30.0         # pF  (vestibular afferent terminal)
    g_leak: float = 3.0               # nS
    e_leak: float = -70.0             # mV
    v_threshold: float = -52.0        # mV, spike threshold
    delta_t: float = 3.0              # mV, EIF sharpness
    v_reset: float = -65.0            # mV, post-spike reset
    tau_w: float = 0.050              # s, adaptation time constant
    a_adapt: float = 0.5              # nS, sub-threshold adaptation
    b_adapt: float = 0.02             # nA, spike-triggered adaptation
    g_syn_max: float = 50.0           # nS, max synaptic conductance
    e_syn: float = 0.0                # mV, synaptic reversal
    tau_syn: float = 0.003            # s, synaptic decay


# ── Aggregate build configuration ────────────────────────────────────────────

@dataclass
class AggregateConfig:
    """Configuration for building a cell aggregate (sphere packing)."""
    num_cells: int = 300
    sphere_radius: float = 0.08
    cell_radius: float = 0.004
    jitter: float = 0.15
    rng_seed: int = 7
    packing_fraction: float = 0.68
    neighbor_radius_factor: float = 2.2
    k_min_neighbors: int = 8
    k_max_neighbors: int = 16
    num_radial_bands: int = 4
    shell_thickness_factor: float = 2.0
    exposure_threshold: float = 0.30


# ── Simulation configuration ─────────────────────────────────────────────────

@dataclass
class SimulationConfig:
    """Top-level simulation configuration."""
    name: str = "default"
    dt: float = 5e-4                  # time step (s)
    t_end: float = 1.5                # total simulation time (s)
    record_every: int = 20            # record state every N steps
    aggregate: AggregateConfig = field(default_factory=AggregateConfig)
    mechanical: MechanicalParams = field(default_factory=MechanicalParams)
    met: METParams = field(default_factory=METParams)
    hair_cell: HairCellMembraneParams = field(default_factory=HairCellMembraneParams)
    release: ReleaseParams = field(default_factory=ReleaseParams)
    afferent: AfferentParams = field(default_factory=AfferentParams)

    # Stimulus
    stimulus_type: str | None = None  # "translation" or "rotation" or None
    stimulus_onset_fraction: float = 0.4
    stimulus_duration_fraction: float = 1.0
    stimulus_axis: str = "x"
    stimulus_magnitude: float = 500.0
