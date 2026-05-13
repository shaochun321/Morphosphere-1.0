# Tags: [ACTIVE_EXEC][PIPELINE][ENTRY_POINT]
# Role: Sole entry point for the unified mainline execution.
# Must Not: Write semantic labels back into generation layers.
# Producers: user/CLI
# Consumers: all core + preneural + trajectory + ledger modules
"""Main pipeline for Morphosphere V2 (masterplan §4 unified mainline).

Execution chain:
    CellGraphState X(t)
    → PatchAfferentTransmissionGraph
    → PreNeuralSlice P[t-Δ,t]
    → WindowedTrajectoryField Y_k
    → LatentTrajectoryDecomposition {P_k, R_k}
    → Runtime Ledger
    → Semantic Readout Surface

This lives in active_exec/ — the sole active execution layer.
semantic_assets/ and archive_access/ are read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

import numpy as np

from morphosphere.core import (
    CellGraphState,
    SimulationConfig,
    ContactGraph,
    compute_all_mechanical_forces,
    compute_afferent_statistics,
    unified_step,
)
from morphosphere.core.clock import SystemClock
from morphosphere.core.integrator import compute_local_strain
from morphosphere.preneural import (
    PatchAfferentTransmissionGraph,
    PreNeuralSlice,
    PreNeuralSliceAccumulator,
    build_patch_graph_from_state,
    build_slice_from_graph,
)
from morphosphere.trajectory import (
    WindowedTrajectoryField,
    TrajectoryDecomposition,
    build_trajectory_field,
    decompose_graph_smooth_sparse,
)
from morphosphere.ledger import (
    RuntimeLedger,
    LedgerEntry,
    SemanticReadout,
    compute_semantic_readout,
)
from morphosphere.shell0 import quick_shell0_check


@dataclass(frozen=True)
class PipelineResult:
    """Result of a complete V2 pipeline run."""
    run_id: str
    num_cells: int
    num_steps: int
    final_time: float
    num_ledger_entries: int
    final_coherence: float
    final_sparsity: float
    shell0_verdict: str
    dominant_mode: str
    output_dir: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "num_cells": self.num_cells,
            "num_steps": self.num_steps,
            "final_time": self.final_time,
            "num_ledger_entries": self.num_ledger_entries,
            "final_coherence": self.final_coherence,
            "final_sparsity": self.final_sparsity,
            "shell0_verdict": self.shell0_verdict,
            "dominant_mode": self.dominant_mode,
            "output_dir": self.output_dir,
        }


def _build_initial_state(config: SimulationConfig) -> CellGraphState:
    """Build initial CellGraphState from configuration.

    Uses simple random sphere packing. In production, this would
    integrate with the aggregate builder from cell_sphere_core.
    """
    rng = np.random.default_rng(config.aggregate.rng_seed)
    n = config.aggregate.num_cells
    R = config.aggregate.sphere_radius
    r_cell = config.aggregate.cell_radius

    # Generate positions inside a sphere
    positions = []
    while len(positions) < n:
        candidate = rng.uniform(-R, R, size=3)
        if np.linalg.norm(candidate) < R - r_cell:
            positions.append(candidate)
    pos_array = np.array(positions, dtype=np.float64)

    # Lift the sphere so it sits above z=0
    pos_array[:, 2] += R + 2 * r_cell

    # Build neighbor graph using distance threshold
    from scipy.spatial import cKDTree
    tree = cKDTree(pos_array)
    neighbor_radius = config.aggregate.neighbor_radius_factor * r_cell
    pairs = tree.query_pairs(neighbor_radius, output_type='ndarray')

    if len(pairs) == 0:
        edges = np.empty((0, 2), dtype=np.int64)
        rest_lengths = np.empty(0, dtype=np.float64)
        edge_types = np.empty(0, dtype=np.int64)
    else:
        edges = pairs.astype(np.int64)
        d_vec = pos_array[edges[:, 1]] - pos_array[edges[:, 0]]
        rest_lengths = np.linalg.norm(d_vec, axis=1)
        edge_types = np.zeros(len(edges), dtype=np.int64)

    contact_graph = ContactGraph(
        edges=edges,
        rest_lengths=rest_lengths,
        edge_types=edge_types,
    )

    # Classify surface cells
    center = np.mean(pos_array, axis=0)
    radii = np.linalg.norm(pos_array - center, axis=1)
    r_threshold = R * (1.0 - config.aggregate.shell_thickness_factor * r_cell / R)
    is_surface = radii > r_threshold

    # Radial band assignment
    num_bands = config.aggregate.num_radial_bands
    band_boundaries = np.linspace(0, R, num_bands + 1)
    radial_band_index = np.clip(
        np.digitize(radii, band_boundaries) - 1,
        0, num_bands - 1,
    ).astype(np.int64)

    state = CellGraphState(
        clock_n=0,
        time=0.0,
        run_id=config.name,
        positions=pos_array,
        velocities=np.zeros((n, 3), dtype=np.float64),
        radii=np.full(n, r_cell, dtype=np.float64),
        masses=np.ones(n, dtype=np.float64),
        is_surface=is_surface,
        radial_band_index=radial_band_index,
        contact_graph=contact_graph,
        num_radial_bands=num_bands,
    )

    # Initialize all electrophysiology
    state.initialize_electrophysiology()

    return state


def _resolve_stimulus(
    config: SimulationConfig,
    step: int,
    total_steps: int,
) -> np.ndarray | None:
    """Compute stimulus acceleration for the current step."""
    if config.stimulus_type is None:
        return None

    onset_step = int(total_steps * config.stimulus_onset_fraction)
    duration_steps = max(1, int(total_steps * config.stimulus_duration_fraction))
    offset_step = min(total_steps + 1, onset_step + duration_steps)

    if step < onset_step or step > offset_step:
        return None

    axis_map = {
        "x": np.array([1.0, 0.0, 0.0]),
        "y": np.array([0.0, 1.0, 0.0]),
        "z": np.array([0.0, 0.0, 1.0]),
    }
    axis = axis_map.get(config.stimulus_axis, axis_map["x"])
    return config.stimulus_magnitude * axis


def run_pipeline(
    config: SimulationConfig,
    outdir: str | Path,
) -> PipelineResult:
    """Run the complete Morphosphere V2 pipeline.

    Masterplan §4 unified mainline:
        CellGraphState → PatchGraph → PreNeuralSlice →
        TrajectoryField → Decomposition → Ledger → Readout
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # ── Initialize ────────────────────────────────────────────────────────
    state = _build_initial_state(config)
    clock = SystemClock.create(run_id=config.name, dt=config.dt)
    ledger = RuntimeLedger(run_id=config.name)
    accumulator = PreNeuralSliceAccumulator(window_duration=0.1)

    gravity = np.array([0.0, 0.0, -9.81], dtype=np.float64)
    total_steps = int(config.t_end / config.dt)

    # State snapshots for output
    state_snapshots: list[dict] = []
    decomposition_results: list[dict] = []
    readout_results: list[dict] = []
    last_decomposition: TrajectoryDecomposition | None = None
    last_readout: SemanticReadout | None = None

    # ── Main simulation loop ──────────────────────────────────────────────
    for step in range(total_steps + 1):
        # Resolve stimulus
        stimulus = _resolve_stimulus(config, step, total_steps)

        # Unified step: mechanics + electrophysiology
        if step > 0:
            unified_step(state, config.dt, config, gravity=gravity, stimulus_accel=stimulus)

        # Record at specified intervals
        if step % config.record_every == 0 or step == total_steps:
            # Compute afferent statistics
            aff_stats = compute_afferent_statistics(
                state.spike_times,
                window_start=max(0.0, state.time - 0.1),
                window_end=state.time,
            )

            # Build patch graph from state
            graph = build_patch_graph_from_state(state, afferent_stats=aff_stats)

            # Accumulate into slice
            accumulator.ingest(graph)
            slice_ = accumulator.build_slice()

            if slice_ is not None and slice_.num_points > 0:
                # Build trajectory field
                field = build_trajectory_field(slice_)

                # Decompose: P/R separation (no semantic labels!)
                decomp = decompose_graph_smooth_sparse(
                    field,
                    smoothness_lambda=1.0,
                    sparsity_weight=0.1,
                )
                last_decomposition = decomp

                # Semantic readout (post-hoc ONLY)
                readout = compute_semantic_readout(decomp)
                last_readout = readout

                # Shell0 quick check
                shell0_check = quick_shell0_check(state)

                # Record in ledger
                entry = LedgerEntry(
                    step_index=step,
                    time=state.time,
                    clock_n=state.clock_n,
                    state_hash=state.provenance_hash(),
                    slice_hash=slice_.slice_hash,
                    coherence_score=decomp.coherence_score(),
                    sparsity_score=decomp.sparsity_score(),
                    p_energy_fraction=decomp.coherence_score(),
                    r_energy_fraction=1.0 - decomp.coherence_score(),
                    shell0_status=shell0_check.verdict.name,
                )
                ledger.append(entry)

                decomposition_results.append(decomp.to_dict())
                readout_results.append(readout.to_dict())

            # Record state snapshot
            state_snapshots.append(state.to_snapshot())

    # ── Export results ────────────────────────────────────────────────────
    # Ledger
    ledger_dir = outdir / "ledger"
    ledger.export(ledger_dir / "runtime_ledger.json")

    # Decomposition trace
    (outdir / "trajectory").mkdir(parents=True, exist_ok=True)
    (outdir / "trajectory" / "decomposition_trace.json").write_text(
        json.dumps(decomposition_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Readout trace
    (outdir / "trajectory" / "semantic_readout_trace.json").write_text(
        json.dumps(readout_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Summary
    final_coherence = last_decomposition.coherence_score() if last_decomposition else 0.0
    final_sparsity = last_decomposition.sparsity_score() if last_decomposition else 0.0
    shell0_verdict = ledger.latest().shell0_status if ledger.latest() else "untested"
    dominant_mode = last_readout.dominant_mode if last_readout else "unknown"

    result = PipelineResult(
        run_id=config.name,
        num_cells=state.num_cells,
        num_steps=total_steps,
        final_time=state.time,
        num_ledger_entries=ledger.num_entries,
        final_coherence=final_coherence,
        final_sparsity=final_sparsity,
        shell0_verdict=shell0_verdict,
        dominant_mode=dominant_mode,
        output_dir=str(outdir),
    )

    (outdir / "pipeline_result.json").write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return result
