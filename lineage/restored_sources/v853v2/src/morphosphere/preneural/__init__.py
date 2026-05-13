"""Preneural carrier layer: PatchAfferentTransmissionGraph + PreNeuralSlice.

v5 additions: PreNeuralGeometry, PreNeuralSignalWindow, PreNeuralPointSetSlice.
"""

from .patch_graph import (
    PatchNode,
    PatchEdge,
    PatchAfferentTransmissionGraph,
    build_patch_graph_from_state,
)
from .preneural_slice import (
    SlicePoint,
    PreNeuralSlice,
    PreNeuralPointSetSlice,
    PreNeuralSliceAccumulator,
    build_slice_from_graph,
)
from .geometry import (
    PreNeuralGeometry,
    build_geometry_from_state,
)
from .signal_window import (
    SignalAccumulator,
)
from .met_channel import METChannelState, met_open_probability

__all__ = [
    "PatchNode",
    "PatchEdge",
    "PatchAfferentTransmissionGraph",
    "build_patch_graph_from_state",
    "SlicePoint",
    "PreNeuralSlice",
    "PreNeuralPointSetSlice",
    "PreNeuralSliceAccumulator",
    "build_slice_from_graph",
    "PreNeuralGeometry",
    "build_geometry_from_state",
    "SignalAccumulator",
    "METChannelState",
    "met_open_probability",
]
