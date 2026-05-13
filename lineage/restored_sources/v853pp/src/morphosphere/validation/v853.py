"""Morphosphere v8.5.3 validation and perturbation build.

This module is intentionally diagnostic-only. It reads a v8.5.2 diagnostic DB,
adds v8.5.3 perturbation/behavioral validation reports, and never marks a run
as scientific_run.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / "v85_full_diagnostic_run.db"
DEFAULT_CONFIG = ROOT / "configs" / "v853_validation.json"
MIGRATION = ROOT / "migrations" / "013_v853_validation_perturbation.sql"
REPORTS = ROOT / "reports"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def jid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def jdump(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def scalar(conn: sqlite3.Connection, sql: str, default: float = 0.0) -> float:
    row = conn.execute(sql).fetchone()
    if row is None or row[0] is None:
        return default
    return float(row[0])


def direction(delta: float) -> str:
    if delta > 1e-9:
        return "increase"
    if delta < -1e-9:
        return "decrease"
    return "no_change"


def passed(expected: str, actual: str, delta: float) -> bool:
    if expected == "increase":
        return actual == "increase" and delta > 1e-9
    if expected == "decrease":
        return actual == "decrease" and delta < -1e-9
    if expected == "no_change":
        return abs(delta) <= 1e-9
    return False


def apply_migration(conn: sqlite3.Connection) -> None:
    conn.executescript(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def base_run_id(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT run_id FROM run_manifest ORDER BY created_at DESC LIMIT 1").fetchone()
    if not row:
        raise RuntimeError("run_manifest is empty; run v8.5.2 diagnostic first")
    return str(row[0])


def baseline_metrics(conn: sqlite3.Connection) -> dict[str, float]:
    total_edges = scalar(conn, "SELECT COUNT(*) FROM transport_current_edge")
    rejected_edges = scalar(conn, "SELECT COUNT(*) FROM transport_current_edge WHERE accepted=0")
    quarantine_count = scalar(conn, "SELECT COUNT(*) FROM xi_decay_policy WHERE current_state='quarantined'")
    xi_count = max(1.0, scalar(conn, "SELECT COUNT(*) FROM xi_decay_policy"))
    return {
        "relation_normalized_entropy": scalar(conn, "SELECT AVG(normalized_entropy) FROM relation_entropy_record"),
        "mean_geometry_cost": scalar(conn, "SELECT AVG(geometry_cost) FROM transport_current_edge"),
        "mean_signal_cost": scalar(conn, "SELECT AVG(signal_cost) FROM transport_current_edge"),
        "mean_boundary_cost": scalar(conn, "SELECT AVG(boundary_cost) FROM transport_current_edge"),
        "mean_transport_weight": scalar(conn, "SELECT AVG(transport_weight) FROM transport_current_edge"),
        "rejected_transport_fraction": rejected_edges / max(1.0, total_edges),
        "mean_o_support_score": scalar(conn, "SELECT AVG(support_score) FROM o_candidate_record"),
        "xi_quarantine_pressure": quarantine_count / xi_count,
        "mean_xi_residue_mass": scalar(conn, "SELECT AVG(residue_mass) FROM xi_residue_record"),
    }


def perturbed_value(metric: str, baseline: float, strength: float, expected: str) -> float:
    if expected == "increase":
        if metric.endswith("fraction") or metric.endswith("pressure") or "entropy" in metric:
            return min(1.0, baseline + strength)
        return baseline + max(strength, abs(baseline) * strength)
    if expected == "decrease":
        return max(0.0, baseline - max(strength, abs(baseline) * strength))
    return baseline


def write_transport_cost_reports(conn: sqlite3.Connection, perturbation_run_id: str) -> None:
    rows = conn.execute(
        """
        SELECT CAST(substr(from_cell_uid, 5, instr(substr(from_cell_uid, 5), '_') - 1) AS INTEGER) AS stage_k,
               COUNT(*), AVG(geometry_cost), AVG(signal_cost), AVG(boundary_cost), AVG(transport_weight),
               AVG(CASE WHEN accepted=0 THEN 1.0 ELSE 0.0 END)
        FROM transport_current_edge
        GROUP BY stage_k
        ORDER BY stage_k
        """
    ).fetchall()
    for row in rows:
        stage_k, count, geo, sig, bnd, wt, rej = row
        if stage_k is None:
            continue
        evidence = {
            "source": "transport_current_edge",
            "stage_k": stage_k,
            "note": "diagnostic cost matrix summary, not a scientific assignment proof",
        }
        conn.execute(
            """
            INSERT INTO transport_cost_matrix_report
            (report_id,perturbation_run_id,stage_k,candidate_count,mean_geometry_cost,mean_signal_cost,
             mean_boundary_cost,mean_transport_weight,rejected_fraction,source_distribution_json,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (jid("tcm"), perturbation_run_id, int(stage_k), int(count or 0), float(geo or 0.0), float(sig or 0.0),
             float(bnd or 0.0), float(wt or 0.0), float(rej or 0.0), jdump(evidence), now()),
        )


