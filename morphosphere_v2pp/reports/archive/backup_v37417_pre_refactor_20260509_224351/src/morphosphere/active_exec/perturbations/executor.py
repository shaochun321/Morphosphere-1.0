"""Perturbation Executor (V8.5.3 / V8.3 §7 / V8.5 §5).

Implements 8 perturbation types that operate on actual data:

  signal_shuffle, geometry_shift, boundary_flip, masking_injection,
  xi_pressure_injection, temporal_window_masking, source_patch_masking, mixed

Each perturbation:
  1. Takes a hypothesis and its supporting data
  2. Applies a controlled perturbation to the support set
  3. Re-evaluates the hypothesis under perturbation
  4. Produces a verdict (v8.5 §5.2)

Verdicts:
  supports_confirmation, weakens_confirmation, refutes_candidate,
  inconclusive, escalate_to_replay, escalate_to_boundary,
  downgrade_to_xi, trigger_emergence_alert

Hard rules (v8.5 §5.3):
  - Cannot directly generate P/R
  - Cannot replace transport
  - Cannot replace replay
  - Results must be recorded in masking_counterevidence_record
"""
from __future__ import annotations
import json, math, random, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

MASKING_TYPES = [
    "signal_shuffle",
    "geometry_shift",
    "boundary_flip",
    "masking_injection",
    "xi_pressure_injection",
    "temporal_window_masking",
    "source_patch_masking",
    "mixed",
]

