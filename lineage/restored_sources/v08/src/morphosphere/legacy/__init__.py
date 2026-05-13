"""Legacy reference namespace.

This namespace intentionally does not import the top-level `morphosphere_v2`
source tree. It only documents legacy-reference status until explicit adapters
are added in later convergence checkpoints.
"""

from .reference import LEGACY_V2_REFERENCE_MODULES, LegacyReferenceModule

__all__ = ["LEGACY_V2_REFERENCE_MODULES", "LegacyReferenceModule"]
