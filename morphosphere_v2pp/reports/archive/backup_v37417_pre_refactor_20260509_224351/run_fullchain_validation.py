#!/usr/bin/env python3
"""Morphosphere v37.4.15 — Full-Chain End-to-End Validation & Analysis.

Runs all critical pipelines, validates cross-batch consistency,
and produces a comprehensive analysis report.
"""
from __future__ import annotations
import sqlite3, sys, time, json, os, traceback
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
REPORT_DIR = ROOT / "v37.4.15_fullchain_reports"
REPORT_DIR.mkdir(exist_ok=True)

def now(): return datetime.now(timezone.utc).isoformat()

# ═══════════════════════════════════════════════════════════════════
# Phase 0: Discover & validate project structure
# ═══════════════════════════════════════════════════════════════════
def phase0_structure_audit():
    """Audit project structure: modules, migrations, runners."""
    print("=" * 80)
    print("PHASE 0: PROJECT STRUCTURE AUDIT")
    print("=" * 80)

    results = {}

    # Migrations
    mig_dir = ROOT / "migrations"
    migrations = sorted(mig_dir.glob("*.sql")) if mig_dir.exists() else []
    results["migrations"] = [m.name for m in migrations]
    print(f"  Migrations: {len(migrations)}")
    for m in migrations:
        print(f"    {m.name} ({m.stat().st_size} bytes)")

    # Source modules
    src_modules = {}
    src_root = ROOT / "src" / "morphosphere"
    if src_root.exists():
        for py in sorted(src_root.rglob("*.py")):
            rel = py.relative_to(ROOT / "src")
            src_modules[str(rel)] = py.stat().st_size
    results["source_modules"] = len(src_modules)
    print(f"  Source modules: {len(src_modules)}")

    # Runners
    runners = sorted(ROOT.glob("run_*.py"))
    results["runners"] = [r.name for r in runners]
    print(f"  Runners: {len(runners)}")
    for r in runners:
        print(f"    {r.name} ({r.stat().st_size} bytes)")

    # Existing DBs
    dbs = sorted(ROOT.glob("*.db"))
    results["databases"] = {d.name: d.stat().st_size for d in dbs}
    print(f"  Existing databases: {len(dbs)}")
    for d in dbs:
        print(f"    {d.name} ({d.stat().st_size / 1024:.0f} KB)")

    # Pipeline engine
    pe = ROOT / "pipeline_engine.py"
    results["pipeline_engine_size"] = pe.stat().st_size if pe.exists() else 0
    results["pipeline_engine_lines"] = sum(1 for _ in open(pe, encoding="utf-8")) if pe.exists() else 0
    print(f"  pipeline_engine.py: {results['pipeline_engine_lines']} lines, {results['pipeline_engine_size']} bytes")

    return results


# ═══════════════════════════════════════════════════════════════════
# Phase 1: Run each critical batch pipeline
# ═══════════════════════════════════════════════════════════════════
CRITICAL_RUNNERS = [
    ("run_v37412_20260508_batch4.py", "v37412_20260508_batch4.db"),
    ("run_v37412_20260509_batch5.py", "v37412_20260509_batch5.db"),
    ("run_v37415_20260509_batch6.py", "v37415_20260509_batch6.db"),
]

