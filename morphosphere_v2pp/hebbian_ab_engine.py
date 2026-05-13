"""Hebbian A/B Engine — Backward-compatible bridge.

v37.4.92 B3: The actual implementation has been split into the engines/
subpackage per blueprint §17 for independent reviewability:

  engines/_common.py                    — ABConfig, MeasureCoordinate, etc.
  engines/engine_a_manual_strata.py     — Baseline A
  engines/engine_b_topological_inertia.py — Candidate B (+ d_σ_t, V_Φ)
  engines/engine_c_guarded_hybrid.py    — Candidate C
  engines/harness.py                    — DualBlindABHarness

This file re-exports all public API so that existing imports like
  from hebbian_ab_engine import DualBlindABHarness, ABConfig, MeasureCoordinate
continue to work without modification.
"""
from engines._common import (                          # noqa: F401
    ABConfig, MeasureCoordinate, InternalMeasureTime,
    WeightEntry, _now, _jid, _jdump,
)
from engines.engine_a_manual_strata import (           # noqa: F401
    HebbianEngine_A_ManualStrata,
)
from engines.engine_b_topological_inertia import (     # noqa: F401
    HebbianEngine_B_TopologicalInertia,
)
from engines.engine_c_guarded_hybrid import (          # noqa: F401
    HebbianEngine_C_GuardedHybrid,
)
from engines.harness import DualBlindABHarness         # noqa: F401
