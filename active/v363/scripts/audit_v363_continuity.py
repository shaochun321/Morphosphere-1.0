#!/usr/bin/env python3
import argparse, sqlite3, sys
parser = argparse.ArgumentParser()
parser.add_argument('--db', required=True)
args = parser.parse_args()
con = sqlite3.connect(args.db)
cur = con.cursor()
issues = []
# Ledger smoothing must be sandbox-only and must not rewrite facts.
bad = cur.execute('SELECT COUNT(*) FROM v363_ledger_guided_smoothing_proposal WHERE sandbox_only != 1 OR source_facts_rewritten != 0').fetchone()[0]
if bad:
    issues.append(f'ledger smoothing boundary violations: {bad}')
# PDE-like residual must not claim PDE.
bad = cur.execute('SELECT COUNT(*) FROM v363_pde_like_continuity_residual WHERE pde_claimed != 0 OR pde_like_proxy_only != 1').fetchone()[0]
if bad:
    issues.append(f'pde claim violations: {bad}')
# Pseudo-continuity risks must be represented.
risk = cur.execute("SELECT COUNT(*) FROM v363_pseudo_continuity_audit WHERE verdict='pseudo_continuity_risk'").fetchone()[0]
print(f'pseudo_continuity_risk rows: {risk}')
if not risk:
    issues.append('no pseudo continuity risk rows found')
if issues:
    print('FAIL')
    for item in issues:
        print(item)
    sys.exit(1)
print('PASS v36.3 downgrade and guardrail audit')
