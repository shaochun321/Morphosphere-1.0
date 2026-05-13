"""CTC Real Data Source Adapter — Cell Tracking Challenge Fluo-N2DH-GOWT1.

Reads real cell centroid trajectories from data/ctc_centroids_real_v24.csv
and produces CellRecord sequences identical in interface to the synthetic
CellSphereAdapter / Cell2DRealAdapter.

Data source:
  Dataset: Fluo-N2DH-GOWT1 (Cell Tracking Challenge)
  DOI: 10.5281/zenodo.15608211
  License: CC-BY-4.0
  Rows: 4,575 centroid observations across 92 frames × 2 sequences
  Columns: centroid_x, centroid_y, area, track_id, frame, sequence_id, ...

Signal mapping (real → unified interface):
  x, y         ← centroid_x, centroid_y  (true spatial coordinates)
  z            ← 0.0  (2D imaging data)
  V_mean       ← area_normalized  (cell area as signal proxy, 0–1)
  spike_rate   ← inter-frame displacement  (motion velocity signal)
  release_proxy← area change rate  (growth/shrink signal)
  adaptation   ← track_duration / total_frames  (persistence metric)
"""
from __future__ import annotations

import csv
import hashlib
import math
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

# Import the shared CellRecord and EnvelopeRecord from source_adapters
import sys
_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE / "src"))
from morphosphere.active_exec.source_adapters import CellRecord, EnvelopeRecord, _normalize


