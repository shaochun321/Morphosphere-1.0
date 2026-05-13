"""FamilySurfaceIndexBuilder: Builds FamilyRecursiveSurfaceIndex with V8-T4 fields.

V8-T4 deliverables:
  - maturity_flag: derived from transition coherence and P-band strength
  - suspension_status: from transition confidence thresholds
  - aggregation_role: from shell0 verdict and transition topology
"""
import uuid
from typing import List, Optional

from .recursive_surface import FamilyRecursiveSurfaceIndex
from ..freezing.transition import RecursiveTransitionRecord


class FamilySurfaceIndexBuilder:

    # Maturity thresholds
    MATURITY_FROZEN_CONFIDENCE = 0.8
    MATURITY_MATURED_CONFIDENCE = 0.95

    # Suspension thresholds
    SUSPENSION_CONFIDENCE_MIN = 0.5

    def build_surface(
        self,
        clock_n: int,
        transitions: List[RecursiveTransitionRecord],
        shell0_verdict: str,
        origin_anchor_id: Optional[str] = None,
        t_seed_id: Optional[str] = None,
        transition_confidence: Optional[float] = None,
    ) -> FamilyRecursiveSurfaceIndex:
        """Build a FamilyRecursiveSurfaceIndex with V8-T4 maturity/suspension/role fields.

        Args:
            clock_n: System clock tick
            transitions: List of recursive transition records
            shell0_verdict: Shell0 boundary verdict string
            origin_anchor_id: Optional Omega_k reference
            t_seed_id: Optional T_seed reference
            transition_confidence: Optional aggregate confidence score (0-1)
        """
        # Compute aggregate confidence from transitions if not provided
        if transition_confidence is None and transitions:
            confidences = [t.transition_confidence for t in transitions if hasattr(t, 'transition_confidence')]
            transition_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # V8-T4: Derive maturity_flag
        maturity_flag = self._derive_maturity(transition_confidence, transitions)

        # V8-T4: Derive suspension_status
        suspension_status = self._derive_suspension(transition_confidence, shell0_verdict)

        # V8-T4: Derive aggregation_role
        aggregation_role = self._derive_aggregation_role(shell0_verdict, transitions)

        # Build extended verdict (preserves legacy behavior)
        extended_verdict = shell0_verdict
        if origin_anchor_id and t_seed_id:
            extended_verdict += f" | Anchored by {origin_anchor_id} -> Seeds {t_seed_id}"

        return FamilyRecursiveSurfaceIndex(
            surface_id=f"fam_surf_{uuid.uuid4().hex[:8]}",
            clock_n=clock_n,
            transition_ids=[t.transition_id for t in transitions],
            shell0_verdict=extended_verdict,
            maturity_flag=maturity_flag,
            suspension_status=suspension_status,
            aggregation_role=aggregation_role,
            origin_anchor_id=origin_anchor_id,
            t_seed_id=t_seed_id,
        )

    def _derive_maturity(
        self,
        confidence: Optional[float],
        transitions: List[RecursiveTransitionRecord],
    ) -> str:
        """Derive maturity flag from transition confidence and P-band strength."""
        if confidence is None:
            return "candidate"

        if confidence >= self.MATURITY_MATURED_CONFIDENCE and len(transitions) > 0:
            return "matured"
        elif confidence >= self.MATURITY_FROZEN_CONFIDENCE:
            return "frozen"
        else:
            return "candidate"

    def _derive_suspension(
        self,
        confidence: Optional[float],
        shell0_verdict: str,
    ) -> str:
        """Derive suspension status from confidence and shell0 verdict."""
        # If shell0 is unresolved, mark as suspended present
        if "mixed" in shell0_verdict.lower() or "indeterminate" in shell0_verdict.lower():
            return "SUSPENDED_PRESENT"

        # If confidence is too low, mark as suspended numerical closure
        if confidence is not None and confidence < self.SUSPENSION_CONFIDENCE_MIN:
            return "SUSPENDED_NUMERICAL_CLOSURE"

        return "ACTIVE"

    def _derive_aggregation_role(
        self,
        shell0_verdict: str,
        transitions: List[RecursiveTransitionRecord],
    ) -> str:
        """Derive canonical aggregation role from shell0 verdict and transition count."""
        verdict_lower = shell0_verdict.lower()

        # Boundary region → boundary_fence
        if "boundary" in verdict_lower or "fragmented" in verdict_lower:
            return "boundary_fence"

        # Multiple transitions → transition_hub
        if len(transitions) > 1:
            return "transition_hub"

        # Default → index_root
        return "index_root"