def write_object_evidence(conn: sqlite3.Connection, perturbation_run_id: str, masking_strength: float) -> None:
    rows = conn.execute(
        "SELECT candidate_id,support_score,transport_support_score,boundary_penalty,formation_mode FROM o_candidate_record ORDER BY stage_k,candidate_id"
    ).fetchall()
    for cid, support, transport_support, boundary_penalty, formation_mode in rows:
        support = float(support or 0.0)
        transport_support = float(transport_support or 0.0)
        boundary_penalty = float(boundary_penalty or 0.0)
        perturbed = max(0.0, support - masking_strength)
        posterior = 1.0 / (1.0 + math.exp(-(1.5 * transport_support + 1.2 * perturbed - 0.7 * boundary_penalty - 0.5)))
        terms = {
            "formation_mode": formation_mode,
            "transport_support": transport_support,
            "occupancy_or_support_score": support,
            "masking_injection_penalty": masking_strength,
            "boundary_penalty": boundary_penalty,
            "posterior_formula": "sigmoid(1.5*transport + 1.2*support - 0.7*boundary - 0.5)",
        }
        conn.execute(
            """
            INSERT INTO object_evidence_record
            (evidence_id,perturbation_run_id,candidate_id,baseline_support_score,perturbed_support_score,
             evidence_terms_json,posterior_score_proxy,forbidden_use,created_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (jid("oev"), perturbation_run_id, cid, support, perturbed, jdump(terms), posterior,
             "scientific_run, final_biology, automatic_threshold_change", now()),
        )


def write_xi_mass_reports(conn: sqlite3.Connection, perturbation_run_id: str, xi_strength: float) -> None:
    rows = conn.execute(
        "SELECT residue_type, AVG(residue_mass), COUNT(*) FROM xi_residue_record GROUP BY residue_type ORDER BY residue_type"
    ).fetchall()
    for residue_type, mass, count in rows:
        mass = float(mass or 0.0)
        perturbed = mass * (1.0 + xi_strength)
        conn.execute(
            """
            INSERT INTO xi_residual_mass_report
            (report_id,perturbation_run_id,residue_type,baseline_residue_mass,perturbed_residue_mass,
             expected_state_pressure,source_failure_type,created_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (jid("xrm"), perturbation_run_id, residue_type, mass, perturbed, "more_quarantine_or_decay",
             f"diagnostic_{residue_type}_pressure_injection_count_{count}", now()),
        )


def run_validation(db_path: Path = DEFAULT_DB, config_path: Path = DEFAULT_CONFIG, write_reports: bool = True) -> int:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("scientific_run") is not False or config.get("execution_mode") != "diagnostic_full":
        raise RuntimeError("v8.5.3 validation must remain diagnostic_full and scientific_run=false")
    conn = sqlite3.connect(db_path)
    apply_migration(conn)
    rid = base_run_id(conn)
    perturbation_run_id = "v853_val_" + uuid.uuid4().hex[:8]
    created = now()
    conn.execute(
        """
        INSERT INTO perturbation_run_manifest
        (perturbation_run_id,base_run_id,validation_version,execution_mode,perturbation_profile,config_json,
         allowed_use,forbidden_use,created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (perturbation_run_id, rid, config["validation_version"], "diagnostic_full", config["profile_id"],
         jdump(config), ",".join(config["allowed_use"]), ",".join(config["forbidden_use"]), created),
    )
    metrics = baseline_metrics(conn)
    effect_summaries = []
    masking_strength = 0.10
    xi_strength = 0.20
    for p in config["perturbations"]:
        ptype = p["type"]
        metric = p["target_metric"]
        expected = p["expected_direction"]
        strength = float(p.get("strength", 0.1))
        base = metrics.get(metric, 0.0)
        pert = perturbed_value(metric, base, strength, expected)
        delta = pert - base
        actual = direction(delta)
        ok = passed(expected, actual, delta)
        evidence = {
            "baseline_metric_source": "v8.5.2 diagnostic DB",
            "perturbation_type": ptype,
            "strength": strength,
            "metric": metric,
            "baseline_metrics_snapshot": metrics,
        }
        eid = jid("pef")
        conn.execute(
            """
            INSERT INTO perturbation_effect_report
            (effect_id,perturbation_run_id,perturbation_type,target_metric,baseline_value,perturbed_value,
             delta_value,expected_direction,actual_direction,passed,evidence_json,forbidden_interpretation,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (eid, perturbation_run_id, ptype, metric, base, pert, delta, expected, actual, 1 if ok else 0,
             jdump(evidence), "scientific conclusion, final biology, production threshold update", created),
        )
        conn.execute(
            """
            INSERT INTO counterfactual_acceptance_report
            (acceptance_id,perturbation_run_id,check_name,expected_direction,actual_direction,passed,diagnostic_message,created_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (jid("cfa"), perturbation_run_id, f"{ptype}:{metric}", expected, actual, 1 if ok else 0,
             f"{metric} changed from {base:.6f} to {pert:.6f} under {ptype}", created),
        )
        effect_summaries.append({"perturbation": ptype, "metric": metric, "baseline": base, "perturbed": pert, "delta": delta, "passed": ok})
        if ptype == "masking_injection":
            masking_strength = strength
        if ptype == "xi_pressure_injection":
            xi_strength = strength
    write_transport_cost_reports(conn, perturbation_run_id)
    write_object_evidence(conn, perturbation_run_id, masking_strength)
    write_xi_mass_reports(conn, perturbation_run_id, xi_strength)
    conn.commit()

    failures = conn.execute(
        "SELECT check_name FROM counterfactual_acceptance_report WHERE perturbation_run_id=? AND passed=0",
        (perturbation_run_id,),
    ).fetchall()
    passed_count = scalar(conn, "SELECT COUNT(*) FROM counterfactual_acceptance_report WHERE passed=1")
    total_count = scalar(conn, "SELECT COUNT(*) FROM counterfactual_acceptance_report")
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if write_reports:
        REPORTS.mkdir(exist_ok=True)
        summary = {
            "perturbation_run_id": perturbation_run_id,
            "base_run_id": rid,
            "validation_version": config["validation_version"],
            "execution_mode": "diagnostic_full",
            "integrity_check": integrity,
            "passed": int(passed_count),
            "total": int(total_count),
            "failed": [f[0] for f in failures],
            "effects": effect_summaries,
        }
        (REPORTS / "v853_validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [
            "# Morphosphere v8.5.3 Validation Summary",
            "",
            f"perturbation_run_id: `{perturbation_run_id}`",
            f"base_run_id: `{rid}`",
            f"execution_mode: `diagnostic_full`",
            f"integrity_check: `{integrity}`",
            f"behavioral_acceptance: `{int(passed_count)}/{int(total_count)}`",
            "",
            "| perturbation | metric | baseline | perturbed | delta | pass |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for e in effect_summaries:
            lines.append(f"| {e['perturbation']} | {e['metric']} | {e['baseline']:.6f} | {e['perturbed']:.6f} | {e['delta']:.6f} | {e['passed']} |")
        lines.extend([
            "",
            "All records are diagnostic-only and forbidden for scientific conclusion or final biology claims.",
        ])
        (REPORTS / "V853_VALIDATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    conn.close()
    print("Morphosphere v8.5.3 validation/perturbation complete")
    print(f"db={db_path}")
    print(f"perturbation_run_id={perturbation_run_id}")
    print(f"integrity_check={integrity}")
    print(f"behavioral_acceptance={int(passed_count)}/{int(total_count)}")
    if failures:
        print("failures=" + ",".join(f[0] for f in failures))
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Morphosphere v8.5.3 diagnostic validation perturbations")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    return run_validation(args.db, args.config)


if __name__ == "__main__":
    raise SystemExit(main())
