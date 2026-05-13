"""Cold-path decomposition diagnostics (V8 §8.11).

Provides threshold sensitivity analysis, solver stability reporting,
and BW/contradiction diagnostics. These are NOT part of the hot path
and are computed asynchronously for ledger/audit purposes.
"""
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import scipy.sparse as sp

from .proposer import PRDecompositionResult
from ..freezing.thresholds import ThresholdProfile


@dataclass
class ThresholdSensitivityReport:
    """Report on how P/R classification changes under threshold perturbation."""
    base_profile: str
    perturbation_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_profile": self.base_profile,
            "perturbation_results": self.perturbation_results,
        }


@dataclass
class SolverStabilityReport:
    """Report on solver convergence and numerical stability."""
    converged: bool = False
    iterations: int = 0
    final_objective: float = 0.0
    objective_decrease_monotonic: bool = True
    max_p_norm: float = 0.0
    max_r_norm: float = 0.0
    condition_estimate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "converged": self.converged,
            "iterations": self.iterations,
            "final_objective": self.final_objective,
            "objective_decrease_monotonic": self.objective_decrease_monotonic,
            "max_p_norm": self.max_p_norm,
            "max_r_norm": self.max_r_norm,
            "condition_estimate": self.condition_estimate,
        }


class DecompositionDiagnostics:
    """Cold-path diagnostics for the P/R decomposition.

    V8 §8.11 cold path:
      - BW/contradiction/boundary full diagnostics
      - Threshold sensitivity report
      - Solver stability report
      - External pilot comparison hooks
    """

    def compute_threshold_sensitivity(
        self,
        result: PRDecompositionResult,
        base_profile: ThresholdProfile,
        perturbation_range: float = 0.2,
        n_steps: int = 5,
    ) -> ThresholdSensitivityReport:
        """Sweep threshold parameters and report classification stability."""
        report = ThresholdSensitivityReport(base_profile="default")
        
        for step in range(n_steps):
            factor = 1.0 - perturbation_range + (2 * perturbation_range * step / max(n_steps - 1, 1))
            perturbed = ThresholdProfile(
                theta_P=base_profile.theta_P * factor,
                theta_kappa=base_profile.theta_kappa * factor,
                theta_bw=base_profile.theta_bw * factor,
                theta_R=base_profile.theta_R * factor,
                theta_boundary=base_profile.theta_boundary * factor,
            )
            
            n_p = int(np.sum(result.E_P > perturbed.theta_P))
            n_r = int(np.sum(result.E_R > perturbed.theta_R))
            n_coherent = int(np.sum(result.kappa > perturbed.theta_kappa))
            
            report.perturbation_results.append({
                "factor": round(factor, 3),
                "n_p_candidates": n_p,
                "n_r_candidates": n_r,
                "n_coherent": n_coherent,
                "theta_P_used": round(perturbed.theta_P, 4),
                "theta_R_used": round(perturbed.theta_R, 4),
            })

        return report

    def compute_solver_stability(
        self,
        result: PRDecompositionResult,
    ) -> SolverStabilityReport:
        """Analyze solver convergence and stability from diagnostics."""
        obj_hist = result.objective_history

        # Check monotonicity
        monotonic = True
        for i in range(1, len(obj_hist)):
            if obj_hist[i] > obj_hist[i - 1] + 1e-10:
                monotonic = False
                break

        p_norms = result.solver_diagnostics.get("p_norm_history", [])
        r_norms = result.solver_diagnostics.get("r_norm_history", [])

        return SolverStabilityReport(
            converged=result.converged,
            iterations=result.iterations,
            final_objective=obj_hist[-1] if obj_hist else 0.0,
            objective_decrease_monotonic=monotonic,
            max_p_norm=max(p_norms) if p_norms else 0.0,
            max_r_norm=max(r_norms) if r_norms else 0.0,
            condition_estimate=result.solver_diagnostics.get("convergence_gap", 0.0),
        )

    def compute_full_diagnostics(
        self,
        result: PRDecompositionResult,
        threshold_profile: Optional[ThresholdProfile] = None,
    ) -> Dict[str, Any]:
        """Compute all cold-path diagnostics and return as a serializable dict."""
        tp = threshold_profile or ThresholdProfile.default()

        sensitivity = self.compute_threshold_sensitivity(result, tp)
        stability = self.compute_solver_stability(result)

        return {
            "threshold_sensitivity": sensitivity.to_dict(),
            "solver_stability": stability.to_dict(),
            "decomposition_summary": result.to_diagnostics_dict(),
        }