def phase1_run_pipelines():
    """Run all critical batch pipelines and capture results."""
    print("\n" + "=" * 80)
    print("PHASE 1: FULL-CHAIN PIPELINE EXECUTION")
    print("=" * 80)

    results = {}
    for runner_name, db_name in CRITICAL_RUNNERS:
        runner_path = ROOT / runner_name
        db_path = ROOT / db_name
        print(f"\n{'─' * 60}")
        print(f"  Running: {runner_name}")
        print(f"{'─' * 60}")

        # Delete existing DB for clean run
        if db_path.exists():
            db_path.unlink()

        t0 = time.time()
        try:
            # Run in subprocess to isolate
            import subprocess
            proc = subprocess.run(
                [sys.executable, str(runner_path)],
                capture_output=True, text=True, timeout=120,
                cwd=str(ROOT),
                encoding='utf-8', errors='replace',
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
            elapsed = time.time() - t0
            success = proc.returncode == 0

            # Extract key metrics from output
            output = (proc.stdout or '') + (proc.stderr or '')
            last_lines = output.strip().split("\n")[-30:]

            results[runner_name] = {
                "success": success,
                "returncode": proc.returncode,
                "elapsed": round(elapsed, 2),
                "db_size_kb": round(db_path.stat().st_size / 1024, 1) if db_path.exists() else 0,
                "last_lines": last_lines,
            }

            # Check acceptance gate
            gate_pass = any("ALL PASS" in l for l in last_lines)
            results[runner_name]["acceptance_pass"] = gate_pass

            status = "✅ PASS" if (success and gate_pass) else "❌ FAIL"
            print(f"  {status} — elapsed={elapsed:.2f}s, db={results[runner_name]['db_size_kb']}KB")
            if not success:
                print(f"  STDERR: {proc.stderr[-500:]}")

        except subprocess.TimeoutExpired:
            results[runner_name] = {"success": False, "error": "TIMEOUT (120s)"}
            print(f"  ❌ TIMEOUT")
        except Exception as e:
            results[runner_name] = {"success": False, "error": str(e)}
            print(f"  ❌ ERROR: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════
# Phase 2: Cross-batch database deep analysis
# ═══════════════════════════════════════════════════════════════════
def phase2_db_analysis():
    """Deep analysis of all batch databases."""
    print("\n" + "=" * 80)
    print("PHASE 2: CROSS-BATCH DATABASE ANALYSIS")
    print("=" * 80)

    results = {}
    for _, db_name in CRITICAL_RUNNERS:
        db_path = ROOT / db_name
        if not db_path.exists():
            results[db_name] = {"error": "DB not found"}
            continue

        conn = sqlite3.connect(str(db_path))
        batch = db_name.replace(".db", "")

        # Integrity
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]

        # All tables
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        table_counts = {}
        for t in tables:
            try:
                table_counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except:
                table_counts[t] = -1

        populated = {t: c for t, c in table_counts.items() if c > 0}
        empty = [t for t, c in table_counts.items() if c == 0]
        total_rows = sum(c for c in table_counts.values() if c > 0)

        # Core metrics
        run_id = conn.execute("SELECT run_id FROM run_manifest LIMIT 1").fetchone()
        run_id = run_id[0] if run_id else "unknown"

        # PR confirmation graph
        pr_dist = {}
        try:
            for r in conn.execute("SELECT current_node, COUNT(*) FROM pr_confirmation_graph_record GROUP BY current_node"):
                pr_dist[r[0]] = r[1]
        except: pass

        # Hebbian
        heb = {"count": 0, "avg": 0, "max": 0}
        try:
            h = conn.execute("SELECT COUNT(*), AVG(weight_value), MAX(weight_value) FROM fhpms_hebbian_association_weight").fetchone()
            heb = {"count": h[0], "avg": round(h[1] or 0, 4), "max": round(h[2] or 0, 4)}
        except: pass

        # Transport
        transport = {"total": 0, "accepted": 0, "cross_domain": 0}
        try:
            transport["total"] = conn.execute("SELECT COUNT(*) FROM transport_current_edge").fetchone()[0]
            transport["accepted"] = conn.execute("SELECT COUNT(*) FROM transport_current_edge WHERE accepted=1").fetchone()[0]
        except: pass
        try:
            transport["cross_domain"] = conn.execute("SELECT COUNT(*) FROM transport_current_edge WHERE transport_variant='cross_domain_normalized'").fetchone()[0]
        except: pass

        # Xi residues
        xi = {"total": 0, "types": {}}
        try:
            xi["total"] = conn.execute("SELECT COUNT(*) FROM xi_residue_record").fetchone()[0]
            for r in conn.execute("SELECT residue_type, COUNT(*) FROM xi_residue_record GROUP BY residue_type"):
                xi["types"][r[0]] = r[1]
        except: pass

        # Maturity gates
        gates = {}
        try:
            for r in conn.execute("SELECT gate_result, COUNT(*) FROM maturity_gate_record GROUP BY gate_result"):
                gates[r[0]] = r[1]
        except: pass

        # RLIS
        rlis = {}
        try:
            rlis["events"] = conn.execute("SELECT COUNT(*) FROM rlis_ledger_event_spacetime").fetchone()[0]
            rlis["gamma_avg"] = round(conn.execute("SELECT AVG(gamma_strength) FROM rlis_gamma_sync_binding").fetchone()[0] or 0, 4)
            rlis["delta_f_splits"] = conn.execute("SELECT COUNT(*) FROM rlis_delta_f_split").fetchone()[0]
        except: pass

        # v37415 specific (only in batch6)
        v37415 = {}
        try:
            for t in tables:
                if t.startswith("v37415_"):
                    v37415[t] = table_counts.get(t, 0)
            # Convergence
            conv = conn.execute("SELECT verdict, final_drift, true_xin_count, r_core_count, p_band_count, unresolved_count FROM v37415_round_convergence_audit LIMIT 1").fetchone()
            if conv:
                v37415["convergence"] = {
                    "verdict": conv[0], "final_drift": conv[1],
                    "true_xin": conv[2], "r_core": conv[3],
                    "p_band": conv[4], "unresolved": conv[5]
                }
            # PRX decomposition stats
            prx = conn.execute("""
                SELECT dominant_component, COUNT(*),
                       AVG(p_core), AVG(p_band), AVG(r_core), AVG(r_band),
                       AVG(m_band), AVG(x_true), AVG(u_unresolved)
                FROM v37415_round_prx_decomposition
                WHERE round_id = (SELECT round_id FROM v37415_round_registry ORDER BY round_number DESC LIMIT 1)
                GROUP BY dominant_component
            """).fetchall()
            v37415["prx_final"] = [
                {"dominant": r[0], "count": r[1],
                 "p_c": round(r[2],3), "p_b": round(r[3],3),
                 "r_c": round(r[4],3), "r_b": round(r[5],3),
                 "m_b": round(r[6],3), "x": round(r[7],3), "u": round(r[8],3)}
                for r in prx]
            # Xin conservation
            xcon = conn.execute("SELECT conservation_gap, xin_true_count, xin_background_count, xin_pseudo_count FROM v37415_round_xin_ledger_conservation ORDER BY rowid DESC LIMIT 1").fetchone()
            if xcon:
                v37415["xin_conservation"] = {
                    "gap": round(xcon[0], 4), "true": xcon[1],
                    "background": xcon[2], "pseudo": xcon[3]}
            # Potential subsidy
            psub = conn.execute("SELECT AVG(phi_pre_total), AVG(f_effective), AVG(phi_hebb), AVG(phi_hyper) FROM v37415_round_potential_subsidy_state").fetchone()
            if psub and psub[0]:
                v37415["potential_subsidy"] = {
                    "phi_pre_avg": round(psub[0], 4), "f_eff_avg": round(psub[1], 4),
                    "phi_hebb_avg": round(psub[2], 4), "phi_hyper_avg": round(psub[3], 4)}
        except: pass

        results[db_name] = {
            "run_id": run_id,
            "integrity": integrity,
            "tables_total": len(tables),
            "tables_populated": len(populated),
            "tables_empty": len(empty),
            "total_rows": total_rows,
            "db_size_kb": round(db_path.stat().st_size / 1024, 1),
            "pr_distribution": pr_dist,
            "hebbian": heb,
            "transport": transport,
            "xi_residues": xi,
            "maturity_gates": gates,
            "rlis": rlis,
            "v37415": v37415,
            "empty_tables": empty,
            "top_10_tables": dict(sorted(populated.items(), key=lambda x: -x[1])[:10]),
        }

        conn.close()

        # Print summary
        r = results[db_name]
        print(f"\n  📦 {db_name}")
        print(f"    integrity={r['integrity']}  size={r['db_size_kb']}KB  rows={r['total_rows']}")
        print(f"    tables: {r['tables_populated']} populated, {r['tables_empty']} empty")
        print(f"    PR: {r['pr_distribution']}")
        print(f"    Hebbian: {r['hebbian']}")
        print(f"    Transport: {r['transport']}")
        print(f"    Xi: {r['xi_residues']}")
        print(f"    Gates: {r['maturity_gates']}")
        if r.get("v37415"):
            v = r["v37415"]
            if "convergence" in v:
                c = v["convergence"]
                print(f"    v37415 Convergence: {c['verdict']} (drift={c['final_drift']}, "
                      f"true_xin={c['true_xin']}, r_core={c['r_core']}, p_band={c['p_band']})")
            if "xin_conservation" in v:
                xc = v["xin_conservation"]
                print(f"    v37415 Xin Conservation: gap={xc['gap']}, true={xc['true']}, bg={xc['background']}")
            if "potential_subsidy" in v:
                ps = v["potential_subsidy"]
                print(f"    v37415 Potential Subsidy: Φ_pre={ps['phi_pre_avg']}, f_eff={ps['f_eff_avg']}")

    return results


# ═══════════════════════════════════════════════════════════════════
# Phase 3: Cross-batch evolution analysis
# ═══════════════════════════════════════════════════════════════════
def phase3_evolution_analysis(db_results):
    """Analyze evolution across batch4 → batch5 → batch6."""
    print("\n" + "=" * 80)
    print("PHASE 3: CROSS-BATCH EVOLUTION ANALYSIS")
    print("=" * 80)

    batches = ["v37412_20260508_batch4.db", "v37412_20260509_batch5.db", "v37415_20260509_batch6.db"]
    evolution = {}

    for metric_name, extractor in [
        ("total_rows", lambda r: r.get("total_rows", 0)),
        ("tables_populated", lambda r: r.get("tables_populated", 0)),
        ("P_frozen", lambda r: r.get("pr_distribution", {}).get("P_frozen", 0)),
        ("R_frozen", lambda r: r.get("pr_distribution", {}).get("R_frozen", 0)),
        ("hebbian_max", lambda r: r.get("hebbian", {}).get("max", 0)),
        ("hebbian_avg", lambda r: r.get("hebbian", {}).get("avg", 0)),
        ("transport_accepted", lambda r: r.get("transport", {}).get("accepted", 0)),
        ("cross_domain", lambda r: r.get("transport", {}).get("cross_domain", 0)),
        ("xi_total", lambda r: r.get("xi_residues", {}).get("total", 0)),
        ("gate_pass", lambda r: r.get("maturity_gates", {}).get("pass", 0)),
        ("rlis_gamma_avg", lambda r: r.get("rlis", {}).get("gamma_avg", 0)),
        ("db_size_kb", lambda r: r.get("db_size_kb", 0)),
    ]:
        values = []
        for b in batches:
            r = db_results.get(b, {})
            values.append(extractor(r))
        evolution[metric_name] = values

    print(f"\n  {'Metric':<25s} {'batch4':>10s} {'batch5':>10s} {'batch6':>10s} {'Δ4→6':>10s}")
    print(f"  {'─'*25} {'─'*10} {'─'*10} {'─'*10} {'─'*10}")
    for name, vals in evolution.items():
        delta = vals[2] - vals[0] if len(vals) == 3 else "—"
        fmt = lambda v: f"{v:>10.4f}" if isinstance(v, float) else f"{v:>10}"
        print(f"  {name:<25s} {fmt(vals[0])} {fmt(vals[1])} {fmt(vals[2])} {fmt(delta)}")

    return evolution


# ═══════════════════════════════════════════════════════════════════
# Phase 4: Architecture integrity checks
# ═══════════════════════════════════════════════════════════════════
def phase4_architecture_checks(db_results):
    """Run architecture-level integrity checks."""
    print("\n" + "=" * 80)
    print("PHASE 4: ARCHITECTURE INTEGRITY CHECKS")
    print("=" * 80)

    checks = {}

    # 1. All DBs pass integrity check
    for db, r in db_results.items():
        checks[f"integrity_{db}"] = r.get("integrity") == "ok"

    # 2. P_frozen exists in batch5+ 
    for db in ["v37412_20260509_batch5.db", "v37415_20260509_batch6.db"]:
        r = db_results.get(db, {})
        checks[f"P_frozen_{db}"] = r.get("pr_distribution", {}).get("P_frozen", 0) > 0

    # 3. R_frozen exists in batch5+
    for db in ["v37412_20260509_batch5.db", "v37415_20260509_batch6.db"]:
        r = db_results.get(db, {})
        checks[f"R_frozen_{db}"] = r.get("pr_distribution", {}).get("R_frozen", 0) > 0

    # 4. Hebbian strengthened (max > 0.15)
    for db in ["v37412_20260509_batch5.db", "v37415_20260509_batch6.db"]:
        r = db_results.get(db, {})
        checks[f"hebbian_strong_{db}"] = r.get("hebbian", {}).get("max", 0) > 0.15

    # 5. Cross-domain transport exists
    for db in ["v37412_20260509_batch5.db", "v37415_20260509_batch6.db"]:
        r = db_results.get(db, {})
        checks[f"cross_domain_{db}"] = r.get("transport", {}).get("cross_domain", 0) > 0

    # 6. Maturity gates pass
    for db, r in db_results.items():
        checks[f"gate_pass_{db}"] = r.get("maturity_gates", {}).get("pass", 0) > 0

    # 7. RLIS populated
    for db, r in db_results.items():
        checks[f"rlis_{db}"] = r.get("rlis", {}).get("events", 0) > 0

    # 8. v37415 convergence (batch6 only)
    b6 = db_results.get("v37415_20260509_batch6.db", {})
    v37415 = b6.get("v37415", {})
    conv = v37415.get("convergence", {})
    checks["v37415_convergence"] = conv.get("verdict") in ("CONVERGED", "STABILIZING")
    checks["v37415_r_core_exists"] = conv.get("r_core", 0) > 0
    checks["v37415_p_band_exists"] = conv.get("p_band", 0) > 0
    checks["v37415_xin_conservation"] = v37415.get("xin_conservation", {}).get("gap", 99) < 1.0

    # 9. No empty critical tables
    critical_tables = [
        "spacetime_cell", "information_fiber", "transport_current_edge",
        "run_manifest", "system_clock_entry", "pr_confirmation_graph_record",
        "fhpms_hebbian_association_weight", "rlis_ledger_event_spacetime",
    ]
    for db, r in db_results.items():
        empty = r.get("empty_tables", [])
        missing_critical = [t for t in critical_tables if t in empty]
        checks[f"critical_tables_{db}"] = len(missing_critical) == 0

    # 10. Row growth monotonic (batch4 ≤ batch5 ≤ batch6)
    rows = [db_results.get(db, {}).get("total_rows", 0) for _, db in CRITICAL_RUNNERS]
    checks["row_growth_monotonic"] = rows[0] <= rows[1] <= rows[2]

    # Print
    pass_count = sum(1 for v in checks.values() if v)
    fail_count = sum(1 for v in checks.values() if not v)
    for name, ok in sorted(checks.items()):
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"\n  TOTAL: {pass_count} PASS, {fail_count} FAIL out of {len(checks)}")

    return checks


