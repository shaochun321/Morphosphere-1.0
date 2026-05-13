"""USGS Earthquake Source Adapter — Real geophysical motion data.

Reads USGS FDSN earthquake event CSV and produces CellRecord-compatible
sequences for the Morphosphere runtime. Each earthquake event maps to
a "cell" with spatial (lat/lon/depth) and signal (magnitude, gap) fields.

Data source:
  API: https://earthquake.usgs.gov/fdsnws/event/1/
  License: Public Domain (USGS)
  Format: CSV with time, latitude, longitude, depth, mag, magType, ...

Signal mapping (earthquake -> unified interface):
  x, y         <- longitude, latitude (geographic coordinates)
  z            <- depth (km, inverted: shallow = high z)
  V_mean       <- magnitude normalized [0,1]
  spike_rate   <- magnitude (raw, as "intensity" proxy)
  release_proxy <- depth_normalized (shallow = high energy release)
  adaptation   <- temporal position in sequence [0,1]
"""
from __future__ import annotations

import csv
import hashlib
import math
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import sys
_BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(_BASE / "src"))
from morphosphere.active_exec.source_adapters import CellRecord, EnvelopeRecord, _normalize


class USGSEarthquakeAdapter:
    """Source adapter for USGS earthquake event data.

    Maps earthquake events into time windows (1 window = 1 day),
    producing CellRecord sequences compatible with the Morphosphere pipeline.
    """

    def __init__(self, csv_path: Optional[str] = None,
                 window_hours: float = 24.0,
                 min_magnitude: float = 2.5,
                 split_role: str = "calibration",
                 max_windows: Optional[int] = None):
        self.csv_path = csv_path or str(_BASE / "data" / "usgs_earthquakes_2026.csv")
        self.window_hours = window_hours
        self.min_magnitude = min_magnitude
        self.split_role = split_role
        self.max_windows = max_windows

        self.adapter_id = f"usgs_eq_{uuid.uuid4().hex[:8]}"
        self.adapter_name = "usgs_earthquake"
        self.adapter_type = "geophysical_event"
        self.geometry_model = "geographic_3d"
        self.signal_model = "earthquake_magnitude"
        self.calibration_profile = "usgs_fdsn_earthquake"
        self.cell_count = 0

        self._loaded = False
        self._windows: Dict[int, List[dict]] = defaultdict(list)
        self._total_windows = 0
        self._mag_range = (2.5, 9.0)
        self._depth_range = (0.0, 700.0)
        self._field_extent = {
            "lon_min": -180, "lon_max": 180,
            "lat_min": -90, "lat_max": 90,
        }

        self.signal_range = {
            "V_mean": (0.0, 1.0),
            "spike_rate": (0.0, 10.0),
            "release_proxy": (0.0, 1.0),
            "adaptation_state": (0.0, 1.0),
        }

    def _ensure_loaded(self):
        if self._loaded:
            return

        events = []
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    mag = float(row.get("mag", 0))
                    if mag < self.min_magnitude:
                        continue
                    lat = float(row["latitude"])
                    lon = float(row["longitude"])
                    depth = float(row.get("depth", 0))
                    time_str = row.get("time", "")
                    events.append({
                        "time": time_str, "lat": lat, "lon": lon,
                        "depth": depth, "mag": mag,
                        "magType": row.get("magType", ""),
                        "place": row.get("place", ""),
                        "id": row.get("id", ""),
                    })
                except (ValueError, KeyError):
                    continue

        if not events:
            self._loaded = True
            return

        # Sort by time
        events.sort(key=lambda e: e["time"])

        # Parse time range
        t0_str = events[0]["time"]
        try:
            t0 = datetime.fromisoformat(t0_str.replace("Z", "+00:00"))
        except Exception:
            t0 = datetime(2026, 1, 1)

        # Assign events to time windows
        for ev in events:
            try:
                t = datetime.fromisoformat(ev["time"].replace("Z", "+00:00"))
                hours_elapsed = (t - t0).total_seconds() / 3600.0
            except Exception:
                hours_elapsed = 0.0
            window_k = int(hours_elapsed / self.window_hours)
            self._windows[window_k].append(ev)

        # Apply split logic
        all_keys = sorted(self._windows.keys())
        n = len(all_keys)
        if self.split_role == "calibration":
            keep = set(all_keys[:int(n * 0.6)])
        elif self.split_role == "validation":
            keep = set(all_keys[int(n * 0.6):int(n * 0.8)])
        elif self.split_role == "holdout":
            keep = set(all_keys[int(n * 0.8):])
        else:
            keep = set(all_keys)

        self._windows = {k: v for k, v in self._windows.items() if k in keep}
        if self.max_windows:
            limited = dict(list(sorted(self._windows.items()))[:self.max_windows])
            self._windows = limited

        self._total_windows = max(self._windows.keys()) + 1 if self._windows else 0
        self.cell_count = max(
            (len(evs) for evs in self._windows.values()), default=0
        )

        mags = [ev["mag"] for evs in self._windows.values() for ev in evs]
        if mags:
            self._mag_range = (min(mags), max(mags))
        depths = [ev["depth"] for evs in self._windows.values() for ev in evs]
        if depths:
            self._depth_range = (min(depths), max(depths))

        self._loaded = True
        total_events = sum(len(v) for v in self._windows.values())
        print(f"  USGSEarthquakeAdapter: {len(self._windows)} windows, "
              f"{total_events} events, mag {self._mag_range[0]:.1f}-{self._mag_range[1]:.1f}")

    @property
    def total_windows(self) -> int:
        self._ensure_loaded()
        return self._total_windows

    def normalize_cell(self, cell: CellRecord) -> dict:
        return {
            "V_norm": _normalize(cell.V_mean, *self.signal_range["V_mean"]),
            "spike_norm": _normalize(cell.spike_rate, *self.signal_range["spike_rate"]),
            "release_norm": _normalize(cell.release_proxy, *self.signal_range["release_proxy"]),
            "adapt_norm": _normalize(cell.adaptation_state, *self.signal_range["adaptation_state"]),
        }

    def generate_cells(self, window_k: int) -> List[CellRecord]:
        self._ensure_loaded()
        events = self._windows.get(window_k, [])
        if not events:
            return []

        cells = []
        for i, ev in enumerate(events):
            lat, lon, depth, mag = ev["lat"], ev["lon"], ev["depth"], ev["mag"]

            mag_norm = _normalize(mag, self._mag_range[0], self._mag_range[1])
            depth_norm = _normalize(depth, self._depth_range[0], self._depth_range[1])
            release = 1.0 - depth_norm  # shallow = more surface energy

            prov = hashlib.sha256(
                f"{self.adapter_id}:{window_k}:{ev['id']}".encode()
            ).hexdigest()[:16]

            cells.append(CellRecord(
                uid=f"usgs_{window_k}_{i}",
                node_id=i,
                x=lon, y=lat, z=depth,
                V_mean=mag_norm,
                V_slope=0.0,
                release_proxy=release,
                afferent_current=0.0,
                spike_rate=mag,
                spike_regularity=0.5,
                timing_precision=0.01,
                adaptation_state=window_k / max(self._total_windows, 1),
                signal_uncertainty=0.05,
                normal_x=0.0, normal_y=0.0, normal_z=1.0,
                boundary_distance=100.0,
                support_radius=10.0 ** (mag / 2.0),
                neighbor_ids=self._find_nearest(events, i, lat, lon),
                patch_id=f"usgs_w{window_k}",
                provenance_hash=prov,
                source_signal_refs={
                    "window_k": window_k,
                    "node_id": i,
                    "adapter": self.adapter_name,
                    "event_id": ev["id"],
                    "dataset": "USGS_FDSN",
                    "real_data": True,
                },
                calibration_profile=self.calibration_profile,
            ))
        return cells

    @staticmethod
    def _find_nearest(events, self_idx, lat, lon, k=4):
        dists = []
        for j, ev in enumerate(events):
            if j == self_idx:
                continue
            d = math.sqrt((lat - ev["lat"]) ** 2 + (lon - ev["lon"]) ** 2)
            dists.append((d, j))
        dists.sort()
        return [j for _, j in dists[:k]]

    def make_envelope(self, window_k: int) -> EnvelopeRecord:
        self._ensure_loaded()
        events = self._windows.get(window_k, [])
        n = len(events)
        return EnvelopeRecord(
            envelope_id=f"env_usgs_{window_k}_{uuid.uuid4().hex[:6]}",
            adapter_id=self.adapter_id,
            adapter_name=self.adapter_name,
            adapter_type=self.adapter_type,
            geometry_model=self.geometry_model,
            signal_model=self.signal_model,
            spatial_extent={
                "type": "geographic",
                "lon_range": [-180, 180],
                "lat_range": [-90, 90],
                "real_data": True,
                "dataset": "USGS_FDSN",
            },
            temporal_extent={
                "window_k": window_k,
                "dt": self.window_hours * 3600,
                "total_windows": self._total_windows,
            },
            noise_budget=0.05,
            dissipation_budget=0.02,
            energy_in=10.0 + n * 2.0,
            energy_out=8.0 + n * 1.5,
        )
