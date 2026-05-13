#!/usr/bin/env python3
"""Necropolis Stress Test — Force nodes to die and verify DNA tombstones.

Runs a high-stress Hebbian cycle with:
  1. Normal build phase (accumulate Φ)
  2. Staleness phase (sustained zero V_Φ → dead_node_suspected)
  3. Contradiction phase (push M_eff toward singularity)

Goal: produce at least 1 node_necropolis record with dna_snapshot_json.
"""
import os, sys, sqlite3, json, math, time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE))

from engines._common import ABConfig
from engines.harness import DualBlindABHarness
from pipeline_isolator import IsolatedPipeline, MotionRegimeOracle, _now, _jid
from ctc_source_adapter import CTCRealDataAdapter
import pipeline_engine as pe

DB = str(BASE / "db" / "v37495_necropolis_stress.db")

def main():
    print("=" * 72)
    print("Morphosphere v37.4.95 — Necropolis Stress Test")
    print("=" * 72)

    if os.path.exists(DB):
        os.remove(DB)
    conn = sqlite3.connect(DB)
    pe.apply_migrations(conn)
    conn.commit()

    run_id = "necropolis_stress_001"

    # Use low M_max so nodes can actually die within a reasonable tick count
    config = ABConfig(
        M_max=4.0,        # lowered from 8.0 → death threshold = 3.6
        alpha=1.5,        # aggressive inertia growth
        eta=0.18,
        decay_epsilon=0.001,  # minimal decay so Φ accumulates
    )

    adapter = CTCRealDataAdapter(sequence="01", max_frames=15)
    pipe = IsolatedPipeline("stress", [adapter], conn, run_id,
                            config=config, windows=15)

    # Phase 1: Normal ingest
    print("\n  Phase 1: Ingest...")
    pipe.run_ingest()

    # Phase 2: Run Hebbian A/B with HEAVY repetition to accumulate Φ
    print("  Phase 2: Stress Hebbian (200 ticks)...")
    ns = "stress"
    ts = _now()
    engine_b = pipe.harness.engine_b

    for stress_round in range(20):  # 20 rounds × 10 windows = 200 ticks
        for k in range(min(10, pipe.windows)):
            cells = adapter.generate_cells(k)
            if not cells:
                continue
            n = min(5, len(cells))
            for i in range(n):
                for j in range(i + 1, n):
                    # Massive external hits to push Φ sky-high
                    engine_b.update(
                        cells[i].uid, cells[j].uid,
                        a_i=0.9, a_j=0.9, gamma=1.5,
                        freeze_bonus=2.0,
                        is_external=True,
                        xin_residual=0.0)

            engine_b.apply_global_decay()
            engine_b.maybe_absorb_slow_layer()

    # Check how many nodes are near death
    dead_threshold = 0.9 * config.M_max
    near_death = [(k, w) for k, w in engine_b.weights.items()
                  if w.inertia_mass > dead_threshold]
    all_masses = [w.inertia_mass for w in engine_b.weights.values()]
    print(f"  Weights: {len(engine_b.weights)}, "
          f"max_mass={max(all_masses):.2f}, "
          f"near_death={len(near_death)} (threshold={dead_threshold:.1f})")

    if not near_death:
        # Phase 3: Extra contradiction stress to push more nodes over
        print("  Phase 3: Contradiction stress (100 more ticks)...")
        for _ in range(10):
            for k in range(10):
                cells = adapter.generate_cells(k % pipe.windows)
                if not cells:
                    continue
                n = min(3, len(cells))
                for i in range(n):
                    for j in range(i + 1, n):
                        engine_b.update(
                            cells[i].uid, cells[j].uid,
                            a_i=0.95, a_j=0.95, gamma=2.0,
                            freeze_bonus=3.0,
                            is_external=True,
                            xin_residual=0.8)  # high contradiction
                engine_b.apply_global_decay()
                engine_b.maybe_absorb_slow_layer()

        near_death = [(k, w) for k, w in engine_b.weights.items()
                      if w.inertia_mass > dead_threshold]
        all_masses = [w.inertia_mass for w in engine_b.weights.values()]
        print(f"  After stress: max_mass={max(all_masses):.2f}, "
              f"near_death={len(near_death)}")

    # Phase 4: Write results (this triggers necropolis writes)
    print("  Phase 4: Writing Hebbian weights + necropolis...")
    tick = engine_b.tick
    dead_count = 0
    for (f, t), we in engine_b.weights.items():
        is_dead = 1 if we.inertia_mass > dead_threshold else 0
        try:
            conn.execute(
                f"INSERT INTO pipe_{ns}_hebbian_weight "
                "(weight_id,from_entity_id,to_entity_id,"
                "association_type,weight_value,"
                "inertia_mass,cumulative_potential,"
                "external_hits,internal_hits,stability_ticks,"
                "is_dead_node,pipeline,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("phw"), f, t, "hebbian_b_inertia", we.weight,
                 we.inertia_mass, we.cumulative_potential,
                 we.external_hit_count, we.internal_only_count,
                 we.stability_ticks, is_dead, ns, ts))
        except Exception:
            pass

        if is_dead:
            dead_count += 1
            # Extract DNA snapshot
            connected = []
            for (f2, t2), we2 in engine_b.weights.items():
                if f2 == f or t2 == f:
                    connected.append({
                        "from": f2, "to": t2,
                        "weight": round(we2.weight, 6),
                        "inertia_mass": round(we2.inertia_mass, 4),
                        "cumulative_potential": round(we2.cumulative_potential, 4),
                        "external_hits": we2.external_hit_count,
                    })
            connected.sort(key=lambda e: e["weight"], reverse=True)
            dna = connected[:3]

            v_phi = engine_b.d_sigma_history[-1]["v_phi"] if engine_b.d_sigma_history else 0.0
            death_reason = ("v_phi_sustained_zero" if v_phi < 1e-5
                            else "inertia_singularity")
            try:
                conn.execute(
                    f"INSERT OR IGNORE INTO pipe_{ns}_node_necropolis "
                    "(node_uid,run_id,birth_tick,death_tick,"
                    "last_v_phi,death_reason,dna_snapshot_json,"
                    "pipeline,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (f"{ns}_{f}", run_id, 0, tick,
                     v_phi, death_reason,
                     json.dumps(dna, ensure_ascii=False),
                     ns, ts))
            except Exception as e:
                print(f"  ERROR writing necropolis: {e}")

    conn.commit()
    print(f"  Dead nodes written to necropolis: {dead_count}")

    # ═══════════════════════════════════════════════════════════
    # THE EXTRACTION — 蓝图第一刀
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("🪦  NECROPOLIS EXTRACTION — 蓝图 2026.5.14.1 第一刀")
    print("=" * 72)

    rows = conn.execute(
        f"SELECT node_uid, birth_tick, death_tick, last_v_phi, "
        f"death_reason, dna_snapshot_json "
        f"FROM pipe_{ns}_node_necropolis LIMIT 3"
    ).fetchall()

    if not rows:
        print("  [NO DEAD NODES] — System is too healthy to produce corpses.")
    else:
        for i, row in enumerate(rows):
            node_uid, birth, death, v_phi, reason, dna_json = row
            dna = json.loads(dna_json)
            print(f"\n  ╔══ Tombstone #{i+1} ══════════════════════════════════════")
            print(f"  ║ node_uid:      {node_uid}")
            print(f"  ║ birth_tick:    {birth}")
            print(f"  ║ death_tick:    {death}")
            print(f"  ║ last_v_phi:    {v_phi:.8f}")
            print(f"  ║ death_reason:  {reason}")
            print(f"  ║ dna_snapshot:  {len(dna)} edges preserved")
            for j, edge in enumerate(dna):
                print(f"  ║   edge[{j}]: {edge['from'][:20]} → {edge['to'][:20]}")
                print(f"  ║           weight={edge['weight']:.6f}, "
                      f"M_eff={edge['inertia_mass']:.4f}, "
                      f"Φ={edge['cumulative_potential']:.4f}, "
                      f"ext_hits={edge['external_hits']}")
            print(f"  ╚{'═' * 52}")

    # Also show oscillation PRX (第二刀)
    print(f"\n{'=' * 72}")
    print("🌊  OSCILLATION PRX — 蓝图 2026.5.14.1 第二刀")
    print("=" * 72)

    # Use the multi-pipeline DB for oscillation data
    mp_db = str(BASE / "db" / "v37493_multi_pipeline.db")
    if os.path.exists(mp_db):
        mp_conn = sqlite3.connect(mp_db)
        osc_rows = mp_conn.execute(
            "SELECT window_k, adapter_name, p_core, r_core, m_band, "
            "x_true, regime_label FROM pipe_fluo_prx_decomp "
            "WHERE regime_label = 'oscillation' LIMIT 5"
        ).fetchall()
        for row in osc_rows:
            print(f"  k={row[0]:2d} | adapter={row[1]} | "
                  f"P={row[2]:.3f} R={row[3]:.3f} M={row[4]:.3f} "
                  f"X={row[5]:.3f} | regime={row[6]}")
        mp_conn.close()
    else:
        print("  [multi-pipeline DB not found]")

    conn.close()
    print(f"\n  Database: {DB} ({os.path.getsize(DB) // 1024} KB)")

if __name__ == "__main__":
    main()
