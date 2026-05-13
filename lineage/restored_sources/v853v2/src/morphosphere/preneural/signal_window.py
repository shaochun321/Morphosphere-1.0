# Tags: [CORE_RUNTIME][TEMPORAL][VERSIONED]
# Role: PreNeuralSignalWindow — time-windowed signal aggregation per node.
# Must Not: Import semantic_readout or legacy modules.
# Producers: pipeline
# Consumers: preneural_slice, observation_field
"""PreNeuralSignalWindow — signal aggregation (v5 P04).

Aggregates per-node signal values across a time window,
producing SignalWindow entries suitable for building
PreNeuralPointSetSlice objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from morphosphere.core.cell_graph_state import CellGraphState
from morphosphere.core.clock import AnalysisWindow
from morphosphere.core.schema import SignalWindow, SignalWindowEntry
from morphosphere.core.dynamics import compute_afferent_statistics


@dataclass
class SignalAccumulator:
    """Accumulates CellGraphState snapshots over a time window.

    When the window is complete, produces a SignalWindow with
    time-averaged signal values per node.
    """
    window_duration_ticks: int = 200  # number of ticks to accumulate
    _snapshots: list[dict[str, np.ndarray]] = field(default_factory=list)
    _clock_ticks: list[int] = field(default_factory=list)

    def ingest(self, state: CellGraphState) -> None:
        """Ingest a state snapshot."""
        snap = {
            "V_hair_cell": state.V_hair_cell.copy() if state.V_hair_cell.size > 0 else np.array([]),
            "calcium": state.calcium.copy() if state.calcium.size > 0 else np.array([]),
            "release_rate": state.release_rate.copy() if state.release_rate.size > 0 else np.array([]),
            "V_afferent": state.V_afferent.copy() if state.V_afferent.size > 0 else np.array([]),
            "met_open_probability": state.met_open_probability.copy() if state.met_open_probability.size > 0 else np.array([]),
            "local_strain": state.local_strain.copy() if state.local_strain.size > 0 else np.array([]),
        }
        self._snapshots.append(snap)
        self._clock_ticks.append(state.clock_n)

        # Prune old snapshots
        if len(self._clock_ticks) > self.window_duration_ticks:
            cutoff = len(self._clock_ticks) - self.window_duration_ticks
            self._snapshots = self._snapshots[cutoff:]
            self._clock_ticks = self._clock_ticks[cutoff:]

    def build_signal_window(
        self,
        state: CellGraphState,
        run_id: str = "",
    ) -> SignalWindow | None:
        """Build a SignalWindow from accumulated snapshots."""
        if not self._snapshots:
            return None

        n = state.num_cells
        if n == 0:
            return None

        clock_start = self._clock_ticks[0]
        clock_end = self._clock_ticks[-1]
        window_id = f"sw_{run_id}_{clock_start}_{clock_end}"

        # Compute time-averaged values
        n_snaps = len(self._snapshots)
        V_means = np.zeros(n)
        V_slopes = np.zeros(n)
        release_proxies = np.zeros(n)
        adaptation_states = np.zeros(n)

        for snap in self._snapshots:
            if snap["V_hair_cell"].size == n:
                V_means += snap["V_hair_cell"]
            if snap["release_rate"].size == n:
                release_proxies += snap["release_rate"]
            if snap["met_open_probability"].size == n:
                adaptation_states += snap["met_open_probability"]

        V_means /= max(n_snaps, 1)
        release_proxies /= max(n_snaps, 1)
        adaptation_states /= max(n_snaps, 1)

        # Compute V_slope from first and last snapshot
        if n_snaps >= 2 and self._snapshots[0]["V_hair_cell"].size == n and self._snapshots[-1]["V_hair_cell"].size == n:
            V_slopes = (self._snapshots[-1]["V_hair_cell"] - self._snapshots[0]["V_hair_cell"]) / max(n_snaps, 1)

        # Compute afferent statistics
        aff_stats = compute_afferent_statistics(
            state.spike_times,
            window_start=max(0.0, state.time - 0.1),
            window_end=state.time,
        )

        entries: list[SignalWindowEntry] = []
        for i in range(n):
            entry = SignalWindowEntry(
                node_id=f"c{i}",
                V_mean=float(V_means[i]),
                V_slope=float(V_slopes[i]),
                release_proxy=float(release_proxies[i]),
                afferent_current=float(state.synaptic_conductance[i]) if state.synaptic_conductance.size > 0 else 0.0,
                spike_rate=float(aff_stats["rate"][i]),
                spike_regularity=float(aff_stats["regularity"][i]),
                timing_precision=float(aff_stats["timing_precision"][i]),
                adaptation_state=float(adaptation_states[i]),
            )
            entries.append(entry)

        return SignalWindow(
            window_id=window_id,
            clock_start=clock_start,
            clock_end=clock_end,
            entries=entries,
        )
