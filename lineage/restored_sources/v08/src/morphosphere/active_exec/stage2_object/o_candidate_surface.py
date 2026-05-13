"""OCandidateSurface: 候选簇 / 候选原点 / 候选边界对象层

V8-T5: Adds factory method to populate candidate clusters from
PRDecompositionResult using threshold profile.
"""
import uuid
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .decomposition.proposer import PRDecompositionResult
from .freezing.thresholds import ThresholdProfile


class OCandidateCluster(BaseModel):
    """OCandidateCluster: 单个候选簇

    V8.3 P2: candidate_type, solver_converged, maturity_flag enforce
    the v8.1-T3 requirement that P/R cannot bypass O_candidate.
    """
    cluster_id: str = Field(..., description="Unique cluster ID")
    field_id: str = Field(..., description="Source Field ID")
    node_indices: List[int] = Field(default_factory=list, description="Indices of nodes in this cluster")
    cluster_score: float = Field(default=0.0, description="Proposal score")
    cluster_type: str = Field(default="unknown", description="Cluster type: 'p_candidate' | 'r_candidate' | 'mixed'")
    # V8.3 P2: Maturity tracking
    candidate_type: str = Field(
        default="candidate_p",
        description="candidate_p/candidate_r/candidate_origin/candidate_boundary/candidate_xi"
    )
    solver_converged: bool = Field(default=False, description="Whether upstream solver converged")
    maturity_flag: str = Field(
        default="scaffold",
        description="scaffold/candidate/freezable/frozen — v8.1 §3.1 maturity level"
    )
    transport_support_score: float = Field(default=0.0, description="Transport support for this candidate")
    replay_support_score: float = Field(default=0.0, description="Replay alignment support")


class OCandidateSurface(BaseModel):
    """OCandidateSurface: 候选簇 / 候选原点 / 候选边界对象层"""
    candidate_surface_id: str = Field(..., description="Unique candidate surface ID")
    field_surface_id: str = Field(..., description="Source field surface ID")

    clusters: List[OCandidateCluster] = Field(default_factory=list, description="Proposed clusters")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OCandidateSurface":
        return cls.model_validate(row)

    @classmethod
    def from_decomposition(
        cls,
        field_surface_id: str,
        result: PRDecompositionResult,
        threshold_profile: Optional[ThresholdProfile] = None,
    ) -> "OCandidateSurface":
        """V8-T5: Build candidate surface from PRDecompositionResult.

        Creates P-candidate and R-candidate clusters based on E_P, E_R, kappa
        and the threshold profile.
        """
        tp = threshold_profile or ThresholdProfile.default()
        candidate_surface_id = f"cand_surf_{uuid.uuid4().hex[:8]}"
        clusters = []

        import numpy as np

        # P-candidate clusters: nodes with high P energy and coherence
        p_mask = (result.E_P > tp.theta_P) & (result.kappa > tp.theta_kappa)
        p_indices = np.where(p_mask)[0].tolist()
        if p_indices:
            clusters.append(OCandidateCluster(
                cluster_id=f"clus_p_{uuid.uuid4().hex[:6]}",
                field_id=field_surface_id,
                node_indices=p_indices,
                cluster_score=float(np.mean(result.E_P[p_mask])),
                cluster_type="p_candidate",
            ))

        # R-candidate clusters: nodes with high R energy
        r_mask = (result.E_R > tp.theta_R)
        r_indices = np.where(r_mask)[0].tolist()
        if r_indices:
            clusters.append(OCandidateCluster(
                cluster_id=f"clus_r_{uuid.uuid4().hex[:6]}",
                field_id=field_surface_id,
                node_indices=r_indices,
                cluster_score=float(np.mean(result.E_R[r_mask])),
                cluster_type="r_candidate",
            ))

        # Mixed/indeterminate: low E_P, low E_R but non-trivial activity
        mixed_mask = ~p_mask & ~r_mask & ((result.E_P > 0.1) | (result.E_R > 0.1))
        mixed_indices = np.where(mixed_mask)[0].tolist()
        if mixed_indices:
            clusters.append(OCandidateCluster(
                cluster_id=f"clus_m_{uuid.uuid4().hex[:6]}",
                field_id=field_surface_id,
                node_indices=mixed_indices,
                cluster_score=float(np.mean(result.E_P[mixed_mask] + result.E_R[mixed_mask])),
                cluster_type="mixed",
            ))

        return cls(
            candidate_surface_id=candidate_surface_id,
            field_surface_id=field_surface_id,
            clusters=clusters,
        )
