"""Morphosphere v36.6 Dual-Source Adapters.

Two bottom-layer information generators:
  1. CellSphereAdapter  — 3D electromechanical cell sphere (300 cells on a sphere)
  2. Cell2DRealAdapter   — 2D real cell data (300 cells on a plane, calcium dynamics)

Both adapters produce a unified output format consumed by the ProcessWindow
registration layer. Coordinates are retained in the adapter output for audit,
but the mainline only consumes measure-based relations (μ_ST, μ_IE).
"""
from __future__ import annotations

import hashlib
import math
import random
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Optional


def _normalize(v: float, lo: float, hi: float) -> float:
    """Map value from [lo, hi] to [0, 1]."""
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (v - lo) / (hi - lo)))


@dataclass
class CellRecord:
    """Unified cell output from any source adapter."""
    uid: str
    node_id: int
    x: float
    y: float
    z: float
    # Signal channels (unified names; semantics differ per adapter)
    V_mean: float = 0.0
    V_slope: float = 0.0
    release_proxy: float = 0.0
    afferent_current: float = 0.0
    spike_rate: float = 0.0
    spike_regularity: float = 0.0
    timing_precision: float = 0.0
    adaptation_state: float = 0.0
    signal_uncertainty: float = 0.0
    # Geometry
    normal_x: float = 0.0
    normal_y: float = 0.0
    normal_z: float = 1.0
    boundary_distance: float = 0.0
    support_radius: float = 1.0
    # Topology
    neighbor_ids: List[int] = field(default_factory=list)
    patch_id: str = ""
    # Provenance
    provenance_hash: str = ""
    source_signal_refs: Dict = field(default_factory=dict)
    calibration_profile: str = ""


@dataclass
class EnvelopeRecord:
    """External input envelope describing the reality constraints of one adapter window."""
    envelope_id: str
    adapter_id: str
    adapter_name: str
    adapter_type: str
    geometry_model: str
    signal_model: str
    spatial_extent: Dict
    temporal_extent: Dict
    noise_budget: float
    dissipation_budget: float
    energy_in: float
    energy_out: float


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def _hash_cell(adapter_id: str, k: int, i: int, sig: dict) -> str:
    raw = f"{adapter_id}:{k}:{i}:{sig}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ============================================================================
# Adapter 1: 3D Electromechanical Cell Sphere
# ============================================================================