class CTCRealDataAdapter:
    """Source adapter that reads real CTC cell tracking centroid data.

    Implements the same interface as CellSphereAdapter / Cell2DRealAdapter:
      - generate_cells(window_k) -> List[CellRecord]
      - make_envelope(window_k) -> EnvelopeRecord
      - normalize_cell(cell) -> dict

    The adapter lazily loads the CSV on first use and organizes data by
    frame (=window_k) and track_id (=cell identity).
    """

    def __init__(self, sequence: str = "01",
                 csv_path: Optional[str] = None,
                 max_frames: Optional[int] = None,
                 split_role: str = "calibration"):
        """Initialize the CTC adapter.

        Args:
            sequence: Which CTC sequence to use ("01" or "02").
                      Separate sequences enable independent train/test.
            csv_path: Path to the CSV file. Defaults to data/ctc_centroids_real_v24.csv.
            max_frames: Limit the number of frames to process (for quick testing).
            split_role: One of 'calibration', 'validation', 'holdout', 'all'.
                       - calibration: seq01 frames 0-69
                       - validation:  seq01 frames 70-91
                       - holdout:     seq02 (entire sequence, frozen)
                       - all:         no filtering (legacy behavior)
        """
        self.sequence = sequence
        self.csv_path = csv_path or str(_BASE / "data" / "ctc_centroids_real_v24.csv")
        self.max_frames = max_frames
        self.split_role = split_role

        # Override sequence based on split_role
        if split_role == "holdout":
            self.sequence = "02"  # holdout is always seq02
        elif split_role in ("calibration", "validation"):
            self.sequence = "01"  # cal/val both come from seq01
        else:
            self.sequence = sequence

        self.adapter_id = f"ctc_real_{sequence}_{uuid.uuid4().hex[:8]}"
        self.adapter_name = f"ctc_real_seq{sequence}"
        self.adapter_type = "ctc_real_data"
        self.geometry_model = "2d_plane"
        self.signal_model = "ctc_centroid_motion"
        self.calibration_profile = "ctc_fluo_n2dh_gowt1"
        self.cell_count = 0  # set after loading

        # Lazy-loaded data structures
        self._loaded = False
        self._frames: Dict[int, List[dict]] = defaultdict(list)  # frame -> [row, ...]
        self._track_info: Dict[str, dict] = {}  # track_id -> {start, end, parent}
        self._prev_positions: Dict[str, tuple] = {}  # track_id -> (x, y) at previous frame
        self._prev_areas: Dict[str, float] = {}  # track_id -> area at previous frame
        self._total_frames = 0
        self._field_extent = {"x_min": 0, "x_max": 1024, "y_min": 0, "y_max": 1024}

        # Signal normalization ranges (computed from data)
        self.signal_range = {
            'V_mean': (0.0, 1.0),
            'spike_rate': (0.0, 50.0),
            'release_proxy': (0.0, 1.0),
            'adaptation_state': (0.0, 1.0),
        }

    def _ensure_loaded(self):
        """Lazy-load the CSV data on first access."""
        if self._loaded:
            return

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_areas = []
            for row in reader:
                # Filter by sequence
                seq = row.get("sequence_id", "").strip()
                if seq != self.sequence:
                    continue

                frame = int(row["frame"])
                if self.max_frames is not None and frame >= self.max_frames:
                    continue

                # Split-based frame filtering (§14)
                if self.split_role == "calibration" and frame >= 70:
                    continue  # calibration = seq01 frames 0-69
                elif self.split_role == "validation" and frame < 70:
                    continue  # validation = seq01 frames 70-91

                self._frames[frame].append(row)

                # Track metadata
                tid = row.get("track_id", "0")
                if tid not in self._track_info:
                    self._track_info[tid] = {
                        "parent": row.get("parent_track_id", "0"),
                        "start": int(row.get("start_frame", frame)),
                        "end": int(row.get("end_frame", frame)),
                    }

                area = float(row.get("area", 0))
                all_areas.append(area)

                # Track field extent
                cx = float(row["centroid_x"])
                cy = float(row["centroid_y"])
                self._field_extent["x_min"] = min(self._field_extent["x_min"], cx)
                self._field_extent["x_max"] = max(self._field_extent["x_max"], cx)
                self._field_extent["y_min"] = min(self._field_extent["y_min"], cy)
                self._field_extent["y_max"] = max(self._field_extent["y_max"], cy)

        self._total_frames = max(self._frames.keys()) + 1 if self._frames else 0
        self._area_range = (min(all_areas), max(all_areas)) if all_areas else (1, 10000)

        # Cell count = max cells in any frame
        self.cell_count = max(len(cells) for cells in self._frames.values()) if self._frames else 0

        self._loaded = True
        print(f"  CTCRealDataAdapter seq={self.sequence}: {self._total_frames} frames, "
              f"{len(self._track_info)} tracks, max {self.cell_count} cells/frame, "
              f"area range [{self._area_range[0]:.0f}, {self._area_range[1]:.0f}]")

    @property
    def total_windows(self) -> int:
        """Number of available time windows in this sequence."""
        self._ensure_loaded()
        return self._total_frames

    def normalize_cell(self, cell: CellRecord) -> dict:
        """Return normalized signal dict [0,1] for cross-domain comparison."""
        return {
            'V_norm': _normalize(cell.V_mean, *self.signal_range['V_mean']),
            'spike_norm': _normalize(cell.spike_rate, *self.signal_range['spike_rate']),
            'release_norm': _normalize(cell.release_proxy, *self.signal_range['release_proxy']),
            'adapt_norm': _normalize(cell.adaptation_state, *self.signal_range['adaptation_state']),
        }

    def generate_cells(self, window_k: int) -> List[CellRecord]:
        """Generate CellRecord list for the given time window from real CTC data.

        Each row in the CSV for frame=window_k becomes one CellRecord.
        Signal channels are derived from real geometric properties:
          - V_mean: normalized cell area (proxy for cell size/health)
          - spike_rate: displacement from previous frame (motion velocity)
          - release_proxy: area change rate (growth/division signal)
          - adaptation_state: fraction of total lifetime elapsed
        """
        self._ensure_loaded()

        frame_rows = self._frames.get(window_k, [])
        if not frame_rows:
            return []

        cells = []
        for i, row in enumerate(frame_rows):
            cx = float(row["centroid_x"])
            cy = float(row["centroid_y"])
            area = float(row.get("area", 1000))
            tid = row.get("track_id", str(i))

            # Signal: normalized area (0-1)
            area_norm = _normalize(area, self._area_range[0], self._area_range[1])

            # Motion: displacement from previous frame
            prev_pos = self._prev_positions.get(tid)
            if prev_pos is not None:
                dx = cx - prev_pos[0]
                dy = cy - prev_pos[1]
                displacement = math.sqrt(dx * dx + dy * dy)
            else:
                displacement = 0.0
            self._prev_positions[tid] = (cx, cy)

            # Growth: area change rate
            prev_area = self._prev_areas.get(tid)
            if prev_area is not None and prev_area > 0:
                area_change = (area - prev_area) / prev_area
            else:
                area_change = 0.0
            self._prev_areas[tid] = area

            # Adaptation: fraction of track lifetime elapsed
            t_info = self._track_info.get(tid, {})
            t_start = t_info.get("start", 0)
            t_end = t_info.get("end", self._total_frames)
            track_len = max(t_end - t_start, 1)
            adaptation = min(1.0, (window_k - t_start) / track_len)

            # Spike rate: scale displacement to reasonable range
            spike_rate = min(50.0, displacement * 2.0)

            # Release proxy: clamp area change to [0, 1]
            release = max(0.0, min(1.0, 0.5 + area_change * 5.0))

            # Boundary distance
            x_ext = self._field_extent
            bdist = min(
                cx - x_ext["x_min"],
                x_ext["x_max"] - cx,
                cy - x_ext["y_min"],
                x_ext["y_max"] - cy
            )

            # Neighbor IDs: indices of other cells in this frame (nearest 4)
            neighbor_ids = self._find_nearest(frame_rows, i, cx, cy, k=4)

            # Provenance
            sig_dict = {"area": area, "displacement": displacement, "track_id": tid}
            prov = hashlib.sha256(
                f"{self.adapter_id}:{window_k}:{tid}:{sig_dict}".encode()
            ).hexdigest()[:16]

            cells.append(CellRecord(
                uid=f"ctc_{self.sequence}_{window_k}_{i}",
                node_id=i,
                x=cx, y=cy, z=0.0,
                V_mean=area_norm,
                V_slope=area_change,
                release_proxy=release,
                afferent_current=0.0,  # not available in CTC centroid data
                spike_rate=spike_rate,
                spike_regularity=0.8 if displacement < 5.0 else 0.3,
                timing_precision=0.05,
                adaptation_state=adaptation,
                signal_uncertainty=0.1,  # real data has higher uncertainty
                normal_x=0.0, normal_y=0.0, normal_z=1.0,
                boundary_distance=max(0, bdist),
                support_radius=math.sqrt(area / math.pi) if area > 0 else 1.0,
                neighbor_ids=neighbor_ids,
                patch_id=f"ctc_track_{tid}",
                provenance_hash=prov,
                source_signal_refs={
                    "window_k": window_k,
                    "node_id": i,
                    "adapter": self.adapter_name,
                    "track_id": tid,
                    "dataset": "Fluo-N2DH-GOWT1",
                    "doi": "10.5281/zenodo.15608211",
                    "real_data": True,
                },
                calibration_profile=self.calibration_profile,
            ))

        return cells

    @staticmethod
    def _find_nearest(frame_rows, self_idx, cx, cy, k=4):
        """Find k nearest neighbor indices in the same frame."""
        dists = []
        for j, row in enumerate(frame_rows):
            if j == self_idx:
                continue
            jx = float(row["centroid_x"])
            jy = float(row["centroid_y"])
            d = math.sqrt((cx - jx) ** 2 + (cy - jy) ** 2)
            dists.append((d, j))
        dists.sort()
        return [j for _, j in dists[:k]]

    def make_envelope(self, window_k: int) -> EnvelopeRecord:
        """Create an EnvelopeRecord for the given time window."""
        self._ensure_loaded()
        frame_rows = self._frames.get(window_k, [])
        n_cells = len(frame_rows)

        x_ext = self._field_extent
        field_w = x_ext["x_max"] - x_ext["x_min"]
        field_h = x_ext["y_max"] - x_ext["y_min"]

        return EnvelopeRecord(
            envelope_id=f"env_ctc_{self.sequence}_{window_k}_{uuid.uuid4().hex[:6]}",
            adapter_id=self.adapter_id,
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            geometry_model=self.geometry_model,
            signal_model=self.signal_model,
            spatial_extent={
                "type": "rectangle",
                "width": field_w, "height": field_h,
                "origin": [x_ext["x_min"], x_ext["y_min"]],
                "z": 0.0,
                "real_data": True,
                "dataset": "Fluo-N2DH-GOWT1",
            },
            temporal_extent={
                "window_k": window_k,
                "dt": 1.0,  # CTC frame interval
                "total_frames": self._total_frames,
            },
            noise_budget=0.10,  # higher for real data
            dissipation_budget=0.05,
            energy_in=50.0 + 2 * n_cells,
            energy_out=45.0 + 1.8 * n_cells,
        )
