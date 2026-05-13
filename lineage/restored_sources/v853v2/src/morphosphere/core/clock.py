# Tags: [CORE_SCHEMA][CORE_RUNTIME][TEMPORAL][VERSIONED]
# Role: Defines the canonical SystemClock and AnalysisWindow objects used by
#       all runtime artifacts. Every runtime object must bind to a clock_n.
# Must Not: Import semantic_readout or legacy modules.
# Producers: pipeline.run_loop, integrator.unified_step
# Consumers: all runtime objects, windows.builder, pointset.builder, surfaces
"""SystemClock and AnalysisWindow — canonical time objects (v5 §3.1).

SystemClock provides the ONLY legal time index for the system.
All runtime objects must bind to clock_n.
Float time or wall-clock time alone cannot serve as primary keys.

AnalysisWindow defines the time envelope for analysis operations.
It is NOT a source of truth — just an analysis envelope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import hashlib


class WindowType(Enum):
    """Type of analysis window."""
    ROLLING = "rolling"
    CAUSAL = "causal"
    CENTERED = "centered"


@dataclass
class SystemClock:
    """Unique legal time index (v5 §3.1.1).

    Invariants:
        - All runtime objects MUST bind to clock_n
        - Float time or wall-clock alone cannot be primary keys
        - All windows must be expandable to clock_n intervals

    Attributes:
        clock_n: Monotonically increasing integer tick >= 0
        dt_seconds: Time step size in seconds (> 0)
        run_id: Unique identifier for the simulation run
        wall_clock_created_at: Wall-clock time when this clock was created
        tick_hash: Content hash for provenance tracking
    """
    clock_n: int = 0
    dt_seconds: float = 5e-4
    run_id: str = ""
    wall_clock_created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    tick_hash: str = ""

    @property
    def time_seconds(self) -> float:
        """Current simulation time in seconds."""
        return self.clock_n * self.dt_seconds

    def tick(self) -> None:
        """Advance the clock by one step and update the hash."""
        self.clock_n += 1
        self._update_hash()

    def _update_hash(self) -> None:
        """Compute a tick hash for provenance tracking."""
        h = hashlib.sha256()
        h.update(f"run={self.run_id}".encode())
        h.update(f"n={self.clock_n}".encode())
        h.update(f"dt={self.dt_seconds:.10e}".encode())
        self.tick_hash = h.hexdigest()[:16]

    def validate(self) -> list[str]:
        """Check internal consistency."""
        errors: list[str] = []
        if self.clock_n < 0:
            errors.append(f"clock_n must be >= 0, got {self.clock_n}")
        if self.dt_seconds <= 0:
            errors.append(f"dt_seconds must be > 0, got {self.dt_seconds}")
        if not self.run_id:
            errors.append("run_id must be non-empty")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "clock_n": self.clock_n,
            "dt_seconds": self.dt_seconds,
            "run_id": self.run_id,
            "wall_clock_created_at": self.wall_clock_created_at.isoformat(),
            "tick_hash": self.tick_hash,
            "time_seconds": self.time_seconds,
        }

    @classmethod
    def create(cls, run_id: str, dt: float) -> "SystemClock":
        """Factory: create a new SystemClock at tick 0."""
        clock = cls(clock_n=0, dt_seconds=dt, run_id=run_id)
        clock._update_hash()
        return clock


@dataclass
class AnalysisWindow:
    """Time window for analysis operations (v5 §3.1.2).

    The window is NOT a source of truth — it is only an analysis envelope.

    Invariants:
        - clock_start <= window_center <= clock_end
        - Within a run_id, window stride rules are fixed
        - Windows are expandable to [clock_start, clock_end] as clock_n range

    Attributes:
        window_id: Unique identifier for this window
        clock_start: First clock tick in window (inclusive)
        clock_end: Last clock tick in window (inclusive)
        window_center: Center tick of the window
        window_size: Number of ticks in window
        window_stride: Stride between consecutive windows
        window_type: Type of window (rolling / causal / centered)
        parent_run_id: Run ID this window belongs to
    """
    window_id: str = ""
    clock_start: int = 0
    clock_end: int = 0
    window_center: int = 0
    window_size: int = 1
    window_stride: int = 1
    window_type: WindowType = WindowType.ROLLING
    parent_run_id: str = ""

    @property
    def duration_ticks(self) -> int:
        """Number of ticks spanned by this window."""
        return self.clock_end - self.clock_start + 1

    def contains_tick(self, clock_n: int) -> bool:
        """Check if a given tick falls within this window."""
        return self.clock_start <= clock_n <= self.clock_end

    def validate(self) -> list[str]:
        """Check invariants."""
        errors: list[str] = []
        if self.clock_start > self.clock_end:
            errors.append(
                f"clock_start ({self.clock_start}) > clock_end ({self.clock_end})"
            )
        if not (self.clock_start <= self.window_center <= self.clock_end):
            errors.append(
                f"window_center ({self.window_center}) not in "
                f"[{self.clock_start}, {self.clock_end}]"
            )
        if self.window_size < 1:
            errors.append(f"window_size must be >= 1, got {self.window_size}")
        if self.window_stride < 1:
            errors.append(f"window_stride must be >= 1, got {self.window_stride}")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "clock_start": self.clock_start,
            "clock_end": self.clock_end,
            "window_center": self.window_center,
            "window_size": self.window_size,
            "window_stride": self.window_stride,
            "window_type": self.window_type.value,
            "parent_run_id": self.parent_run_id,
            "duration_ticks": self.duration_ticks,
        }

    @classmethod
    def create_rolling(
        cls,
        *,
        center_tick: int,
        half_width: int,
        stride: int = 1,
        run_id: str = "",
    ) -> "AnalysisWindow":
        """Factory: create a rolling window centered on a tick."""
        start = max(0, center_tick - half_width)
        end = center_tick + half_width
        size = end - start + 1
        window_id = f"w_{run_id}_{start}_{end}"
        return cls(
            window_id=window_id,
            clock_start=start,
            clock_end=end,
            window_center=center_tick,
            window_size=size,
            window_stride=stride,
            window_type=WindowType.ROLLING,
            parent_run_id=run_id,
        )

    @classmethod
    def create_causal(
        cls,
        *,
        end_tick: int,
        lookback: int,
        stride: int = 1,
        run_id: str = "",
    ) -> "AnalysisWindow":
        """Factory: create a causal window ending at a tick."""
        start = max(0, end_tick - lookback + 1)
        center = (start + end_tick) // 2
        size = end_tick - start + 1
        window_id = f"wc_{run_id}_{start}_{end_tick}"
        return cls(
            window_id=window_id,
            clock_start=start,
            clock_end=end_tick,
            window_center=center,
            window_size=size,
            window_stride=stride,
            window_type=WindowType.CAUSAL,
            parent_run_id=run_id,
        )