class CellSphereAdapter:
    """3D cell sphere with MET-channel-driven membrane potential simulation.

    300 cells uniformly distributed on a sphere of radius 5.0.
    Signal model: sinusoidal hair-cell potential drive → MET gate → release → afferent.
    """

    def __init__(self, cell_count: int = 300, radius: float = 5.0, seed: int = 42):
        self.cell_count = cell_count
        self.radius = radius
        self.adapter_id = f"sphere_{uuid.uuid4().hex[:8]}"
        self.adapter_name = "cell_sphere_3d"
        self.adapter_type = "cell_sphere_3d"
        self.geometry_model = "3d_sphere"
        self.signal_model = "electromechanical"
        self.calibration_profile = "sphere_electromechanical_v366"
        self._rng = random.Random(seed)
        # Pre-compute fixed positions using Fibonacci sphere
        self._positions = self._fibonacci_sphere(cell_count, radius)
        self._prev_signals: Dict[int, float] = {}
        # Signal normalization ranges for cross-domain transport
        self.signal_range = {
            'V_mean': (-80.0, -50.0),
            'spike_rate': (0.0, 60.0),
            'release_proxy': (0.0, 0.15),
            'adaptation_state': (0.3, 0.6),
        }

    def normalize_cell(self, cell: CellRecord) -> dict:
        """Return normalized signal dict [0,1] for cross-domain comparison."""
        return {
            'V_norm': _normalize(cell.V_mean, *self.signal_range['V_mean']),
            'spike_norm': _normalize(cell.spike_rate, *self.signal_range['spike_rate']),
            'release_norm': _normalize(cell.release_proxy, *self.signal_range['release_proxy']),
            'adapt_norm': _normalize(cell.adaptation_state, *self.signal_range['adaptation_state']),
        }

    @staticmethod
    def _fibonacci_sphere(n: int, r: float) -> List[tuple]:
        """Generate n points on a sphere of radius r using Fibonacci lattice."""
        points = []
        golden = (1 + math.sqrt(5)) / 2
        for i in range(n):
            theta = math.acos(1 - 2 * (i + 0.5) / n)
            phi = 2 * math.pi * i / golden
            x = r * math.sin(theta) * math.cos(phi)
            y = r * math.sin(theta) * math.sin(phi)
            z = r * math.cos(theta)
            points.append((x, y, z))
        return points

    def _neighbors(self, i: int) -> List[int]:
        """Simple ring neighbors on index space (proxy for geodesic neighbors)."""
        return [(i - 1) % self.cell_count, (i + 1) % self.cell_count,
                (i - 2) % self.cell_count, (i + 2) % self.cell_count]

    def generate_cells(self, window_k: int) -> List[CellRecord]:
        cells = []
        for i in range(self.cell_count):
            x, y, z = self._positions[i]
            # Wobble positions slightly per window
            dx = 0.03 * math.sin(window_k * 0.5 + i * 0.1)
            dy = 0.02 * math.cos(window_k * 0.3 + i * 0.07)
            dz = 0.01 * math.sin(window_k + i * 0.2)
            cx, cy, cz = x + dx, y + dy, z + dz
            r_actual = math.sqrt(cx**2 + cy**2 + cz**2)

            # Hair cell membrane potential (sinusoidal drive)
            V_hair = -66.0 + 7.5 * math.sin(0.7 * window_k + i * 0.19) + \
                     1.2 * math.cos(i * 0.07) + 0.5 * self._rng.gauss(0, 1)
            V_slope = V_hair - self._prev_signals.get(i, V_hair)
            self._prev_signals[i] = V_hair

            # MET channel gating
            release = 0.08 * _sigmoid((V_hair + 65.0) / 4.0)
            V_aff = -70.0 + 350.0 * release
            spike_rate = max(0.0, 5.0 * (V_aff - (-60.0)))
            spike_reg = 1.0 / (1.0 + abs(spike_rate - 20.0) / 25.0)
            timing_prec = 0.01 + 0.001 * (i % 7)
            adapt = 0.45 + 0.05 * math.sin(window_k + i * 0.17)
            sig_unc = 0.02 + 0.001 * (i % 3)

            # Normal vector (radial)
            nx = cx / max(r_actual, 1e-9)
            ny = cy / max(r_actual, 1e-9)
            nz = cz / max(r_actual, 1e-9)
            bdist = abs(r_actual - self.radius) + 0.02 * (i % 5) + 0.015 * window_k

            sig_dict = {"V_mean": V_hair, "release": release, "spike_rate": spike_rate}
            prov = _hash_cell(self.adapter_id, window_k, i, sig_dict)

            cells.append(CellRecord(
                uid=f"sph_{window_k}_{i}",
                node_id=i,
                x=cx, y=cy, z=cz,
                V_mean=V_hair, V_slope=V_slope,
                release_proxy=release, afferent_current=V_aff,
                spike_rate=spike_rate, spike_regularity=spike_reg,
                timing_precision=timing_prec, adaptation_state=adapt,
                signal_uncertainty=sig_unc,
                normal_x=nx, normal_y=ny, normal_z=nz,
                boundary_distance=bdist, support_radius=1.0,
                neighbor_ids=self._neighbors(i),
                patch_id=f"spatch_{i % 15}",
                provenance_hash=prov,
                source_signal_refs={"window_k": window_k, "node_id": i, "adapter": self.adapter_name},
                calibration_profile=self.calibration_profile,
            ))
        return cells

    def make_envelope(self, window_k: int) -> EnvelopeRecord:
        return EnvelopeRecord(
            envelope_id=f"env_sph_{window_k}_{uuid.uuid4().hex[:6]}",
            adapter_id=self.adapter_id,
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            geometry_model=self.geometry_model,
            signal_model=self.signal_model,
            spatial_extent={"type": "sphere", "radius": self.radius, "center": [0, 0, 0]},
            temporal_extent={"window_k": window_k, "dt": 0.01},
            noise_budget=0.05,
            dissipation_budget=0.02,
            energy_in=100.0 + 5 * window_k,
            energy_out=95.0 + 4.8 * window_k,
        )


# ============================================================================
# Adapter 2: 2D Real Cell Data (Calcium Dynamics)
# ============================================================================

