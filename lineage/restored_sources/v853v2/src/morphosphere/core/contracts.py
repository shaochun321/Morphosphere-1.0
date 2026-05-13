# Tags: [CORE_SCHEMA][QA_VALIDATION]
# Role: Object contracts and invariant checking for v5 objects.
# Must Not: Import semantic_readout or legacy modules.
"""Object contracts and invariant checking (v5 §1).

Hard constraints that must hold at all times:
  1. No-Semantic-Backflow: semantic labels never enter generation layer
  2. P/R Neutrality: decomposition is label-free
  3. Ledger-Only: ledger records, never drives
  4. Shell0-Testable: shell0 is hypothesis, not fact
  5. Back-Projectable: every point has provenance
"""

from __future__ import annotations

from typing import Any

from .cell_graph_state import CellGraphState
from .clock import SystemClock, AnalysisWindow


# ── Contract violation error ────────────────────────────────────────────────

class ContractViolation(Exception):
    """Raised when a v5 invariant is violated."""
    pass


# ── CellGraphState contracts ───────────────────────────────────────────────

def check_state_contracts(state: CellGraphState) -> list[str]:
    """Check all contracts on a CellGraphState.

    Returns list of violation messages. Empty = all good.
    """
    violations: list[str] = []

    # C1: Must have non-negative clock_n
    if state.clock_n < 0:
        violations.append(f"C1: clock_n must be >= 0, got {state.clock_n}")

    # C2: Shape consistency
    violations.extend(state.validate())

    # C3: Time and clock_n should be consistent if clock_n > 0
    # (soft check — float drift is expected)

    return violations


def check_clock_contracts(clock: SystemClock) -> list[str]:
    """Check all contracts on a SystemClock."""
    return clock.validate()


def check_window_contracts(window: AnalysisWindow) -> list[str]:
    """Check all contracts on an AnalysisWindow."""
    return window.validate()


# ── Pipeline-level contracts ────────────────────────────────────────────────

FORBIDDEN_SEMANTIC_TOKENS = frozenset({
    "translation", "rotation", "family", "dominant_family",
    "motion_class", "audit_verdict", "reader_summary",
    "onset", "recovery",
})


def check_no_semantic_leakage(data: dict[str, Any],
                                context: str = "") -> list[str]:
    """Check that a dict does not contain forbidden semantic tokens.

    Used to verify P/R decomposition results are label-free.
    """
    violations: list[str] = []
    data_str = str(data).lower()
    for token in FORBIDDEN_SEMANTIC_TOKENS:
        if token in data_str:
            violations.append(
                f"Semantic leakage: '{token}' found in {context or 'data'}"
            )
    return violations


def check_provenance_present(points: list[dict[str, Any]],
                               context: str = "") -> list[str]:
    """Check that every point has provenance information."""
    violations: list[str] = []
    for i, p in enumerate(points):
        if not p.get("provenance_hash"):
            violations.append(
                f"Missing provenance_hash on point {i} in {context or 'data'}"
            )
        source_cells = p.get("source_cell_ids", [])
        source_patches = p.get("source_patch_ids", [])
        if not source_cells and not source_patches:
            violations.append(
                f"No source_cell_ids or source_patch_ids on point {i} in {context or 'data'}"
            )
    return violations


# ── Aggregate checker ───────────────────────────────────────────────────────

def run_all_contracts(state: CellGraphState,
                       clock: SystemClock | None = None,
                       decomposition: dict[str, Any] | None = None) -> list[str]:
    """Run all available contract checks and return violations."""
    violations: list[str] = []

    violations.extend(check_state_contracts(state))

    if clock is not None:
        violations.extend(check_clock_contracts(clock))

    if decomposition is not None:
        violations.extend(
            check_no_semantic_leakage(decomposition, "decomposition")
        )

    return violations
