"""
pr_decomposition_pilot_glsr.py

EXTERNAL_TRANSITIONAL Module
Bridge ID: pr_pilot_bridge

Role: Graph Laplacian Smooth + Group Sparse Residual testbed for proposing P/R separation.
Produces candidate fields. Must never write to final P_Band/R_Band records.

P7 fix: Now accepts real signal data and produces actual P/R candidate reports
using a simplified GLSR approach for comparison with mainline proposer.
"""
import numpy as np
import scipy.sparse as sp


class PRDecompositionPilotGLSR:
    """GLSR pilot decomposition for candidate P/R comparison.

    This module produces CANDIDATE reports only — never writes to mainline P/R bands.
    """

    def propose_decomposition(self, x_m, l_m, w_prior=None):
        """Propose P/R decomposition using simplified GLSR.

        Args:
            x_m: Signal matrix (N x D), real data from SignalWindow
            l_m: Graph Laplacian (N x N)
            w_prior: Optional transport prior

        Returns candidate report (never mainline truth).
        """
        if x_m is None or x_m.size == 0:
            return {
                "status": "SUSPENDED_MAINLINE_PROMOTION",
                "report_type": "p_candidate_report",
                "p_candidate": None,
                "r_candidate": None,
                "reason": "No input data",
            }

        N, D = x_m.shape

        # Simplified GLSR: smooth component via graph filtering
        # P = (I + λL)^{-1} X
        lambda_g = 0.5
        I = sp.eye(N, format='csc')
        if sp.issparse(l_m):
            A = I + lambda_g * l_m
        else:
            A = I + lambda_g * sp.csc_matrix(l_m)

        P_candidate = np.zeros_like(x_m)
        for d in range(D):
            P_candidate[:, d] = sp.linalg.spsolve(A, x_m[:, d])

        R_candidate = x_m - P_candidate

        E_P = np.linalg.norm(P_candidate, axis=1)
        E_R = np.linalg.norm(R_candidate, axis=1)

        return {
            "status": "SUSPENDED_MAINLINE_PROMOTION",
            "report_type": "p_candidate_report",
            "p_candidate_energy_mean": float(np.mean(E_P)),
            "r_candidate_energy_mean": float(np.mean(E_R)),
            "n_p_dominant": int(np.sum(E_P > E_R)),
            "n_r_dominant": int(np.sum(E_R > E_P)),
            "reconstruction_error": float(np.sum((x_m - P_candidate - R_candidate)**2)),
        }