class Cell2DRealAdapter:
    """2D cell sheet with calcium dynamics simulation.

    300 cells randomly distributed on a 2D plane (100×100).
    Signal model: calcium concentration waves with diffusion, fluorescence decay,
    and noise injection. This simulates real calcium imaging data characteristics.
    """

    def __init__(self, cell_count: int = 300, field_size: float = 100.0, seed: int = 137):
        self.cell_count = cell_count
        self.field_size = field_size
        self.adapter_id = f"flat2d_{uuid.uuid4().hex[:8]}"
        self.adapter_name = "cell_2d_real"
        self.adapter_type = "cell_2d_real"
        self.geometry_model = "2d_plane"
        self.signal_model = "calcium_dynamics"
        self.calibration_profile = "2d_calcium_dynamics_v366"
        self._rng = random.Random(seed)
        # Pre-compute random positions
        self._positions = [(self._rng.uniform(5, field_size - 5),
                            self._rng.uniform(5, field_size - 5))
                           for _ in range(cell_count)]
        # Pre-compute neighbor graph based on proximity
        self._neighbors_cache = self._build_neighbors()
        self._prev_calcium: Dict[int, float] = {}
        self.signal_range = {
            'V_mean': (0.0, 1.0),
            'spike_rate': (0.0, 50.0),
            'release_proxy': (0.0, 1.0),
            'adaptation_state': (0.0, 0.8),
        }
        # Calcium wave centers (simulate propagating waves)
        self._wave_centers = [(self._rng.uniform(20, 80), self._rng.uniform(20, 80))
                              for _ in range(3)]

    def normalize_cell(self, cell: CellRecord) -> dict:
        """Return normalized signal dict [0,1] for cross-domain comparison."""
        return {
            'V_norm': _normalize(cell.V_mean, *self.signal_range['V_mean']),
            'spike_norm': _normalize(cell.spike_rate, *self.signal_range['spike_rate']),
            'release_norm': _normalize(cell.release_proxy, *self.signal_range['release_proxy']),
            'adapt_norm': _normalize(cell.adaptation_state, *self.signal_range['adaptation_state']),
        }

    def _build_neighbors(self) -> Dict[int, List[int]]:
        """Build k-nearest neighbors (k=4) based on 2D Euclidean distance."""
        neighbors = {}
        for i in range(self.cell_count):
            xi, yi = self._positions[i]
            dists = []
            for j in range(self.cell_count):
                if i == j:
                    continue
                xj, yj = self._positions[j]
                d = math.sqrt((xi - xj)**2 + (yi - yj)**2)
                dists.append((d, j))
            dists.sort()
            neighbors[i] = [j for _, j in dists[:4]]
        return neighbors

    def generate_cells(self, window_k: int) -> List[CellRecord]:
        cells = []
        for i in range(self.cell_count):
            px, py = self._positions[i]

            # Calcium dynamics: wave propagation + diffusion + decay
            calcium = 0.0
            for wc_idx, (wx, wy) in enumerate(self._wave_centers):
                # Wave moves outward over time
                wave_radius = 10.0 + 5.0 * window_k + 3.0 * wc_idx
                dist_to_wave = abs(math.sqrt((px - wx)**2 + (py - wy)**2) - wave_radius)
                wave_width = 8.0
                calcium += 0.6 * math.exp(-dist_to_wave**2 / (2 * wave_width**2))

            # Add cell-specific baseline + noise
            calcium += 0.1 + 0.05 * math.sin(i * 0.3)
            calcium += 0.03 * self._rng.gauss(0, 1)
            calcium = max(0.0, min(1.0, calcium))

            # Fluorescence signal (GCaMP-like transformation)
            fluorescence = calcium ** 1.5  # nonlinear calcium-to-fluorescence
            # Photobleaching decay
            fluorescence *= math.exp(-0.01 * window_k)

            # Calcium slope (temporal derivative)
            prev_ca = self._prev_calcium.get(i, calcium)
            ca_slope = calcium - prev_ca
            self._prev_calcium[i] = calcium

            # Map to unified signal interface:
            # V_mean → calcium concentration (normalized 0-1)
            # V_slope → calcium temporal derivative
            # release_proxy → fluorescence intensity
            # afferent_current → intercellular calcium coupling
            coupling = 0.0
            for ni in self._neighbors_cache.get(i, []):
                n_ca = self._prev_calcium.get(ni, 0.3)
                coupling += 0.1 * (n_ca - calcium)
            coupling = max(-0.5, min(0.5, coupling))

            # spike_rate → calcium event rate (transient detection)
            event_rate = max(0.0, 50.0 * ca_slope) if ca_slope > 0.02 else 0.0
            regularity = 1.0 / (1.0 + abs(event_rate - 10.0) / 15.0)
            timing = 0.05 + 0.01 * (i % 5)
            adapt = calcium * 0.8  # adaptation tracks calcium level
            unc = 0.05 + 0.02 * self._rng.random()

            # Boundary distance (distance to field edge)
            bdist = min(px, py, self.field_size - px, self.field_size - py)

            sig_dict = {"calcium": calcium, "fluorescence": fluorescence}
            prov = _hash_cell(self.adapter_id, window_k, i, sig_dict)

            cells.append(CellRecord(
                uid=f"c2d_{window_k}_{i}",
                node_id=i,
                x=px, y=py, z=0.0,
                V_mean=calcium, V_slope=ca_slope,
                release_proxy=fluorescence,
                afferent_current=coupling,
                spike_rate=event_rate,
                spike_regularity=regularity,
                timing_precision=timing,
                adaptation_state=adapt,
                signal_uncertainty=unc,
                normal_x=0.0, normal_y=0.0, normal_z=1.0,
                boundary_distance=bdist,
                support_radius=2.0,
                neighbor_ids=self._neighbors_cache.get(i, []),
                patch_id=f"cpatch_{i % 20}",
                provenance_hash=prov,
                source_signal_refs={"window_k": window_k, "node_id": i, "adapter": self.adapter_name},
                calibration_profile=self.calibration_profile,
            ))
        return cells

    def make_envelope(self, window_k: int) -> EnvelopeRecord:
        return EnvelopeRecord(
            envelope_id=f"env_2d_{window_k}_{uuid.uuid4().hex[:6]}",
            adapter_id=self.adapter_id,
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            geometry_model=self.geometry_model,
            signal_model=self.signal_model,
            spatial_extent={"type": "rectangle", "width": self.field_size,
                            "height": self.field_size, "z": 0.0},
            temporal_extent={"window_k": window_k, "dt": 0.05},
            noise_budget=0.08,
            dissipation_budget=0.03,
            energy_in=80.0 + 3 * window_k,
            energy_out=75.0 + 2.9 * window_k,
        )
