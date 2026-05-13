"""Pipeline Isolator — Independent Hebbian hypergraphs per data source.

v37.4.93: Implements §17/§19 multi-source isolation:
  1. Each pipeline has its own DualBlindABHarness + namespaced DB tables
  2. MotionRegimeOracle reads all pipelines but writes only to its own tables
  3. One-way data flow: oracle → pipelines (read-only regime labels)

Architecture:
  IsolatedPipeline  — owns one DualBlindABHarness, writes to pipe_{ns}_* tables
  MotionRegimeOracle — reads displacement data from all pipelines, classifies regimes
  run_isolated_multi_pipeline — orchestrates execution with isolation guarantees
"""
from __future__ import annotations
import math, uuid, json, time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from engines._common import ABConfig, MeasureCoordinate, _now, _jid, _jdump
from engines.harness import DualBlindABHarness
import pipeline_engine as pe


# ═══════════════════════════════════════════════════════════════
# 1. Isolated Pipeline
# ═══════════════════════════════════════════════════════════════

class IsolatedPipeline:
    """A fully isolated pipeline with its own Hebbian hypergraph.

    Each pipeline:
      - Has its own DualBlindABHarness (independent A/B/C engine weights)
      - Writes Hebbian weights to pipe_{namespace}_hebbian_weight table
      - Writes metrics to pipe_{namespace}_metric_log table
      - Receives regime labels as read-only annotations (no write-back)
    """

    def __init__(self, namespace: str, adapters: list, conn, run_id: str,
                 config: ABConfig = None, windows: int = 15):
        self.namespace = namespace
        self.adapters = adapters
        self.conn = conn
        self.run_id = run_id
        self.windows = windows
        self.config = config or ABConfig()

        # Own harness — fully independent engine weights
        self.harness = DualBlindABHarness(conn, run_id, self.config)

        # Regime labels received from oracle (read-only)
        self._regime_labels: Dict[Tuple[str, int], str] = {}

        # Track xi_ids created during ingest for lifecycle closure
        self._xi_ids: List[str] = []

        # Create namespaced tables
        self._create_tables()

    def _create_tables(self):
        """Create pipeline-specific namespaced tables."""
        ns = self.namespace
        self.conn.executescript(f"""
            CREATE TABLE IF NOT EXISTS pipe_{ns}_hebbian_weight (
                weight_id TEXT PRIMARY KEY,
                from_entity_id TEXT NOT NULL,
                to_entity_id TEXT NOT NULL,
                association_type TEXT NOT NULL,
                weight_value REAL NOT NULL,
                inertia_mass REAL DEFAULT 1.0,
                cumulative_potential REAL DEFAULT 0.0,
                external_hits INTEGER DEFAULT 0,
                internal_hits INTEGER DEFAULT 0,
                stability_ticks INTEGER DEFAULT 0,
                is_dead_node INTEGER DEFAULT 0,
                pipeline TEXT NOT NULL DEFAULT '{ns}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pipe_{ns}_dead_node_trace (
                trace_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                from_entity_id TEXT NOT NULL,
                to_entity_id TEXT NOT NULL,
                inertia_mass REAL,
                cumulative_potential REAL,
                external_hits INTEGER,
                internal_hits INTEGER,
                weight_value REAL,
                tick_suspected INTEGER,
                tick_recovered INTEGER,
                recovery_cause TEXT,
                pipeline TEXT NOT NULL DEFAULT '{ns}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pipe_{ns}_node_necropolis (
                node_uid TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                birth_tick INTEGER NOT NULL,
                death_tick INTEGER NOT NULL,
                last_v_phi REAL NOT NULL,
                death_reason TEXT NOT NULL,
                dna_snapshot_json TEXT NOT NULL,
                pipeline TEXT NOT NULL DEFAULT '{ns}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pipe_{ns}_xin_lifecycle (
                record_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                xi_uid TEXT NOT NULL,
                original_state TEXT,
                final_state TEXT,
                residue_mass REAL,
                adapter_name TEXT,
                transition_reason TEXT,
                pipeline TEXT NOT NULL DEFAULT '{ns}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pipe_{ns}_metric_log (
                record_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                engine TEXT NOT NULL,
                tick INTEGER,
                phase TEXT,
                weight_entropy REAL,
                dead_node_count INTEGER,
                avg_weight REAL,
                max_weight REAL,
                total_weights INTEGER,
                pipeline TEXT NOT NULL DEFAULT '{ns}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pipe_{ns}_prx_decomp (
                record_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                window_k INTEGER,
                adapter_name TEXT,
                p_core REAL, p_band REAL,
                r_core REAL, r_band REAL,
                m_band REAL, x_true REAL, u REAL,
                regime_label TEXT,
                pipeline TEXT NOT NULL DEFAULT '{ns}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pipe_{ns}_convergence (
                record_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                total_rounds INTEGER,
                final_drift REAL,
                converged INTEGER,
                verdict TEXT,
                pipeline TEXT NOT NULL DEFAULT '{ns}',
                created_at TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def feed_regime_labels(self, labels: Dict[Tuple[str, int], str]):
        """Receive regime labels from oracle (read-only injection)."""
        self._regime_labels = dict(labels)

    def run_ingest(self):
        """Ingest data from all adapters into the pipeline engine (shared tables)."""
        prev_cells = {}
        prev_block_id = {}
        prev_event_id = {}

        for k in range(self.windows):
            for adapter in self.adapters:
                cells = adapter.generate_cells(k)
                if not cells:
                    continue

                env = adapter.make_envelope(k)
                env_id = pe.write_envelope(self.conn, self.run_id, env)
                pw_id = pe.write_process_window(
                    self.conn, self.run_id, adapter, k, env_id,
                    len(cells), ["ingest", "transport", "hypothesize"])
                pe.write_cells(self.conn, self.run_id, adapter, k, cells)

                akey = adapter.adapter_name
                if akey in prev_cells:
                    # Truncate to min length to avoid IndexError when
                    # cell populations vary between windows (e.g. USGS)
                    n_min = min(len(prev_cells[akey]), len(cells))
                    if n_min > 0:
                        pe.write_transport(self.conn, self.run_id, adapter,
                                           k, prev_cells[akey][:n_min],
                                           cells[:n_min])

                hyps = pe.write_hypotheses(self.conn, self.run_id, adapter, k, cells)
                xi_id = pe.write_xi(self.conn, self.run_id, adapter, k, hyps, cells[:5])
                self._xi_ids.append(xi_id)  # Track for lifecycle closure
                pe.write_v366_xin_binding(self.conn, self.run_id, xi_id, pw_id, env_id, 0.15)

                p_m = 0.4 + 0.02 * k
                r_m = 0.2 + 0.01 * k
                origin_anchors = [f"anchor_{akey}_{k}"]
                res = pe.write_v374_fhpms_rlis_trace(
                    self.conn, self.run_id, adapter, k, pw_id, env_id,
                    origin_anchors, p_m, r_m, 0.15,
                    prev_block_id=prev_block_id.get(akey),
                    prev_event_id=prev_event_id.get(akey),
                    cells=cells)

                pe.write_v366_measures(self.conn, self.run_id, pw_id, adapter, k, cells)
                pe.write_external_ledgers(self.conn, self.run_id, adapter, k, env, cells)

                prev_cells[akey] = cells
                prev_block_id[akey] = res["block_id"]
                prev_event_id[akey] = res["event_id"]

            self.conn.commit()

    def run_hebbian_ab(self):
        """Run the isolated Hebbian A/B engine with pipeline-specific data."""
        ns = self.namespace
        ts = _now()
        tick = 0

        for k in range(self.windows):
            for adapter in self.adapters:
                cells = adapter.generate_cells(k)
                if not cells:
                    continue

                akey = adapter.adapter_name
                regime = self._regime_labels.get((akey, k))

                for i, cell in enumerate(cells):
                    for j_idx in cell.neighbor_ids[:3]:
                        if j_idx >= len(cells):
                            continue
                        nc = cells[j_idx]

                        z_t = MeasureCoordinate(
                            transition_cost=abs(cell.V_mean - nc.V_mean) * 0.3,
                            drift_cost=abs(cell.spike_rate) * 0.02,
                            gamma_desync_cost=0.1,
                            xin_residual_cost=cell.signal_uncertainty,
                            potential_displacement_cost=abs(cell.V_slope) * 0.5,
                            cross_slice_churn_cost=0.05,
                            magnitude_disturbance_cost=cell.spike_rate * 0.01,
                        )

                        self.harness.feed_update(
                            cell.uid, nc.uid,
                            cell.V_mean, nc.V_mean,
                            gamma=0.8, freeze_bonus=1.0,
                            xin_force=cell.release_proxy,
                            z_t=z_t)

                self.harness.tick()
                tick += 1

                # Log metrics to namespaced table
                for ename, engine in [("A", self.harness.engine_a),
                                       ("B", self.harness.engine_b),
                                       ("C", self.harness.engine_c)]:
                    m = engine.get_metrics()
                    try:
                        self.conn.execute(
                            f"INSERT INTO pipe_{ns}_metric_log "
                            "(record_id,run_id,engine,tick,phase,"
                            "weight_entropy,dead_node_count,avg_weight,"
                            "max_weight,total_weights,pipeline,created_at) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (_jid("pm"), self.run_id, ename, tick,
                             f"window_{k}", m.get("entropy", 0),
                             m.get("dead_nodes", 0), m.get("avg", 0),
                             m.get("max", 0), m.get("count", 0), ns, ts))
                    except Exception:
                        pass

        # Write Hebbian weights with full WeightEntry state to namespaced table
        engine_b = self.harness.engine_b
        dead_threshold = 0.9 * self.config.M_max
        for (f, t), we in engine_b.weights.items():
            is_dead = 1 if we.inertia_mass > dead_threshold else 0
            try:
                self.conn.execute(
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

            # Write dead_node_trace for suspected dead nodes
            if is_dead:
                try:
                    self.conn.execute(
                        f"INSERT INTO pipe_{ns}_dead_node_trace "
                        "(trace_id,run_id,from_entity_id,to_entity_id,"
                        "inertia_mass,cumulative_potential,"
                        "external_hits,internal_hits,weight_value,"
                        "tick_suspected,tick_recovered,recovery_cause,"
                        "pipeline,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (_jid("dnt"), self.run_id, f, t,
                         we.inertia_mass, we.cumulative_potential,
                         we.external_hit_count, we.internal_only_count,
                         we.weight, tick, None, None, ns, ts))
                except Exception:
                    pass

                # Write node_necropolis with DNA snapshot (top-3 edges)
                try:
                    dna_edges = self._extract_dna_snapshot(engine_b, f)
                    v_phi = engine_b.d_sigma_history[-1]["v_phi"] if engine_b.d_sigma_history else 0.0
                    death_reason = (
                        "v_phi_sustained_zero" if v_phi < 1e-5
                        else "inertia_singularity")
                    self.conn.execute(
                        f"INSERT OR IGNORE INTO pipe_{ns}_node_necropolis "
                        "(node_uid,run_id,birth_tick,death_tick,"
                        "last_v_phi,death_reason,dna_snapshot_json,"
                        "pipeline,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (f"{ns}_{f}", self.run_id, 0, tick,
                         v_phi, death_reason,
                         json.dumps(dna_edges, ensure_ascii=False),
                         ns, ts))
                except Exception:
                    pass

        self.conn.commit()
        return {
            "namespace": ns,
            "tick": tick,
            "weights_b": len(engine_b.weights),
            "metrics_b": self.harness.engine_b.get_metrics(),
        }

    @staticmethod
    def _extract_dna_snapshot(engine_b, node_id: str, top_n: int = 3) -> list:
        """Extract top-N strongest Hebbian edges connected to node_id.

        Returns list of dicts with edge topology and weights — the 'DNA'
        that allows future forensic reconstruction of this node's
        connectivity pattern at the moment of death.
        """
        connected = []
        for (f, t), we in engine_b.weights.items():
            if f == node_id or t == node_id:
                connected.append({
                    "from": f, "to": t,
                    "weight": round(we.weight, 6),
                    "inertia_mass": round(we.inertia_mass, 4),
                    "cumulative_potential": round(we.cumulative_potential, 4),
                    "external_hits": we.external_hit_count,
                })
        # Sort by weight descending, take top N
        connected.sort(key=lambda e: e["weight"], reverse=True)
        return connected[:top_n]

    def run_xin_lifecycle_closure(self):
        """Execute Xin lifecycle closure for this pipeline only.

        Uses the xi_ids collected during this pipeline's ingest phase.
        Does NOT touch records belonging to other pipelines.

        States handled:
          - discard_after_audit → write lifecycle record
          - proto_candidate (mass > 0.1) → recycle
          - quarantined (persistence >= 5) → demote to decaying
          - held (persistence >= 3) → promote to proto_candidate
        """
        ns = self.namespace
        ts = _now()
        stats = {"discarded": 0, "recycled": 0, "demoted": 0, "promoted": 0}

        if not self._xi_ids:
            return stats

        # Query xi_decay_policy ONLY for this pipeline's xi_ids
        placeholders = ",".join("?" for _ in self._xi_ids)
        all_xi = self.conn.execute(
            f"SELECT xi_id, current_state, mass_current, persistence_window_count "
            f"FROM xi_decay_policy WHERE run_id=? AND xi_id IN ({placeholders})",
            [self.run_id] + self._xi_ids
        ).fetchall()

        adapter_name = self.adapters[0].adapter_name if self.adapters else ns

        for xi_id, state, mass, persist in all_xi:
            original_state = state
            final_state = None
            reason = None

            if state == "discard_after_audit":
                final_state = "final_discard"
                reason = "lifecycle_closure_discarded"
                stats["discarded"] += 1
            elif state == "proto_candidate" and mass > 0.1:
                final_state = "recycled_to_candidate"
                reason = "lifecycle_closure_recycled"
                stats["recycled"] += 1
            elif state == "quarantined" and persist >= 5:
                final_state = "decaying"
                reason = "lifecycle_closure_demoted"
                self.conn.execute(
                    "UPDATE xi_decay_policy SET current_state='decaying' "
                    "WHERE xi_id=? AND run_id=?", (xi_id, self.run_id))
                stats["demoted"] += 1
            elif state == "held" and persist >= 3:
                final_state = "proto_candidate"
                reason = "lifecycle_closure_promoted"
                self.conn.execute(
                    "UPDATE xi_decay_policy SET current_state='proto_candidate' "
                    "WHERE xi_id=? AND run_id=?", (xi_id, self.run_id))
                stats["promoted"] += 1

            if final_state:
                try:
                    self.conn.execute(
                        f"INSERT INTO pipe_{ns}_xin_lifecycle "
                        "(record_id,run_id,xi_uid,original_state,final_state,"
                        "residue_mass,adapter_name,transition_reason,"
                        "pipeline,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (_jid("xlc"), self.run_id, xi_id,
                         original_state, final_state,
                         mass, adapter_name, reason, ns, ts))
                except Exception:
                    pass

        self.conn.commit()
        return stats

    def run_convergence(self, num_rounds: int = 5):
        """Run isolated PRX convergence WITH Hebbian feedback loop.

        Phase 1.2 upgrade: each round now feeds back into Hebbian weights,
        creating non-trivial drift that converges to a true fixed point.

        Feedback mechanism:
          After each round's PRX computation:
          1. P-P edge reinforcement: w += η · ρ_f(p_core) · ρ_t(p_core)
          2. P-R edge weakening:     w -= δ · ρ_f(p_core) · ρ_t(r_core)
          3. Threshold adaptation:    if u_ratio high → lower threshold
          Learning rate decays: η(t) = η₀ / (1 + t/τ)

        Convergence: drift < 0.01 for 3 consecutive rounds, or max rounds.
        """
        ns = self.namespace
        ts = _now()
        drifts = []
        entropies = []

        # Feedback hyperparameters
        eta_0 = 0.05         # initial learning rate
        tau = 3.0            # decay time constant
        delta_ratio = 0.5    # weakening = delta_ratio * eta
        converge_eps = 0.01  # convergence threshold
        converge_streak_req = 3  # consecutive rounds below eps

        # Hebbian weight modulation buffer — tracks cumulative PRX feedback
        if not hasattr(self, '_prx_weight_bias'):
            self._prx_weight_bias = {}  # (adapter, k) → bias dict

        converge_streak = 0
        converged_at_round = None

        for r in range(1, num_rounds + 1):
            eta = eta_0 / (1.0 + r / tau)  # decaying learning rate

            # ── Step 1: Compute per-window PRX using regime + Hebbian bias ──
            rho_all = {}
            for adapter in self.adapters:
                akey = adapter.adapter_name
                for k in range(1, self.windows):
                    regime = self._regime_labels.get((akey, k), "unknown")
                    base_rho = self._regime_to_prx(regime)

                    # Apply accumulated Hebbian bias from previous rounds
                    bias = self._prx_weight_bias.get((akey, k), {})
                    rho = {}
                    for comp in base_rho:
                        rho[comp] = max(0.001, base_rho[comp] + bias.get(comp, 0.0))

                    # Re-normalize to sum = 1.0
                    total = sum(rho.values())
                    for comp in rho:
                        rho[comp] = rho[comp] / total

                    rho_all[(akey, k)] = rho

                    try:
                        self.conn.execute(
                            f"INSERT INTO pipe_{ns}_prx_decomp "
                            "(record_id,run_id,window_k,adapter_name,"
                            "p_core,p_band,r_core,r_band,m_band,x_true,u,"
                            "regime_label,pipeline,created_at) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (_jid("prx"), self.run_id, k, akey,
                             rho["p_core"], rho["p_band"],
                             rho["r_core"], rho["r_band"],
                             rho["m_band"], rho["x_true"], rho["u"],
                             regime, ns, ts))
                    except Exception:
                        pass

            # ── Step 2: Compute drift from previous round ──
            drift = 0.0
            if r > 1 and hasattr(self, '_prev_rho'):
                for key in rho_all:
                    if key in self._prev_rho:
                        for z in rho_all[key]:
                            drift += abs(rho_all[key][z] - self._prev_rho[key][z])
                drift /= max(len(rho_all), 1)

            # ── Step 3: Compute entropy of current PRX distribution ──
            round_entropy = 0.0
            for key, rho in rho_all.items():
                for comp, val in rho.items():
                    if val > 1e-10:
                        round_entropy -= val * math.log(val)
            round_entropy /= max(len(rho_all), 1)
            entropies.append(round_entropy)

            self._prev_rho = rho_all
            drifts.append(drift)

            # ── Step 4: Hebbian feedback — update PRX bias for next round ──
            for key, rho in rho_all.items():
                bias = self._prx_weight_bias.get(key, {c: 0.0 for c in rho})

                p_strength = rho["p_core"] + rho["p_band"]
                r_strength = rho["r_core"] + rho["r_band"]
                u_ratio = rho["u"]

                # Feedback 1: P-P reinforcement (sharpen p_core)
                bias["p_core"] = bias.get("p_core", 0) + eta * p_strength * rho["p_core"]
                bias["p_band"] = bias.get("p_band", 0) + eta * p_strength * rho["p_band"] * 0.5

                # Feedback 2: P-R weakening (reduce r when p is strong)
                delta = eta * delta_ratio
                bias["r_core"] = bias.get("r_core", 0) - delta * p_strength * r_strength
                bias["r_band"] = bias.get("r_band", 0) - delta * p_strength * r_strength * 0.5

                # Feedback 3: High uncertainty → boost x_true exploration
                if u_ratio > 0.15:
                    bias["x_true"] = bias.get("x_true", 0) + eta * u_ratio * 0.3
                    bias["u"] = bias.get("u", 0) - eta * u_ratio * 0.2

                # Clamp biases to prevent runaway
                for comp in bias:
                    bias[comp] = max(-0.3, min(0.3, bias[comp]))

                self._prx_weight_bias[key] = bias

            # ── Step 5: Convergence check ──
            if drift < converge_eps and r > 1:
                converge_streak += 1
                if converge_streak >= converge_streak_req and converged_at_round is None:
                    converged_at_round = r
            else:
                converge_streak = 0

        final_drift = drifts[-1] if drifts else 1.0
        initial_drift = drifts[1] if len(drifts) > 1 else 0.0

        # Entropy should decrease (distribution sharpens)
        entropy_decreased = (len(entropies) >= 2 and entropies[-1] < entropies[0])

        if converged_at_round is not None:
            verdict = "CONVERGED"
        elif final_drift < 0.02:
            verdict = "NEAR_CONVERGED"
        elif initial_drift > 0:
            verdict = "STABILIZING"
        else:
            verdict = "NO_DYNAMICS"

        try:
            self.conn.execute(
                f"INSERT INTO pipe_{ns}_convergence "
                "(record_id,run_id,total_rounds,final_drift,"
                "converged,verdict,pipeline,created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (_jid("conv"), self.run_id, num_rounds, final_drift,
                 1 if verdict == "CONVERGED" else 0, verdict, ns, ts))
        except Exception:
            pass

        self.conn.commit()
        return {
            "drifts": drifts,
            "verdict": verdict,
            "final_drift": final_drift,
            "initial_drift": initial_drift,
            "converged_at_round": converged_at_round,
            "entropies": entropies,
            "entropy_decreased": entropy_decreased,
        }

    @staticmethod
    def _regime_to_prx(regime: str) -> dict:
        """Map regime label to PRX scores (read-only from oracle)."""
        REGIME_PRX = {
            "stationary":   {"p_core": 0.35, "p_band": 0.20, "r_core": 0.05, "r_band": 0.05, "m_band": 0.05, "x_true": 0.10, "u": 0.20},
            "slow_drift":   {"p_core": 0.20, "p_band": 0.25, "r_core": 0.10, "r_band": 0.15, "m_band": 0.10, "x_true": 0.10, "u": 0.10},
            "fast_drift":   {"p_core": 0.10, "p_band": 0.15, "r_core": 0.15, "r_band": 0.20, "m_band": 0.15, "x_true": 0.15, "u": 0.10},
            "oscillation":  {"p_core": 0.10, "p_band": 0.10, "r_core": 0.20, "r_band": 0.25, "m_band": 0.10, "x_true": 0.10, "u": 0.15},
            "jump":         {"p_core": 0.05, "p_band": 0.10, "r_core": 0.10, "r_band": 0.10, "m_band": 0.10, "x_true": 0.35, "u": 0.20},
            "diffusion":    {"p_core": 0.10, "p_band": 0.10, "r_core": 0.05, "r_band": 0.10, "m_band": 0.30, "x_true": 0.15, "u": 0.20},
        }
        return REGIME_PRX.get(regime, {"p_core": 0.15, "p_band": 0.15, "r_core": 0.10, "r_band": 0.10, "m_band": 0.15, "x_true": 0.15, "u": 0.20})


# ═══════════════════════════════════════════════════════════════
# 2. Motion Regime Oracle (Read-Only)
# ═══════════════════════════════════════════════════════════════

class MotionRegimeOracle:
    """Read-only motion regime classifier.

    Reads displacement data from all pipelines, classifies each
    (adapter, window) into a regime label, writes ONLY to its own
    oracle tables. No Hebbian weights, no state modification.

    Regime taxonomy:
      stationary  — mean displacement < 1.0
      slow_drift  — displacement 1.0-5.0
      fast_drift  — displacement 5.0-15.0
      oscillation — high variance, low mean
      jump        — sudden large displacement (> 15.0)
      diffusion   — moderate displacement, high variance
    """

    def __init__(self, conn, run_id: str):
        self.conn = conn
        self.run_id = run_id
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS motion_regime_oracle_log (
                record_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                adapter_name TEXT NOT NULL,
                window_k INTEGER NOT NULL,
                regime TEXT NOT NULL,
                confidence REAL NOT NULL,
                mean_displacement REAL,
                var_displacement REAL,
                max_displacement REAL,
                written_by TEXT NOT NULL DEFAULT 'oracle',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS motion_regime_class_diversity (
                record_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                total_sources INTEGER,
                total_regimes INTEGER,
                regime_list TEXT,
                source_list TEXT,
                class_diversity_score INTEGER,
                created_at TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def classify_all(self, pipelines: List[IsolatedPipeline]) -> Dict[Tuple[str, int], str]:
        """Classify regimes for all (adapter, window) pairs across all pipelines.

        Returns dict of (adapter_name, window_k) -> regime_label.
        """
        ts = _now()
        labels = {}
        all_regimes = set()
        all_sources = set()

        for pipe in pipelines:
            for adapter in pipe.adapters:
                akey = adapter.adapter_name
                all_sources.add(akey)
                prev_cells = None
                # Track displacement history for autocorrelation
                displacement_history: List[float] = []

                for k in range(pipe.windows):
                    cells = adapter.generate_cells(k)
                    if not cells:
                        labels[(akey, k)] = "unknown"
                        continue

                    # Compute displacement statistics
                    displacements = []
                    if prev_cells and len(prev_cells) > 0:
                        n = min(len(cells), len(prev_cells))
                        for i in range(n):
                            dx = cells[i].x - prev_cells[i].x
                            dy = cells[i].y - prev_cells[i].y
                            dz = getattr(cells[i], 'z', 0) - getattr(prev_cells[i], 'z', 0)
                            displacements.append(math.sqrt(dx*dx + dy*dy + dz*dz))

                    if not displacements:
                        regime, conf = "stationary", 0.9
                    else:
                        mean_d = sum(displacements) / len(displacements)
                        var_d = sum((d - mean_d)**2 for d in displacements) / max(len(displacements), 1)
                        max_d = max(displacements)
                        cv = math.sqrt(var_d) / max(mean_d, 1e-6)

                        # Compute lag-1 autocorrelation from displacement history
                        displacement_history.append(mean_d)
                        autocorr = self._lag1_autocorrelation(displacement_history)

                        regime, conf = self._classify_regime(
                            mean_d, var_d, max_d, cv, autocorr)

                    labels[(akey, k)] = regime
                    all_regimes.add(regime)

                    # Write to oracle log (oracle-only table)
                    try:
                        m_d = sum(displacements) / max(len(displacements), 1) if displacements else 0
                        v_d = sum((d - m_d)**2 for d in displacements) / max(len(displacements), 1) if displacements else 0
                        x_d = max(displacements) if displacements else 0
                        self.conn.execute(
                            "INSERT INTO motion_regime_oracle_log "
                            "(record_id,run_id,adapter_name,window_k,"
                            "regime,confidence,mean_displacement,"
                            "var_displacement,max_displacement,"
                            "written_by,created_at) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (_jid("mro"), self.run_id, akey, k,
                             regime, conf, m_d, v_d, x_d, "oracle", ts))
                    except Exception:
                        pass

                    prev_cells = cells

        # Write class diversity summary
        class_div = len(all_sources)
        try:
            self.conn.execute(
                "INSERT INTO motion_regime_class_diversity "
                "(record_id,run_id,total_sources,total_regimes,"
                "regime_list,source_list,class_diversity_score,created_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (_jid("mcd"), self.run_id, len(all_sources),
                 len(all_regimes),
                 json.dumps(sorted(all_regimes)),
                 json.dumps(sorted(all_sources)),
                 class_div, ts))
        except Exception:
            pass

        self.conn.commit()
        return labels

    @staticmethod
    def _lag1_autocorrelation(series: List[float]) -> float:
        """Compute lag-1 autocorrelation. Negative = oscillation."""
        if len(series) < 4:
            return 0.0
        n = len(series)
        mean_s = sum(series) / n
        var_s = sum((x - mean_s)**2 for x in series) / n
        if var_s < 1e-10:
            return 0.0
        cov = sum((series[i] - mean_s) * (series[i+1] - mean_s)
                  for i in range(n - 1)) / (n - 1)
        return cov / var_s

    @staticmethod
    def _classify_regime(mean_d, var_d, max_d, cv, autocorr=0.0):
        """Pure function: displacement stats + autocorrelation → (regime, confidence).

        Enhanced v37.4.94:
          - autocorr < -0.25 → oscillation (alternating direction)
          - cv > 0.8 && mean_d ∈ [3,15) → diffusion (stochastic spread)
          - High var_d with positive autocorr → diffusion (random walk)
        """
        if max_d > 15.0:
            return "jump", min(0.95, 0.5 + max_d * 0.02)
        if mean_d < 1.0:
            return "stationary", min(0.95, 0.9 - mean_d * 0.3)

        # Diffusion: high variance + non-negative autocorrelation = random walk
        # Check this BEFORE oscillation to avoid masking
        if mean_d >= 3.0 and cv > 0.7 and autocorr >= -0.15:
            return "diffusion", min(0.85, 0.4 + cv * 0.15)

        # Oscillation: negative autocorrelation = alternating high/low
        if autocorr < -0.25 and mean_d > 0.5:
            return "oscillation", min(0.9, 0.5 + abs(autocorr) * 0.5)
        if mean_d < 5.0:
            if cv > 1.2:
                return "oscillation", min(0.9, 0.5 + cv * 0.15)
            return "slow_drift", min(0.9, 0.5 + mean_d * 0.08)
        if mean_d < 15.0:
            if cv > 0.8:
                return "diffusion", min(0.85, 0.4 + cv * 0.15)
            return "fast_drift", min(0.9, 0.4 + mean_d * 0.03)
        return "fast_drift", 0.7


# ═══════════════════════════════════════════════════════════════
# 3. Orchestrator
# ═══════════════════════════════════════════════════════════════

def run_isolated_multi_pipeline(conn, pipelines: List[IsolatedPipeline],
                                 oracle: MotionRegimeOracle,
                                 convergence_rounds: int = 3):
    """Run all pipelines with isolation guarantees.

    Flow:
      1. Each pipeline ingests its own data
      2. Oracle classifies regimes from all pipelines (read-only)
      3. Regime labels injected into each pipeline (one-way)
      4. Each pipeline runs its own Hebbian A/B test
      5. Each pipeline runs its own PRX convergence
      6. Returns combined results

    Isolation guarantee: No pipeline's Hebbian weights or metrics
    appear in another pipeline's namespaced tables.
    """
    results = {}

    # Phase 1: Ingest (each pipeline independently)
    print("\n  ═══ Phase 1: Independent Ingest ═══")
    for pipe in pipelines:
        t0 = time.time()
        pipe.run_ingest()
        dt = time.time() - t0
        print(f"    [{pipe.namespace}] Ingested {pipe.windows} windows "
              f"× {len(pipe.adapters)} adapters ({dt:.1f}s)")

    # Phase 2: Oracle classifies regimes (read-only)
    print("\n  ═══ Phase 2: Motion Regime Oracle ═══")
    labels = oracle.classify_all(pipelines)
    regime_counts = {}
    for (_, _), r in labels.items():
        regime_counts[r] = regime_counts.get(r, 0) + 1
    print(f"    Regimes detected: {dict(sorted(regime_counts.items()))}")

    # Phase 3: Inject labels (one-way) + run Hebbian A/B
    print("\n  ═══ Phase 3: Isolated Hebbian A/B ═══")
    for pipe in pipelines:
        # Filter labels for this pipeline's adapters only
        pipe_labels = {k: v for k, v in labels.items()
                       if k[0] in {a.adapter_name for a in pipe.adapters}}
        pipe.feed_regime_labels(pipe_labels)

        t0 = time.time()
        ab_result = pipe.run_hebbian_ab()
        dt = time.time() - t0
        m = ab_result["metrics_b"]
        print(f"    [{pipe.namespace}] B weights={ab_result['weights_b']}, "
              f"entropy={m.get('entropy',0):.3f}, "
              f"avg_mass={m.get('avg_inertia_mass',0):.3f} ({dt:.1f}s)")
        results[pipe.namespace] = {"ab": ab_result}

    # Phase 4: Independent convergence
    print("\n  ═══ Phase 4: Isolated Convergence ═══")
    for pipe in pipelines:
        conv = pipe.run_convergence(num_rounds=convergence_rounds)
        print(f"    [{pipe.namespace}] {conv['verdict']} "
              f"(drift={conv['final_drift']:.4f})")
        results[pipe.namespace]["convergence"] = conv

    # Phase 5: Xin lifecycle closure (per-pipeline, isolated)
    print("\n  ═══ Phase 5: Xin Lifecycle Closure ═══")
    for pipe in pipelines:
        lc_stats = pipe.run_xin_lifecycle_closure()
        total_lc = sum(lc_stats.values())
        print(f"    [{pipe.namespace}] discarded={lc_stats['discarded']}, "
              f"recycled={lc_stats['recycled']}, "
              f"demoted={lc_stats['demoted']}, "
              f"promoted={lc_stats['promoted']}")
        results[pipe.namespace]["xin_lifecycle"] = lc_stats

    # Summary
    results["oracle"] = {
        "total_labels": len(labels),
        "regime_counts": regime_counts,
        "class_diversity": len({a.adapter_name for p in pipelines for a in p.adapters}),
    }

    return results
