"""SemanticReadoutBuilder: 后验语义贴标层 (V8 §12, Readonly).

P8 fix: Uses physical quantities (maturity_flag, E_P, kappa) to drive
semantic label assignment instead of string matching on surface_id.
"""
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field
from ...stage2_object.family_surface.recursive_surface import FamilyRecursiveSurfaceIndex

class SemanticReadoutSurface(BaseModel):
    """SemanticReadoutSurface: 后验语义贴标层 (Readonly)"""
    readout_id: str = Field(..., description="Unique Readout ID")
    surface_id: str = Field(..., description="Source FamilyRecursiveSurfaceIndex ID")

    dominant_family_label: str = Field(..., description="Semantic label of the dynamic family")
    onset_category: str = Field(default="unknown", description="Onset feature category")
    readout_confidence: float = Field(default=0.0, description="Confidence of semantic translation")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SemanticReadoutSurface":
        return cls.model_validate(row)


class SemanticReadoutBuilder:
    """P8 fix: Physics-driven semantic readout.

    Uses maturity_flag, aggregation_role, and suspension_status from
    FamilyRecursiveSurfaceIndex to assign semantic labels.
    Strict rule: Must not mutate the incoming family_surface or any core objects.
    """

    # Mapping from physical state to semantic label
    MATURITY_LABEL_MAP = {
        "matured": "stable_propagation",
        "frozen": "consolidating",
        "candidate": "emerging",
    }

    ROLE_LABEL_MAP = {
        "transition_hub": "transition_like",
        "boundary_fence": "boundary_fragmented",
        "index_root": "cohesive_core",
    }

    def build_readout(
        self,
        family_surface: FamilyRecursiveSurfaceIndex,
        mean_E_P: Optional[float] = None,
        mean_kappa: Optional[float] = None,
    ) -> SemanticReadoutSurface:
        """Translates a physical recursive surface into a semantic readout.

        Uses physical quantities from the family surface:
          - maturity_flag → base label
          - aggregation_role → label refinement
          - mean_E_P, mean_kappa → confidence estimation

        Strict rule: Must not mutate the incoming family_surface or any core objects.
        """
        # Base label from maturity
        base_label = self.MATURITY_LABEL_MAP.get(
            family_surface.maturity_flag, "unknown"
        )

        # Refine with aggregation role
        role_label = self.ROLE_LABEL_MAP.get(
            family_surface.aggregation_role, ""
        )

        # Composite label
        if role_label:
            label = f"{base_label}_{role_label}"
        else:
            label = base_label

        # Onset category from suspension status
        if family_surface.suspension_status == "SUSPENDED_PRESENT":
            onset = "indeterminate_onset"
        elif family_surface.suspension_status == "SUSPENDED_NUMERICAL_CLOSURE":
            onset = "deferred_onset"
        else:
            onset = "resolved_onset"

        # Confidence from physical quantities
        confidence = 0.5  # base
        if mean_E_P is not None:
            # Higher P energy → more confident in propagation label
            confidence += min(0.3, mean_E_P * 0.1)
        if mean_kappa is not None:
            # Higher coherence → more confident
            confidence += min(0.2, mean_kappa * 0.2)
        confidence = min(confidence, 1.0)

        return SemanticReadoutSurface(
            readout_id=f"readout_{uuid.uuid4().hex[:8]}",
            surface_id=family_surface.surface_id,
            dominant_family_label=label,
            onset_category=onset,
            readout_confidence=round(confidence, 4),
        )
