"""Adapters that keep legacy v2 preneural objects out of the v8/v8.5 hot path."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from morphosphere.active_exec.preneural.carrier_slice import (
    PreNeuralCarrierSlice,
    carrier_from_legacy_slice_like,
    carrier_from_pointset_slice,
)
from morphosphere.active_exec.preneural.pointset_slice import PreNeuralPointSetSlice


def adapt_pointset_slice(
    pointset: PreNeuralPointSetSlice,
    *,
    patch_to_cells: Mapping[int, Sequence[int]] | None = None,
) -> PreNeuralCarrierSlice:
    """Convert the current v8/v8.5 pointset implementation into carrier boundary view."""

    return carrier_from_pointset_slice(pointset, patch_to_cells=patch_to_cells)


def adapt_legacy_preneural_slice(legacy_slice: Any) -> PreNeuralCarrierSlice:
    """Convert a legacy v2 PreNeuralSlice-like object into carrier boundary view."""

    return carrier_from_legacy_slice_like(legacy_slice)
