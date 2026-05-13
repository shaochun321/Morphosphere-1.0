"""V8.3 P6-P7: Xi Residue Carrier, Relation Entropy, Maturity Gate.

P6: Ξ_k is the unresolved residue carrier — NOT R, NOT noise, NOT garbage.
P7: MaturityGate enforces evidence-based object promotion.

Design principles:
  - Ξ cannot directly become P/R/Omega/T_seed (v8.2 §5.7)
  - Ξ must default-decay: |Ξ_{k+1}| < |Ξ_k| + ε, ρ < 1 (v8.2 §5.6)
  - Relation entropy is read-only: can trigger review but NOT confirm (v8.2 §9.4)
  - MaturityGate blocks promotion when evidence is missing (v8.3 §3.8)
"""
import json
import uuid
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════
#  P6: Xi Residue Carrier
# ═══════════════════════════════════════════════════════════════════════

XI_RESIDUE_TYPES = [
    "stochastic_noise",
    "unresolved_memory",
    "proto_structure",
    "boundary_uncertain",
    "numerical_residue",
    "unknown",
]

XI_CARRY_MODES = [
    "carry",       # Persist to next stage
    "decay",       # Apply exponential decay
    "promote",     # Upgrade to R_candidate or proto_structure
    "quarantine",  # Isolate for review
    "discard",     # Remove (only after review)
]


class XiResidueRecord(BaseModel):
    """V8.3 P6 / v8.2 §5: Unresolved residue carrier.

    Ξ_k is what remains after P/R extraction that cannot be structurally
    explained but also cannot be discarded. It is NOT R (R has object status).
    """
    residue_id: str = Field(..., description="Unique residue ID")
    run_id: str = Field(..., description="Run identifier")
    stage_k: int = Field(default=0)
    source_o_surface_id: Optional[str] = Field(default=None)
    source_hypothesis_refs_json: str = Field(default="[]")
    # Magnitude
    residue_norm: float = Field(default=0.0, description="||Ξ_k||")
    residue_mass: float = Field(default=0.0, description="Total residue mass")
    residue_entropy_proxy: float = Field(default=0.0, description="Entropy of residue distribution")
    # Support
    spatial_support_cell_uids_json: str = Field(default="[]")
    temporal_support_window_ids_json: str = Field(default="[]")
    # Classification
    residue_type: str = Field(default="unknown", description="Type of residue")
    # Dynamics
    carry_mode: str = Field(default="carry", description="carry/decay/promote/quarantine/discard")
    decay_rate: float = Field(default=0.1, description="Exponential decay rate ρ")
    memory_depth: int = Field(default=1, description="How many stages this residue persists")
    carry_weight: float = Field(default=1.0, description="Weight for next-stage carry")
    # Gates
    promotion_conditions_json: Optional[str] = Field(default=None)
    quarantine_conditions_json: Optional[str] = Field(default=None)
    # Audit links
    linked_noise_budget_ref: Optional[str] = Field(default=None)
    linked_anomaly_ref: Optional[str] = Field(default=None)
    linked_entropy_ref: Optional[str] = Field(default=None)
    linked_solver_diagnostic_ref: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "XiResidueRecord":
        return cls.model_validate(row)

    @staticmethod
    def from_decomposition_residual(
        run_id: str,
        stage_k: int,
        Y: np.ndarray,
        P: np.ndarray,
        R: np.ndarray,
        cell_uids: List[str],
        window_ids: List[str],
    ) -> "XiResidueRecord":
        """Create Ξ record from Y - P - R residual.

        v8.2 §5.2: Y_m = P_m + R_m + Ξ_m + ε^num_m
        """
        xi = Y - P - R
        xi_norm = float(np.linalg.norm(xi))
        xi_mass = float(np.sum(np.abs(xi)))
        # Entropy proxy: normalized entropy of |xi| distribution
        xi_abs = np.abs(xi).flatten()
        xi_abs_sum = np.sum(xi_abs)
        if xi_abs_sum > 0:
            probs = xi_abs / xi_abs_sum
            probs = probs[probs > 0]
            entropy = float(-np.sum(probs * np.log(probs)))
        else:
            entropy = 0.0

        # Classify
        if xi_norm < 0.01:
            residue_type = "numerical_residue"
            carry_mode = "discard"
        elif xi_norm < 0.1:
            residue_type = "stochastic_noise"
            carry_mode = "decay"
        else:
            residue_type = "unknown"
            carry_mode = "carry"

        return XiResidueRecord(
            residue_id=f"xi_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            stage_k=stage_k,
            residue_norm=xi_norm,
            residue_mass=xi_mass,
            residue_entropy_proxy=entropy,
            spatial_support_cell_uids_json=json.dumps(cell_uids[:10]),
            temporal_support_window_ids_json=json.dumps(window_ids),
            residue_type=residue_type,
            carry_mode=carry_mode,
        )


