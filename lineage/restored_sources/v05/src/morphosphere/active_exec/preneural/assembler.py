"""PreNeuralAssembler: Builds PreNeuralPointSetSlice from PatchGraph over an AnalysisWindow.

V8-T1: Activates runtime carrier objects — every slice carries populated
GeometryNode and SignalWindow instances with real data from CellGraphState.

Phase A: Multi-frame SignalHistory buffer enables V_slope, spike_rate,
spike_regularity, and timing_precision computation across frames.
"""
import hashlib
import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..contracts.clock import AnalysisWindow
from ..stage1_physics.cell_graph_state import CellGraphState, PatchGraph
from .geometry import GeometryNode
from .signal_window import SignalWindow
from .pointset_slice import PreNeuralPointSetSlice


class SignalHistory:
    """Multi-frame signal buffer for computing temporal derivatives.

    Stores per-node V_mean history and per-cell spike_times for computing:
      - V_slope = (V_mean[t] - V_mean[t-1]) / dt
      - spike_rate, spike_regularity, timing_precision from spike events
    """

    def __init__(self, max_frames: int = 8):
        self.max_frames = max_frames
        # node_id -> list of (clock_n, V_mean)
        self._v_mean_history: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
        # cell_id -> list of spike times (accumulated across frames)
        self._spike_times: Dict[int, List[float]] = defaultdict(list)

    def record_v_mean(self, node_id: int, clock_n: int, v_mean: float) -> None:
        """Record V_mean for a node at a given clock tick."""
        hist = self._v_mean_history[node_id]
        hist.append((clock_n, v_mean))
        if len(hist) > self.max_frames:
            hist.pop(0)

    def get_v_slope(self, node_id: int, dt: float = 1.0) -> float:
        """Compute V_slope = dV/dt from the last two recorded V_mean values."""
        hist = self._v_mean_history.get(node_id, [])
        if len(hist) < 2:
            return 0.0
        clock_prev, v_prev = hist[-2]
        clock_curr, v_curr = hist[-1]
        d_clock = clock_curr - clock_prev
        if d_clock == 0:
            return 0.0
        return (v_curr - v_prev) / (d_clock * dt)

    def record_spike_times(self, cell_id: int, times: List[float]) -> None:
        """Record spike times for a cell."""
        self._spike_times[cell_id] = times

    def get_spike_stats(
        self,
        source_cell_ids: List[int],
        window_start: float,
        window_end: float,
    ) -> Tuple[float, float, float]:
        """Compute spike_rate, spike_regularity, timing_precision.

        Returns (spike_rate, spike_regularity, timing_precision).
        """
        all_spikes = []
        for cid in source_cell_ids:
            times = self._spike_times.get(cid, [])
            all_spikes.extend(t for t in times if window_start <= t <= window_end)

        window_dur = window_end - window_start
        if window_dur <= 0:
            return 0.0, 0.0, 0.0

        # Spike rate (Hz)
        n_spikes = len(all_spikes)
        spike_rate = n_spikes / window_dur if window_dur > 0 else 0.0

        if n_spikes < 2:
            return spike_rate, 0.0, 0.0

        # ISI statistics
        sorted_spikes = sorted(all_spikes)
        isis = [sorted_spikes[i+1] - sorted_spikes[i] for i in range(len(sorted_spikes)-1)]
        isis = [x for x in isis if x > 0]
        if not isis:
            return spike_rate, 0.0, 0.0

        mean_isi = np.mean(isis)
        std_isi = np.std(isis)

        # Regularity = mean_ISI / std_ISI (higher = more regular)
        if std_isi > 1e-12:
            spike_regularity = float(mean_isi / std_isi)
        else:
            spike_regularity = 100.0  # perfectly regular

        # Timing precision = 1 / std_ISI
        timing_precision = float(1.0 / max(std_isi, 1e-6))

        return float(spike_rate), spike_regularity, timing_precision

    def clear(self) -> None:
        """Clear all history."""
        self._v_mean_history.clear()
        self._spike_times.clear()


