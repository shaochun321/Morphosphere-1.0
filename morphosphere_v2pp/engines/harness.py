"""DualBlindABHarness 鈥?Runs A/B/C engines on identical input.

Blueprint 搂10-12: Three-metric judgment framework.
Extracted per 搂17 for independent review.
"""
from __future__ import annotations
from typing import List, Tuple, Optional

from engines._common import (
    ABConfig, MeasureCoordinate, InternalMeasureTime, WeightEntry,
    _now, _jid, _jdump,
)
from engines.engine_a_manual_strata import HebbianEngine_A_ManualStrata
from engines.engine_b_topological_inertia import HebbianEngine_B_TopologicalInertia
from engines.engine_c_guarded_hybrid import HebbianEngine_C_GuardedHybrid


class DualBlindABHarness:
    """Runs all three engines on identical input, measures metrics.

    Judgment criteria (from 2026.5.10.1 §10-12):
      1. P-Core Survival Rate under noise storm
      2. Adaptation Latency to regime shift
      3. Compute Overhead
      4. Contradiction escape
      5. Staleness wind-down

    B must win ALL THREE core metrics to be promoted.
    """

    def __init__(self, conn, run_id, config: ABConfig = None):
        self.conn = conn
        self.run_id = run_id
        self.config = config or ABConfig()
        self.engine_a = HebbianEngine_A_ManualStrata(self.config)
        self.engine_b = HebbianEngine_B_TopologicalInertia(self.config)
        self.engine_c = HebbianEngine_C_GuardedHybrid(self.config)
        self.metric_log = []

        # Write config snapshot
        conn.execute(
            "INSERT INTO v37450_ab_config "
            "(config_id,run_id,m_max,alpha,decay_epsilon,oja_lambda,eta,"
            "strata_absorb_interval,noise_storm_ticks,regime_shift_ticks,"
            "warmup_ticks,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (_jid("cfg"), run_id, self.config.M_max, self.config.alpha,
             self.config.decay_epsilon, self.config.oja_lambda, self.config.eta,
             self.config.strata_absorb_interval, 30, 20, 10, _now()))
        conn.commit()

    def feed_update(self, from_id: str, to_id: str, a_i: float, a_j: float,
                    gamma: float, freeze_bonus: float = 1.0, xin_force: float = 0.0,
                    z_t: Optional[MeasureCoordinate] = None):
        """Feed identical update to all three engines."""
        self.engine_a.update(from_id, to_id, a_i, a_j, gamma, freeze_bonus, xin_force)
        self.engine_b.update(from_id, to_id, a_i, a_j, gamma, freeze_bonus, xin_force, z_t=z_t)
        self.engine_c.update(from_id, to_id, a_i, a_j, gamma, freeze_bonus, xin_force, z_t=z_t)

    def tick(self):
        """Advance one tick for all three engines."""
        self.engine_a.apply_global_decay()
        self.engine_b.apply_global_decay()
        self.engine_c.apply_global_decay()
        self.engine_a.maybe_absorb_slow_layer()
        self.engine_b.maybe_absorb_slow_layer()
        self.engine_c.maybe_absorb_slow_layer()

    def snapshot_p_cores(self, p_core_ids: List[str]):
        """Snapshot P-core identities for survival test."""
        self.engine_a.snapshot_p_cores(p_core_ids)
        self.engine_b.snapshot_p_cores(p_core_ids)
        self.engine_c.snapshot_p_cores(p_core_ids)

    def measure_survival(self) -> Tuple[float, float, float]:
        """After noise storm: what fraction of original P-core edges survived?

        Returns (surv_a, surv_b, surv_c).
        """
        threshold = 0.05

        def _survival(engine, snapshot_ids):
            if not snapshot_ids:
                return 1.0
            ew = engine.get_effective_weights()
            survived = 0
            total = 0
            for (f, t), w in ew.items():
                if f in snapshot_ids or t in snapshot_ids:
                    total += 1
                    if w > threshold:
                        survived += 1
            return survived / max(total, 1)

        surv_a = _survival(self.engine_a, self.engine_a.p_cores_at_snapshot)
        surv_b = _survival(self.engine_b, self.engine_b.p_cores_at_snapshot)
        surv_c = _survival(self.engine_c, self.engine_c.p_cores_at_snapshot)
        return surv_a, surv_b, surv_c

    def measure_adaptation_latency(self, new_regime_features: List[Tuple],
                                    truth_label: str) -> Tuple[int, int, int]:
        """Feed a new regime pattern and measure how many ticks until
        the engine's strongest association aligns with the new pattern.

        v37.4.61: Tracks ALL new-regime edge identities for A, B, and C.

        Returns (latency_a, latency_b, latency_c) in ticks.
        """
        new_regime_nodes = set()
        for (from_id, to_id, *_) in new_regime_features:
            new_regime_nodes.add(from_id)
            new_regime_nodes.add(to_id)

        latency_a = len(new_regime_features)
        latency_b = len(new_regime_features)
        latency_c = len(new_regime_features)

        for tick_i, (from_id, to_id, a_i, a_j, gamma) in enumerate(new_regime_features):
            self.feed_update(from_id, to_id, a_i, a_j, gamma, xin_force=a_i*a_j)
            self.tick()

            # Check all three engines
            for eng, lat_ref, name in [
                (self.engine_a, 'a', 'A'),
                (self.engine_b, 'b', 'B'),
                (self.engine_c, 'c', 'C'),
            ]:
                ew = eng.get_effective_weights()
                if ew:
                    top_keys = sorted(ew.items(), key=lambda x: -x[1])[:10]
                    new_count = sum(1 for (f, t), _ in top_keys
                                    if f in new_regime_nodes or t in new_regime_nodes)
                    if new_count >= 3:
                        if lat_ref == 'a' and latency_a == len(new_regime_features):
                            latency_a = tick_i + 1
                        elif lat_ref == 'b' and latency_b == len(new_regime_features):
                            latency_b = tick_i + 1
                        elif lat_ref == 'c' and latency_c == len(new_regime_features):
                            latency_c = tick_i + 1

        return latency_a, latency_b, latency_c

    def log_metrics(self, tick: int, phase: str):
        """Record current metrics for all three engines to DB."""
        for engine_name, engine in [("A_strata", self.engine_a),
                                     ("B_inertia", self.engine_b),
                                     ("C_hybrid", self.engine_c)]:
            m = engine.get_metrics()
            self.conn.execute(
                "INSERT INTO v37450_ab_metric_log "
                "(record_id,run_id,engine,tick,phase,"
                "p_core_survival_rate,adaptation_latency,compute_overhead_ms,"
                "weight_entropy,dead_node_count,exploded_count,"
                "avg_weight,max_weight,min_weight,total_weights,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("abl"), self.run_id, engine_name, tick, phase,
                 0.0, 0.0, 0.0,
                 m["entropy"], m["dead_nodes"], m["exploded"],
                 m["avg"], m["max"], m["min"], m["count"], _now()))

    def write_weight_snapshots(self, tick: int):
        """Write current weight states to mirror table for all engines."""
        for engine_name, engine in [("A_strata", self.engine_a),
                                     ("B_inertia", self.engine_b),
                                     ("C_hybrid", self.engine_c)]:
            if engine_name == "A_strata":
                for (f, t), w in engine.weights_fast.items():
                    self.conn.execute(
                        "INSERT INTO v37450_ab_weight_mirror "
                        "(record_id,run_id,engine,from_entity_id,to_entity_id,"
                        "weight_value,inertia_mass,cumulative_potential,layer,tick,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (_jid("wm"), self.run_id, engine_name, f, t,
                         w.weight, 1.0, w.cumulative_potential, "fast", tick, _now()))
            elif engine_name == "B_inertia":
                for (f, t), w in engine.weights.items():
                    self.conn.execute(
                        "INSERT INTO v37450_ab_weight_mirror "
                        "(record_id,run_id,engine,from_entity_id,to_entity_id,"
                        "weight_value,inertia_mass,cumulative_potential,layer,tick,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (_jid("wm"), self.run_id, engine_name, f, t,
                         w.weight, w.inertia_mass, w.cumulative_potential,
                         "single", tick, _now()))
            else:  # C_hybrid
                for (f, t), w in engine.weights_fast.items():
                    self.conn.execute(
                        "INSERT INTO v37450_ab_weight_mirror "
                        "(record_id,run_id,engine,from_entity_id,to_entity_id,"
                        "weight_value,inertia_mass,cumulative_potential,layer,tick,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (_jid("wm"), self.run_id, engine_name, f, t,
                         w.weight, w.inertia_mass, w.cumulative_potential,
                         "fast", tick, _now()))

    def flush_inertia_audit(self, tick: int):
        """Flush Engine B's per-event audit buffer to topological_inertia_event table (搂16.5)."""
        ts = _now()
        for rec in self.engine_b.audit_buffer:
            self.conn.execute(
                "INSERT INTO topological_inertia_event "
                "(record_id,engine_id,tick,event_id,class_id,from_entity,to_entity,"
                "phi,m_eff,delta_w,external_hits,internal_only_hits,"
                "recent_xin_residual,contradiction_penalty,a_t_gate,"
                "mass_clipped,singularity_flag,collapse_flag,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("tie"), "B_inertia", tick, "", "",
                 rec["from"], rec["to"],
                 rec["phi"], rec["m_eff"], rec["delta_w"],
                 rec["ext_hits"], rec["int_hits"],
                 rec["xin_res"], rec["contradiction"], rec["a_t"],
                 rec["clipped"], rec["singularity"], rec["collapse"], ts))
        count = len(self.engine_b.audit_buffer)
        self.engine_b.audit_buffer.clear()
        return count

    def write_source_events(self, events: list):
        """Write source event provenance records (搂16.1).

        events: list of dicts with keys:
            source_id, event_id, event_time, payload_hash, split_role,
            external_real_data, source_url, raw_ref
        """
        ts = _now()
        for ev in events:
            try:
                self.conn.execute(
                    "INSERT OR IGNORE INTO source_event "
                    "(event_id,source_id,split_role,event_time,payload_hash,"
                    "raw_ref,external_real_data,source_url,license_or_policy,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (ev.get("event_id", _jid("se")),
                     ev.get("source_id", "unknown"),
                     ev.get("split_role", "calibration"),
                     ev.get("event_time", ts),
                     ev.get("payload_hash", ""),
                     ev.get("raw_ref", ""),
                     ev.get("external_real_data", 0),
                     ev.get("source_url", ""),
                     ev.get("license_or_policy", ""),
                     ts))
            except Exception:
                pass  # ignore duplicate inserts

    def write_measure_coordinate(self, event_id: str,
                                  transition_cost: float = 0.0,
                                  drift_cost: float = 0.0,
                                  gamma_desync_cost: float = 0.0,
                                  xin_residual_cost: float = 0.0,
                                  potential_displacement_cost: float = 0.0,
                                  cross_slice_churn_cost: float = 0.0,
                                  magnitude_disturbance_cost: float = 0.0):
        """Write non-semantic measure coordinate z_t (搂16.3)."""
        self.conn.execute(
            "INSERT INTO measure_coordinate "
            "(record_id,event_id,transition_cost,drift_cost,gamma_desync_cost,"
            "xin_residual_cost,potential_displacement_cost,cross_slice_churn_cost,"
            "magnitude_disturbance_cost,semantic_leakage_flag,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (_jid("mc"), event_id,
             transition_cost, drift_cost, gamma_desync_cost,
             xin_residual_cost, potential_displacement_cost,
             cross_slice_churn_cost, magnitude_disturbance_cost,
             0, _now()))

    def render_verdict(self, survival_a: float, survival_b: float,
                       latency_a: float, latency_b: float,
                       overhead_a_ms: float, overhead_b_ms: float) -> dict:
        """Three-metric judgment. B must win ALL THREE."""
        wins_a = wins_b = 0

        # Metric 1: Survival (higher is better)
        if survival_b > survival_a + 0.01:
            surv_winner = "B_inertia"; wins_b += 1
        elif survival_a > survival_b + 0.01:
            surv_winner = "A_strata"; wins_a += 1
        else:
            surv_winner = "DRAW"

        # Metric 2: Latency (lower is better)
        if latency_b < latency_a - 0.5:
            lat_winner = "B_inertia"; wins_b += 1
        elif latency_a < latency_b - 0.5:
            lat_winner = "A_strata"; wins_a += 1
        else:
            lat_winner = "DRAW"

        # Metric 3: Overhead (B must not exceed A by > 20%)
        if overhead_b_ms <= overhead_a_ms * 1.2:
            if overhead_b_ms < overhead_a_ms * 0.9:
                oh_winner = "B_inertia"; wins_b += 1
            else:
                oh_winner = "DRAW"  # within 20% tolerance
        else:
            oh_winner = "A_strata"; wins_a += 1

        # Final verdict: B must win ALL THREE
        if wins_b == 3:
            winner = "B_inertia"
            rationale = "Candidate B wins all 3 metrics: survival, latency, overhead"
        elif wins_b > wins_a:
            winner = "A_strata"
            rationale = f"B wins {wins_b}/3 but not all 3 鈥?Occam's razor keeps A"
        elif wins_a > wins_b:
            winner = "A_strata"
            rationale = f"A wins {wins_a}/3 metrics"
        else:
            winner = "A_strata"
            rationale = "Draw 鈥?Occam's razor keeps simpler A"

        verdict = {
            "winner": winner,
            "survival_a": survival_a, "survival_b": survival_b, "survival_winner": surv_winner,
            "latency_a": latency_a, "latency_b": latency_b, "latency_winner": lat_winner,
            "overhead_a_ms": overhead_a_ms, "overhead_b_ms": overhead_b_ms, "overhead_winner": oh_winner,
            "wins_a": wins_a, "wins_b": wins_b, "rationale": rationale,
        }

        self.conn.execute(
            "INSERT INTO v37450_ab_verdict "
            "(verdict_id,run_id,winner,survival_a,survival_b,survival_winner,"
            "latency_a,latency_b,latency_winner,"
            "overhead_a_ms,overhead_b_ms,overhead_winner,"
            "wins_a,wins_b,rationale,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (_jid("vrd"), self.run_id, winner,
             survival_a, survival_b, surv_winner,
             latency_a, latency_b, lat_winner,
             overhead_a_ms, overhead_b_ms, oh_winner,
             wins_a, wins_b, rationale, _now()))

        # 搂16.7: Write formal promotion_decision record
        overhead_pct = ((overhead_b_ms / max(overhead_a_ms, 0.001)) - 1.0) * 100
        m_b = self.engine_b.get_metrics()
        has_singularity = m_b.get("singularity_events", 0) > 0
        has_collapse = m_b.get("collapse_events", 0) > 0
        decision = ("PROMOTE" if wins_b == 3 else
                    "KEEP_AS_CANDIDATE" if wins_b > wins_a else
                    "REJECT" if has_singularity or has_collapse else
                    "KEEP_A")
        try:
            self.conn.execute(
                "INSERT INTO promotion_decision "
                "(decision_id,run_id,candidate_engine,decision,rationale,"
                "compute_overhead_pct,holdout_metric_delta,"
                "chaos_survival_delta,novelty_latency_delta,"
                "false_lockin_flag,singularity_count,collapse_count,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("pd"), self.run_id, "B_inertia", decision,
                 f"overhead={overhead_pct:.1f}% | "
                 f"survival_delta={survival_b - survival_a:.3f} | "
                 f"latency_delta={latency_a - latency_b:.1f} | "
                 f"ext_hits={m_b.get('external_hits', 0)} | "
                 f"int_hits={m_b.get('internal_hits', 0)} | "
                 f"avg_M={m_b.get('avg_inertia_mass', 0)}",
                 overhead_pct, 0.0,
                 survival_b - survival_a,
                 latency_a - latency_b,
                 0, m_b.get("singularity_events", 0),
                 m_b.get("collapse_events", 0), _now()))
        except Exception:
            pass

        return verdict

    def write_stress_metrics(self, stream_id: str, metrics: dict,
                              split_role: str = "calibration"):
        """Write per-stream per-engine stress metrics (搂16.6)."""
        ts = _now()
        for engine_id, engine_metrics in metrics.items():
            for metric_name, metric_value in engine_metrics.items():
                try:
                    self.conn.execute(
                        "INSERT INTO ab_stress_metrics "
                        "(record_id,run_id,engine_id,stream_id,metric_name,"
                        "metric_value,split_role,generated_at) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (_jid("asm"), self.run_id, engine_id, stream_id,
                         metric_name, float(metric_value), split_role, ts))
                except Exception:
                    pass

    def flush_engine_state(self, phase: str, tick: int):
        """Write per-phase engine state snapshot to engine_state table (搂16.4)."""
        ts = _now()
        for engine_id, engine in [("A_strata", self.engine_a),
                                   ("B_inertia", self.engine_b),
                                   ("C_hybrid", self.engine_c)]:
            m = engine.get_metrics()
            # Build state summaries
            fast_json = ""
            slow_json = ""
            prior_json = ""
            if hasattr(engine, 'weights_fast'):
                fast_json = _jdump({"count": len(engine.weights_fast),
                                    "avg": m.get("avg", 0)})
            if hasattr(engine, 'weights_slow'):
                slow_json = _jdump({"count": len(engine.weights_slow)})
            if hasattr(engine, 'weights_prior'):
                prior_json = _jdump({"count": len(engine.weights_prior),
                                     "mean": m.get("mean_prior", 0)})
            elif hasattr(engine, 'weights'):
                fast_json = _jdump({"count": len(engine.weights),
                                    "avg_mass": m.get("avg_inertia_mass", 0)})
            # Basin depth average
            if hasattr(engine, 'weights'):
                wvals = list(engine.weights.values())
                basin_avg = (sum(w.cumulative_potential for w in wvals) /
                             max(len(wvals), 1)) if wvals else 0.0
            elif hasattr(engine, 'weights_fast'):
                wvals = list(engine.weights_fast.values())
                basin_avg = (sum(w.cumulative_potential for w in wvals) /
                             max(len(wvals), 1)) if wvals else 0.0
            else:
                basin_avg = 0.0
            try:
                self.conn.execute(
                    "INSERT INTO engine_state "
                    "(record_id,run_id,engine_id,phase,tick,weight_count,"
                    "avg_weight,max_weight,entropy,basin_depth_avg,"
                    "dead_nodes,fast_state_json,slow_state_json,"
                    "prior_state_json,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (_jid("es"), self.run_id, engine_id, phase, tick,
                     m.get("count", 0), m.get("avg", 0), m.get("max", 0),
                     m.get("entropy", 0), basin_avg,
                     m.get("dead_nodes", 0),
                     fast_json, slow_json, prior_json, ts))
            except Exception:
                pass

    def write_process_window(self, event_id: str, origin_anchor: str,
                              cell_count: int, window_duration: int,
                              reprojection_hash: str = ""):
        """Write process window record (搂16.2)."""
        try:
            self.conn.execute(
                "INSERT INTO process_window "
                "(window_id,event_id,origin_anchor,reprojection_hash,"
                "cell_count,window_duration_ticks,created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (_jid("pw"), event_id, origin_anchor, reprojection_hash,
                 cell_count, window_duration, _now()))
        except Exception:
            pass

    def write_self_reference_audit(self, engine_id: str, tick: int,
                                    ext_hits: int, int_hits: int,
                                    xin_residual: float,
                                    internal_deps: str = "",
                                    external_dep: str = "",
                                    rlis_sync: str = "synchronized"):
        """Write self-reference audit event (搂13.3 鈥?7 required fields)."""
        try:
            self.conn.execute(
                "INSERT INTO self_reference_event "
                "(record_id,run_id,self_reference_event_id,engine_id,"
                "internal_state_dependencies,external_event_dependency,"
                "external_hit_count,internal_only_activation_count,"
                "rlis_sync_state,xin_residual_state,tick,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("sre"), self.run_id, _jid("sref"), engine_id,
                 internal_deps, external_dep,
                 ext_hits, int_hits,
                 rlis_sync, xin_residual, tick, _now()))
        except Exception:
            pass

    def flush_d_sigma_v_phi(self, phase: str):
        """Write Engine B's d_蟽_t and V_桅 history to d_sigma_v_phi_log (搂4.5/搂4.6).

        Returns (count_written, d_sigma_mean, v_phi_mean) for verification.
        """
        ts = _now()
        history = self.engine_b.d_sigma_history
        if not history:
            return 0, 0.0, 0.0

        d_sigma_sum = 0.0
        v_phi_sum = 0.0
        count = 0
        for rec in history:
            try:
                self.conn.execute(
                    "INSERT INTO d_sigma_v_phi_log "
                    "(record_id,run_id,engine_id,tick,phase,d_sigma_t,"
                    "phi_t,phi_prev,v_phi,clock_delta,source_delta,"
                    "reproj_delta,phi_displacement,rlis_delta,churn_delta,"
                    "created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (_jid("dsv"), self.run_id, "B_inertia", rec["tick"], phase,
                     rec["d_sigma_t"], rec["phi_t"], rec["phi_prev"], rec["v_phi"],
                     rec.get("clock_delta", 1.0), rec.get("source_delta", 0.0),
                     rec.get("reproj_delta", 0.0), rec.get("phi_displacement", 0.0),
                     rec.get("rlis_delta", 0.0), rec.get("churn_delta", 0.0),
                     ts))
                d_sigma_sum += rec["d_sigma_t"]
                v_phi_sum += rec["v_phi"]
                count += 1
            except Exception:
                pass

        # Clear history after flush
        self.engine_b.d_sigma_history.clear()

        d_sigma_mean = d_sigma_sum / max(count, 1)
        v_phi_mean = v_phi_sum / max(count, 1)
        return count, d_sigma_mean, v_phi_mean

    def flush_v_phi_alerts(self, phase: str):
        """Flush Engine B's V_桅 anomaly alerts to v_phi_alert_log (B2, 搂22).

        Returns count of alerts written.
        """
        ts = _now()
        alerts = self.engine_b.v_phi_alerts
        count = 0
        for rec in alerts:
            try:
                self.conn.execute(
                    "INSERT INTO v_phi_alert_log "
                    "(record_id,run_id,engine_id,tick,alert_type,"
                    "v_phi_current,v_phi_moving_avg,threshold,"
                    "consecutive_zero_ticks,phase,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (_jid("vpa"), self.run_id, "B_inertia", rec["tick"],
                     rec["alert_type"], rec["v_phi_current"],
                     rec["v_phi_moving_avg"], rec["threshold"],
                     rec["consecutive_zero_ticks"], phase, ts))
                count += 1
            except Exception:
                pass
        self.engine_b.v_phi_alerts.clear()
        return count

    def run_sensitivity_sweep(self, c4_values: list,
                               sweep_ticks: int = 10,
                               rng=None):
        """A4: Run d_蟽_t coefficient sensitivity sweep for c4 (搂4.5).

        Creates a temporary InternalMeasureTime for each c4 value,
        feeds identical synthetic events, and records how d_蟽_t and V_桅
        respond to different c4 settings.

        Returns list of (c4, d_sigma_mean, v_phi_mean, v_phi_max).
        """
        import random as _rng_mod
        if rng is None:
            rng = _rng_mod.Random(42)

        results = []
        ts = _now()
        # Generate a fixed test sequence
        test_events = []
        for _ in range(sweep_ticks):
            a_i = 0.5 + rng.random() * 1.5
            a_j = 0.5 + rng.random() * 1.5
            z = MeasureCoordinate(
                transition_cost=rng.random() * 0.5,
                drift_cost=rng.random() * 0.3,
                gamma_desync_cost=rng.random() * 0.8,
                xin_residual_cost=rng.random() * 0.6,
                potential_displacement_cost=rng.random() * 1.0,
                cross_slice_churn_cost=rng.random() * 0.4,
                magnitude_disturbance_cost=rng.random() * 0.7,
            )
            test_events.append((a_i, a_j, z))

        for c4 in c4_values:
            mt = InternalMeasureTime(c4=c4)
            phi_prev = 0.0
            d_sigma_sum = 0.0
            v_phi_sum = 0.0
            v_phi_max = 0.0

            for tick_i, (a_i, a_j, z) in enumerate(test_events):
                d_sigma = mt.compute_from_z(z)
                phi_t = a_i * a_j * 0.5 + tick_i * 0.1  # synthetic cumulative
                phi_disp = abs(phi_t - phi_prev)
                v_phi = phi_disp / (1e-6 + d_sigma)

                d_sigma_sum += d_sigma
                v_phi_sum += v_phi
                v_phi_max = max(v_phi_max, v_phi)
                phi_prev = phi_t

            n = len(test_events)
            d_mean = d_sigma_sum / n
            v_mean = v_phi_sum / n

            results.append((c4, d_mean, v_mean, v_phi_max))

            try:
                self.conn.execute(
                    "INSERT INTO d_sigma_sensitivity_log "
                    "(record_id,run_id,c4_value,d_sigma_mean,v_phi_mean,"
                    "v_phi_max,ticks,created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (_jid("dss"), self.run_id, c4, d_mean, v_mean,
                     v_phi_max, n, ts))
            except Exception:
                pass

        return results
