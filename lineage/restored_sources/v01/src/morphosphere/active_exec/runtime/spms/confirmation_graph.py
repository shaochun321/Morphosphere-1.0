"""V8.5 P1: P/R Confirmation Graph — replaces linear P/R state machine.

V8.5 §4: P/R is no longer a linear promotion chain:
  candidate → provisional → masked_validated → frozen → certified

Instead it is a Confirmation Graph that allows regression, suspension,
Xi routing, emergence alerts, and fast review.

Core nodes:
  O_candidate → PR_candidate → mask_supported → recursion_eligible
  → compute_committed → science_certified

Diversion nodes:
  refuted, suspended, xi_carried, emergence_alerted

Design principles:
  - "Freeze" no longer means terminal truth, only staged compute commitment
  - Masking counterevidence is embedded INTO the confirmation process
  - O_candidate must be associated with masking (V8.5 §4.3)
  - Empty support cannot yield confidence 1.0 (inherited from V8.3)
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════
#  Confirmation Graph Node Definitions
# ═══════════════════════════════════════════════════════════════════════

CONFIRMATION_NODES = [
    "O_candidate",
    "PR_candidate",
    "mask_supported",
    "recursion_eligible",
    "compute_committed",
    "science_certified",
    # Diversion nodes
    "refuted",
    "suspended",
    "xi_carried",
    "emergence_alerted",
]

# Valid transitions in the confirmation graph
VALID_TRANSITIONS = {
    ("O_candidate", "PR_candidate"),
    ("O_candidate", "suspended"),
    ("O_candidate", "refuted"),
    ("PR_candidate", "mask_supported"),
    ("PR_candidate", "refuted"),
    ("PR_candidate", "suspended"),
    ("PR_candidate", "xi_carried"),
    ("mask_supported", "recursion_eligible"),
    ("mask_supported", "refuted"),
    ("mask_supported", "suspended"),
    ("mask_supported", "xi_carried"),
    ("mask_supported", "emergence_alerted"),
    ("recursion_eligible", "compute_committed"),
    ("recursion_eligible", "suspended"),
    ("recursion_eligible", "xi_carried"),
    ("compute_committed", "science_certified"),
    ("compute_committed", "suspended"),
    # Re-entry from diversion
    ("suspended", "PR_candidate"),
    ("suspended", "xi_carried"),
    ("emergence_alerted", "PR_candidate"),
    ("emergence_alerted", "xi_carried"),
    ("emergence_alerted", "suspended"),
}

# V8.5 §5.2: Extended masking verdicts
MASKING_VERDICTS_V85 = [
    "supports_confirmation",
    "weakens_confirmation",
    "refutes_candidate",
    "inconclusive",
    "escalate_to_replay",
    "escalate_to_boundary",
    "downgrade_to_xi",
    "trigger_emergence_alert",
]

# V8.3 → V8.5 verdict mapping
V83_TO_V85_VERDICT = {
    "supports_freeze": "supports_confirmation",
    "weakens_freeze": "weakens_confirmation",
    "refutes_freeze": "refutes_candidate",
    "inconclusive": "inconclusive",
}


# ═══════════════════════════════════════════════════════════════════════
#  Confirmation Graph Record
# ═══════════════════════════════════════════════════════════════════════

class PRConfirmationGraphRecord(BaseModel):
    """V8.5 §4: Confirmation graph state for a P/R/Ξ candidate.

    Replaces the linear maturity_flag. Each candidate has a current
    node in the confirmation graph, with full transition history.
    """
    record_id: str = Field(..., description="Unique record ID")
    run_id: str = Field(...)
    hypothesis_id: str = Field(..., description="Reference to object_hypothesis")
    hypothesis_type: str = Field(default="P_candidate")
    current_node: str = Field(default="O_candidate", description="Current graph node")
    previous_node: Optional[str] = Field(default=None)
    # O-level associations (V8.5 §4.3)
    o_field_surface_id: Optional[str] = Field(default=None)
    o_candidate_surface_id: Optional[str] = Field(default=None)
    o_candidate_lineage_id: Optional[str] = Field(default=None)
    # Evidence summary
    masking_trial_count: int = Field(default=0)
    masking_support_count: int = Field(default=0)
    masking_refute_count: int = Field(default=0)
    replay_pass_count: int = Field(default=0)
    boundary_variant_count: int = Field(default=0)
    transport_support_score: float = Field(default=0.0)
    occupancy_persistence_length: int = Field(default=0)
    xi_pressure: float = Field(default=0.0)
    emergence_alert_id: Optional[str] = Field(default=None)
    # Metadata
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: Optional[str] = Field(default=None)

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "PRConfirmationGraphRecord":
        return cls.model_validate(row)


# ═══════════════════════════════════════════════════════════════════════
#  Confirmation Graph Transition Record
# ═══════════════════════════════════════════════════════════════════════

class PRGraphTransitionRecord(BaseModel):
    """V8.5 §4: Records a single transition in the confirmation graph.

    Every state change must be recorded with evidence and reason.
    This replaces the V8.3 maturity_gate_record as the primary
    promotion/demotion tracking mechanism.
    """
    transition_id: str = Field(..., description="Unique transition ID")
    run_id: str = Field(...)
    hypothesis_id: str = Field(..., description="Target hypothesis")
    from_node: str = Field(..., description="Source node")
    to_node: str = Field(..., description="Destination node")
    trigger: str = Field(default="system", description="What triggered this transition")
    evidence_json: str = Field(default="{}", description="Evidence supporting transition")
    missing_evidence_json: str = Field(default="{}", description="Evidence that was missing")
    masking_record_ids_json: str = Field(default="[]", description="Related masking records")
    verdict: Optional[str] = Field(default=None, description="Masking verdict if applicable")
    is_valid: bool = Field(default=True, description="Whether transition is structurally valid")
    failure_reason: Optional[str] = Field(default=None)
    reviewer: str = Field(default="system")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_row(self) -> dict[str, Any]:
        d = self.model_dump()
        d["is_valid"] = int(d["is_valid"])
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "PRGraphTransitionRecord":
        if "is_valid" in row:
            row["is_valid"] = bool(row["is_valid"])
        return cls.model_validate(row)


# ═══════════════════════════════════════════════════════════════════════
#  Confirmation Graph Evaluator
# ═══════════════════════════════════════════════════════════════════════

class ConfirmationGraphEvaluator:
    """V8.5 §4: Evaluates transitions in the P/R Confirmation Graph.

    Replaces MaturityGateEvaluator with graph-aware logic.
    Key rules:
      - O_candidate → PR_candidate: needs hypothesis + O association
      - PR_candidate → mask_supported: needs masking trial >= 1, no refutation
      - mask_supported → recursion_eligible: needs transport + solver + Xi bounded
      - recursion_eligible → compute_committed: needs multi-run stability
      - compute_committed → science_certified: needs multi-run + multi-boundary + replay

    Diversion rules:
      - Any node → refuted: requires conjunctive refutation (V8.5 §6.2)
      - Any node → xi_carried: unresolved but non-discardable
      - mask_supported → emergence_alerted: non-linear emergence detected
    """

    # Required evidence for each transition
    TRANSITION_REQUIREMENTS = {
        ("O_candidate", "PR_candidate"): [
            "hypothesis_exists",
            "o_candidate_associated",
        ],
        ("PR_candidate", "mask_supported"): [
            "masking_trial_count_ge_1",
            "no_refuted_masking",
        ],
        ("mask_supported", "recursion_eligible"): [
            "transport_support_exists",
            "solver_converged_or_bounded",
            "xi_pressure_bounded",
        ],
        ("recursion_eligible", "compute_committed"): [
            "multi_run_stability",
            "replay_support_above_threshold",
        ],
        ("compute_committed", "science_certified"): [
            "multi_run_stable",
            "multi_boundary_variant",
            "replay_alignment_pass",
            "no_late_counterevidence",
        ],
    }

    # Diversion transitions (no strict requirements, only triggers)
    DIVERSION_TRANSITIONS = {
        "refuted", "suspended", "xi_carried", "emergence_alerted",
    }

    def evaluate_transition(
        self,
        run_id: str,
        hypothesis_id: str,
        from_node: str,
        to_node: str,
        evidence: Dict[str, bool],
        trigger: str = "system",
    ) -> PRGraphTransitionRecord:
        """Evaluate whether a transition is allowed and return a record."""

        # Check structural validity
        is_valid_transition = (from_node, to_node) in VALID_TRANSITIONS
        if not is_valid_transition:
            return PRGraphTransitionRecord(
                transition_id=f"tr_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                hypothesis_id=hypothesis_id,
                from_node=from_node,
                to_node=to_node,
                trigger=trigger,
                is_valid=False,
                failure_reason=f"Invalid transition: {from_node} → {to_node}",
            )

        # Diversion transitions don't require strict evidence
        if to_node in self.DIVERSION_TRANSITIONS:
            return PRGraphTransitionRecord(
                transition_id=f"tr_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                hypothesis_id=hypothesis_id,
                from_node=from_node,
                to_node=to_node,
                trigger=trigger,
                evidence_json=json.dumps({k: v for k, v in evidence.items() if v}),
                is_valid=True,
            )

        # Standard transitions require evidence
        key = (from_node, to_node)
        required = self.TRANSITION_REQUIREMENTS.get(key, [])
        provided = {r: evidence.get(r, False) for r in required}
        missing = {r: True for r in required if not evidence.get(r, False)}

        if missing:
            return PRGraphTransitionRecord(
                transition_id=f"tr_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                hypothesis_id=hypothesis_id,
                from_node=from_node,
                to_node=to_node,
                trigger=trigger,
                evidence_json=json.dumps(provided),
                missing_evidence_json=json.dumps(missing),
                is_valid=True,  # structurally valid, but blocked
                failure_reason=f"Blocked: missing {', '.join(missing.keys())}",
            )

        return PRGraphTransitionRecord(
            transition_id=f"tr_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            hypothesis_id=hypothesis_id,
            from_node=from_node,
            to_node=to_node,
            trigger=trigger,
            evidence_json=json.dumps(provided),
            is_valid=True,
        )

    def determine_masking_action(
        self,
        verdict: str,
        current_node: str,
    ) -> Optional[str]:
        """Given a masking verdict, determine the recommended graph action.

        Returns the target node (or None if no state change recommended).
        """
        if current_node not in ("PR_candidate", "mask_supported"):
            return None

        action_map = {
            "supports_confirmation": "mask_supported" if current_node == "PR_candidate" else None,
            "weakens_confirmation": None,  # stay, lower priority
            "refutes_candidate": "refuted",
            "inconclusive": None,  # stay
            "escalate_to_replay": None,  # add to replay queue, don't change node
            "escalate_to_boundary": None,  # add to boundary queue
            "downgrade_to_xi": "xi_carried",
            "trigger_emergence_alert": "emergence_alerted",
        }
        return action_map.get(verdict)
