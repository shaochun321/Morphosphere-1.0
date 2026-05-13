"""Query all database outputs for user review."""
import sqlite3, json
from pathlib import Path

root = Path(".")
dbs = sorted(root.glob("*.db"), key=lambda p: p.stat().st_size)

print("=" * 80)
print("ALL DATABASE FILES (Project Data Outputs)")
print("=" * 80)
for db in dbs:
    size = db.stat().st_size / 1024
    conn = sqlite3.connect(str(db))
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
    populated = sum(1 for t in tables if conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0] > 0)
    total_rows = sum(conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0] for t in tables)
    conn.close()
    print(f"  {db.name:45s} {size:8.0f} KB  {len(tables):3d} tables ({populated} populated)  {total_rows:6d} rows")

# Motion Recognition DB
print("\n" + "=" * 80)
print("MOTION RECOGNITION DB — v37417_motion_recognition.db")
print("=" * 80)
mdb = Path("v37417_motion_recognition.db")
if mdb.exists():
    conn = sqlite3.connect(str(mdb))
    for t in ["v37417_motion_recognition_log", "v37417_motion_experiment_summary"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t}: {cnt} rows")
    print("\n  Sample recognition log (first 10):")
    print(f"  {'win':>4} {'true':>12} {'predicted':>12} {'ok':>3} {'conf':>5} {'delay':>5} {'phase':>10}")
    for r in conn.execute(
        "SELECT window_k, true_regime, predicted_regime, correct, confidence, delay, phase "
        "FROM v37417_motion_recognition_log ORDER BY window_k LIMIT 10").fetchall():
        ok = "Y" if r[3] else "N"
        print(f"  {r[0]:4d} {r[1]:>12s} {r[2]:>12s} {ok:>3s} {r[4]:5.2f} {r[5]:5d} {r[6]:>10s}")
    print("\n  Experiment summary:")
    for r in conn.execute(
        "SELECT overall_accuracy, async_accuracy, transition_accuracy, sync_accuracy, "
        "final_delay, memory_entries, regime_accuracy_json FROM v37417_motion_experiment_summary").fetchall():
        print(f"    overall={r[0]*100:.1f}%  async={r[1]*100:.1f}%  transition={r[2]*100:.1f}%  sync={r[3]*100:.1f}%")
        print(f"    final_delay={r[4]}  memory={r[5]}")
        print(f"    per_regime: {r[6]}")
    conn.close()

# Formula Competition DB
print("\n" + "=" * 80)
print("FORMULA COMPETITION DB — v37417_formula_competition.db")
print("=" * 80)
fdb = Path("v37417_formula_competition.db")
if fdb.exists():
    conn = sqlite3.connect(str(fdb))
    for t in ["v37417_formula_candidate_registry", "v37417_round_candidate_evaluation",
              "v37417_round_selection_history", "v37417_formula_evolution_summary"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t}: {cnt} rows")
    print("\n  Candidate definitions:")
    for r in conn.execute(
        "SELECT candidate_code, candidate_name, lambda_rlis, lambda_cm, lambda_fhpms, lambda_bottom, description "
        "FROM v37417_formula_candidate_registry ORDER BY candidate_code").fetchall():
        print(f"    {r[0]}: {r[1]:30s} RLIS={r[2]:.2f} CM={r[3]:.2f} FHPMS={r[4]:.2f} BM={r[5]:.2f}  {r[6]}")
    print("\n  Selection history:")
    for r in conn.execute(
        "SELECT round_number, selected_candidate, j_total_selected, runner_up_candidate, "
        "j_total_runner_up, margin FROM v37417_round_selection_history ORDER BY round_number").fetchall():
        print(f"    round={r[0]}  winner={r[1]}  J={r[2]:.3f}  runner_up={r[3]}  J2={r[4]:.3f}  margin={r[5]:.3f}")
    print("\n  Evolution summary:")
    for r in conn.execute(
        "SELECT total_rounds, final_winner, winner_stability_pct, rank_volatility, "
        "convergence_round, formula_switches, verdict, analysis_json "
        "FROM v37417_formula_evolution_summary").fetchall():
        print(f"    rounds={r[0]}  winner={r[1]}  stability={r[2]*100:.0f}%  volatility={r[3]:.3f}")
        print(f"    convergence_round={r[4]}  switches={r[5]}  verdict={r[6]}")
        analysis = json.loads(r[7])
        print(f"    winner_sequence: {analysis['winner_sequence']}")
    conn.close()
