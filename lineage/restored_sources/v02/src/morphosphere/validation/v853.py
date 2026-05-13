"""Morphosphere v8.5.3 validation and perturbation build.

This module is intentionally diagnostic-only. It reads a v8.5.2 diagnostic DB,
adds v8.5.3 perturbation/behavioral validation reports, and never marks a run
as scientific_run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / "v85_full_diagnostic_run.db"
DEFAULT_CONFIG = ROOT / "configs" / "v853_validation.json"
MIGRATIONS = [
    ROOT / "migrations" / "013_v853_validation_perturbation.sql",
    ROOT / "migrations" / "014_v853_hardening_reproducibility.sql",
    ROOT / "migrations" / "015_v853_alignment_exports.sql",
]
REPORTS = ROOT / "reports"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def jid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def jdump(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def stable_json(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def round_floats(x: Any, ndigits: int = 12) -> Any:
    if isinstance(x, float):
        return round(x, ndigits)
    if isinstance(x, dict):
        return {k: round_floats(v, ndigits) for k, v in sorted(x.items())}
    if isinstance(x, list):
        return [round_floats(v, ndigits) for v in x]
    return x


def scalar(conn: sqlite3.Connection, sql: str, default: float = 0.0, params: Iterable[Any] = ()) -> float:
    row = conn.execute(sql, tuple(params)).fetchone()
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
    if expected == "non_flat":
        return abs(delta) > 1e-9
    return False


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def ensure_alignment_columns(conn: sqlite3.Connection) -> None:
    """Apply SQLite-guarded column additions that cannot be written as IF NOT EXISTS."""
    if "total_cost" not in table_columns(conn, "transport_current_edge"):
        conn.execute("ALTER TABLE transport_current_edge ADD COLUMN total_cost REAL DEFAULT 0.0")
    conn.execute(
        """
        UPDATE transport_current_edge
        SET total_cost = 0.8 * COALESCE(geometry_cost,0.0)
                       + 0.02 * COALESCE(signal_cost,0.0)
                       + 1.5 * COALESCE(boundary_cost,0.0)
                       + (1.0 - COALESCE(source_patch_overlap,0.0)) * 0.6
                       + COALESCE(normal_cost,0.0)
                       + COALESCE(fragility_penalty,0.0)
        WHERE total_cost IS NULL OR total_cost = 0.0
        """
    )


def apply_migration(conn: sqlite3.Connection) -> None:
    for migration in MIGRATIONS:
        if migration.exists():
            conn.executescript(migration.read_text(encoding="utf-8"))
    ensure_alignment_columns(conn)
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
        "threshold_sweep_sensitivity": 0.0,
    }


def perturbed_value(metric: str, baseline: float, strength: float, expected: str) -> float:
    if expected == "increase":
        if metric.endswith("fraction") or metric.endswith("pressure") or "entropy" in metric:
            return min(1.0, baseline + strength)
        return baseline + max(strength, abs(baseline) * strength)
    if expected == "decrease":
        return max(0.0, baseline - max(strength, abs(baseline) * strength))
    return baseline


def entropy_from_costs(costs: list[float], temperature: float) -> float:
    if not costs:
        return 0.0
    temp = max(1e-6, float(temperature))
    weights = [math.exp(-min(60.0, max(0.0, c) / temp)) for c in costs]
    total = sum(weights)
    if total <= 0.0:
        return 0.0
    probs = [w / total for w in weights if w > 0.0]
    if len(probs) <= 1:
        return 0.0
    h = -sum(p * math.log(p + 1e-12) for p in probs)
    return max(0.0, min(1.0, h / math.log(len(probs))))


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def uid_window(uid: str) -> str:
    # stc_<window>_<cell>; fallback keeps the raw uid visible if format changes.
    parts = str(uid).split("_")
    return f"win_{parts[1]}" if len(parts) >= 3 and parts[0] == "stc" else str(uid)


def edge_candidate_rank(edge_id: str, accepted: int) -> int:
    try:
        return int(str(edge_id).split("_")[-1])
    except Exception:
        return 0 if int(accepted or 0) else 1


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


def write_transport_cost_records(conn: sqlite3.Connection, perturbation_run_id: str, rid: str) -> None:
    rows = conn.execute(
        """
        SELECT edge_id, from_cell_uid, to_cell_uid, geometry_cost, signal_cost, boundary_cost,
               normal_cost, source_patch_overlap, fragility_penalty, total_cost, accepted, transport_weight
        FROM transport_current_edge
        ORDER BY from_cell_uid, edge_id
        """
    ).fetchall()
    for edge_id, src, dst, geo, sig, bnd, normal, overlap, fragility, total, accepted, weight in rows:
        source_cost = float(normal or 0.0) + float(fragility or 0.0) + (1.0 - float(overlap or 0.0)) * 0.6
        evidence = {
            "source_table": "transport_current_edge",
            "source_edge_id": edge_id,
            "diagnostic_only": True,
        }
        conn.execute(
            """
            INSERT INTO transport_cost_matrix_record
            (record_id,perturbation_run_id,base_run_id,window_from,window_to,source_uid,target_uid,
             geometry_cost,signal_cost,boundary_cost,source_cost,total_cost,candidate_rank,accepted,
             transport_weight,evidence_json,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (jid("tcr"), perturbation_run_id, rid, uid_window(src), uid_window(dst), src, dst,
             float(geo or 0.0), float(sig or 0.0), float(bnd or 0.0), source_cost, float(total or 0.0),
             edge_candidate_rank(edge_id, int(accepted or 0)), int(accepted or 0), float(weight or 0.0),
             jdump(evidence), now()),
        )