# ═══════════════════════════════════════════════════════════════════════
#  P6: Relation Entropy Record
# ═══════════════════════════════════════════════════════════════════════

RELATION_TYPES = [
    "transport_entropy",
    "competition_entropy",
    "origin_support_entropy",
    "residual_accumulation_entropy",
    "xi_residue_entropy",
    "boundary_entropy",
    "replay_divergence_entropy",
    "conserved_quantity_residual",
]


class RelationEntropyRecord(BaseModel):
    """V8.3 P6 / v8.2 §9: Read-only relation record between data groups.

    ALLOWED: audit, visualization, diagnostic, comparison, trigger review
    FORBIDDEN: confirm P/R, select Omega, generate T_seed, mainline truth
    """
    record_id: str = Field(..., description="Unique record ID")
    run_id: str = Field(...)
    relation_type: str = Field(default="transport_entropy")
    subject_group: str = Field(default="", description="Subject data group")
    object_group: str = Field(default="", description="Object data group")
    support_cells_json: str = Field(default="[]")
    support_windows_json: str = Field(default="[]")
    entropy_value: float = Field(default=0.0, description="H_rel(A,B)")
    normalized_entropy: float = Field(default=0.0, description="Normalized to [0,1]")
    effective_sample_size: int = Field(default=0)
    calibration_profile: str = Field(default="default_v83")
    allowed_use: str = Field(default="audit,diagnostic,comparison")
    forbidden_use: str = Field(default="confirm_pr,select_omega,generate_tseed,mainline_truth")
    created_at: Optional[str] = Field(default=None)

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "RelationEntropyRecord":
        return cls.model_validate(row)


# ═══════════════════════════════════════════════════════════════════════
#  P7: Maturity Gate Record
# ═══════════════════════════════════════════════════════════════════════

MATURITY_STATUSES = [
    "candidate", "provisional", "masked_validated", "frozen", "certified",
    "refuted", "suspended",
]

GATE_RESULTS = ["passed", "blocked", "insufficient_evidence"]


class MaturityGateRecord(BaseModel):
    """V8.3 P7 / v8.3 §3.8: Evidence-based maturity promotion gate.

    Blocks promotion when required evidence is missing. Prevents the
    v8.1 failure mode of empty support + confidence 1.0.
    """
    gate_id: str = Field(..., description="Unique gate ID")
    run_id: str = Field(...)
    target_object_type: str = Field(default="P_candidate")
    target_ref: str = Field(..., description="Reference to hypothesis/band being evaluated")
    from_status: str = Field(default="candidate")
    to_status: str = Field(default="provisional")
    required_evidence_json: str = Field(default="{}")
    provided_evidence_json: str = Field(default="{}")
    missing_evidence_json: str = Field(default="{}")
    gate_result: str = Field(default="blocked")
    failure_reason: Optional[str] = Field(default=None)
    reviewer: str = Field(default="system")
    created_at: Optional[str] = Field(default=None)

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "MaturityGateRecord":
        return cls.model_validate(row)


class MaturityGateEvaluator:
    """V8.3 P7: Evaluates whether an object can be promoted.

    Rules (v8.3 §3.8):
      candidate → provisional: needs hypothesis + occupancy
      provisional → masked_validated: needs masking records (>= 1 trial)
      masked_validated → frozen: needs transport + solver + Ξ pressure
      frozen → certified: needs multi-run + replay + stable occupancy
    """

    # Required evidence for each promotion transition
    PROMOTION_REQUIREMENTS = {
        ("candidate", "provisional"): [
            "hypothesis_exists",
            "occupancy_measure_exists",
        ],
        ("provisional", "masked_validated"): [
            "masking_trial_count_ge_1",
            "no_refuted_masking",
        ],
        ("masked_validated", "frozen"): [
            "transport_support_exists",
            "solver_converged_or_bounded",
            "xi_pressure_bounded",
            "replay_support_above_threshold",
        ],
        ("frozen", "certified"): [
            "multi_run_stable",
            "multi_boundary_variant",
            "replay_alignment_pass",
            "no_late_counterevidence",
        ],
    }

    def evaluate(
        self,
        run_id: str,
        target_ref: str,
        target_type: str,
        from_status: str,
        to_status: str,
        evidence: Dict[str, bool],
    ) -> MaturityGateRecord:
        """Evaluate a maturity promotion and return a gate record."""
        key = (from_status, to_status)
        required = self.PROMOTION_REQUIREMENTS.get(key, [])

        required_dict = {r: True for r in required}
        provided_dict = {r: evidence.get(r, False) for r in required}
        missing_dict = {r: True for r in required if not evidence.get(r, False)}

        if missing_dict:
            result = "blocked"
            reason = f"Missing: {', '.join(missing_dict.keys())}"
        else:
            result = "passed"
            reason = None

        return MaturityGateRecord(
            gate_id=f"gate_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            target_object_type=target_type,
            target_ref=target_ref,
            from_status=from_status,
            to_status=to_status,
            required_evidence_json=json.dumps(required_dict),
            provided_evidence_json=json.dumps(provided_dict),
            missing_evidence_json=json.dumps(missing_dict),
            gate_result=result,
            failure_reason=reason,
        )


