"""Quick audit of batch4 database state."""
import sqlite3

conn = sqlite3.connect('v37412_20260508_batch4.db')

# 1. Empty tables
rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
empty = [r[0] for r in rows if conn.execute(f"SELECT COUNT(*) FROM [{r[0]}]").fetchone()[0] == 0]
populated = [r[0] for r in rows if conn.execute(f"SELECT COUNT(*) FROM [{r[0]}]").fetchone()[0] > 0]
print(f"Tables: {len(populated)} populated, {len(empty)} empty (total {len(rows)})")
print(f"\nEmpty tables:")
for t in empty:
    print(f"  {t}")

# 2. Key metrics
print(f"\n{'='*60}")
print("KEY METRICS")
print(f"{'='*60}")

pr = conn.execute("SELECT current_node, COUNT(*) FROM pr_confirmation_graph_record GROUP BY current_node").fetchall()
print(f"\nP/R nodes: {dict(pr)}")

gate = conn.execute("SELECT gate_result, COUNT(*) FROM maturity_gate_record GROUP BY gate_result").fetchall()
print(f"Maturity gate: {dict(gate)}")

xd = conn.execute("SELECT COUNT(*) FROM transport_current_edge WHERE transport_variant='cross_domain_normalized'").fetchone()[0]
print(f"Cross-domain edges: {xd}")

total_edges = conn.execute("SELECT COUNT(*) FROM transport_current_edge").fetchone()[0]
accepted = conn.execute("SELECT COUNT(*) FROM transport_current_edge WHERE accepted=1").fetchone()[0]
print(f"Total transport edges: {total_edges}, accepted: {accepted}")

heb = conn.execute("SELECT COUNT(*), AVG(weight_value), MIN(weight_value), MAX(weight_value) FROM fhpms_hebbian_association_weight").fetchone()
print(f"Hebbian: count={heb[0]}, avg={heb[1]:.4f}, range=[{heb[2]:.4f}, {heb[3]:.4f}]")

xi = conn.execute("SELECT current_state, COUNT(*), AVG(mass_current) FROM xi_decay_policy GROUP BY current_state").fetchall()
print(f"Xi states: {[(x[0], x[1], round(x[2],3)) for x in xi]}")

# 3. Remaining gaps analysis
print(f"\n{'='*60}")
print("GAP ANALYSIS")
print(f"{'='*60}")

# Hebbian strength
print(f"\nHebbian weight distribution:")
for bucket in conn.execute("""
    SELECT 
        CASE 
            WHEN weight_value < 0.01 THEN '<0.01'
            WHEN weight_value < 0.03 THEN '0.01-0.03'
            WHEN weight_value < 0.05 THEN '0.03-0.05'
            WHEN weight_value < 0.1 THEN '0.05-0.10'
            ELSE '>0.10'
        END as bucket, 
        COUNT(*) 
    FROM fhpms_hebbian_association_weight 
    GROUP BY bucket
""").fetchall():
    print(f"  {bucket[0]}: {bucket[1]}")

# P_frozen distribution
print(f"\nP_frozen by adapter:")
frozen = conn.execute("""
    SELECT hypothesis_type, current_node, COUNT(*) 
    FROM pr_confirmation_graph_record 
    WHERE current_node='P_frozen'
    GROUP BY hypothesis_type
""").fetchall()
for f in frozen:
    print(f"  {f[0]} -> {f[1]}: {f[2]}")

# Cross-domain analysis
print(f"\nCross-domain edge quality:")
xd_stats = conn.execute("""
    SELECT AVG(transport_weight), MIN(transport_weight), MAX(transport_weight), AVG(signal_drift)
    FROM transport_current_edge WHERE transport_variant='cross_domain_normalized'
""").fetchone()
if xd_stats[0]:
    print(f"  avg_weight: {xd_stats[0]:.4f}, range: [{xd_stats[1]:.4f}, {xd_stats[2]:.4f}], avg_signal_drift: {xd_stats[3]:.4f}")

# Variational coverage
var = conn.execute("SELECT COUNT(*) FROM v361_euler_lagrange_residual").fetchone()[0]
cells = conn.execute("SELECT COUNT(*) FROM spacetime_cell").fetchone()[0]
print(f"\nVariational coverage: {var}/{cells} ({100*var/max(cells,1):.1f}%)")

# IE metric
ie = conn.execute("SELECT COUNT(*), AVG(d_IE), MIN(d_IE), MAX(d_IE) FROM v361_information_energy_metric").fetchone()
print(f"IE metrics: count={ie[0]}, avg={ie[1]:.4f}, range=[{ie[2]:.4f}, {ie[3]:.4f}]")

# Total rows
total = sum(conn.execute(f"SELECT COUNT(*) FROM [{r[0]}]").fetchone()[0] for r in rows)
print(f"\nTotal rows across all tables: {total}")

conn.close()
print("\nDone.")
