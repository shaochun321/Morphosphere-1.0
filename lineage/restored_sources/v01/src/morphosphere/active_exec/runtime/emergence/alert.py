"""V8.5 P5: Emergence Alert Channel + Raw Emergency Export.

V8.5 §10: The emergence alert channel is a WARNING channel, not a mainline
write channel. It cannot directly freeze P/R, promote Xi, change Omega,
change T_seed, or auto-invoke research to modify mainline.

V8.5 §10.2: Trigger requires basic_condition AND strong_trigger_condition.

V8.5 §11: Raw Emergency Export Bundle is a controlled supplement to the
v8.4 data diode. Still one-way export, no writeback.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════
#  Emergence Alert
# ═══════════════════════════════════════════════════════════════════════

EMERGENCE_SEVERITY = ["low", "medium", "high", "critical"]

EMERGENCE_ACTIONS = [
    "fast_review",
    "raw_emergency_export",
    "repeat_run",
    "add_hard_case",
    "no_action",
]

# V8.5 §10.2: Basic conditions (alone do NOT trigger)
BASIC_CONDITIONS = [
    "solver_nonconvergence_repeated",
    "masking_inconclusive",
    "xi_mild_growth",
    "single_transport_anomaly",
    "single_entropy_deviation",
]

# V8.5 §10.2: Strong trigger conditions
STRONG_TRIGGER_CONDITIONS = [
    "occupancy_persistence_sudden_increase",
    "transport_instability_plus_entropy_anomaly",
    "boundary_topology_tearing",
    "R_proto_center_anomaly_unexplained",
    "scale_persistence_sudden_appearance",
    "xi_mass_occupancy_relation_joint_growth",
    "anomaly_replicated_in_repeated_runs",
]


class EmergenceAlert(BaseModel):
    """V8.5 §10.3: Emergence alert record.

    Can trigger fast review and raw emergency export, but CANNOT:
    - Directly freeze P/R
    - Directly promote Xi
    - Change Omega
    - Change T_seed
    - Auto-invoke research to modify mainline
    - Serve as sole evidence for any mainline change
    """
    alert_id: str = Field(..., description="Unique alert ID")
    run_id: str = Field(...)
    alert_type: str = Field(
        default="real_emergence",
        description="real_emergence / synthetic_test"
    )
    trigger_window_start: int = Field(default=0)
    trigger_window_end: int = Field(default=0)
    related_o_candidates_json: str = Field(default="[]")
    related_pr_candidates_json: str = Field(default="[]")
    related_xi_ids_json: str = Field(default="[]")
    basic_conditions_json: str = Field(default="[]", description="Basic conditions met")
    strong_trigger_conditions_json: str = Field(default="[]", description="Strong triggers met")
    severity: str = Field(default="low")
    recommended_action: str = Field(default="no_action")
    forbidden_actions_acknowledged: bool = Field(default=True)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_row(self) -> dict[str, Any]:
        d = self.model_dump()
        d["forbidden_actions_acknowledged"] = int(d["forbidden_actions_acknowledged"])
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "EmergenceAlert":
        if "forbidden_actions_acknowledged" in row:
            row["forbidden_actions_acknowledged"] = bool(row["forbidden_actions_acknowledged"])
        return cls.model_validate(row)


class EmergenceAlertEvaluator:
    """V8.5 §10.2: Evaluates whether emergence alert should trigger.

    Rule: at_least_one(basic) AND at_least_one(strong) AND not_explainable
    """

    @staticmethod
    def evaluate(
        basic_conditions: List[str],
        strong_conditions: List[str],
        explainable_by_current_pr: bool = False,
    ) -> Dict[str, Any]:
        """Evaluate emergence trigger conditions.

        Returns dict with should_trigger, severity, and recommended_action.
        """
        has_basic = len(basic_conditions) > 0
        has_strong = len(strong_conditions) > 0
        not_explainable = not explainable_by_current_pr

        should_trigger = has_basic and has_strong and not_explainable

        # Severity based on strong condition count
        n_strong = len(strong_conditions)
        if n_strong >= 3:
            severity = "critical"
            action = "raw_emergency_export"
        elif n_strong >= 2:
            severity = "high"
            action = "fast_review"
        elif n_strong >= 1:
            severity = "medium"
            action = "repeat_run"
        else:
            severity = "low"
            action = "no_action"

        return {
            "should_trigger": should_trigger,
            "severity": severity,
            "recommended_action": action,
            "basic_conditions": basic_conditions,
            "strong_conditions": strong_conditions,
            "explainable_by_current_pr": explainable_by_current_pr,
        }


# ═══════════════════════════════════════════════════════════════════════
#  Raw Emergency Export Manifest (V8.5 §11.4)
# ═══════════════════════════════════════════════════════════════════════

EXPORT_TYPES = [
    "real_emergence",
    "synthetic_test",
    "debug_replay",
    "human_requested_review",
]


class RawEmergencyExportManifest(BaseModel):
    """V8.5 §11.4: Emergency export manifest — NOT a confirmation graph bypass.

    Must reference an emergence_alert_id. Cannot auto-trigger P/R state
    updates, threshold modifications, Omega selection, or T_seed generation.
    """
    export_id: str = Field(..., description="Unique export ID")
    export_type: str = Field(default="real_emergence")
    emergence_alert_id: str = Field(..., description="Must reference an alert")
    trigger_conditions_json: str = Field(default="[]")
    run_id: str = Field(...)
    window_start: int = Field(default=0)
    window_end: int = Field(default=0)
    K_scope_json: str = Field(default="[0]", description="Scale indices in scope")
    production_log_allowed: bool = Field(default=False)
    scientific_use_allowed: bool = Field(default=False)
    cleanup_policy: str = Field(default="archive_after_review")
    forbidden_actions_acknowledged: bool = Field(default=True)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_row(self) -> dict[str, Any]:
        d = self.model_dump()
        d["production_log_allowed"] = int(d["production_log_allowed"])
        d["scientific_use_allowed"] = int(d["scientific_use_allowed"])
        d["forbidden_actions_acknowledged"] = int(d["forbidden_actions_acknowledged"])
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "RawEmergencyExportManifest":
        for k in ("production_log_allowed", "scientific_use_allowed", "forbidden_actions_acknowledged"):
            if k in row:
                row[k] = bool(row[k])
        return cls.model_validate(row)
