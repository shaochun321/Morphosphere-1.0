"""V1FullImporter: Reads V1 sensor_nodes.jsonl and produces CellGraphState frames.

Phase B: Maps V1 per-cell data (pos_abs, vel_abs, gate, gate_signal, contact)
to V8 CellGraphState fields for full pipeline processing.

V1 data format (sensor_nodes.jsonl, JSONL):
  - 13 frames, each containing 4 radial layers (72 cells total)
  - Per-cell fields: pos_abs[3], vel_abs[3], r, u_r, v_r, gate, gate_signal, contact
  - Layer fields: band_index, rest_mean_radius, node_count
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from ..active_exec.stage1_physics.cell_graph_state import CellGraphState


class V1FullImporter:
    """Reads V1 sensor_nodes.jsonl and produces CellGraphState frames.

    The V1 data already represents evolved physical state from the V1 model.
    We inject it as observations — we do NOT re-run V8 5-layer dynamics on it.
    """

    def __init__(self):
        self._raw_frames: List[Dict[str, Any]] = []

    def load(self, file_path: str) -> int:
        """Load JSONL file. Returns number of frames loaded."""
        path = Path(file_path)
        self._raw_frames = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._raw_frames.append(json.loads(line))
        return len(self._raw_frames)

    def import_frames(self, run_id: str = "v1_replay") -> List[CellGraphState]:
        """Convert loaded V1 frames to V8 CellGraphState list.

        Field mapping:
          V1 pos_abs[3]     → CellGraphState.positions
          V1 vel_abs[3]     → CellGraphState.velocities (unused in V1 t=0)
          V1 r              → CellGraphState.radii
          V1 gate           → CellGraphState.met_open_probability
          V1 gate_signal    → CellGraphState.v_hair_cell (proxy)
          V1 u_r            → bundle deflection → afferent proxy
          V1 contact        → topology hints
          V1 band_index     → radial_band_index
        """
        states = []
        for idx, raw in enumerate(self._raw_frames):
            state = self._convert_frame(raw, idx, run_id)
            states.append(state)
        return states

    def _convert_frame(
        self, raw: Dict[str, Any], frame_idx: int, run_id: str
    ) -> CellGraphState:
        """Convert a single V1 frame to CellGraphState."""
        layers = raw.get("layers", [])

        # Flatten all cells across layers
        all_positions = []
        all_velocities = []
        all_radii = []
        all_gate = []
        all_gate_signal = []
        all_u_r = []
        all_contact = []
        all_band_index = []
        all_is_surface = []

        for layer in layers:
            band_idx = layer.get("band_index", 0)
            rest_radius = layer.get("rest_mean_radius", 0.01)
            nodes = layer.get("nodes", [])

            for node in nodes:
                # Position: V1 stores [x, y, z] in pos_abs
                pos = node.get("pos_abs", [0.0, 0.0, 0.0])
                all_positions.append(pos)

                vel = node.get("vel_abs", [0.0, 0.0, 0.0])
                all_velocities.append(vel)

                # Radius: use radial distance from V1
                r = node.get("r", rest_radius)
                all_radii.append(r)

                # MET gate → met_open_probability
                gate = node.get("gate", 0.0)
                all_gate.append(gate)

                # Gate signal → proxy for V_hair_cell
                # V1 gate_signal is typically small; map to membrane potential
                gs = node.get("gate_signal", 0.0)
                # Scale: gate_signal ∈ [~0, ~0.01] → V ∈ [-65, -55]
                v_hc = -65.0 + gs * 1000.0  # amplify small signal
                all_gate_signal.append(v_hc)

                # Radial displacement → bundle deflection proxy
                u_r = node.get("u_r", 0.0)
                all_u_r.append(u_r)

                # Contact → topology hint
                contact = node.get("contact", 0.0)
                all_contact.append(contact)

                all_band_index.append(band_idx)

                # Surface = outermost band
                is_surf = node.get("is_surface", band_idx == max(l.get("band_index", 0) for l in layers))
                all_is_surface.append(is_surf)

        num_cells = len(all_positions)
        positions = np.array(all_positions, dtype=np.float64)
        velocities = np.array(all_velocities, dtype=np.float64)
        radii = np.array(all_radii, dtype=np.float64)

        # Derive electrophysiology proxies from V1 data
        v_hair_cell = all_gate_signal
        met_open = all_gate

        # Release proxy: driven by gate * u_r
        release = [abs(g * u) * 10.0 for g, u in zip(all_gate, all_u_r)]

        # Ca proxy: driven by gate
        calcium = [max(0.0, g * 0.5) for g in all_gate]

        # Afferent proxy: driven by u_r displacement
        v_afferent = [-70.0 + abs(u) * 1000.0 for u in all_u_r]

        return CellGraphState(
            clock_n=frame_idx,
            run_id=run_id,
            num_cells=num_cells,
            positions=positions,
            velocities=velocities,
            radii=radii,
            active_flags=np.array(all_is_surface, dtype=bool),
            v_hair_cell=v_hair_cell,
            calcium_concentration=calcium,
            v_afferent=v_afferent,
            met_open_probability=met_open,
            neurotransmitter_release_rate=release,
        )

    def get_raw_frame(self, idx: int) -> Optional[Dict[str, Any]]:
        """Get raw V1 frame for inspection."""
        if 0 <= idx < len(self._raw_frames):
            return self._raw_frames[idx]
        return None

    def get_frame_summary(self, idx: int) -> Dict[str, Any]:
        """Get summary of a frame for diagnostics."""
        raw = self.get_raw_frame(idx)
        if raw is None:
            return {}

        layers = raw.get("layers", [])
        total_cells = sum(len(l.get("nodes", [])) for l in layers)
        layer_counts = {l["band_index"]: len(l.get("nodes", [])) for l in layers}

        process = raw.get("process_state", {})
        stimulus = raw.get("stimulus", {})

        return {
            "frame_idx": idx,
            "total_cells": total_cells,
            "layer_counts": layer_counts,
            "motion_class": process.get("motion_class", "unknown"),
            "motion_confidence": process.get("motion_confidence", 0.0),
            "dominant_axis": process.get("dominant_axis", "unknown"),
            "stimulus_mode": stimulus.get("mode", "unknown"),
            "stimulus_active": stimulus.get("active", False),
        }
