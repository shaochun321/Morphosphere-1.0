"""Morphosphere V2 — physics-first cell electro-mechanical system.

Architecture:
    CellGraphState X(t)
    → PatchAfferentTransmissionGraph
    → PreNeuralSlice P[t-Δ,t]
    → WindowedTrajectoryField Y_k
    → LatentTrajectoryDecomposition {P_k, R_k}
    → Runtime Ledger
    → Semantic Readout Surface

CellGraphState is the sole source of truth.
"""

__version__ = "2.0.0a1"