class PreNeuralAssembler:
    """PreNeuralAssembler: Builds PreNeuralPointSetSlice from PatchGraph over an AnalysisWindow.

    V8 T1 deliverables:
      - runtime GeometryNode population
      - runtime SignalWindow population
      - pointset slice carries geometry/signal/topology/provenance

    Phase A: Multi-frame SignalHistory enables temporal derivative computation.
    """

    def __init__(self, dt: float = 0.01):
        self.signal_history = SignalHistory()
        self.dt = dt

    def build_slice(
        self,
        window: AnalysisWindow,
        patch_graphs: List[PatchGraph],
        cell_state: Optional[CellGraphState] = None,
        positions: Optional[np.ndarray] = None,
        v2_state: Optional[object] = None,
    ) -> PreNeuralPointSetSlice:
        """Aggregates PatchGraphs within the AnalysisWindow to build a point-set slice.

        Args:
            window: The analysis window for this slice.
            patch_graphs: List of PatchGraph objects in the window.
            cell_state: Optional CellGraphState for extracting real geometry/signal.
            positions: Optional Nx3 positions array override. If None, uses
                       cell_state.get_positions_array() when available.
            v2_state: Optional V2 dataclass CellGraphState for spike_times access.
        """
        # P1 fix: derive positions from CellGraphState formal field
        if positions is None and cell_state is not None:
            positions = cell_state.get_positions_array()
        slice_id = f"slice_{uuid.uuid4().hex[:8]}"

        if not patch_graphs:
            return PreNeuralPointSetSlice(
                slice_id=slice_id,
                window_id=window.window_id,
                geometry_node_ids=[],
                edges=[],
                signal_windows_refs=[],
            )

        latest_patch = patch_graphs[-1]

        # Ingest spike_times from V2 state if available
        if v2_state is not None and hasattr(v2_state, 'spike_times'):
            for cid, times in enumerate(v2_state.spike_times):
                self.signal_history.record_spike_times(cid, times)

        geometry_node_ids = []
        geometry_nodes = []
        signal_windows_list = []
        signal_windows_refs = []

        for p_id in range(latest_patch.num_patches):
            node_id = p_id
            geometry_node_ids.append(node_id)

            # --- Build GeometryNode with real data ---
            source_cell_ids = latest_patch.source_cell_ids.get(p_id, [])
            geo_node = self._build_geometry_node(
                node_id=node_id,
                patch_id=p_id,
                source_cell_ids=source_cell_ids,
                positions=positions,
                all_patch_ids=list(range(latest_patch.num_patches)),
            )
            geometry_nodes.append(geo_node)

            # --- Build SignalWindow with real data + temporal derivatives ---
            sig_win = self._build_signal_window(
                window=window,
                node_id=node_id,
                cell_state=cell_state,
                source_cell_ids=source_cell_ids,
            )
            signal_windows_list.append(sig_win)

            # V8.3 P1: Resolvable composite-key reference (v8.1-T2)
            sig_ref = {"window_id": window.window_id, "node_id": node_id}
            signal_windows_refs.append(sig_ref)

        # Build topological edges from spatial proximity
        edges = self._build_topology(geometry_nodes)

        # Set neighbor_ids on geometry nodes from edge topology
        neighbor_map: dict[int, list[int]] = {n.node_id: [] for n in geometry_nodes}
        for e in edges:
            neighbor_map[e[0]].append(e[1])
            neighbor_map[e[1]].append(e[0])
        for gn in geometry_nodes:
            gn.neighbor_ids = neighbor_map.get(gn.node_id, [])

        # Provenance hash
        provenance_hash = self._compute_provenance(window, geometry_nodes, signal_windows_list)

        return PreNeuralPointSetSlice(
            slice_id=slice_id,
            window_id=window.window_id,
            stage_k=window.clock_start,
            geometry_node_ids=geometry_node_ids,
            edges=edges,
            geometry_nodes=geometry_nodes,
            signal_windows=signal_windows_list,
            signal_windows_refs=signal_windows_refs,
            provenance_hash=provenance_hash,
        )

    # ── Private helpers ────────────────────────────────────────────────

    def _build_geometry_node(
        self,
        node_id: int,
        patch_id: int,
        source_cell_ids: List[int],
        positions: Optional[np.ndarray],
        all_patch_ids: List[int],
    ) -> GeometryNode:
        """Build a GeometryNode with real coordinate data when available."""
        # Compute centroid position from source cell positions
        if positions is not None and len(source_cell_ids) > 0:
            valid_ids = [c for c in source_cell_ids if c < len(positions)]
            if valid_ids:
                centroid = np.mean(positions[valid_ids], axis=0)
                pos = tuple(float(x) for x in centroid)
            else:
                pos = (0.0, 0.0, 0.0)

            # Estimate surface normal from centroid relative to aggregate center
            center = np.mean(positions, axis=0)
            direction = centroid - center
            norm = np.linalg.norm(direction)
            if norm > 1e-12:
                normal = tuple(float(x) for x in (direction / norm))
            else:
                normal = (0.0, 0.0, 1.0)

            # Boundary distance: approximate as distance to aggregate center
            boundary_distance = float(norm)

            # Support radius: max distance from centroid to any source cell
            if len(valid_ids) > 1:
                dists = np.linalg.norm(positions[valid_ids] - centroid, axis=1)
                support_radius = float(np.max(dists)) if len(dists) > 0 else 1.0
            else:
                support_radius = 1.0
        else:
            pos = (0.0, 0.0, 0.0)
            normal = (0.0, 0.0, 1.0)
            boundary_distance = 0.0
            support_radius = 1.0

        return GeometryNode(
            node_id=node_id,
            patch_ids=[patch_id],
            position=pos,
            surface_normal=normal,
            area_weight=float(len(source_cell_ids)) if source_cell_ids else 1.0,
            boundary_distance=boundary_distance,
            support_radius=support_radius,
            neighbor_ids=[],  # Will be set later from topology
            source_patch_ids=[patch_id],
        )

    def _build_signal_window(
        self,
        window: AnalysisWindow,
        node_id: int,
        cell_state: Optional[CellGraphState],
        source_cell_ids: List[int],
    ) -> SignalWindow:
        """Build a SignalWindow with real electrophysiology data + temporal derivatives."""
        if cell_state is not None and source_cell_ids:
            # Extract real signal data from CellGraphState
            v_vals = [cell_state.v_hair_cell[c] for c in source_cell_ids
                      if c < len(cell_state.v_hair_cell)] if cell_state.v_hair_cell else []
            V_mean = float(np.mean(v_vals)) if v_vals else 0.0

            # Phase A: Record V_mean and compute V_slope from history
            clock_n = cell_state.clock_n if hasattr(cell_state, 'clock_n') else window.clock_start
            self.signal_history.record_v_mean(node_id, clock_n, V_mean)
            V_slope = self.signal_history.get_v_slope(node_id, dt=self.dt)

            rel_vals = [cell_state.neurotransmitter_release_rate[c] for c in source_cell_ids
                        if c < len(cell_state.neurotransmitter_release_rate)] if cell_state.neurotransmitter_release_rate else []
            release_proxy = float(np.mean(rel_vals)) if rel_vals else 0.0

            aff_vals = [cell_state.v_afferent[c] for c in source_cell_ids
                        if c < len(cell_state.v_afferent)] if cell_state.v_afferent else []
            afferent_current = float(np.mean(aff_vals)) if aff_vals else 0.0

            met_vals = [cell_state.met_open_probability[c] for c in source_cell_ids
                        if c < len(cell_state.met_open_probability)] if cell_state.met_open_probability else []
            adaptation_state = float(np.mean(met_vals)) if met_vals else 0.0

            # Phase A: Spike stats from history
            spike_rate, spike_regularity, timing_precision = \
                self.signal_history.get_spike_stats(
                    source_cell_ids,
                    window_start=float(window.clock_start) * self.dt,
                    window_end=float(window.clock_end) * self.dt,
                )

            energy_level = float(np.sqrt(V_mean**2 + release_proxy**2 + afferent_current**2))

            return SignalWindow(
                window_id=window.window_id,
                node_id=node_id,
                V_mean=V_mean,
                V_slope=V_slope,
                release_proxy=release_proxy,
                afferent_current=afferent_current,
                spike_rate=spike_rate,
                spike_regularity=spike_regularity,
                timing_precision=timing_precision,
                adaptation_state=adaptation_state,
                energy_level=energy_level,
            )
        else:
            return SignalWindow(
                window_id=window.window_id,
                node_id=node_id,
            )

    def _build_topology(self, geometry_nodes: List[GeometryNode]) -> List[List[int]]:
        """Build topological edges from spatial proximity of geometry nodes."""
        if len(geometry_nodes) < 2:
            return []

        positions = np.array([list(g.position) for g in geometry_nodes])
        n = len(positions)

        # Compute pairwise distances
        from scipy.spatial.distance import cdist
        dist_matrix = cdist(positions, positions)

        # Use adaptive threshold: median distance * factor
        np.fill_diagonal(dist_matrix, np.inf)
        median_dist = np.median(dist_matrix[dist_matrix < np.inf])
        threshold = median_dist * 1.5 if median_dist > 0 else float('inf')

        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                if dist_matrix[i, j] < threshold:
                    edges.append([geometry_nodes[i].node_id, geometry_nodes[j].node_id])

        return edges

    def _compute_provenance(
        self,
        window: AnalysisWindow,
        geometry_nodes: List[GeometryNode],
        signal_windows: List[SignalWindow],
    ) -> str:
        """Compute SHA256 provenance hash from source data."""
        h = hashlib.sha256()
        h.update(f"window={window.window_id}".encode())
        for gn in geometry_nodes:
            h.update(f"gn={gn.node_id}:{gn.position}".encode())
        for sw in signal_windows:
            h.update(f"sw={sw.node_id}:{sw.V_mean:.8f}:{sw.release_proxy:.8f}".encode())
        return h.hexdigest()[:16]
