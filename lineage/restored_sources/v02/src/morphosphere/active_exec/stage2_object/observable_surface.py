"""ObservableSurface builder: Translates T_k into O_k.

V8-T5: Updated to accept PRDecompositionResult and create candidate
clusters from actual E_P/E_R/kappa data.
"""
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field

from .t_surface import TStagePacket
from .o_field_surface import OFieldSurface
from .o_candidate_surface import OCandidateSurface, OCandidateCluster
from .decomposition.proposer import PRDecompositionResult
from .freezing.thresholds import ThresholdProfile


class ObservableSurface(BaseModel):
    """ObservableSurface: 组合引用 (O_k)"""
    o_surface_id: str = Field(..., description="Unique Observable Surface ID")
    stage_k: int = Field(..., description="Stage index k")

    t_surface_id: str = Field(..., description="Source T_k ID")
    field_surface_id: str = Field(..., description="OFieldSurface ID")
    candidate_surface_id: str = Field(..., description="OCandidateSurface ID")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ObservableSurface":
        return cls.model_validate(row)


class OBuilder:
    """OBuilder: Translates T_k into O_k."""

    def build_o_surface(
        self,
        t_packet: TStagePacket,
        decomposition_result: Optional[PRDecompositionResult] = None,
        threshold_profile: Optional[ThresholdProfile] = None,
    ) -> ObservableSurface:
        """Creates field and candidate surfaces from T_k.

        V8-T5: When decomposition_result is provided, candidate clusters
        are built from actual E_P/E_R/kappa data instead of mock data.
        """
        field_id = f"field_{uuid.uuid4().hex[:8]}"
        field_surface = OFieldSurface(
            field_id=field_id,
            t_surface_id=t_packet.t_surface_id,
            field_matrix=[]
        )

        # V8-T5: Build candidate surface from decomposition if available
        if decomposition_result is not None:
            candidate_surface = OCandidateSurface.from_decomposition(
                field_surface_id=field_id,
                result=decomposition_result,
                threshold_profile=threshold_profile,
            )
        else:
            # Fallback: surrogate candidate surface
            candidate_surface_id = f"cand_surf_{uuid.uuid4().hex[:8]}"
            candidate_surface = OCandidateSurface(
                candidate_surface_id=candidate_surface_id,
                field_surface_id=field_id,
                clusters=[
                    OCandidateCluster(
                        cluster_id=f"clus_{uuid.uuid4().hex[:8]}",
                        field_id=field_id,
                        node_indices=[0, 1, 2],
                        cluster_score=0.9,
                    )
                ]
            )

        return ObservableSurface(
            o_surface_id=f"osurf_{uuid.uuid4().hex[:8]}",
            stage_k=t_packet.stage_k,
            t_surface_id=t_packet.t_surface_id,
            field_surface_id=field_id,
            candidate_surface_id=candidate_surface.candidate_surface_id,
        )
