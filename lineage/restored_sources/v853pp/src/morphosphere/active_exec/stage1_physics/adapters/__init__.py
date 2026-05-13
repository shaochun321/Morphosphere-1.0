"""Stage-1 adapter namespace."""

from .legacy_v2_state_adapter import legacy_record_to_physical, physical_to_legacy_record

__all__ = ["legacy_record_to_physical", "physical_to_legacy_record"]
