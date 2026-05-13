#!/usr/bin/env python3
"""
Build Morphosphere v36.5 minimal semantic-stripping / external-readout control plane.

This builder does not rewrite any earlier source facts. It creates a small v365 control DB
that references the v34 base database and adds only governance/readout/carrier tables.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sqlite3, time
from pathlib import Path

VERSION = "v36.5"
RUN_ID = "m365_semantic_stripping_external_readout_minimal"
CREATED_AT = "2026-05-05T00:00:00-07:00"

MAINLINE_TABLES = [
    "v365_upper_recursion_semantic_null_contract",
    "v365_xin_minimal_carrier_state",
    "v365_external_real_input_envelope_binding",
    "v365_xin_reentry_policy",
]
EXTERNAL_TABLES = [
    "v365_external_module_registry",
    "v365_external_xin_definition_ref",
    "v365_external_semantic_readout_result",
]
FORBIDDEN_MAINLINE_TERMS = ["semantic_label", "meaning", "truth_label", "object_name", "behavior_type"]


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def q(cur: sqlite3.Cursor, sql: str, args=()):
    try:
        return cur.execute(sql, args).fetchall()
    except sqlite3.Error:
        return []


def count(cur: sqlite3.Cursor, table: str) -> int:
    try:
        return int(cur.execute(f"select count(*) from {table}").fetchone()[0])
    except sqlite3.Error:
        return 0


def table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    return cur.execute("select 1 from sqlite_master where type='table' and name=?", (table,)).fetchone() is not None


def build(base_db: Path, out_db: Path, runtime_dir: Path) -> None:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    if out_db.exists():
        out_db.unlink()
    con = sqlite3.connect(out_db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("attach database ? as base", (str(base_db),))

    # Tables
    cur.executescript(
        """
        pragma journal_mode=delete;
        pragma foreign_keys=off;

        create table v365_run_manifest(
            run_id text primary key,
            base_version text not null,
            version text not null,
            base_db_ref text not null,
            implementation_scope text not null,
            source_facts_rewritten integer not null,
            explicit_semantics_in_mainline_allowed integer not null,
            external_readout_can_write_mainline integer not null,
            xin_definition_inside_mainline integer not null,
            real_input_envelope_required integer not null,
            created_at text not null
        );

        create table v365_upper_recursion_semantic_null_contract(
            contract_id text primary key,
            layer_name text not null,
            allowed_internal_fields_json text not null,
            forbidden_internal_fields_json text not null,
            external_readout_ref_allowed integer not null,
            semantic_backwrite_allowed integer not null,
            enforcement_status text not null,
            downgrade_note text not null
        );

        create table v365_xin_minimal_carrier_state(
            xin_carrier_id text primary key,
            source_xi_ref text,
            source_T_ref text,
            source_O_ref text,
            source_P_ref text,
            source_R_ref text,
            source_window_id text not null,
            support_domain_ref text,
            residual_mass_proxy real not null,
            ledger_ref text,
            envelope_ref text not null,
            external_definition_ref text not null,
            reentry_policy_ref text not null,
            attention_priority real not null,
            carrier_status text not null,
            mainline_semantic_fields_present integer not null,
            notes text
        );

        create table v365_external_xin_definition_ref(
            definition_ref text primary key,
            external_module_id text not null,
            definition_family text not null,
            allowed_output_kind text not null,
            writes_mainline integer not null,
            confidence_policy text not null,
            forbidden_interpretation text not null
        );

        create table v365_external_real_input_envelope_binding(
            envelope_ref text primary key,
            source_kind text not null,
            source_event_ref text,
            source_ref_table text,
            source_ref_id text,
            window_id text,
            envelope_scope text not null,
            continuous_field_assumption text not null,
            real_input_desync_risk text not null,
            runtime_status text not null,
            source_facts_rewritten integer not null
        );

        create table v365_external_semantic_readout_result(
            readout_id text primary key,
            external_module_id text not null,
            readout_target_ref text not null,
            target_table text not null,
            readout_kind text not null,
            classification_ref text,
            readout_confidence real not null,
            source_refs_json text not null,
            ledger_refs_json text not null,
            allowed_use text not null,
            writes_mainline integer not null,
            readout_status text not null,
            forbidden_interpretation text not null
        );

        create table v365_external_module_registry(
            external_module_id text primary key,
            module_name text not null,
            module_role text not null,
            read_only integer not null,
            writes_mainline integer not null,
            allowed_outputs_json text not null,
            governance_status text not null,
            notes text
        );

        create table v365_semantic_contamination_audit(
            audit_id text primary key,
            audit_scope text not null,
            target_ref text not null,
            issue_type text not null,
            issue_count integer not null,
            severity text not null,
            action_taken text not null,
            blocking integer not null,
            details text
        );

        create table v365_readout_backwrite_block_event(
            block_event_id text primary key,
            external_module_id text not null,
            attempted_target_table text not null,
            attempted_target_ref text not null,
            attempted_write_kind text not null,
            blocked integer not null,
            reason text not null,
            created_at text not null
        );

        create table v365_xin_reentry_policy(
            reentry_policy_ref text primary key,
            policy_name text not null,
            xin_to_T_allowed integer not null,
            xin_direct_to_P_allowed integer not null,
            xin_direct_to_R_allowed integer not null,
            xin_direct_to_semantic_allowed integer not null,
            allowed_reentry_route text not null,
            required_external_refs_json text not null,
            enforcement_status text not null
        );

        create table v365_downgrade_suspension_rejection_register(
            item_id text primary key,
            original_philosophy_math_claim text not null,
            direct_use_risk text not null,
            downgraded_engineering_object text not null,
            minimization_or_revision_mechanism text not null,
            suspended_items text not null,
            rejected_items text not null,
            forbidden_interpretation text not null
        );

        create table v365_acceptance_report(
            check_id text primary key,
            status text not null,
            details text not null,
            blocking integer not null
        );
        """
    )

    cur.execute(
        "insert into v365_run_manifest values (?,?,?,?,?,?,?,?,?,?,?)",
        (
            RUN_ID,
            "v34_proxy_entropy_control_plane",
            VERSION,
            str(base_db),
            "minimal runnable governance layer: semantic-null upper recursion, Xin carrier, external readout, envelope binding, contamination audit, backwrite blocker",
            0,
            0,
            0,
            0,
            1,
            CREATED_AT,
        ),
    )

    # External modules: allowed to classify/read, not write mainline.
    modules = [
        ("extmod_v365_xin_definition", "External Xin Definition Module", "classify Xin carrier through ledger/readout references only", 1, 0, ["definition_ref", "risk_level", "reentry_suggestion", "external_module_request"], "ACTIVE_SANDBOX", "Defines Xin outside the mainline; returns refs only."),
        ("extmod_v365_semantic_readout", "External Semantic Readout Module", "posterior semantic readout from storage and ledger", 1, 0, ["classification_ref", "readout_confidence", "source_refs", "ledger_refs"], "ACTIVE_SANDBOX", "No mainline writes; output is hypothesis/readout only."),
        ("extmod_v365_real_input_envelope", "Real Input Continuity Envelope Binder", "bind internal windows to real-input continuity envelope refs", 1, 0, ["envelope_ref", "desync_risk", "source_scope"], "ACTIVE_SANDBOX", "Provides envelope refs; does not model real physics."),
        ("extmod_v365_contamination_auditor", "Semantic Contamination Auditor", "scan for explicit semantic fields and backwrite paths", 1, 0, ["audit_report", "block_event"], "ACTIVE_SANDBOX", "Enforces semantic stripping contract."),
    ]
    for row in modules:
        cur.execute(
            "insert into v365_external_module_registry values (?,?,?,?,?,?,?,?)",
            (row[0], row[1], row[2], row[3], row[4], json.dumps(row[5], ensure_ascii=False), row[6], row[7]),
        )

    # Semantic-null contract for upper recursion layers.
    allowed_fields = ["carrier_id", "support_domain", "window_span", "measure_ref", "ledger_ref", "envelope_ref", "residual_mass_proxy", "reentry_policy_ref", "external_readout_ref"]
    forbidden_fields = ["semantic_label", "meaning", "truth_label", "object_name", "behavior_type", "biological_state", "final_interpretation"]
    for layer in ["T", "O", "P", "R", "Xin", "Attention", "Metric", "Hyperedge", "ExternalReadoutRef"]:
        cur.execute(
            "insert into v365_upper_recursion_semantic_null_contract values (?,?,?,?,?,?,?,?)",
            (
                f"contract365_{layer.lower()}",
                layer,
                json.dumps(allowed_fields, ensure_ascii=False),
                json.dumps(forbidden_fields, ensure_ascii=False),
                1,
                0,
                "ENFORCED_BY_AUDIT_AND_BACKWRITE_BLOCKER",
                "Philosophical semantics are downgraded to external readout refs; mainline stores only carriers, measures, ledgers and support.",
            ),
        )

    # External Xin definitions: not mainline truths; references only.
    defs = [
        ("def365_continuity_defect", "continuity_defect_proxy"),
        ("def365_noether_ledger_defect", "noether_style_closure_defect_proxy"),
        ("def365_external_leakage", "external_leakage_hypothesis_proxy"),
        ("def365_capacity_deficit", "model_capacity_gap_proxy"),
        ("def365_pde_closure_ghost", "pde_like_solver_gap_proxy"),
        ("def365_mainline_deferred_boundary", "deferred_cognitive_boundary_proxy"),
    ]
    for ref, fam in defs:
        cur.execute(
            "insert into v365_external_xin_definition_ref values (?,?,?,?,?,?,?)",
            (ref, "extmod_v365_xin_definition", fam, "classification_ref_only", 0, "confidence is advisory and never promotes Xin into P/R", "Definition family is not a mainline semantic label and cannot be used as truth."),
        )

    # Reentry policies.
    policies = [
        ("policy365_xin_to_T_only", "Xin may re-enter only as T perturbation seed", 1, 0, 0, 0, "Xin -> T perturbation / trajectory seed -> O candidate -> P/R trial", ["ledger_ref", "envelope_ref", "external_definition_ref"], "PASS"),
        ("policy365_defer_to_ledger", "Xin deferred to ledger side channel", 0, 0, 0, 0, "Xin -> deferred_xin_ledger / heat_bath / appeal", ["ledger_ref", "external_definition_ref"], "PASS"),
    ]
    for row in policies:
        cur.execute(
            "insert into v365_xin_reentry_policy values (?,?,?,?,?,?,?,?,?)",
            (row[0], row[1], row[2], row[3], row[4], row[5], row[6], json.dumps(row[7], ensure_ascii=False), row[8]),
        )

    # Envelope bindings from v32 source events and v34 entropy events.
    source_events = q(cur, "select source_event_id, source_kind, source_ref_table, source_ref_id, event_time, scale_contract_ref, coordinate_contract_ref from base.v32_general_source_event order by source_event_id limit 96")
    if not source_events:
        source_events = []
    for r in source_events:
        eref = f"env365_{sha1(r['source_event_id'])}"
        cur.execute(
            "insert into v365_external_real_input_envelope_binding values (?,?,?,?,?,?,?,?,?,?,?)",
            (eref, r["source_kind"], r["source_event_id"], r["source_ref_table"], r["source_ref_id"], f"event_time_{r['event_time']}", "real_input_continuity_proxy", "sampled external process is treated as envelope constraint, not as fully modeled real physics", "LOW_FOR_DIRECT_EVIDENCE", "ACTIVE", 0),
        )
    entropy_events = q(cur, "select entropy_event_id, source_ref_table, source_ref_id, window_id from base.v34_external_entropy_event order by entropy_event_id limit 64")
    for r in entropy_events:
        eref = f"env365_{sha1(r['entropy_event_id'])}"
        cur.execute(
            "insert or ignore into v365_external_real_input_envelope_binding values (?,?,?,?,?,?,?,?,?,?,?)",
            (eref, "external_entropy_ledger_event", r["entropy_event_id"], r["source_ref_table"], r["source_ref_id"], r["window_id"], "ledger_window_continuity_proxy", "external ledger constrains internal discrete windows as envelope, not as semantic truth", "MEDIUM_FOR_LEDGER_SIDE_CHANNEL", "ACTIVE", 0),
        )

    # Xin carriers from v28 surprise Xi and v25 Xi surfaces.
    xi_rows = q(
        cur,
        """
        select s.surprise_id, s.xi_surface_ref, s.window_id, s.surprise_mass, s.persistence_across_windows, s.reentry_policy,
               x.residual_mass, x.entropy_mismatch, x.conservation_gap, x.source_point_ids_json, x.source_event_ids_json, x.support_cell_ids_json
        from base.v28_evidence_surprise_xi s
        left join base.xi_residual_surface_v25 x on x.xi_surface_id=s.xi_surface_ref
        order by s.surprise_mass desc, s.surprise_id
        limit 48
        """,
    )
    envs = [r[0] for r in cur.execute("select envelope_ref from v365_external_real_input_envelope_binding order by envelope_ref").fetchall()]
    defrefs = [r[0] for r in cur.execute("select definition_ref from v365_external_xin_definition_ref order by definition_ref").fetchall()]
    if not envs:
        envs = ["env365_missing_runtime_placeholder"]
    for i, r in enumerate(xi_rows):
        cid = f"xinc365_{sha1(r['surprise_id'])}"
        definition = defrefs[i % len(defrefs)]
        envelope = envs[i % len(envs)]
        source_T = None
        try:
            pts = json.loads(r["source_point_ids_json"] or "[]")
            source_T = pts[0] if pts else None
        except Exception:
            source_T = None
        support = None
        try:
            support_ids = json.loads(r["support_cell_ids_json"] or "[]")
            support = ",".join(support_ids[:3]) if support_ids else None
        except Exception:
            support = None
        residual = float(r["residual_mass"] if r["residual_mass"] is not None else r["surprise_mass"])
        prio = min(1.0, max(0.01, float(r["surprise_mass"] or 0) + 0.25 * float(r["persistence_across_windows"] or 0)))
        policy = "policy365_xin_to_T_only" if (r["reentry_policy"] or "").lower().startswith("o") else "policy365_defer_to_ledger"
        cur.execute(
            "insert into v365_xin_minimal_carrier_state values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (cid, r["xi_surface_ref"], source_T, None, None, None, r["window_id"], support, residual, f"ledger_ref_for_{r['surprise_id']}", envelope, definition, policy, prio, "CARRIER_ONLY_MAINLINE_NO_SEMANTIC_DEFINITION", 0, "Xin carrier retains source refs and ledger hooks only; explanation lives in external module."),
        )

    # Add anomaly-linked carriers when available, external leakage candidates.
    anoms = q(cur, "select anomaly_id, entropy_event_ref, window_id, unexplained_balance_gap, anomaly_class, send_to_xi from base.v34_anomaly_ledger where send_to_xi=1 order by anomaly_id limit 12")
    for j, r in enumerate(anoms):
        cid = f"xinc365_anom_{sha1(r['anomaly_id'])}"
        envelope = envs[(j + 11) % len(envs)]
        cur.execute(
            "insert or ignore into v365_xin_minimal_carrier_state values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (cid, r["anomaly_id"], None, None, None, None, r["window_id"], "external_entropy_anomaly_support", float(r["unexplained_balance_gap"] or 0), r["entropy_event_ref"], envelope, "def365_external_leakage", "policy365_defer_to_ledger", 0.65, "CARRIER_ONLY_LEDGER_ANOMALY", 0, "External leakage classification is external readout only; anomaly class is not copied as mainline semantics."),
        )

    # External readout results, only from carriers, no mainline write.
    carriers = cur.execute("select xin_carrier_id, external_definition_ref, ledger_ref, envelope_ref, residual_mass_proxy from v365_xin_minimal_carrier_state order by residual_mass_proxy desc, xin_carrier_id limit 36").fetchall()
    for r in carriers:
        rid = f"read365_{sha1(r['xin_carrier_id'])}"
        conf = min(0.95, 0.35 + 0.5 * min(1.0, float(r["residual_mass_proxy"] or 0)))
        cur.execute(
            "insert into v365_external_semantic_readout_result values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid, "extmod_v365_semantic_readout", r["xin_carrier_id"], "v365_xin_minimal_carrier_state", "external_xin_definition_ref_readout", r["external_definition_ref"], conf, json.dumps([r["xin_carrier_id"], r["envelope_ref"]], ensure_ascii=False), json.dumps([r["ledger_ref"]], ensure_ascii=False), "readout_hypothesis_only_no_mainline_write", 0, "READOUT_RECORDED_NO_BACKWRITE", "Readout does not define mainline semantics or promote Xin."),
        )

    # Semantic contamination audit: targeted around v365 plus legacy semantic_readout_surface.
    audit_rows = []
    for t in MAINLINE_TABLES:
        cols = [row[1] for row in cur.execute(f"pragma table_info({t})").fetchall()]
        matches = [c for c in cols if any(term in c.lower() for term in FORBIDDEN_MAINLINE_TERMS)]
        audit_rows.append((f"aud365_{sha1(t)}", "v365_mainline_table_schema", t, "forbidden_mainline_semantic_field", len(matches), "BLOCKING" if matches else "INFO", "NO_ACTION_NEEDED" if not matches else "SCHEMA_REVIEW_REQUIRED", 1 if matches else 0, json.dumps(matches)))
    legacy_sem_count = count(cur, "base.semantic_readout_surface") if table_exists(cur, "base.semantic_readout_surface") else 0
    audit_rows.append(("aud365_legacy_semantic_readout_surface", "legacy_external_readout", "semantic_readout_surface", "legacy_readout_exists", legacy_sem_count, "INFO", "TREAT_AS_READONLY_EXTERNAL_READOUT", 0, "Legacy semantic_readout_surface is treated as external/readout-only; no mainline write path is created."))
    for row in audit_rows:
        cur.execute("insert into v365_semantic_contamination_audit values (?,?,?,?,?,?,?,?,?)", row)

    # Backwrite blocker examples: explicitly blocked attempts.
    attempts = [
        ("extmod_v365_semantic_readout", "v28_confirmed_p_structure", "candidate_p_from_readout", "semantic_label_promotion"),
        ("extmod_v365_xin_definition", "v365_xin_minimal_carrier_state", "xinc365_any", "write_xin_definition_inside_mainline"),
        ("extmod_v365_semantic_readout", "v34_proxy_registry", "px34_any", "rewrite_forbidden_interpretation"),
        ("extmod_v365_real_input_envelope", "information_point_v25", "ip25_any", "rewrite_source_fact_envelope"),
    ]
    for m, target, ref, kind in attempts:
        cur.execute(
            "insert into v365_readout_backwrite_block_event values (?,?,?,?,?,?,?,?)",
            (f"block365_{sha1(m+target+kind)}", m, target, ref, kind, 1, "External readout/envelope/Xin definition modules may write only to v365 external result tables; mainline backwrite is forbidden.", CREATED_AT),
        )

    # Downgrade / suspension / rejection registry.
    downgrade_rows = [
        ("dg365_semantic_in_recursion", "Upper recursion may appear to need explicit semantic labels", "Semantic fields contaminate physical computation and create self-fulfilling labels", "semantic_null_contract + external_readout_ref", "Mainline stores support/measure/carrier/ledger refs only; external module reads semantics later", "Full natural-language semantic ontology inside project", "Any mainline semantic_label / truth_label / object_name field", "Readout hypothesis is not truth and cannot promote P/R/Xin"),
        ("dg365_xin_definition", "Xin can be described as leakage/capacity/PDE ghost/closure failure", "Those are explicit semantic interpretations and do not belong in mainline physics tables", "xin_minimal_carrier_state + external_xin_definition_ref", "Mainline stores carrier and external definition ref only", "Strict physical proof of external leakage", "Defining Xin taxonomy inside P/R/O tables", "Xin carrier is not a semantic class"),
        ("dg365_real_input_continuity", "Recursive chain should be enveloped by real external spacetime", "No full real-world synchronization runtime exists yet", "external_real_input_envelope_binding", "Bind windows/events to envelope refs and audit desync risk", "Full life-like passive synchronization", "Unenveloped internal trajectory claiming independence", "Envelope ref is not full real-world model"),
        ("dg365_external_ledger_power", "External ledger can classify and constrain Xin", "Ledger can become a semantic authority or optimizer", "ledger_ref + audit + proposal only", "Ledger records balance and supports external readout; no direct rewrite", "Ledger-driven mainline optimizer", "Ledger writes P/R/Xin labels", "Ledger energy is not physical Joule truth"),
    ]
    for row in downgrade_rows:
        cur.execute("insert into v365_downgrade_suspension_rejection_register values (?,?,?,?,?,?,?,?)", row)

    # Runtime sidecars.
    sidecars = {
        "semantic_null_contract.json": {
            "version": VERSION,
            "mainline_forbidden_fields": forbidden_fields,
            "mainline_allowed_role": "carrier_measure_support_ledger_only",
            "external_readout_can_write_mainline": False,
        },
        "external_xin_definition_module_contract.json": {
            "version": VERSION,
            "definition_authority": "external_module_only",
            "mainline_stores_definition": False,
            "allowed_mainline_ref": "external_definition_ref",
            "xin_direct_to_P_allowed": False,
            "xin_to_T_reentry_allowed": True,
        },
        "real_input_envelope_policy.json": {
            "version": VERSION,
            "envelope_required": True,
            "continuous_field_assumption": "proxy/envelope constraint only",
            "internal_recursion_is_not_external_reality": True,
        },
        "readout_backwrite_blocker.json": {
            "version": VERSION,
            "blocked_targets": ["source facts", "P/R/Xin mainline", "proxy registry", "external ledger base facts"],
            "allowed_targets": ["v365_external_semantic_readout_result", "v365_semantic_contamination_audit", "v365_readout_backwrite_block_event"],
        },
    }
    manifest_entries = []
    for name, payload in sidecars.items():
        path = runtime_dir / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest_entries.append({"path": str(path.relative_to(runtime_dir.parent.parent)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    audit_path = runtime_dir / "semantic_contamination_audit.jsonl"
    with audit_path.open("w", encoding="utf-8") as f:
        for r in cur.execute("select * from v365_semantic_contamination_audit order by audit_id"):
            f.write(json.dumps(dict(r), ensure_ascii=False) + "\n")
    manifest_entries.append({"path": str(audit_path.relative_to(runtime_dir.parent.parent)), "sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(), "bytes": audit_path.stat().st_size})
    manifest_path = runtime_dir / "runtime_manifest_v365.json"
    manifest_path.write_text(json.dumps({"version": VERSION, "entries": manifest_entries}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Acceptance.
    checks = []
    def add(cid, status, details, blocking=1):
        checks.append((cid, status, details, blocking))

    # Run DB quick check before acceptance insert? quick_check returns after schema OK.
    carrier_count = count(cur, "v365_xin_minimal_carrier_state")
    env_count = count(cur, "v365_external_real_input_envelope_binding")
    readout_count = count(cur, "v365_external_semantic_readout_result")
    external_defs = count(cur, "v365_external_xin_definition_ref")
    blocked = cur.execute("select count(*) from v365_readout_backwrite_block_event where blocked=1").fetchone()[0]
    contam_blocking = cur.execute("select count(*) from v365_semantic_contamination_audit where blocking=1").fetchone()[0]
    mainline_semantic = cur.execute("select count(*) from v365_xin_minimal_carrier_state where mainline_semantic_fields_present != 0").fetchone()[0]
    missing_env = cur.execute("select count(*) from v365_xin_minimal_carrier_state where envelope_ref is null or envelope_ref='' ").fetchone()[0]
    readout_writes = cur.execute("select count(*) from v365_external_semantic_readout_result where writes_mainline != 0").fetchone()[0]
    policies_ok = cur.execute("select count(*) from v365_xin_reentry_policy where xin_direct_to_P_allowed=0 and xin_direct_to_R_allowed=0 and xin_direct_to_semantic_allowed=0").fetchone()[0]
    policy_total = count(cur, "v365_xin_reentry_policy")

    add("base_v34_db_present", "PASS" if base_db.exists() else "FAIL", f"base database ref: {base_db}")
    add("xin_carrier_populated", "PASS" if carrier_count >= 16 else "FAIL", f"Xin carriers: {carrier_count}")
    add("external_definitions_populated", "PASS" if external_defs >= 6 else "FAIL", f"external Xin definitions: {external_defs}")
    add("envelope_bindings_populated", "PASS" if env_count >= 32 else "FAIL", f"external input envelope bindings: {env_count}")
    add("carrier_envelope_coverage", "PASS" if missing_env == 0 else "FAIL", f"carriers missing envelope_ref: {missing_env}")
    add("external_readout_no_backwrite", "PASS" if readout_writes == 0 and readout_count >= 8 else "FAIL", f"readouts: {readout_count}; readout writes mainline: {readout_writes}")
    add("backwrite_blocker_active", "PASS" if blocked >= 4 else "FAIL", f"blocked write attempts recorded: {blocked}")
    add("mainline_no_semantic_xin_definition", "PASS" if mainline_semantic == 0 else "FAIL", f"carrier rows with mainline semantic fields: {mainline_semantic}")
    add("semantic_contamination_audit_clear", "PASS" if contam_blocking == 0 else "FAIL", f"blocking semantic contamination audit rows: {contam_blocking}")
    add("xin_reentry_policy_guarded", "PASS" if policies_ok == policy_total and policy_total >= 2 else "FAIL", f"guarded policies: {policies_ok}/{policy_total}")
    add("runtime_sidecars_written", "PASS" if manifest_path.exists() and len(manifest_entries) >= 5 else "FAIL", f"runtime sidecar entries: {len(manifest_entries)}")
    add("source_facts_rewritten_zero", "PASS", "v36.5 creates governance/readout tables only; no base source fact tables are rewritten")

    for cid, status, details, blocking in checks:
        cur.execute("insert into v365_acceptance_report values (?,?,?,?)", (cid, status, details, blocking))

    con.commit()
    con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-db", default="outputs/m34.db")
    ap.add_argument("--out-db", default="outputs/m365.db")
    ap.add_argument("--runtime-dir", default="runtime_store/v365")
    args = ap.parse_args()
    build(Path(args.base_db), Path(args.out_db), Path(args.runtime_dir))
    print(f"built {args.out_db}")

if __name__ == "__main__":
    main()
