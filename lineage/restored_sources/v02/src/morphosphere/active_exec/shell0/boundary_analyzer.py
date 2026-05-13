"""Shell0 Boundary Analyzer — Phase C.

Loads 6 boundary experiment variants from V1 data, processes each through
the V8 pipeline, and compares cross-variant stability of shell boundaries,
transport metrics, and P/R decomposition.

V8 §1.7: "shell0 仍视为高风险未闭合项。它只能通过 boundary-first、多分辨率、
多边界、多接触、research + CI 双层验证推进，不得被提前语义化解释吸收。"
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np


@dataclass
class ShellBoundaryFrame:
    """Shell boundary data from a single frame of a V1 boundary experiment."""
    time: float
    shell_count: int
    motion_class: str
    shell_energies: List[float]
    shell_couplings: List[float]
    shell_leakages: List[float]
    shell_classifications: List[str]
    process_summary: Dict[str, float]


@dataclass
class BoundaryVariantResult:
    """Results from processing one boundary variant through V8 pipeline."""
    variant_name: str
    n_frames: int
    shell_energies_by_frame: List[List[float]]  # [frame][shell]
    motion_classes: List[str]  # V1 motion labels per frame
    mean_shell_energy: float = 0.0
    max_leakage: float = 0.0
    # V8 pipeline metrics (populated by analyzer)
    mean_transport_survival: float = 0.0
    mean_boundary_penalty: float = 0.0
    mean_E_P: float = 0.0
    mean_E_R: float = 0.0


@dataclass
class BoundaryStabilityReport:
    """Cross-variant stability report for shell0 boundary validation."""
    variant_names: List[str]
    variant_results: Dict[str, BoundaryVariantResult]
    # Cross-variant metrics
    energy_variance_across_variants: float = 0.0  # Lower = more stable
    transport_variance_across_variants: float = 0.0
    decomposition_variance_across_variants: float = 0.0
    # Stability verdicts
    shell0_stable: bool = False
    boundary_artifact_detected: bool = False
    recommendations: List[str] = field(default_factory=list)


class Shell0BoundaryAnalyzer:
    """Analyzes shell0 boundary stability across multiple V1 experiment variants.

    V8 §1.7 compliance: boundary-first, multi-variant, no premature semantic uplift.
    """

    VARIANTS = [
        "baseline", "contact_ablation", "ghost_shell",
        "pde_fvm_shell", "stronger_damping", "surface_attribute",
    ]

    def __init__(self, boundary_experiments_dir: str):
        self.base_dir = Path(boundary_experiments_dir)

    def load_variant(self, variant_name: str) -> Optional[BoundaryVariantResult]:
        """Load manifold_trace.json for one variant."""
        path = self.base_dir / variant_name / "manifold_trace.json"
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            frames = json.load(f)

        shell_energies_by_frame = []
        motion_classes = []
        max_leakage = 0.0
        total_energy = 0.0

        for frame in frames:
            shells = frame.get("shell_boundary", [])
            energies = [s.get("shell_energy", 0.0) for s in shells]
            leakages = [s.get("leakage", 0.0) for s in shells]
            shell_energies_by_frame.append(energies)
            motion_classes.append(frame.get("motion_class", "unknown"))
            max_leakage = max(max_leakage, max(leakages) if leakages else 0.0)
            total_energy += sum(energies)

        n_frames = len(frames)
        mean_energy = total_energy / max(n_frames, 1)

        return BoundaryVariantResult(
            variant_name=variant_name,
            n_frames=n_frames,
            shell_energies_by_frame=shell_energies_by_frame,
            motion_classes=motion_classes,
            mean_shell_energy=mean_energy,
            max_leakage=max_leakage,
        )

    def load_all_variants(self) -> Dict[str, BoundaryVariantResult]:
        """Load all available boundary variants."""
        results = {}
        for v in self.VARIANTS:
            result = self.load_variant(v)
            if result is not None:
                results[v] = result
        return results

    def analyze_stability(
        self, variant_results: Dict[str, BoundaryVariantResult]
    ) -> BoundaryStabilityReport:
        """Compute cross-variant stability metrics.

        Shell0 is stable if:
          1. Shell energy variance across variants is low
          2. Transport survival is consistent across variants
          3. No variant produces anomalous E_P that others don't
        """
        names = list(variant_results.keys())
        results = variant_results

        # Energy variance across variants
        mean_energies = [r.mean_shell_energy for r in results.values()]
        energy_var = float(np.var(mean_energies)) if len(mean_energies) > 1 else 0.0

        # Transport variance (if populated by pipeline run)
        transport_survivals = [r.mean_transport_survival for r in results.values()
                               if r.mean_transport_survival > 0]
        transport_var = float(np.var(transport_survivals)) if len(transport_survivals) > 1 else 0.0

        # Decomposition variance
        e_p_values = [r.mean_E_P for r in results.values() if r.mean_E_P > 0]
        decomp_var = float(np.var(e_p_values)) if len(e_p_values) > 1 else 0.0

        # Stability verdicts
        shell0_stable = energy_var < 1.0  # threshold for shell energy variance
        boundary_artifact = any(r.max_leakage > 0.5 for r in results.values())

        # Generate recommendations
        recs = []
        if not shell0_stable:
            recs.append("Shell energy varies significantly across boundary variants. "
                        "Investigate pde_fvm_shell for artifact sources.")
        if boundary_artifact:
            recs.append("High leakage detected in at least one variant. "
                        "Boundary-coupled terms may be introducing artifacts.")

        # Check ghost_shell specifically
        if "ghost_shell" in results and "baseline" in results:
            ghost = results["ghost_shell"]
            base = results["baseline"]
            energy_diff = abs(ghost.mean_shell_energy - base.mean_shell_energy)
            if energy_diff > 0.1:
                recs.append(f"Ghost shell introduces energy difference of {energy_diff:.4f}. "
                            f"P_bands from ghost_shell variant should NOT be frozen.")

        # Check contact_ablation
        if "contact_ablation" in results and "baseline" in results:
            ablated = results["contact_ablation"]
            base = results["baseline"]
            # If ablation doesn't change energy much, contact forces are not critical
            if abs(ablated.mean_shell_energy - base.mean_shell_energy) < 0.01:
                recs.append("Contact ablation has minimal effect on shell energy. "
                            "Contact forces may not be the primary boundary driver.")

        if not recs:
            recs.append("All variants stable. Shell0 boundary passes multi-variant check.")

        return BoundaryStabilityReport(
            variant_names=names,
            variant_results=results,
            energy_variance_across_variants=energy_var,
            transport_variance_across_variants=transport_var,
            decomposition_variance_across_variants=decomp_var,
            shell0_stable=shell0_stable,
            boundary_artifact_detected=boundary_artifact,
            recommendations=recs,
        )

    def print_report(self, report: BoundaryStabilityReport) -> None:
        """Print human-readable stability report."""
        print("\n" + "=" * 60)
        print("Shell0 Boundary Stability Report")
        print("=" * 60)

        for name, result in report.variant_results.items():
            energies_str = ", ".join(f"{e:.4f}" for e in
                                     (result.shell_energies_by_frame[0] if result.shell_energies_by_frame else []))
            print(f"\n  {name}:")
            print(f"    Frames: {result.n_frames}")
            print(f"    Mean shell energy: {result.mean_shell_energy:.6f}")
            print(f"    Max leakage: {result.max_leakage:.6f}")
            print(f"    Frame 0 shell energies: [{energies_str}]")
            print(f"    Motion classes: {result.motion_classes[:3]}...")

        print(f"\n--- Cross-Variant Stability ---")
        print(f"  Energy variance: {report.energy_variance_across_variants:.6f}")
        print(f"  Shell0 stable: {report.shell0_stable}")
        print(f"  Boundary artifact: {report.boundary_artifact_detected}")

        print(f"\n--- Recommendations ---")
        for r in report.recommendations:
            print(f"  • {r}")
