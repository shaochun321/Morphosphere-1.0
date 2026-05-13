from typing import Any, List, Optional
from pydantic import BaseModel, Field
import hashlib


class SystemClock(BaseModel):
    """SystemClock: 唯一合法时间索引"""
    clock_n: int = Field(default=0, description="Canonical discrete time index")
    dt_seconds: float = Field(default=0.001, description="Time delta per tick")
    run_id: str = Field(..., description="Unique run identifier")
    wall_clock_created_at: float = Field(..., description="Wall-clock timestamp of creation")
    tick_hash: str = Field(default="", description="Provenance hash for the tick")

    @property
    def time(self) -> float:
        return self.clock_n * self.dt_seconds

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SystemClock":
        return cls.model_validate(row)


class SystemClockEntry(BaseModel):
    """V8.3 P0: Canonical system clock entry for database persistence.

    Every cell_graph_state.clock_n must reference a SystemClockEntry.
    """
    clock_n: int = Field(..., description="Discrete time index")
    run_id: str = Field(..., description="Run identifier")
    time_s: float = Field(default=0.0, description="Simulation time in seconds")
    dt_s: float = Field(default=0.001, description="Time step in seconds")
    clock_hash: str = Field(default="", description="Provenance hash")
    schema_version: str = Field(default="v8.3", description="Schema version")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SystemClockEntry":
        return cls.model_validate(row)


class SystemClockManager:
    """V8.3 P0: Manages system_clock_entry population.

    Backfill generates clock entries for all ticks in a run,
    ensuring cell_graph_state.clock_n foreign key validity.
    """

    @staticmethod
    def backfill(run_id: str, n_ticks: int, dt: float = 0.001) -> List[SystemClockEntry]:
        """Generate SystemClockEntry objects for ticks 0..n_ticks-1."""
        entries = []
        for n in range(n_ticks):
            h = hashlib.sha256(f"{run_id}:{n}:{dt}".encode()).hexdigest()[:12]
            entries.append(SystemClockEntry(
                clock_n=n,
                run_id=run_id,
                time_s=n * dt,
                dt_s=dt,
                clock_hash=h,
            ))
        return entries

    @staticmethod
    def validate_coverage(clock_entries: List[SystemClockEntry], required_ticks: List[int]) -> List[int]:
        """Return list of ticks NOT covered by clock entries."""
        covered = {e.clock_n for e in clock_entries}
        return [t for t in required_ticks if t not in covered]


class AnalysisWindow(BaseModel):
    """AnalysisWindow: 最小可比较、可存储的信息窗口"""
    window_id: str = Field(..., description="Unique window identifier")
    clock_start: int = Field(..., description="Start clock_n (inclusive)")
    clock_end: int = Field(..., description="End clock_n (exclusive)")
    window_center: int = Field(..., description="Center clock_n")
    window_size: int = Field(..., description="Size of window in ticks")
    window_stride: int = Field(..., description="Stride used for window generation")
    window_type: str = Field(default="standard", description="Type of window")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "AnalysisWindow":
        return cls.model_validate(row)

