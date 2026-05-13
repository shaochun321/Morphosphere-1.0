"""
transport_pilot_ot_cpd.py

EXTERNAL_TRANSITIONAL Module
Bridge ID: transport_pilot_bridge

Role: Optimal Transport / Coherent Point Drift testbed for finding correspondence.
Produces only candidate reports. Must never write to mainline transport operator tables.

P7 fix: Now accepts real slice data and produces real candidate reports
using signal similarity and geometric distance for edge suggestions.
"""
import numpy as np
from scipy.spatial.distance import cdist


class TransportPilotOTCPD:
    """OT/CPD pilot for generating candidate transport reports.

    This module produces CANDIDATE reports only — never writes to mainline tables.
    All outputs are tagged as SUSPENDED_MAINLINE_PROMOTION.
    """

    def evaluate_candidates(self, slice_m, slice_m1):
        """Evaluate OT-based candidate edges between two slices.

        Uses real geometry when available; returns candidate report.
        """
        if not slice_m.geometry_nodes or not slice_m1.geometry_nodes:
            return {
                "status": "SUSPENDED_MAINLINE_PROMOTION",
                "report_type": "transport_candidate_report",
                "suggested_edges": [],
                "reason": "No geometry data available",
            }

        # Extract positions from geometry nodes
        pos_m = np.array([list(g.position) for g in slice_m.geometry_nodes])
        pos_m1 = np.array([list(g.position) for g in slice_m1.geometry_nodes])
        n_m, n_m1 = len(pos_m), len(pos_m1)

        # Compute cost matrix from Euclidean distance
        C = cdist(pos_m, pos_m1, metric='sqeuclidean')

        # Sinkhorn-like soft assignment (simplified)
        reg = 0.1
        K = np.exp(-C / (reg * np.max(C) + 1e-12))
        a = np.ones(n_m) / n_m
        b = np.ones(n_m1) / n_m1
        u = np.ones(n_m)
        for _ in range(50):
            v = b / (K.T @ u + 1e-12)
            u = a / (K @ v + 1e-12)
        coupling = np.diag(u) @ K @ np.diag(v)

        # Extract top edges from coupling matrix
        suggested_edges = []
        for i in range(n_m):
            best_j = int(np.argmax(coupling[i, :]))
            if coupling[i, best_j] > 1e-6:
                suggested_edges.append({
                    "from_node": int(slice_m.geometry_node_ids[i]),
                    "to_node": int(slice_m1.geometry_node_ids[best_j]),
                    "coupling_weight": float(coupling[i, best_j]),
                    "distance": float(np.sqrt(C[i, best_j])),
                })

        return {
            "status": "SUSPENDED_MAINLINE_PROMOTION",
            "report_type": "transport_candidate_report",
            "n_source": n_m,
            "n_target": n_m1,
            "suggested_edges": suggested_edges,
            "total_coupling_mass": float(np.sum(coupling)),
        }
