"""Optimal Transport Module — True Wasserstein distance via POT library.

Phase 2.2 of the v38 improvement plan.

Replaces the heuristic Euclidean-distance + threshold transport with
mathematically rigorous Optimal Transport using the Sinkhorn algorithm.

Features:
  - Wasserstein distance between cell distributions (windows)
  - Transport plan (which cells map to which) via entropy-regularized OT
  - Batch computation for multi-window pipeline
  - Falls back to Euclidean if POT is not installed

Usage:
  ot_engine = OptimalTransportEngine()
  plan, w_dist = ot_engine.compute_transport(source_cells, target_cells)
"""
from __future__ import annotations
import math
from typing import Dict, List, Optional, Tuple

try:
    import numpy as np
    import ot as pot
    HAS_POT = True
except ImportError:
    HAS_POT = False


class OptimalTransportEngine:
    """Computes optimal transport between cell distributions.

    Uses entropy-regularized OT (Sinkhorn algorithm) via the POT library
    for O(n² · log(n)) computation with numerical stability guarantees.
    """

    def __init__(self, reg: float = 0.05, max_iter: int = 200):
        """Initialize OT engine.

        Args:
            reg: Sinkhorn entropy regularization (smaller = closer to exact OT)
            max_iter: maximum Sinkhorn iterations
        """
        self.reg = reg
        self.max_iter = max_iter
        self._available = HAS_POT

    @property
    def is_available(self) -> bool:
        return self._available

    def _cells_to_features(self, cells) -> 'np.ndarray':
        """Extract spatial + signal features from cells for cost matrix."""
        features = []
        for c in cells:
            x = getattr(c, 'x', 0.0)
            y = getattr(c, 'y', 0.0)
            z = getattr(c, 'z', 0.0)
            v = getattr(c, 'V_mean', 0.0)
            sr = getattr(c, 'spike_rate', 0.0)
            rp = getattr(c, 'release_proxy', 0.0)
            features.append([x, y, z, v * 0.3, sr * 0.1, rp * 0.1])
        return np.array(features, dtype=np.float64)

    def compute_transport(self, source_cells, target_cells):
        """Compute optimal transport between two cell populations.

        Args:
            source_cells: list of cell objects (window k-1)
            target_cells: list of cell objects (window k)

        Returns:
            transport_plan: (n_source × n_target) matrix of optimal mass flow
            wasserstein_distance: scalar Wasserstein distance
            cost_matrix: (n_source × n_target) pairwise cost matrix
        """
        if not self._available:
            return self._fallback_transport(source_cells, target_cells)

        X_s = self._cells_to_features(source_cells)
        X_t = self._cells_to_features(target_cells)

        n_s = len(X_s)
        n_t = len(X_t)

        if n_s == 0 or n_t == 0:
            return np.array([]), 0.0, np.array([])

        # Uniform mass distributions
        a = np.ones(n_s) / n_s
        b = np.ones(n_t) / n_t

        # Cost matrix: squared Euclidean distance
        cost_matrix = pot.dist(X_s, X_t, metric='sqeuclidean')

        # Sinkhorn algorithm (entropy-regularized OT)
        transport_plan = pot.sinkhorn(
            a, b, cost_matrix,
            reg=self.reg,
            numItermax=self.max_iter,
            stopThr=1e-8
        )

        # Wasserstein distance = <T, C> (Frobenius inner product)
        wasserstein = float(np.sum(transport_plan * cost_matrix))

        return transport_plan, wasserstein, cost_matrix

    def compute_batch_distances(self, windows_cells: List[list]) -> List[float]:
        """Compute Wasserstein distances between consecutive windows.

        Args:
            windows_cells: list of cell lists, one per window

        Returns:
            distances: list of Wasserstein distances [W(w0,w1), W(w1,w2), ...]
        """
        distances = []
        for i in range(1, len(windows_cells)):
            _, w_dist, _ = self.compute_transport(
                windows_cells[i - 1], windows_cells[i])
            distances.append(w_dist)
        return distances

    def _fallback_transport(self, source_cells, target_cells):
        """Fallback: greedy nearest-neighbor matching (not true OT)."""
        n_s = len(source_cells)
        n_t = len(target_cells)

        if n_s == 0 or n_t == 0:
            return [], 0.0, []

        total_dist = 0.0
        for sc in source_cells:
            min_dist = float('inf')
            for tc in target_cells:
                dx = getattr(sc, 'x', 0) - getattr(tc, 'x', 0)
                dy = getattr(sc, 'y', 0) - getattr(tc, 'y', 0)
                dz = getattr(sc, 'z', 0) - getattr(tc, 'z', 0)
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                min_dist = min(min_dist, dist)
            total_dist += min_dist

        avg_dist = total_dist / max(n_s, 1)
        return None, avg_dist, None


def validate_ot_engine():
    """Self-test: verify OT engine produces sensible results."""
    if not HAS_POT:
        print("  POT library not installed, skipping OT validation")
        return False

    class FakeCell:
        def __init__(self, x, y, z=0, V_mean=0.5, spike_rate=0.1, release_proxy=0.1):
            self.x, self.y, self.z = x, y, z
            self.V_mean = V_mean
            self.spike_rate = spike_rate
            self.release_proxy = release_proxy

    engine = OptimalTransportEngine(reg=0.05)

    # Test 1: Identical distributions → W ≈ 0
    cells_a = [FakeCell(i * 0.1, 0) for i in range(10)]
    cells_b = [FakeCell(i * 0.1, 0) for i in range(10)]
    _, w1, _ = engine.compute_transport(cells_a, cells_b)

    # Test 2: Shifted distribution → W > 0
    cells_c = [FakeCell(i * 0.1 + 1.0, 0) for i in range(10)]
    _, w2, _ = engine.compute_transport(cells_a, cells_c)

    # Test 3: Very different distribution → W >> W2
    cells_d = [FakeCell(i * 0.1 + 5.0, 0) for i in range(10)]
    _, w3, _ = engine.compute_transport(cells_a, cells_d)

    checks = {
        "identical_near_zero": w1 < 0.1,  # small due to signal feature overlap
        "shifted_positive": w2 > 0.1,
        "more_shift_more_cost": w3 > w2,
        "monotonic_ordering": w1 < w2 < w3,
    }

    print(f"  OT Self-Test:")
    print(f"    W(identical) = {w1:.6f}")
    print(f"    W(shifted+1) = {w2:.6f}")
    print(f"    W(shifted+5) = {w3:.6f}")

    all_pass = True
    for check, passed in checks.items():
        icon = "✅" if passed else "❌"
        print(f"    {icon} {check}: {'PASS' if passed else 'FAIL'}")
        if not passed:
            all_pass = False

    return all_pass


if __name__ == "__main__":
    print("Optimal Transport Engine — Self Validation")
    print("=" * 50)
    result = validate_ot_engine()
    print(f"\n{'ALL CHECKS PASSED ✅' if result else 'SOME CHECKS FAILED ❌'}")