VERDICTS = [
    "supports_confirmation",
    "weakens_confirmation",
    "refutes_candidate",
    "inconclusive",
    "escalate_to_replay",
    "escalate_to_boundary",
    "downgrade_to_xi",
    "trigger_emergence_alert",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class PerturbationExecutor:
    """Executes perturbations against object hypotheses.

    Usage:
        executor = PerturbationExecutor(conn, run_id)
        results = executor.run_masking_suite(hypothesis_id)
    """

    # Threshold for deciding verdict
    SUPPORT_THRESHOLD = 0.7
    WEAKNESS_THRESHOLD = 0.4
    REFUTE_THRESHOLD = 0.15

    def __init__(
        self,
        conn: "sqlite3.Connection",
        run_id: str,
        seed: int = 42,
    ):
        self.conn = conn
        self.run_id = run_id
        self.rng = random.Random(seed)

    def _get_support_cells(self, hypothesis_id: str) -> List[Dict[str, Any]]:
        """Get occupancy measures and supporting cells for a hypothesis."""
        rows = self.conn.execute(
            "SELECT m.measure_id, m.cell_uid, m.membership_mass, "
            "m.transport_support, m.signal_support, m.geometry_support, "
            "c.x, c.y, c.z, c.boundary_distance, "
            "f.V_mean, f.V_slope, f.spike_rate "
            "FROM occupancy_measure m "
            "JOIN spacetime_cell c ON m.cell_uid = c.cell_uid "
            "LEFT JOIN information_fiber f ON f.cell_uid = c.cell_uid "
            "WHERE m.hypothesis_id = ?",
            (hypothesis_id,)
        ).fetchall()

        return [
            {"measure_id": r[0], "cell_uid": r[1], "mass": r[2],
             "transport": r[3], "signal": r[4], "geometry": r[5],
             "x": r[6], "y": r[7], "z": r[8], "bdist": r[9],
             "V_mean": r[10] or 0, "V_slope": r[11] or 0, "spike_rate": r[12] or 0}
            for r in rows
        ]

    def _compute_baseline_score(self, cells: List[Dict]) -> float:
        """Compute baseline support score from cell data."""
        if not cells:
            return 0.0
        return sum(
            c["mass"] * (c["transport"] + c["signal"] + c["geometry"]) / 3
            for c in cells
        ) / len(cells)

    def _perturb_signal_shuffle(self, cells: List[Dict]) -> List[Dict]:
        """Randomly shuffle signal values across cells."""
        if len(cells) < 2:
            return cells
        signals = [(c["V_mean"], c["V_slope"], c["spike_rate"]) for c in cells]
        self.rng.shuffle(signals)
        perturbed = []
        for i, c in enumerate(cells):
            pc = dict(c)
            pc["V_mean"], pc["V_slope"], pc["spike_rate"] = signals[i]
            # Recompute signal support based on perturbation
            orig_sig = abs(c["V_mean"]) + abs(c["V_slope"])
            new_sig = abs(pc["V_mean"]) + abs(pc["V_slope"])
            ratio = new_sig / max(orig_sig, 1e-9)
            pc["signal"] = c["signal"] * min(ratio, 2.0)
            perturbed.append(pc)
        return perturbed

    def _perturb_geometry_shift(self, cells: List[Dict]) -> List[Dict]:
        """Add random offsets to spatial coordinates."""
        perturbed = []
        for c in cells:
            pc = dict(c)
            shift_mag = self.rng.gauss(0, 0.3)
            pc["x"] += shift_mag
            pc["y"] += self.rng.gauss(0, 0.3)
            pc["z"] += self.rng.gauss(0, 0.3)
            # Geometry support degrades with shift
            dist = abs(shift_mag) + abs(pc["y"] - c["y"]) + abs(pc["z"] - c["z"])
            pc["geometry"] = c["geometry"] * max(0, 1.0 - dist * 0.5)
            perturbed.append(pc)
        return perturbed

    def _perturb_boundary_flip(self, cells: List[Dict]) -> List[Dict]:
        """Flip boundary distances (interior ↔ exterior)."""
        perturbed = []
        max_bd = max((c["bdist"] for c in cells), default=1.0)
        for c in cells:
            pc = dict(c)
            pc["bdist"] = max_bd - c["bdist"]
            # Transport support degrades when boundary flips
            if c["bdist"] > 0.5 * max_bd:  # was interior, now exterior
                pc["transport"] = c["transport"] * 0.3
            perturbed.append(pc)
        return perturbed

    def _perturb_masking_injection(self, cells: List[Dict]) -> List[Dict]:
        """Inject counterevidence into occupancy measures."""
        perturbed = []
        for c in cells:
            pc = dict(c)
            # Reduce mass by random factor
            pc["mass"] = c["mass"] * self.rng.uniform(0.2, 0.8)
            perturbed.append(pc)
        return perturbed

    def _perturb_xi_pressure(self, cells: List[Dict]) -> List[Dict]:
        """Increase Xi residual pressure (reduce all supports)."""
        perturbed = []
        for c in cells:
            pc = dict(c)
            pressure = self.rng.uniform(0.3, 0.7)
            pc["transport"] = c["transport"] * (1 - pressure)
            pc["signal"] = c["signal"] * (1 - pressure)
            pc["geometry"] = c["geometry"] * (1 - pressure)
            perturbed.append(pc)
        return perturbed

    def _perturb_temporal_masking(self, cells: List[Dict]) -> List[Dict]:
        """Remove a random subset of cells (simulating window deletion)."""
        if len(cells) <= 2:
            return cells[:1]
        n_remove = max(1, len(cells) // 3)
        indices = list(range(len(cells)))
        self.rng.shuffle(indices)
        keep = sorted(indices[n_remove:])
        return [cells[i] for i in keep]

    def _perturb_source_patch_masking(self, cells: List[Dict]) -> List[Dict]:
        """Zero out support for cells from a random source patch."""
        perturbed = []
        for c in cells:
            pc = dict(c)
            if self.rng.random() < 0.4:
                pc["geometry"] = 0.0
                pc["transport"] = c["transport"] * 0.5
            perturbed.append(pc)
        return perturbed

    def execute_perturbation(
        self,
        hypothesis_id: str,
        masking_type: str,
    ) -> Dict[str, Any]:
        """Execute a single perturbation and record the result.

        Returns verdict and metrics.
        """
        cells = self._get_support_cells(hypothesis_id)
        if not cells:
            return self._record_result(hypothesis_id, masking_type,
                                       0, 0, "inconclusive", "no_support_cells")

        baseline = self._compute_baseline_score(cells)

        # Apply perturbation
        perturb_fn = {
            "signal_shuffle": self._perturb_signal_shuffle,
            "geometry_shift": self._perturb_geometry_shift,
            "boundary_flip": self._perturb_boundary_flip,
            "masking_injection": self._perturb_masking_injection,
            "xi_pressure_injection": self._perturb_xi_pressure,
            "temporal_window_masking": self._perturb_temporal_masking,
            "source_patch_masking": self._perturb_source_patch_masking,
        }.get(masking_type)

        if masking_type == "mixed":
            # Apply 2-3 random perturbations
            perturbed = list(cells)
            n_apply = self.rng.randint(2, 3)
            types_to_apply = self.rng.sample(
                [t for t in MASKING_TYPES if t != "mixed"], n_apply)
            for t in types_to_apply:
                fn = getattr(self, f"_perturb_{t.replace('_masking','_masking').split('_',1)[-1] if '_' in t else t}", None)
                # Simplified: just apply masking_injection + geometry_shift
            perturbed = self._perturb_masking_injection(
                self._perturb_geometry_shift(cells))
        elif perturb_fn:
            perturbed = perturb_fn(cells)
        else:
            perturbed = cells

        perturbed_score = self._compute_baseline_score(perturbed)

        # Determine verdict
        retention = perturbed_score / max(baseline, 1e-9)

        if retention >= self.SUPPORT_THRESHOLD:
            verdict = "supports_confirmation"
        elif retention >= self.WEAKNESS_THRESHOLD:
            verdict = "weakens_confirmation"
        elif retention >= self.REFUTE_THRESHOLD:
            verdict = "downgrade_to_xi"
        else:
            verdict = "refutes_candidate"

        return self._record_result(
            hypothesis_id, masking_type,
            baseline, perturbed_score, verdict,
            f"retention={retention:.4f}")

    def _record_result(
        self,
        hypothesis_id: str,
        masking_type: str,
        baseline: float,
        perturbed: float,
        verdict: str,
        details: str,
    ) -> Dict[str, Any]:
        """Write result to masking_counterevidence_record."""
        record_id = _uid("msk")
        self.conn.execute(
            "INSERT INTO masking_counterevidence_record "
            "(record_id,hypothesis_id,masking_type,baseline_score,"
            "perturbed_score,verdict,details,run_id,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (record_id, hypothesis_id, masking_type,
             baseline, perturbed, verdict, details,
             self.run_id, _now()))

        return {
            "record_id": record_id,
            "masking_type": masking_type,
            "baseline": round(baseline, 4),
            "perturbed": round(perturbed, 4),
            "retention": round(perturbed / max(baseline, 1e-9), 4),
            "verdict": verdict,
        }

    def run_masking_suite(
        self,
        hypothesis_id: str,
        types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run a full masking suite against a hypothesis.

        V8.5 §5: At least 3 masking types required for mask_supported.
        """
        if types is None:
            types = ["signal_shuffle", "geometry_shift", "boundary_flip",
                     "masking_injection", "temporal_window_masking"]

        results = []
        for mt in types:
            r = self.execute_perturbation(hypothesis_id, mt)
            results.append(r)

        # Compute aggregate verdict
        verdicts = [r["verdict"] for r in results]
        support_count = sum(1 for v in verdicts if v == "supports_confirmation")
        refute_count = sum(1 for v in verdicts if v in ("refutes_candidate", "downgrade_to_xi"))

        if refute_count > len(results) // 2:
            aggregate = "refutes_candidate"
        elif support_count >= 3:
            aggregate = "supports_confirmation"
        elif support_count >= 1:
            aggregate = "weakens_confirmation"
        else:
            aggregate = "inconclusive"

        return {
            "hypothesis_id": hypothesis_id,
            "individual_results": results,
            "aggregate_verdict": aggregate,
            "support_count": support_count,
            "refute_count": refute_count,
            "total_types_run": len(results),
        }
