"""V8.5 §14: Proxy Provenance — anti-fraud mechanism for temporary fills.

Proxy is NOT fraud. It is explicitly marked temporary engineering fill.
Its legitimacy comes from explicit marking, not default trust.

V8.5 §14.4: Proxy density budget limits proxy concentration per run type.
V8.5 §14.5: Proxy overload gate triggers run type downgrade.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


PROXY_TYPES = [
    "synthetic",     # Generated test data
    "surrogate",     # Replacement from related measurement
    "mock",          # Empty/constant placeholder
    "pilot",         # External pilot algorithm output
    "inferred",      # Derived from indirect evidence
    "placeholder",   # Structural placeholder, no data
]


class ProxyProvenance(BaseModel):
    """V8.5 §14.2: Proxy provenance record."""
    proxy_id: str = Field(..., description="Unique proxy ID")
    run_id: str = Field(...)
    target_field: str = Field(..., description="Field being proxied")
    proxy_type: str = Field(default="placeholder")
    proxy_reason: str = Field(default="", description="Why proxy is used")
    source_assumption: str = Field(default="", description="Underlying assumption")
    maturity_status: str = Field(default="active", description="Proxy lifecycle status")
    replacement_condition: str = Field(default="", description="When proxy should be replaced")
    forbidden_interpretation: str = Field(
        default="scientific_conclusion,final_pr_certification",
        description="What this proxy CANNOT be used for"
    )
    created_by: str = Field(default="system")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    review_due: Optional[str] = Field(default=None)

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ProxyProvenance":
        return cls.model_validate(row)


# ═══════════════════════════════════════════════════════════════════════
#  Proxy Density Budget (V8.5 §14.4)
# ═══════════════════════════════════════════════════════════════════════

PROXY_DENSITY_BUDGETS = {
    "diagnostic_run": 0.8,
    "construction_run": 0.5,
    "calibration_run": 0.3,
    "scientific_run": 0.1,
    "publication_run": 0.02,
}


class ProxyDensityReport(BaseModel):
    """V8.5 §14.4: Proxy density report for a run."""
    report_id: str = Field(default_factory=lambda: f"pdr_{uuid.uuid4().hex[:8]}")
    run_id: str = Field(...)
    run_type: str = Field(default="diagnostic_run")
    total_fields_checked: int = Field(default=0)
    proxy_fields_count: int = Field(default=0)
    proxy_density: float = Field(default=0.0)
    critical_path_proxy_density: float = Field(default=0.0)
    geometry_proxy_density: float = Field(default=0.0)
    transport_proxy_density: float = Field(default=0.0)
    pr_proxy_density: float = Field(default=0.0)
    ledger_proxy_density: float = Field(default=0.0)
    allowed_budget: float = Field(default=0.8)
    overload_gate_triggered: bool = Field(default=False)
    downgrade_run_type_to: Optional[str] = Field(default=None)

    def to_row(self) -> dict[str, Any]:
        d = self.model_dump()
        d["overload_gate_triggered"] = int(d["overload_gate_triggered"])
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ProxyDensityReport":
        if "overload_gate_triggered" in row:
            row["overload_gate_triggered"] = bool(row["overload_gate_triggered"])
        return cls.model_validate(row)


class ProxyDensityEvaluator:
    """V8.5 §14.5: Evaluates proxy density against budget."""

    @staticmethod
    def evaluate(
        run_id: str,
        run_type: str,
        proxy_count: int,
        total_fields: int,
        critical_path_proxy_count: int = 0,
        critical_path_total: int = 0,
    ) -> ProxyDensityReport:
        density = proxy_count / total_fields if total_fields > 0 else 0.0
        critical_density = (
            critical_path_proxy_count / critical_path_total
            if critical_path_total > 0 else 0.0
        )
        budget = PROXY_DENSITY_BUDGETS.get(run_type, 0.8)
        overload = critical_density > budget

        downgrade = None
        if overload:
            types = list(PROXY_DENSITY_BUDGETS.keys())
            idx = types.index(run_type) if run_type in types else 0
            if idx > 0:
                downgrade = types[idx - 1]
            else:
                downgrade = "diagnostic_run"

        return ProxyDensityReport(
            run_id=run_id,
            run_type=run_type,
            total_fields_checked=total_fields,
            proxy_fields_count=proxy_count,
            proxy_density=density,
            critical_path_proxy_density=critical_density,
            allowed_budget=budget,
            overload_gate_triggered=overload,
            downgrade_run_type_to=downgrade,
        )
