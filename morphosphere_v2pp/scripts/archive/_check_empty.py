"""Deep diagnostic: P/R stability, memory, and generalization analysis."""
import sqlite3, json, math

DB = "v37412_20260508_batch3.db"
conn = sqlite3.connect(DB)

print("=" * 70)
print("1. P/R 记忆诊断")
print("=" * 70)

# P/R confirmation graph: check if any hypothesis has moved beyond O_candidate
pr_rows = conn.execute("""
    SELECT hypothesis_id, hypothesis_type, current_node, 
           masking_trial_count, masking_support_count, masking_refute_count,
           replay_pass_count, transport_support_score, occupancy_persistence_length, xi_pressure
    FROM pr_confirmation_graph_record
""").fetchall()
print(f"\nP/R Confirmation Graph records: {len(pr_rows)}")

node_dist = {}
for r in pr_rows:
    node = r[2]
    node_dist[node] = node_dist.get(node, 0) + 1
print(f"Node distribution: {node_dist}")

# Check transitions: has anything moved from O_candidate -> P_candidate -> P_frozen?
transitions = conn.execute("""
    SELECT from_state, to_state, COUNT(*) as cnt
    FROM pr_graph_transition_record
    GROUP BY from_state, to_state
""").fetchall()
print(f"\nP/R Transitions:")
for t in transitions:
    print(f"  {t[0]} -> {t[1]}  count={t[2]}")

# Maturity gates
gates = conn.execute("""
    SELECT gate_result, failure_reason, COUNT(*) as cnt
    FROM maturity_gate_record
    GROUP BY gate_result, failure_reason
""").fetchall()
print(f"\nMaturity Gate results:")
for g in gates:
    print(f"  result={g[0]}  reason={g[1]}  count={g[2]}")

# Masking counterevidence verdicts
masking = conn.execute("""
    SELECT verdict, COUNT(*) as cnt, AVG(baseline_score), AVG(perturbed_score)
    FROM masking_counterevidence_record
    GROUP BY verdict
""").fetchall()
print(f"\nMasking Counterevidence:")
for m in masking:
    print(f"  verdict={m[0]}  count={m[1]}  avg_baseline={m[2]:.4f}  avg_perturbed={m[3]:.4f}")

# Occupancy persistence
occ_persist = conn.execute("""
    SELECT AVG(occupancy_persistence_length), MAX(occupancy_persistence_length),
           AVG(transport_support_score), AVG(xi_pressure)
    FROM pr_confirmation_graph_record
""").fetchone()
print(f"\nOccupancy Persistence: avg={occ_persist[0]:.1f}, max={occ_persist[1]}")
print(f"Transport Support Score: avg={occ_persist[2]:.4f}")
print(f"Xi Pressure: avg={occ_persist[3]:.4f}")

# Xi lifecycle (have any Xi been reintegrated?)
xi_states = conn.execute("""
    SELECT current_state, COUNT(*), SUM(mass_current), AVG(persistence_window_count)
    FROM xi_decay_policy
    GROUP BY current_state
""").fetchall()
print(f"\nXi Decay Policy states:")
for x in xi_states:
    print(f"  state={x[0]}  count={x[1]}  total_mass={x[2]:.4f}  avg_persist={x[3]:.1f}")

# Hebbian weights — is there consolidation?
heb = conn.execute("""
    SELECT COUNT(*), AVG(weight_value), MIN(weight_value), MAX(weight_value)
    FROM fhpms_hebbian_association_weight
""").fetchone()
print(f"\nHebbian Weights: count={heb[0]}, avg={heb[1]:.6f}, range=[{heb[2]:.6f}, {heb[3]:.6f}]")

# Anchor stability
anchors = conn.execute("""
    SELECT overall_verdict, COUNT(*)
    FROM v367_anchor_validation_result
    GROUP BY overall_verdict
""").fetchall()
print(f"\nAnchor Validation:")
for a in anchors:
    print(f"  {a[0]}: {a[1]}")

print("\n" + "=" * 70)
print("2. 双源信号差异 (泛化能力指标)")
print("=" * 70)

# Cross-source transport: do edges ever cross adapters?
cross = conn.execute("""
    SELECT COUNT(*) FROM transport_current_edge 
    WHERE from_cell_uid LIKE '%sph%' AND to_cell_uid LIKE '%c2d%'
""").fetchone()
print(f"\nCross-source transport edges: {cross[0]}")

# Signal domain comparison
for src, label in [("sph", "Sphere(3D)"), ("c2d", "Calcium(2D)")]:
    row = conn.execute(f"""
        SELECT AVG(V_mean), MIN(V_mean), MAX(V_mean),
               AVG(spike_rate), AVG(adaptation_state), AVG(release_proxy)
        FROM information_fiber WHERE fiber_id LIKE 'fib_{src}_%'
    """).fetchone()
    # Manual stdev
    vals = [r[0] for r in conn.execute(f"SELECT V_mean FROM information_fiber WHERE fiber_id LIKE 'fib_{src}_%'").fetchall()]
    mean_v = sum(vals)/len(vals)
    std_v = math.sqrt(sum((v-mean_v)**2 for v in vals)/len(vals))
    print(f"\n  {label}:")
    print(f"    V_mean: {mean_v:.4f} +/- {std_v:.4f} [{row[1]:.4f}, {row[2]:.4f}]")
    print(f"    spike_rate: {row[3]:.4f}")
    print(f"    adaptation: {row[4]:.4f}, release_proxy: {row[5]:.4f}")

# IE metric cross-domain
ie = conn.execute("""
    SELECT AVG(d_IE), MIN(d_IE), MAX(d_IE), COUNT(*)
    FROM v361_information_energy_metric
""").fetchone()
print(f"\nIE Metric: avg={ie[0]:.4f}, range=[{ie[1]:.4f}, {ie[2]:.4f}], count={ie[3]}")

# Variational residual distribution
elr = conn.execute("""
    SELECT AVG(el_residual_norm), MIN(el_residual_norm), MAX(el_residual_norm),
           AVG(xin_variational), AVG(constraint_violation)
    FROM v361_euler_lagrange_residual
""").fetchone()
print(f"\nEL Residual: avg={elr[0]:.6f}, range=[{elr[1]:.6f}, {elr[2]:.6f}]")
print(f"Xin_var avg: {elr[3]:.6f}, constraint_violation avg: {elr[4]:.6f}")

# Relation readout proxy
rrp = conn.execute("""
    SELECT relation_type, COUNT(*), AVG(d_IE_value), AVG(confidence)
    FROM v361_relation_readout_proxy
    GROUP BY relation_type
""").fetchall()
print(f"\nRelation Readout Proxy:")
for r in rrp:
    print(f"  {r[0]}: count={r[1]}, avg_d_IE={r[2]:.4f}, avg_conf={r[3]:.4f}")

conn.close()
print("\nDone.")