# ═══════════════════════════════════════════════════════════════════
# Phase 5: Generate comprehensive report
# ═══════════════════════════════════════════════════════════════════
def phase5_report(structure, pipeline_results, db_results, evolution, arch_checks, elapsed):
    """Generate final comprehensive report."""
    print("\n" + "=" * 80)
    print("PHASE 5: COMPREHENSIVE REPORT")
    print("=" * 80)

    report = {
        "timestamp": now(),
        "total_elapsed_s": round(elapsed, 2),
        "structure": {
            "migrations": len(structure.get("migrations", [])),
            "source_modules": structure.get("source_modules", 0),
            "runners": len(structure.get("runners", [])),
            "pipeline_engine_lines": structure.get("pipeline_engine_lines", 0),
        },
        "pipeline_runs": {},
        "database_analysis": {},
        "evolution": evolution,
        "architecture_checks": {k: ("PASS" if v else "FAIL") for k, v in arch_checks.items()},
        "summary": {},
    }

    for runner, res in pipeline_results.items():
        report["pipeline_runs"][runner] = {
            "success": res.get("success", False),
            "elapsed": res.get("elapsed", 0),
            "acceptance": res.get("acceptance_pass", False),
        }

    for db, res in db_results.items():
        report["database_analysis"][db] = {
            "integrity": res.get("integrity"),
            "total_rows": res.get("total_rows"),
            "tables_populated": res.get("tables_populated"),
            "db_size_kb": res.get("db_size_kb"),
            "pr_distribution": res.get("pr_distribution"),
            "hebbian": res.get("hebbian"),
            "transport": res.get("transport"),
            "rlis": res.get("rlis"),
            "v37415": res.get("v37415"),
        }

    # Summary
    all_runners_pass = all(r.get("success") and r.get("acceptance_pass") for r in pipeline_results.values())
    all_arch_pass = all(arch_checks.values())
    arch_pass = sum(1 for v in arch_checks.values() if v)
    arch_total = len(arch_checks)

    report["summary"] = {
        "all_runners_pass": all_runners_pass,
        "architecture_pass_rate": f"{arch_pass}/{arch_total}",
        "all_architecture_pass": all_arch_pass,
        "overall_verdict": "FULL PASS" if (all_runners_pass and all_arch_pass) else "ISSUES DETECTED",
    }

    # Save
    report_path = REPORT_DIR / "fullchain_validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Report saved: {report_path}")

    # Final verdict
    print(f"\n{'═' * 80}")
    print(f"  OVERALL VERDICT: {report['summary']['overall_verdict']}")
    print(f"  Pipelines: {'ALL PASS' if all_runners_pass else 'SOME FAILED'}")
    print(f"  Architecture: {arch_pass}/{arch_total} checks pass")
    print(f"  Total elapsed: {elapsed:.1f}s")
    print(f"{'═' * 80}")

    return report


def main():
    t0 = time.time()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║  Morphosphere v37.4.15 — Full-Chain End-to-End Validation          ║")
    print("║  batch4 → batch5 → batch6 + cross-batch analysis                  ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    # Phase 0: Structure
    structure = phase0_structure_audit()

    # Phase 1: Run all pipelines
    pipeline_results = phase1_run_pipelines()

    # Phase 2: DB deep analysis
    db_results = phase2_db_analysis()

    # Phase 3: Evolution
    evolution = phase3_evolution_analysis(db_results)

    # Phase 4: Architecture checks
    arch_checks = phase4_architecture_checks(db_results)

    # Phase 5: Report
    elapsed = time.time() - t0
    report = phase5_report(structure, pipeline_results, db_results, evolution, arch_checks, elapsed)

    return report


if __name__ == "__main__":
    main()
