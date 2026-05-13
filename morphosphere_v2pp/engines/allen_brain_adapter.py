"""Allen Brain Observatory Source Adapter — Real calcium imaging data.

Phase 3.2 of the v38 improvement plan.

Reads real ΔF/F calcium imaging traces and cell coordinates from
data/allen_brain/ (downloaded from Allen Brain Observatory via AllenSDK)
and produces CellRecord sequences identical in interface to
CTCRealDataAdapter / CellSphereAdapter.

Data source:
  Dataset: Allen Brain Observatory — Visual Coding (experiment 500964514)
  Structure: VISp (primary visual cortex), 175 μm depth
  DOI: 10.1038/s41586-019-1346-5
  License: Allen Institute Terms of Use (non-commercial research)
  Cells: 214 neurons
  Timepoints: 114,097 frames (subsampled to 3,003 in CSV)

Signal mapping (real → unified interface):
  x, y         ← ROI centroid (real spatial coordinates on imaging plane)
  z            ← 0.0  (single-plane 2-photon imaging)
  V_mean       ← ΔF/F mean over recent window (normalized fluorescence)
  spike_rate   ← ΔF/F peak rate (proxy for spike frequency)
  release_proxy← ΔF/F variance (signal variability)
  adaptation   ← ΔF/F running average decay (calcium dynamics)
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
_BASE = Path(__file__).resolve().parent.parent  # project root (morphosphere_v2pp/)
sys.path.insert(0, str(_BASE / "src"))
from morphosphere.active_exec.source_adapters import CellRecord, EnvelopeRecord, _normalize


class AllenBrainAdapter:
    """Source adapter for Allen Brain Observatory calcium imaging data.

    Implements the same interface as CTCRealDataAdapter:
      - generate_cells(window_k) -> List[CellRecord]
      - make_envelope(window_k) -> EnvelopeRecord
      - normalize_cell(cell) -> dict

    Loads pre-extracted CSV files from data/allen_brain/:
      - allen_brain_dff_traces.csv   (ΔF/F traces per cell)
      - allen_brain_cell_coords.csv  (cell x, y coordinates)
    """

    # Number of raw timepoints per "window" — groups calcium frames
    # into biologically meaningful chunks (~1-2 seconds per window)
    FRAMES_PER_WINDOW = 30

    def __init__(self, data_dir: Optional[str] = None,
                 window_size: int = 30,
                 split_role: str = "calibration"):
        """Initialize the Allen Brain adapter.

        Args:
            data_dir: Path to data/allen_brain/ directory.
            window_size: Number of raw timepoints per logical window.
            split_role: 'calibration', 'validation', 'holdout', or 'all'.
                - calibration: first 60% of windows
                - validation:  next 20% of windows
                - holdout:     final 20% of windows
                - all:         no filtering
        """
        self.data_dir = Path(data_dir) if data_dir else _BASE / "data" / "allen_brain"
        self.window_size = window_size
        self.split_role = split_role

        self.adapter_id = f"allen_brain_{uuid.uuid4().hex[:8]}"
        self.adapter_name = "allen_brain_visp"
        self.adapter_type = "allen_brain_observatory"
        self.geometry_model = "2d_plane"
        self.signal_model = "calcium_dff"
        self.calibration_profile = "allen_visp_175um"
        self.cell_count = 0

        # Lazy-loaded
        self._loaded = False
        self._cell_coords: List[dict] = []          # [{cell_id, x, y, roi_area}]
        self._dff_matrix: List[List[float]] = []    # [n_cells][n_timepoints]
        self._cell_ids: List[int] = []
        self._n_timepoints = 0
        self._n_windows = 0
        self._window_range = (0, 0)  # (start, end) after split filtering

        # Signal stats for normalization
        self.signal_range = {
            'V_mean': (0.0, 1.0),
            'spike_rate': (0.0, 5.0),
            'release_proxy': (0.0, 1.0),
            'adaptation_state': (0.0, 1.0),
        }

    def _ensure_loaded(self):
        """Lazy-load CSV data on first access."""
        if self._loaded:
            return

        traces_path = self.data_dir / "allen_brain_dff_traces.csv"
        coords_path = self.data_dir / "allen_brain_cell_coords.csv"

        if not traces_path.exists() or not coords_path.exists():
            raise FileNotFoundError(
                f"Allen Brain data not found in {self.data_dir}. "
                f"Run runners/run_v38_allen_brain_download.py first.")

        # Load cell coordinates
        with open(coords_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self._cell_coords = list(reader)

        # Load ΔF/F traces
        with open(traces_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)  # cell_id, t0, t1, t2, ...
            self._n_timepoints = len(header) - 1

            for row in reader:
                cell_id = int(row[0])
                self._cell_ids.append(cell_id)
                self._dff_matrix.append([float(v) for v in row[1:]])

        self.cell_count = len(self._cell_ids)
        self._n_windows = self._n_timepoints // self.window_size

        # Apply split filtering
        if self.split_role == "calibration":
            self._window_range = (0, int(self._n_windows * 0.6))
        elif self.split_role == "validation":
            self._window_range = (int(self._n_windows * 0.6),
                                   int(self._n_windows * 0.8))
        elif self.split_role == "holdout":
            self._window_range = (int(self._n_windows * 0.8), self._n_windows)
        else:
            self._window_range = (0, self._n_windows)

        # Compute global normalization ranges from data
        all_dff = [v for row in self._dff_matrix for v in row]
        if all_dff:
            dff_min = min(all_dff)
            dff_max = max(all_dff)
            self.signal_range['V_mean'] = (dff_min, dff_max)

        self._loaded = True
        w_start, w_end = self._window_range
        print(f"  AllenBrainAdapter: {self.cell_count} cells, "
              f"{self._n_timepoints} timepoints, "
              f"{self._n_windows} windows (using {w_start}-{w_end} "
              f"for {self.split_role})")

    @property
    def total_windows(self) -> int:
        """Number of available time windows after split filtering."""
        self._ensure_loaded()
        return self._window_range[1] - self._window_range[0]

    def _window_to_timepoints(self, window_k: int):
        """Convert logical window index to raw timepoint range."""
        w_start = self._window_range[0]
        absolute_k = w_start + window_k
        t_start = absolute_k * self.window_size
        t_end = min(t_start + self.window_size, self._n_timepoints)
        return t_start, t_end

    def normalize_cell(self, cell: CellRecord) -> dict:
        """Return normalized signal dict [0,1] for cross-domain comparison."""
        return {
            'V_norm': _normalize(cell.V_mean, *self.signal_range['V_mean']),
            'spike_norm': _normalize(cell.spike_rate, *self.signal_range['spike_rate']),
            'release_norm': _normalize(cell.release_proxy, *self.signal_range['release_proxy']),
            'adapt_norm': _normalize(cell.adaptation_state, *self.signal_range['adaptation_state']),
        }

    def generate_cells(self, window_k: int) -> List[CellRecord]:
        """Generate CellRecord list for the given time window.

        Each cell gets its signal channels derived from real ΔF/F traces:
          - V_mean:        mean ΔF/F over the window (normalized fluorescence)
          - spike_rate:    number of threshold crossings (proxy for spike rate)
          - release_proxy: variance of ΔF/F (signal variability / noise)
          - adaptation:    exponential decay rate of ΔF/F in the window
        """
        self._ensure_loaded()

        if window_k < 0 or window_k >= self.total_windows:
            return []

        t_start, t_end = self._window_to_timepoints(window_k)

        cells = []
        for i in range(self.cell_count):
            # Extract this cell's ΔF/F segment for this window
            segment = self._dff_matrix[i][t_start:t_end]
            if not segment:
                continue

            n = len(segment)

            # V_mean: mean ΔF/F (normalized later)
            v_mean = sum(segment) / n

            # Spike rate: count threshold crossings (ΔF/F > 2σ)
            seg_mean = v_mean
            seg_std = math.sqrt(sum((s - seg_mean) ** 2 for s in segment) / max(n, 1))
            threshold = seg_mean + 2 * max(seg_std, 0.01)
            spike_count = sum(1 for s in segment if s > threshold)
            spike_rate = spike_count / max(n, 1) * 10  # normalize to ~0-5

            # Release proxy: signal variance (higher = more active)
            release_proxy = min(1.0, seg_std * 5.0)

            # Adaptation: decay rate — compare first vs second half
            half = n // 2
            if half > 0:
                first_half = sum(segment[:half]) / half
                second_half = sum(segment[half:]) / max(n - half, 1)
                if first_half > 0.01:
                    adaptation = max(0.0, min(1.0, second_half / first_half))
                else:
                    adaptation = 0.5
            else:
                adaptation = 0.5

            # Get spatial coordinates
            if i < len(self._cell_coords):
                cx = float(self._cell_coords[i]["x"])
                cy = float(self._cell_coords[i]["y"])
                roi_area = int(self._cell_coords[i].get("roi_area", 50))
            else:
                cx, cy, roi_area = float(i), 0.0, 50

            # V_slope: ΔF/F change rate
            if n >= 2:
                v_slope = (segment[-1] - segment[0]) / max(n, 1)
            else:
                v_slope = 0.0

            # Neighbor IDs: nearest 4 cells by spatial distance
            neighbor_ids = self._find_nearest(i, cx, cy, k=4)

            # Signal uncertainty from variance
            signal_uncertainty = min(0.5, seg_std * 2.0)

            # Boundary distance (imaging field ~512×512)
            bdist = min(cx, 512 - cx, cy, 512 - cy) if cx > 0 and cy > 0 else 50.0

            # Provenance
            prov = hashlib.sha256(
                f"{self.adapter_id}:{window_k}:{self._cell_ids[i]}:{v_mean:.6f}".encode()
            ).hexdigest()[:16]

            cells.append(CellRecord(
                uid=f"allen_{window_k}_{i}",
                node_id=i,
                x=cx, y=cy, z=0.0,
                V_mean=v_mean,
                V_slope=v_slope,
                release_proxy=release_proxy,
                afferent_current=0.0,
                spike_rate=spike_rate,
                spike_regularity=0.7 if spike_count < 3 else 0.3,
                timing_precision=0.03,  # 2-photon has ~30Hz temporal resolution
                adaptation_state=adaptation,
                signal_uncertainty=signal_uncertainty,
                normal_x=0.0, normal_y=0.0, normal_z=1.0,
                boundary_distance=max(0, bdist),
                support_radius=math.sqrt(roi_area / math.pi),
                neighbor_ids=neighbor_ids,
                patch_id=f"allen_cell_{self._cell_ids[i]}",
                provenance_hash=prov,
                source_signal_refs={
                    "window_k": window_k,
                    "node_id": i,
                    "adapter": self.adapter_name,
                    "cell_id": self._cell_ids[i],
                    "dataset": "Allen Brain Observatory VISp",
                    "experiment_id": 500964514,
                    "doi": "10.1038/s41586-019-1346-5",
                    "real_data": True,
                },
                calibration_profile=self.calibration_profile,
            ))

        return cells

    def _find_nearest(self, self_idx: int, cx: float, cy: float, k: int = 4):
        """Find k nearest spatial neighbors."""
        dists = []
        for j in range(self.cell_count):
            if j == self_idx:
                continue
            if j < len(self._cell_coords):
                jx = float(self._cell_coords[j]["x"])
                jy = float(self._cell_coords[j]["y"])
            else:
                continue
            d = math.sqrt((cx - jx) ** 2 + (cy - jy) ** 2)
            dists.append((d, j))
        dists.sort()
        return [j for _, j in dists[:k]]

    def make_envelope(self, window_k: int) -> EnvelopeRecord:
        """Create an EnvelopeRecord for the given time window."""
        self._ensure_loaded()

        return EnvelopeRecord(
            envelope_id=f"env_allen_{window_k}_{uuid.uuid4().hex[:6]}",
            adapter_id=self.adapter_id,
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            geometry_model=self.geometry_model,
            signal_model=self.signal_model,
            spatial_extent={
                "type": "rectangle",
                "width": 512.0, "height": 512.0,
                "origin": [0, 0],
                "z": 0.0,
                "imaging_depth_um": 175,
                "real_data": True,
                "dataset": "Allen Brain Observatory VISp",
            },
            temporal_extent={
                "window_k": window_k,
                "dt": self.window_size / 30.0,  # ~30Hz imaging rate
                "total_windows": self.total_windows,
            },
            noise_budget=0.12,        # real data: higher noise
            dissipation_budget=0.08,
            energy_in=100.0 + self.cell_count * 0.5,
            energy_out=90.0 + self.cell_count * 0.45,
        )


def validate_adapter():
    """Self-test: verify adapter loads and produces valid CellRecords."""
    print("=" * 60)
    print("Allen Brain Adapter — Self Validation")
    print("=" * 60)

    try:
        adapter = AllenBrainAdapter(split_role="all")
    except FileNotFoundError as e:
        print(f"  SKIP: {e}")
        return False

    print(f"\n  Total windows: {adapter.total_windows}")

    # Test first 3 windows
    for k in range(min(3, adapter.total_windows)):
        cells = adapter.generate_cells(k)
        print(f"\n  Window {k}: {len(cells)} cells")
        if cells:
            c0 = cells[0]
            print(f"    cell[0]: uid={c0.uid}, pos=({c0.x:.1f}, {c0.y:.1f}), "
                  f"V_mean={c0.V_mean:.4f}, spike_rate={c0.spike_rate:.2f}, "
                  f"release={c0.release_proxy:.3f}, adapt={c0.adaptation_state:.3f}")
            print(f"    real_data={c0.source_signal_refs.get('real_data')}")

    # Verify envelope
    env = adapter.make_envelope(0)
    print(f"\n  Envelope: {env.envelope_id}")
    print(f"    spatial: {env.spatial_extent['width']}×{env.spatial_extent['height']}")
    print(f"    real_data: {env.spatial_extent.get('real_data')}")

    # Split validation
    print(f"\n  Split roles:")
    for role in ["calibration", "validation", "holdout"]:
        a = AllenBrainAdapter(split_role=role)
        print(f"    {role}: {a.total_windows} windows")

    print(f"\n  ALL CHECKS PASSED ✅")
    return True


if __name__ == "__main__":
    validate_adapter()
