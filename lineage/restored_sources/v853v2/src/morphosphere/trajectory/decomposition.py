# Tags: [CORE_RUNTIME][TRAJECTORY][NEUTRAL][VERSIONED]
# Role: P/R decomposition — neutral, label-free.
# Must Not: Import semantic_readout or produce semantic labels.
# Producers: observation_field
# Consumers: band_records, o_surface, ledger, semantic_readout (read-only)
"""LatentTrajectoryDecomposition — P/R separation (masterplan §8.2).

Decomposes the neutral trajectory field Y_k into:
  P_k: primary propagation / primary energy subspace coherent support
  R_k: residual / competing propagation / local anomalous active support

Key principles (masterplan §8.2):
  - Separate structure first, then name structure
  - Any translation / rotation / onset / recovery labels can ONLY be
    produced AFTER P/R decomposition
  - P_k seeks coherent support of the main propagation/energy subspace
  - R_k represents residuals relative to P_k
  - First version: graph-smooth + sparse residual approximation

Design: 先分离结构，再命名结构。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

from morphosphere.core.types import Float64Array
from .observation_field import WindowedTrajectoryField


@dataclass
class TrajectoryDecomposition:
    """Result of P/R decomposition on a trajectory field.

    P_k: (N, D) primary component — spatially smooth, coherent propagation
    R_k: (N, D) residual component — sparse, local anomalies

    Together they satisfy: Y_k ≈ P_k + R_k
    """
    t_start: float
    t_end: float
    P: Float64Array              # (N, D) primary component
    R: Float64Array              # (N, D) residual component
    positions: Float64Array      # (N, 3) spatial coordinates
    provenance_hashes: list[str] # per-point provenance

    # Decomposition metadata
    smoothness_lambda: float = 1.0
    sparsity_weight: float = 0.1
    num_iterations: int = 0
    reconstruction_error: float = 0.0

    @property
    def num_points(self) -> int:
        return self.P.shape[0]

    @property
    def num_dims(self) -> int:
        return self.P.shape[1] if self.P.ndim == 2 else 0

    def coherence_score(self) -> float:
        """Fraction of total energy in the primary component."""
        e_total = np.sum(self.P ** 2) + np.sum(self.R ** 2)
        if e_total < 1e-12:
            return 0.0
        return float(np.sum(self.P ** 2) / e_total)

    def sparsity_score(self) -> float:
        """Fraction of residual points with near-zero energy."""
        if self.num_points == 0:
            return 0.0
        point_energy = np.sum(self.R ** 2, axis=1)
        threshold = 0.01 * np.mean(point_energy) if np.mean(point_energy) > 0 else 1e-6
        return float(np.mean(point_energy < threshold))

    def to_dict(self) -> dict[str, Any]:
        return {
            "t_start": self.t_start,
            "t_end": self.t_end,
            "num_points": self.num_points,
            "num_dims": self.num_dims,
            "coherence_score": self.coherence_score(),
            "sparsity_score": self.sparsity_score(),
            "smoothness_lambda": self.smoothness_lambda,
            "sparsity_weight": self.sparsity_weight,
            "num_iterations": self.num_iterations,
            "reconstruction_error": self.reconstruction_error,
        }


def _build_spatial_graph_laplacian(
    positions: Float64Array,
    k_neighbors: int = 10,
) -> Float64Array:
    """Build a graph Laplacian from spatial positions.

    Uses k-nearest-neighbor graph with Gaussian weights.
    Returns sparse-like (N, N) Laplacian matrix.
    """
    n = positions.shape[0]
    if n <= 1:
        return np.zeros((n, n))

    k = min(k_neighbors, n - 1)
    tree = cKDTree(positions)
    distances, indices = tree.query(positions, k=k + 1)  # +1 because self is included

    # Build adjacency with Gaussian weights
    sigma = np.median(distances[:, 1:]) if n > 1 else 1.0
    sigma = max(sigma, 1e-12)

    W = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j_idx in range(1, k + 1):  # skip self (index 0)
            j = indices[i, j_idx]
            w = np.exp(-distances[i, j_idx] ** 2 / (2 * sigma ** 2))
            W[i, j] = w
            W[j, i] = w  # symmetric

    D = np.diag(np.sum(W, axis=1))
    L = D - W
    return L


def decompose_graph_smooth_sparse(
    field: WindowedTrajectoryField,
    *,
    smoothness_lambda: float = 1.0,
    sparsity_weight: float = 0.1,
    k_neighbors: int = 10,
    max_iterations: int = 50,
    tolerance: float = 1e-4,
) -> TrajectoryDecomposition:
    """Decompose Y_k into P_k (graph-smooth) + R_k (sparse residual).

    First version implementation (masterplan §8.2):
        "第一版可采用 graph-smooth + sparse residual 的近似实现"

    Algorithm:
        1. Build spatial graph Laplacian from positions
        2. P_k = argmin ||P||_L² + λ·||P^T L P||_F²  s.t.  ||Y - P||₁ ≤ ε
        3. R_k = Y_k - P_k
        4. Soft-threshold R_k for sparsity

    Simplified version: iterative graph smoothing + sparse thresholding.
    """
    n = field.num_points
    d = field.num_dims

    if n == 0 or d == 0:
        return TrajectoryDecomposition(
            t_start=field.t_start,
            t_end=field.t_end,
            P=np.empty((0, d)),
            R=np.empty((0, d)),
            positions=field.positions,
            provenance_hashes=field.provenance_hashes,
        )

    Y = field.Y.copy()

    # Normalize for stability
    Y_norm = field.normalize().Y

    # Build graph Laplacian
    L = _build_spatial_graph_laplacian(field.positions, k_neighbors=min(k_neighbors, n - 1))

    # Iterative decomposition: alternating graph smoothing + sparse thresholding
    P = Y_norm.copy()
    R = np.zeros_like(Y_norm)

    # Graph smoothing matrix: (I + λL)^{-1}
    I = np.eye(n)
    smooth_matrix = np.linalg.solve(I + smoothness_lambda * L, I)

    for iteration in range(max_iterations):
        # Step 1: Graph smooth P
        P_new = smooth_matrix @ (Y_norm - R)

        # Step 2: Compute residual
        R_new = Y_norm - P_new

        # Step 3: Soft threshold for sparsity
        threshold = sparsity_weight * np.std(R_new)
        R_mag = np.sqrt(np.sum(R_new ** 2, axis=1, keepdims=True))
        R_scale = np.maximum(0.0, 1.0 - threshold / np.maximum(R_mag, 1e-12))
        R_new = R_new * R_scale

        # Check convergence
        delta = np.max(np.abs(P_new - P))
        P = P_new
        R = R_new

        if delta < tolerance:
            break

    # Scale back to original space
    means = np.mean(Y, axis=0, keepdims=True)
    stds = np.std(Y, axis=0, keepdims=True)
    stds[stds < 1e-12] = 1.0

    P_original = P * stds + means * (np.sum(P, axis=0, keepdims=True) / max(np.sum(P ** 2), 1e-12))
    R_original = Y - P_original

    # Reconstruction error
    recon_error = float(np.sqrt(np.mean((Y - P_original - R_original) ** 2)))

    return TrajectoryDecomposition(
        t_start=field.t_start,
        t_end=field.t_end,
        P=P_original,
        R=R_original,
        positions=field.positions.copy(),
        provenance_hashes=list(field.provenance_hashes),
        smoothness_lambda=smoothness_lambda,
        sparsity_weight=sparsity_weight,
        num_iterations=iteration + 1 if n > 0 else 0,
        reconstruction_error=recon_error,
    )
