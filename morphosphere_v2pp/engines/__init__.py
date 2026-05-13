"""Hebbian A/B/C engines package — blueprint §17 structure.

Re-exports all public API so that `from engines import X` works.
"""
from engines._common import (
    ABConfig, MeasureCoordinate, InternalMeasureTime, WeightEntry,
    _now, _jid, _jdump,
)
from engines.engine_a_manual_strata import HebbianEngine_A_ManualStrata
from engines.engine_b_topological_inertia import HebbianEngine_B_TopologicalInertia
from engines.engine_c_guarded_hybrid import HebbianEngine_C_GuardedHybrid
from engines.harness import DualBlindABHarness

__all__ = [
    "ABConfig", "MeasureCoordinate", "InternalMeasureTime", "WeightEntry",
    "HebbianEngine_A_ManualStrata",
    "HebbianEngine_B_TopologicalInertia",
    "HebbianEngine_C_GuardedHybrid",
    "DualBlindABHarness",
]