# ═══════════════════════════════════════════════════════════════════════
#  V8.5 P2: Xi Decay Policy — Lifecycle Management
# ═══════════════════════════════════════════════════════════════════════

XI_LIFECYCLE_STATES = [
    "held",                   # Retained for observation
    "decaying",               # Default exponential decay active
    "proto_candidate",        # Shows cross-window/cross-scale persistence
    "promoted",               # Promoted to O_candidate (never direct P/R)
    "quarantined",            # Isolated for review
    "discarded_after_audit",  # Removed with audit trail
]


class XiDecayPolicy(BaseModel):
    """V8.5 §7.1: Xi lifecycle management and accumulation guard.

    Xi is NOT a garbage bin. Every Xi record must enter lifecycle management
    with decay, audit, and anti-unbounded-accumulation rules.
    """
    xi_id: str = Field(..., description="Reference to xi_residue_record")
    run_id: str = Field(...)
    current_state: str = Field(default="held", description="Xi lifecycle state")
    mass_current: float = Field(default=0.0, description="Current Xi mass")
    mass_previous: float = Field(default=0.0, description="Previous Xi mass")
    decay_rate: float = Field(default=0.1, description="Exponential decay rate rho")
    persistence_window_count: int = Field(default=0, description="Windows this Xi has persisted")
    relation_support_score: float = Field(default=0.0, description="Relation ledger support")
    occupancy_support_score: float = Field(default=0.0, description="Occupancy support")
    carryover_allowed: bool = Field(default=True, description="Whether carryover is allowed")
    discard_after_audit_allowed: bool = Field(default=False)
    audit_reason: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)

    def to_row(self) -> dict[str, Any]:
        d = self.model_dump()
        d["carryover_allowed"] = int(d["carryover_allowed"])
        d["discard_after_audit_allowed"] = int(d["discard_after_audit_allowed"])
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "XiDecayPolicy":
        if "carryover_allowed" in row:
            row["carryover_allowed"] = bool(row["carryover_allowed"])
        if "discard_after_audit_allowed" in row:
            row["discard_after_audit_allowed"] = bool(row["discard_after_audit_allowed"])
        return cls.model_validate(row)


