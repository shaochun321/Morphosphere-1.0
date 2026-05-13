"""Trajectory analysis: observation field, P/R decomposition, transport,
O-surface, band records, and origin/transition (v5 P04-P09).
"""

from .observation_field import (
    WindowedTrajectoryField,
    OBSERVATION_DIMS,
    D_STATE,
    build_trajectory_field,
)
from .decomposition import (
    TrajectoryDecomposition,
    decompose_graph_smooth_sparse,
)
from .transport import (
    TransportOperator,
    NodeCorrespondence,
    TrajectoryStitcher,
    compute_transport,
)
from .o_surface import (
    ObservableSurface,
    ObservableFieldSurface,
    ObservableCandidateSurface,
    ObservableFieldEntry,
    CandidateCluster,
    build_observable_surface,
)
from .band_records import (
    PrimaryBandRecord,
    ResidualBandRecord,
    OccupancyState,
    BoundaryElasticityRecord,
    freeze_bands_from_decomposition,
)
from .origin import (
    OriginAnchorBundle,
    RecursiveTransitionRecord,
    TSeedReplayPacket,
    build_transition_record,
)
from .family_surface import (
    FamilyRecursiveSurface,
    FamilyEvidenceRow,
)

__all__ = [
    "WindowedTrajectoryField",
    "OBSERVATION_DIMS",
    "D_STATE",
    "build_trajectory_field",
    "TrajectoryDecomposition",
    "decompose_graph_smooth_sparse",
    "TransportOperator",
    "NodeCorrespondence",
    "TrajectoryStitcher",
    "compute_transport",
    "ObservableSurface",
    "ObservableFieldSurface",
    "ObservableCandidateSurface",
    "ObservableFieldEntry",
    "CandidateCluster",
    "build_observable_surface",
    "PrimaryBandRecord",
    "ResidualBandRecord",
    "OccupancyState",
    "BoundaryElasticityRecord",
    "freeze_bands_from_decomposition",
    "OriginAnchorBundle",
    "RecursiveTransitionRecord",
    "TSeedReplayPacket",
    "build_transition_record",
    "FamilyRecursiveSurface",
    "FamilyEvidenceRow",
]
