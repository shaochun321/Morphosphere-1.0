# Tags: [ARCHIVE_ACCESS][LEGACY_READONLY]
# Role: Read-only access to v1 data. NEVER writes back to active_exec.
"""Archive access — read-only compatibility layer for v1 data."""

from .v1_reader import V1Reader, V1RefactorSummary, V1ObjectCoreRecord, V1Shell0Diagnosis

__all__ = [
    "V1Reader",
    "V1RefactorSummary",
    "V1ObjectCoreRecord",
    "V1Shell0Diagnosis",
]