class XiDecayEvaluator:
    """V8.5 §7.1: Evaluates Xi decay and lifecycle transitions.

    Default rules:
      - No growth + no relation support + no occupancy → decaying
      - Sustained decay → mass trending to zero → discarded_after_audit
      - Weak persistence but unstructured → held or decaying
      - Cross-scale persistence or boundary sensitivity → proto_candidate
      - Masking + ledger + transport jointly support → apply for O_candidate review
      - Numerical residue → solver diagnostics, not structural carry
    """

    @staticmethod
    def evaluate(
        xi_record: "XiResidueRecord",
        prev_mass: float = 0.0,
        persistence_windows: int = 0,
        relation_support: float = 0.0,
        occupancy_support: float = 0.0,
    ) -> XiDecayPolicy:
        """Determine Xi lifecycle state based on current evidence."""
        mass = xi_record.residue_mass
        rtype = xi_record.residue_type

        # Numerical residue → always discard via solver diagnostics
        if rtype == "numerical_residue":
            return XiDecayPolicy(
                xi_id=xi_record.residue_id,
                run_id=xi_record.run_id,
                current_state="discarded_after_audit",
                mass_current=mass,
                mass_previous=prev_mass,
                decay_rate=xi_record.decay_rate,
                persistence_window_count=persistence_windows,
                relation_support_score=relation_support,
                occupancy_support_score=occupancy_support,
                carryover_allowed=False,
                discard_after_audit_allowed=True,
                audit_reason="numerical_residue_routed_to_solver_diagnostics",
            )

        # Check for potential proto-structure
        has_persistence = persistence_windows >= 3
        has_relation = relation_support > 0.3
        has_occupancy = occupancy_support > 0.2
        growing = mass > prev_mass * 1.1 if prev_mass > 0 else False

        if has_persistence and (has_relation or has_occupancy):
            state = "proto_candidate"
            audit = "cross_window_persistence_with_support"
        elif growing and (has_relation or has_occupancy):
            state = "held"
            audit = "growing_with_partial_support"
        elif mass < prev_mass * 0.5 and not has_relation:
            state = "decaying"
            audit = "mass_declining_no_support"
        elif mass < 0.01 and persistence_windows > 5:
            state = "discarded_after_audit"
            audit = "near_zero_mass_long_persistence"
        else:
            state = "held"
            audit = "default_hold"

        return XiDecayPolicy(
            xi_id=xi_record.residue_id,
            run_id=xi_record.run_id,
            current_state=state,
            mass_current=mass,
            mass_previous=prev_mass,
            decay_rate=xi_record.decay_rate,
            persistence_window_count=persistence_windows,
            relation_support_score=relation_support,
            occupancy_support_score=occupancy_support,
            carryover_allowed=state not in ("discarded_after_audit",),
            discard_after_audit_allowed=state == "discarded_after_audit",
            audit_reason=audit,
        )


# ═══════════════════════════════════════════════════════════════════════
#  V8.5 P2: Refutation Conjunctive Evaluator (§6.2)
# ═══════════════════════════════════════════════════════════════════════

class RefutationConjunctiveEvaluator:
    """V8.5 §6.2: Conjunctive conditions for refutation.

    A candidate h enters 'refuted' only when ALL of:
      - masking_refutes(h) is true
      - temporal_persistence(h) < theta_time
      - scale_persistence(h, K) < theta_scale
      - occupancy_length(h) → 0
      - relation_entropy(h) → background_entropy
      - no_Xi_carryover(h) is true
    """

    @staticmethod
    def evaluate_refutation(
        masking_refutes: bool,
        temporal_persistence: float,
        scale_persistence: float,
        occupancy_length: float,
        relation_entropy_near_background: bool,
        no_xi_carryover: bool,
        theta_time: float = 0.3,
        theta_scale: float = 0.2,
        occupancy_threshold: float = 0.05,
    ) -> Dict[str, Any]:
        """Evaluate conjunctive refutation conditions.

        Returns dict with 'should_refute' and per-condition details.
        """
        conditions = {
            "masking_refutes": masking_refutes,
            "temporal_persistence_below_threshold": temporal_persistence < theta_time,
            "scale_persistence_below_threshold": scale_persistence < theta_scale,
            "occupancy_near_zero": occupancy_length < occupancy_threshold,
            "relation_entropy_at_background": relation_entropy_near_background,
            "no_xi_carryover": no_xi_carryover,
        }
        should_refute = all(conditions.values())

        return {
            "should_refute": should_refute,
            "conditions": conditions,
            "met_count": sum(1 for v in conditions.values() if v),
            "total_count": len(conditions),
        }


# ═══════════════════════════════════════════════════════════════════════
#  V8.5 P2: Scale Index K (§6.0)
# ═══════════════════════════════════════════════════════════════════════

class ScaleIndexK(BaseModel):
    """V8.5 §6.0: Formal scale/coarse-graining/resolution index.

    K is NOT time index k. K=0 is finest resolution (point-set/carrier).
    K+1 is coarser relation or measure representation.
    """
    K: int = Field(..., description="Scale level, 0 = finest")
    construction_method: str = Field(..., description="How this K level was constructed")
    input_source: str = Field(default="", description="Input data for this K level")
    reversible: bool = Field(default=False, description="Whether K→K-1 is reversible or audit-only")
    generates_proxy_provenance: bool = Field(default=False)
    allowed_influence: str = Field(
        default="support_report_only",
        description="support_report_only / confirmation_graph_input"
    )

    def to_row(self) -> dict[str, Any]:
        d = self.model_dump()
        d["reversible"] = int(d["reversible"])
        d["generates_proxy_provenance"] = int(d["generates_proxy_provenance"])
        return d

