"""PhC-C2DH-U373 Source Adapter — Phase Contrast Glioblastoma Cell Tracking.

Reads centroids extracted from PhC-C2DH-U373 training data (Cell Tracking
Challenge) and produces CellRecord sequences. This is a DIFFERENT imaging
modality (phase contrast) and cell type (glioblastoma) from the existing
Fluo-N2DH-GOWT1 fluorescence data.

Data source:
  Dataset: PhC-C2DH-U373 (Cell Tracking Challenge)
  URL: http://celltrackingchallenge.net/2d-datasets/
  License: CC-BY-4.0
  Modality: Phase Contrast microscopy
  Cell type: Glioblastoma-astrocytoma U373 cells
  Motion regime: Slow crawling migration (distinct from GOWT1 division)

Signal mapping:
  x, y         <- centroid_x, centroid_y
  z            <- 0.0 (2D)
  V_mean       <- area_normalized
  spike_rate   <- inter-frame displacement
  release_proxy <- area change rate
  adaptation   <- track lifetime fraction
"""
from __future__ import annotations

import csv
import hashlib
import math
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import sys
_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE / "src"))
from morphosphere.active_exec.source_adapters import CellRecord, EnvelopeRecord, _normalize


class PhCU373Adapter:
    """Source adapter for PhC-C2DH-U373 phase contrast cell tracking data.

    Same interface as CTCRealDataAdapter but reads from phc_u373_centroids.csv.
    """

    def __init__(self, sequence: str = "01",
                 csv_path: Optional[str] = None,
                 max_frames: Optional[int] = None,
                 split_role: str = "calibration"):
        self.sequence = sequence
        self.csv_path = csv_path or str(_BASE / "data" / "phc_u373_centroids.csv")
        self.max_frames = max_frames
        self.split_role = split_role

        if split_role == "holdout":
            self.sequence = "02"
        elif split_role in ("calibration", "validation"):
            self.sequence = "01"

        self.adapter_id = f"phc_u373_{sequence}_{uuid.uuid4().hex[:8]}"
        self.adapter_name = f"phc_u373_seq{sequence}"
        self.adapter_type = "ctc_phase_contrast"
        self.geometry_model = "2d_plane"
        self.signal_model = "phc_centroid_motion"
        self.calibration_profile = "ctc_phc_c2dh_u373"
        self.cell_count = 0

        self._loaded = False
        self._frames: Dict[int, List[dict]] = defaultdict(list)
        self._track_info: Dict[str, dict] = {}
        self._prev_positions: Dict[str, tuple] = {}
        self._prev_areas: Dict[str, float] = {}
        self._total_frames = 0
        self._area_range = (1, 50000)
        self._field_extent = {"x_min": 0, "x_max": 1024, "y_min": 0, "y_max": 1024}

        self.signal_range = {
            "V_mean": (0.0, 1.0),
            "spike_rate": (0.0, 30.0),
            "release_proxy": (0.0, 1.0),
            "adaptation_state": (0.0, 1.0),
        }

    def _ensure_loaded(self):
        if self._loaded:
            return

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            all_areas = []
            for row in reader:
                seq = row.get("sequence_id", "").strip()
                if seq != self.sequence:
                    continue
                frame = int(row["frame"])
                if self.max_frames is not None and frame >= self.max_frames:
                    continue
                # Split-based filtering
                if self.split_role == "calibration" and frame >= 80:
                    continue
                elif self.split_role == "validation" and frame < 80:
                    continue

                self._frames[frame].append(row)
                tid = row.get("track_id", "0")
                if tid not in self._track_info:
                    self._track_info[tid] = {
                        "parent": row.get("parent_track_id", "0"),
                        "start": int(row.get("start_frame", frame)),
                        "end": int(row.get("end_frame", frame)),
                    }
                area = float(row.get("area", 0))
                all_areas.append(area)

                cx = float(row["centroid_x"])
                cy = float(row["centroid_y"])
                self._field_extent["x_min"] = min(self._field_extent["x_min"], cx)
                self._field_extent["x_max"] = max(self._field_extent["x_max"], cx)
                self._field_extent["y_min"] = min(self._field_extent["y_min"], cy)
                self._field_extent["y_max"] = max(self._field_extent["y_max"], cy)

        self._total_frames = max(self._frames.keys()) + 1 if self._frames else 0
        self._area_range = (min(all_areas), max(all_areas)) if all_areas else (1, 50000)
        self.cell_count = max(
            (len(cells) for cells in self._frames.values()), default=0
        )
        self._loaded = True
        print(f"  PhCU373Adapter seq={self.sequence}: {self._total_frames} frames, "
              f"{len(self._track_info)} tracks, max {self.cell_count} cells/frame")

    @property
    def total_windows(self) -> int:
        self._ensure_loaded()
        return self._total_frames

    def normalize_cell(self, cell: CellRecord) -> dict:
        return {
            "V_norm": _normalize(cell.V_mean, *self.signal_range["V_mean"]),
            "spike_norm": _normalize(cell.spike_rate, *self.signal_range["spike_rate"]),
            "release_norm": _normalize(cell.release_proxy, *self.signal_range["release_proxy"]),
            "adapt_norm": _normalize(cell.adaptation_state, *self.signal_range["adaptation_state"]),
        }

    def generate_cells(self, window_k: int) -> List[CellRecord]:
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

            area_norm = _normalize(area, self._area_range[0], self._area_range[1])

            prev_pos = self._prev_positions.get(tid)
            if prev_pos is not None:
                dx = cx - prev_pos[0]
                dy = cy - prev_pos[1]
                displacement = math.sqrt(dx * dx + dy * dy)
            else:
                displacement = 0.0
            self._prev_positions[tid] = (cx, cy)

            prev_area = self._prev_areas.get(tid)
            if prev_area is not None and prev_area > 0:
                area_change = (area - prev_area) / prev_area
            else:
                area_change = 0.0
            self._prev_areas[tid] = area

            t_info = self._track_info.get(tid, {})
            t_start = t_info.get("start", 0)
            t_end = t_info.get("end", self._total_frames)
            track_len = max(t_end - t_start, 1)
            adaptation = min(1.0, (window_k - t_start) / track_len)

            spike_rate = min(30.0, displacement * 1.5)
            release = max(0.0, min(1.0, 0.5 + area_change * 5.0))

            neighbor_ids = self._find_nearest(frame_rows, i, cx, cy)

            prov = hashlib.sha256(
                f"{self.adapter_id}:{window_k}:{tid}".encode()
            ).hexdigest()[:16]

            cells.append(CellRecord(
                uid=f"phc_{self.sequence}_{window_k}_{i}",
                node_id=i,
                x=cx, y=cy, z=0.0,
                V_mean=area_norm,
                V_slope=area_change,
                release_proxy=release,
                afferent_current=0.0,
                spike_rate=spike_rate,
                spike_regularity=0.9 if displacement < 3.0 else 0.4,
                timing_precision=0.05,
                adaptation_state=adaptation,
                signal_uncertainty=0.08,
                normal_x=0.0, normal_y=0.0, normal_z=1.0,
                boundary_distance=max(0, min(
                    cx - self._field_extent["x_min"],
                    self._field_extent["x_max"] - cx,
                    cy - self._field_extent["y_min"],
                    self._field_extent["y_max"] - cy,
                )),
                support_radius=math.sqrt(area / math.pi) if area > 0 else 1.0,
                neighbor_ids=neighbor_ids,
                patch_id=f"phc_track_{tid}",
                provenance_hash=prov,
                source_signal_refs={
                    "window_k": window_k,
                    "node_id": i,
                    "adapter": self.adapter_name,
                    "track_id": tid,
                    "dataset": "PhC-C2DH-U373",
                    "real_data": True,
                },
                calibration_profile=self.calibration_profile,
            ))
        return cells

    @staticmethod
    def _find_nearest(frame_rows, self_idx, cx, cy, k=4):
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
        self._ensure_loaded()
        frame_rows = self._frames.get(window_k, [])
        n = len(frame_rows)
        x_ext = self._field_extent
        return EnvelopeRecord(
            envelope_id=f"env_phc_{self.sequence}_{window_k}_{uuid.uuid4().hex[:6]}",
            adapter_id=self.adapter_id,
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            geometry_model=self.geometry_model,
            signal_model=self.signal_model,
            spatial_extent={
                "type": "rectangle",
                "width": x_ext["x_max"] - x_ext["x_min"],
                "height": x_ext["y_max"] - x_ext["y_min"],
                "real_data": True,
                "dataset": "PhC-C2DH-U373",
            },
            temporal_extent={
                "window_k": window_k,
                "dt": 1.0,
                "total_frames": self._total_frames,
            },
            noise_budget=0.12,
            dissipation_budget=0.06,
            energy_in=40.0 + 3 * n,
            energy_out=35.0 + 2.5 * n,
        )