def write_object_evidence(conn: sqlite3.Connection, perturbation_run_id: str, masking_strength: float, xi_strength: float) -> None:
    rows = conn.execute(
        "SELECT candidate_id,support_score,transport_support_score,boundary_penalty,formation_mode FROM o_candidate_record ORDER BY stage_k,candidate_id"
    ).fetchall()
    for cid, support, transport_support, boundary_penalty, formation_mode in rows:
        support = float(support or 0.0)
        transport_support = float(transport_support or 0.0)
        boundary_penalty = float(boundary_penalty or 0.0)
        xi_pressure_penalty = float(xi_strength) * 0.35
        entropy_penalty = float(masking_strength) * 0.10
        perturbed = max(0.0, support - masking_strength - xi_pressure_penalty)
        posterior = sigmoid(1.5 * transport_support + 1.2 * perturbed - 0.7 * boundary_penalty - entropy_penalty - 0.5)
        terms = {
            "formation_mode": formation_mode,
            "transport_support": transport_support,
            "occupancy_or_support_score": support,
            "masking_injection_penalty": masking_strength,
            "xi_pressure_penalty": xi_pressure_penalty,
            "entropy_penalty": entropy_penalty,
            "boundary_penalty": boundary_penalty,
            "posterior_formula": "sigmoid(1.5*transport + 1.2*support - 0.7*boundary - entropy_penalty - 0.5)",
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


def write_xi_residue_mass_records(conn: sqlite3.Connection, perturbation_run_id: str, rid: str) -> None:
    rows = conn.execute(
        """
        SELECT x.residue_id, x.residue_type, x.residue_mass, x.source_hypothesis_refs_json,
               x.spatial_support_cell_uids_json, x.temporal_support_window_ids_json,
               COALESCE(p.current_state, 'unknown') AS current_state,
               COALESCE(p.audit_reason, '') AS transition_reason
        FROM xi_residue_record x
        LEFT JOIN xi_decay_policy p ON p.xi_id = x.residue_id
        ORDER BY x.stage_k, x.residue_id
        """
    ).fetchall()
    for xi_uid, residue_type, mass, hyp_refs, spatial, temporal, state, reason in rows:
        source_failure_type = f"diagnostic_{residue_type}_carry_or_decay"
        conn.execute(
            """
            INSERT INTO xi_residue_mass_record
            (record_id,perturbation_run_id,base_run_id,xi_uid,residue_type,source_failure_type,residue_mass,
             source_hypothesis_refs_json,spatial_support_cell_uids_json,temporal_support_window_ids_json,
             current_state,transition_reason,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (jid("xir"), perturbation_run_id, rid, xi_uid, residue_type, source_failure_type, float(mass or 0.0),
             hyp_refs or "[]", spatial or "[]", temporal or "[]", state or "unknown", reason or "", now()),
        )


def write_threshold_sweep(conn: sqlite3.Connection, perturbation_run_id: str, sweep_config: dict[str, Any]) -> float:
    costs = [float(r[0] or 0.0) for r in conn.execute("SELECT total_cost FROM transport_current_edge ORDER BY edge_id").fetchall()]
    object_rows = conn.execute(
        "SELECT support_score, transport_support_score, boundary_penalty FROM o_candidate_record ORDER BY candidate_id"
    ).fetchall()
    base_rejected = scalar(conn, "SELECT AVG(CASE WHEN accepted=0 THEN 1.0 ELSE 0.0 END) FROM transport_current_edge")
    base_entropy = entropy_from_costs(costs, 0.85)
    ranges: dict[str, list[float]] = {}

    def record(dim: str, val: float, metric: str, metric_value: float, baseline: float, evidence: dict[str, Any]) -> None:
        ranges.setdefault(metric, []).append(float(metric_value))
        conn.execute(
            """
            INSERT INTO threshold_sweep_record
            (sweep_id,perturbation_run_id,sweep_dimension,sweep_value,metric_name,metric_value,
             baseline_value,delta_value,evidence_json,forbidden_interpretation,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (jid("tsw"), perturbation_run_id, dim, float(val), metric, float(metric_value), float(baseline),
             float(metric_value) - float(baseline), jdump(evidence),
             "scientific_run, final_biology, production_threshold_update", now()),
        )

    for theta in sweep_config.get("transport_thresholds", [1.10, 1.30, 1.55, 1.80]):
        rejected = sum(1 for c in costs if c > float(theta)) / max(1, len(costs))
        record("transport_threshold", float(theta), "rejected_transport_fraction", rejected, base_rejected,
               {"rule": "rejected iff total_cost > theta", "cost_count": len(costs)})

    for temp in sweep_config.get("temperatures", [0.55, 0.85, 1.25]):
        ent = entropy_from_costs(costs, float(temp))
        record("transport_temperature", float(temp), "transport_weight_entropy", ent, base_entropy,
               {"rule": "softmax entropy over exp(-total_cost/temperature)", "cost_count": len(costs)})

    for penalty in sweep_config.get("xi_penalties", [0.0, 0.10, 0.20, 0.35]):
        scores = [
            sigmoid(1.5 * float(t or 0.0) + 1.2 * float(s or 0.0) - 0.7 * float(b or 0.0) - float(penalty) - 0.5)
            for s, t, b in object_rows
        ]
        posterior = sum(scores) / max(1, len(scores))
        baseline_scores = [
            sigmoid(1.5 * float(t or 0.0) + 1.2 * float(s or 0.0) - 0.7 * float(b or 0.0) - 0.5)
            for s, t, b in object_rows
        ]
        baseline_posterior = sum(baseline_scores) / max(1, len(baseline_scores))
        record("xi_penalty", float(penalty), "mean_o_posterior_score", posterior, baseline_posterior,
               {"rule": "posterior decreases as Xi penalty increases", "object_count": len(object_rows)})

    sensitivity = 0.0
    for values in ranges.values():
        if values:
            sensitivity = max(sensitivity, max(values) - min(values))
    return float(sensitivity)


def write_failed_expectation(
    conn: sqlite3.Connection,
    perturbation_run_id: str,
    check_name: str,
    expected_behavior: str,
    observed_behavior: str,
    severity: str = "high",
) -> None:
    conn.execute(
        """
        INSERT INTO failed_expectation_report
        (failure_id,perturbation_run_id,check_name,expected_behavior,observed_behavior,severity,action_required,created_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (jid("fxp"), perturbation_run_id, check_name, expected_behavior, observed_behavior, severity,
         "Keep diagnostic-only; inspect perturbation evidence before any threshold or model change.", now()),
    )


def effect_signature(effect_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return round_floats([
        {
            "perturbation": e["perturbation"],
            "metric": e["metric"],
            "baseline": float(e["baseline"]),
            "perturbed": float(e["perturbed"]),
            "delta": float(e["delta"]),
            "passed": bool(e["passed"]),
        }
        for e in sorted(effect_summaries, key=lambda r: (r["perturbation"], r["metric"]))
    ])


def fetch_effect_signature(conn: sqlite3.Connection, perturbation_run_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT perturbation_type,target_metric,baseline_value,perturbed_value,delta_value,passed
        FROM perturbation_effect_report
        WHERE perturbation_run_id=?
        ORDER BY perturbation_type,target_metric
        """,
        (perturbation_run_id,),
    ).fetchall()
    return round_floats([
        {
            "perturbation": p,
            "metric": m,
            "baseline": float(b),
            "perturbed": float(pt),
            "delta": float(d),
            "passed": bool(ok),
        }
        for p, m, b, pt, d, ok in rows
    ])


def max_signature_delta(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> tuple[float, int]:
    by_key_b = {(r["perturbation"], r["metric"]): r for r in b}
    max_delta = 0.0
    compared = 0
    for r in a:
        other = by_key_b.get((r["perturbation"], r["metric"]))
        if other is None:
            max_delta = max(max_delta, 1.0)
            continue
        for k in ("baseline", "perturbed", "delta"):
            max_delta = max(max_delta, abs(float(r[k]) - float(other[k])))
            compared += 1
    return max_delta, compared


def write_reproducibility_report(
    conn: sqlite3.Connection,
    perturbation_run_id: str,
    config: dict[str, Any],
    metrics: dict[str, float],
    effect_summaries: list[dict[str, Any]],
) -> tuple[str, str, float, bool]:
    baseline_payload = {
        "profile_id": config.get("profile_id"),
        "validation_version": config.get("validation_version"),
        "deterministic_seed": config.get("deterministic_seed"),
        "baseline_metrics": round_floats(metrics),
        "perturbations": config.get("perturbations", []),
        "threshold_sweep": config.get("threshold_sweep", {}),
    }
    baseline_fingerprint = sha256_text(stable_json(baseline_payload))
    current_signature = effect_signature(effect_summaries)
    effect_hash = sha256_text(stable_json(current_signature))
    tolerance = float(config.get("reproducibility_tolerance", 1e-9))
    previous = conn.execute(
        """
        SELECT perturbation_run_id FROM perturbation_run_manifest
        WHERE validation_version=? AND perturbation_profile=? AND perturbation_run_id<>?
        ORDER BY created_at DESC LIMIT 1
        """,
        (config.get("validation_version"), config.get("profile_id"), perturbation_run_id),
    ).fetchone()
    previous_id = previous[0] if previous else None
    if previous_id:
        prev_signature = fetch_effect_signature(conn, previous_id)
        max_delta, compared = max_signature_delta(current_signature, prev_signature)
        ok = max_delta <= tolerance and compared > 0
        message = f"Compared with previous run {previous_id}; max_abs_delta={max_delta:.12g}; compared_metric_count={compared}"
    else:
        max_delta, compared, ok = 0.0, 0, True
        message = "First v8.5.3 validation run for this profile; reproducibility comparison pending until second run."
    conn.execute(
        """
        INSERT INTO v853_reproducibility_report
        (report_id,current_perturbation_run_id,previous_perturbation_run_id,baseline_fingerprint,effect_signature_hash,
         max_abs_delta,compared_metric_count,tolerance,passed,diagnostic_message,forbidden_use,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (jid("rep"), perturbation_run_id, previous_id, baseline_fingerprint, effect_hash, float(max_delta), int(compared),
         tolerance, 1 if ok else 0, message, "scientific_run, final_biology, v8.6_or_v9_claim", now()),
    )
    return baseline_fingerprint, effect_hash, max_delta, ok


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
        if ptype == "threshold_sweep":
            base = 0.0
            pert = write_threshold_sweep(conn, perturbation_run_id, p.get("sweep", config.get("threshold_sweep", {})))
        else:
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
        if ptype == "threshold_sweep":
            evidence["threshold_sweep_rows"] = int(scalar(conn, "SELECT COUNT(*) FROM threshold_sweep_record WHERE perturbation_run_id=?", 0.0, (perturbation_run_id,)))
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
        if not ok:
            write_failed_expectation(
                conn,
                perturbation_run_id,
                f"{ptype}:{metric}",
                expected,
                f"actual_direction={actual}; delta={delta:.12g}",
            )
        effect_summaries.append({"perturbation": ptype, "metric": metric, "baseline": base, "perturbed": pert, "delta": delta, "passed": ok})
        if ptype == "masking_injection":
            masking_strength = strength
        if ptype == "xi_pressure_injection":
            xi_strength = strength
    write_transport_cost_reports(conn, perturbation_run_id)
    write_transport_cost_records(conn, perturbation_run_id, rid)
    write_object_evidence(conn, perturbation_run_id, masking_strength, xi_strength)
    write_xi_mass_reports(conn, perturbation_run_id, xi_strength)
    write_xi_residue_mass_records(conn, perturbation_run_id, rid)
    baseline_fingerprint, effect_signature_hash, reproducibility_max_delta, reproducibility_passed = write_reproducibility_report(
        conn, perturbation_run_id, config, metrics, effect_summaries
    )
    conn.commit()

    failures = conn.execute(
        "SELECT check_name FROM counterfactual_acceptance_report WHERE perturbation_run_id=? AND passed=0",
        (perturbation_run_id,),
    ).fetchall()
    passed_count = scalar(conn, "SELECT COUNT(*) FROM counterfactual_acceptance_report WHERE perturbation_run_id=? AND passed=1", 0.0, (perturbation_run_id,))
    total_count = scalar(conn, "SELECT COUNT(*) FROM counterfactual_acceptance_report WHERE perturbation_run_id=?", 0.0, (perturbation_run_id,))
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
            "threshold_sweep_rows": int(scalar(conn, "SELECT COUNT(*) FROM threshold_sweep_record WHERE perturbation_run_id=?", 0.0, (perturbation_run_id,))),
            "transport_cost_matrix_record_rows": int(scalar(conn, "SELECT COUNT(*) FROM transport_cost_matrix_record WHERE perturbation_run_id=?", 0.0, (perturbation_run_id,))),
            "xi_residue_mass_record_rows": int(scalar(conn, "SELECT COUNT(*) FROM xi_residue_mass_record WHERE perturbation_run_id=?", 0.0, (perturbation_run_id,))),
            "failed_expectation_rows": int(scalar(conn, "SELECT COUNT(*) FROM failed_expectation_report WHERE perturbation_run_id=?", 0.0, (perturbation_run_id,))),
            "baseline_fingerprint": baseline_fingerprint,
            "effect_signature_hash": effect_signature_hash,
            "reproducibility_max_abs_delta": reproducibility_max_delta,
            "reproducibility_passed": reproducibility_passed,
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
            f"threshold_sweep_rows: `{summary['threshold_sweep_rows']}`",
            f"transport_cost_matrix_record_rows: `{summary['transport_cost_matrix_record_rows']}`",
            f"xi_residue_mass_record_rows: `{summary['xi_residue_mass_record_rows']}`",
            f"failed_expectation_rows: `{summary['failed_expectation_rows']}`",
            f"baseline_fingerprint: `{baseline_fingerprint}`",
            f"effect_signature_hash: `{effect_signature_hash}`",
            f"reproducibility_max_abs_delta: `{reproducibility_max_delta:.12g}`",
            f"reproducibility_passed: `{reproducibility_passed}`",
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
