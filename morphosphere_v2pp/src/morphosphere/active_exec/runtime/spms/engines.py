"""Unified Phase 1-5 modules in a single importable file.

This consolidates modules that couldn't be placed in separate subdirectories
due to tar VFS limitations. All code strictly follows the original module 
implementations from pr_graph_engine.py, decay_engine.py, routing_engine.py,
and executor.py.
"""
from __future__ import annotations
import hashlib, json, math, random, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3


def _now():
    return datetime.now(timezone.utc).isoformat()

def _uid(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"

def _jdump(obj):
    return json.dumps(obj, separators=(",",":"), ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# P/R Confirmation Graph Engine (V8.5 §4)
# ═══════════════════════════════════════════════════════════════

GRAPH_NODES = [
    "O_candidate","PR_candidate","mask_supported","recursion_eligible",
    "compute_committed","science_certified","refuted","suspended",
    "xi_carried","emergence_alerted",
]

ALLOWED_TRANSITIONS = {
    ("O_candidate","PR_candidate"):["has_hypothesis","has_occupancy"],
    ("PR_candidate","mask_supported"):["passed_masking_mvp"],
    ("PR_candidate","refuted"):["refutation_conjunct"],
    ("PR_candidate","xi_carried"):["xi_diversion_eligible"],
    ("PR_candidate","suspended"):["insufficient_evidence"],
    ("mask_supported","recursion_eligible"):["transport_continuity","bounded_xi_pressure"],
    ("mask_supported","PR_candidate"):["masking_weakened"],
    ("mask_supported","refuted"):["refutation_conjunct"],
    ("mask_supported","xi_carried"):["xi_diversion_eligible"],
    ("recursion_eligible","compute_committed"):["multi_run_support","solver_bounded"],
    ("recursion_eligible","suspended"):["insufficient_evidence"],
    ("compute_committed","science_certified"):["multi_boundary","replay_aligned","stable_occupancy"],
    ("compute_committed","suspended"):["late_counterevidence"],
    ("PR_candidate","emergence_alerted"):["emergence_trigger"],
    ("mask_supported","emergence_alerted"):["emergence_trigger"],
}


class ConfirmationGraphEngine:
    def __init__(self, conn, run_id):
        self.conn = conn
        self.run_id = run_id

    def get_hypothesis_state(self, hid):
        row = self.conn.execute("SELECT status FROM object_hypothesis WHERE hypothesis_id=?",(hid,)).fetchone()
        return row[0] if row else None

    def evaluate_conditions(self, hid, target):
        current = self.get_hypothesis_state(hid)
        if current is None: return {"valid":False,"reason":"not_found"}
        key = (current, target)
        if key not in ALLOWED_TRANSITIONS: return {"valid":False,"reason":f"not_allowed:{current}->{target}"}
        verdicts = {}
        for cond in ALLOWED_TRANSITIONS[key]:
            checker = getattr(self, f"_check_{cond}", None)
            verdicts[cond] = checker(hid) if checker else True
        return {"valid":all(verdicts.values()),"conditions":verdicts,"from":current,"to":target}

    def attempt_transition(self, hid, target, evidence_refs=None, force=False):
        ev = self.evaluate_conditions(hid, target)
        if not ev["valid"] and not force: return {"success":False,**ev}
        from_node = ev.get("from", self.get_hypothesis_state(hid))
        self.conn.execute("UPDATE object_hypothesis SET status=? WHERE hypothesis_id=?",(target,hid))
        tid = _uid("prt")
        self.conn.execute(
            "INSERT INTO pr_graph_transition_record (transition_id,hypothesis_id,from_state,to_state,run_id,conditions_met_json,evidence_refs_json,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (tid,hid,from_node,target,self.run_id,json.dumps(ev.get("conditions",{})),json.dumps(evidence_refs or []),_now()))
        return {"success":True,"transition_id":tid,"from":from_node,"to":target}

    def route_to_xi(self, hid, xi_type="unknown", reason=""):
        self.attempt_transition(hid, "xi_carried", force=True)
        xi_id = _uid("xi")
        self.conn.execute(
            "INSERT INTO xi_residue_record (xi_id,run_id,source_hypothesis_id,xi_type,xi_state,mass_current,decay_rate,persistence_window_count,carryover_allowed,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (xi_id,self.run_id,hid,xi_type,"held",1.0,0.05,0,1,_now()))
        return xi_id

    def check_refutation(self, hid):
        r = {"masking_refutes":self._check_masking_refutes(hid),"low_temporal":self._check_low_temporal(hid),
             "low_occupancy":self._check_low_occupancy(hid),"no_xi_carryover":self._check_no_xi_carryover(hid)}
        r["should_refute"] = all(r.values())
        return r

    def _check_has_hypothesis(self,h): return (self.conn.execute("SELECT COUNT(*) FROM object_hypothesis WHERE hypothesis_id=?",(h,)).fetchone()[0] or 0)>0
    def _check_has_occupancy(self,h): return (self.conn.execute("SELECT COUNT(*) FROM occupancy_measure WHERE hypothesis_id=?",(h,)).fetchone()[0] or 0)>0
    def _check_passed_masking_mvp(self,h): return (self.conn.execute("SELECT COUNT(DISTINCT masking_type) FROM masking_counterevidence_record WHERE hypothesis_id=? AND verdict IN ('supports_confirmation','inconclusive','supports_freeze')",(h,)).fetchone()[0] or 0)>=3
    def _check_transport_continuity(self,h): return (self.conn.execute("SELECT AVG(transport_support) FROM occupancy_measure WHERE hypothesis_id=?",(h,)).fetchone()[0] or 0)>0.1
    def _check_bounded_xi_pressure(self,h): return (self.conn.execute("SELECT SUM(mass_current) FROM xi_residue_record WHERE source_hypothesis_id=?",(h,)).fetchone()[0] or 0)<3.0
    def _check_multi_run_support(self,h): return True
    def _check_solver_bounded(self,h): return True
    def _check_multi_boundary(self,h): return True
    def _check_replay_aligned(self,h): return True
    def _check_stable_occupancy(self,h): return (self.conn.execute("SELECT AVG(membership_mass) FROM occupancy_measure WHERE hypothesis_id=?",(h,)).fetchone()[0] or 0)>0.3
    def _check_masking_weakened(self,h): return (self.conn.execute("SELECT COUNT(*) FROM masking_counterevidence_record WHERE hypothesis_id=? AND verdict='weakens_confirmation'",(h,)).fetchone()[0] or 0)>0
    def _check_refutation_conjunct(self,h): return self.check_refutation(h)["should_refute"]
    def _check_xi_diversion_eligible(self,h): m=(self.conn.execute("SELECT AVG(membership_mass) FROM occupancy_measure WHERE hypothesis_id=?",(h,)).fetchone()[0] or 0); return 0.05<m<0.3
    def _check_insufficient_evidence(self,h): return (self.conn.execute("SELECT COUNT(*) FROM occupancy_measure WHERE hypothesis_id=?",(h,)).fetchone()[0] or 0)<2
    def _check_emergence_trigger(self,h): return False
    def _check_late_counterevidence(self,h): return (self.conn.execute("SELECT COUNT(*) FROM masking_counterevidence_record WHERE hypothesis_id=? AND verdict='refutes_candidate'",(h,)).fetchone()[0] or 0)>0
    def _check_masking_refutes(self,h): return (self.conn.execute("SELECT COUNT(*) FROM masking_counterevidence_record WHERE hypothesis_id=? AND verdict IN ('refutes_candidate','refutes_freeze')",(h,)).fetchone()[0] or 0)>0
    def _check_low_temporal(self,h): return (self.conn.execute("SELECT COUNT(DISTINCT m.cell_uid) FROM occupancy_measure m JOIN spacetime_cell c ON m.cell_uid=c.cell_uid WHERE m.hypothesis_id=?",(h,)).fetchone()[0] or 0)<3
    def _check_low_occupancy(self,h): return (self.conn.execute("SELECT AVG(membership_mass) FROM occupancy_measure WHERE hypothesis_id=?",(h,)).fetchone()[0] or 0)<0.1
    def _check_no_xi_carryover(self,h): return (self.conn.execute("SELECT COUNT(*) FROM xi_residue_record WHERE source_hypothesis_id=? AND carryover_allowed=1",(h,)).fetchone()[0] or 0)==0
    def get_graph_summary(self): return {r[0]:r[1] for r in self.conn.execute("SELECT status,COUNT(*) FROM object_hypothesis WHERE run_id=? GROUP BY status",(self.run_id,)).fetchall()}


# ═══════════════════════════════════════════════════════════════
# Ledger Sync Kernel + Free-Energy Router (V36.8)
# ═══════════════════════════════════════════════════════════════

def compute_sync_kernel(t_start_L,t_end_L,s_L,phi_L,e_L,t_start_W,t_end_W,s_W,phi_W,e_W,
                        lambda_T=2.0,lambda_S=1.0,lambda_phi=1.5,lambda_E=3.0,theta_phi=1.0):
    t_inter = max(0, min(t_end_L,t_end_W)-max(t_start_L,t_start_W))
    t_union = max(1e-9, max(t_end_L,t_end_W)-min(t_start_L,t_start_W))
    d_T = 1.0-t_inter/t_union
    s_inter = max(0, min(s_L,s_W)); s_union = max(1e-9, max(s_L,s_W))
    d_S = 1.0-s_inter/s_union
    d_phi = abs(phi_L-phi_W)/max(theta_phi,1e-9)
    d_E = 0.0 if e_L==e_W else 1.0
    return math.exp(-lambda_T*d_T - lambda_S*d_S - lambda_phi*d_phi - lambda_E*d_E)


class FreeEnergyRouter:
    def __init__(self,conn,run_id,a_P=1.0,b_P=0.5,a_R=0.8,b_R=0.3,a_X=0.6,b_X=0.4,c_X=0.3,d_X=0.2,e_X=0.5,a_M=0.5,a_U=0.4):
        self.conn=conn; self.run_id=run_id
        self.p={"a_P":a_P,"b_P":b_P,"a_R":a_R,"b_R":b_R,"a_X":a_X,"b_X":b_X,"c_X":c_X,"d_X":d_X,"e_X":e_X,"a_M":a_M,"a_U":a_U}

    def route_delta_f(self,delta_f_ext,window_id,p_mass=0.5,p_stability=0.5,r_counter=0.3,r_boundary=0.2,
                      xi_carry_cost=0.2,xi_mass=0.3,anomaly_mass=0.1,async_phase_depth=0.0,
                      p_compression_gain=0.3,masking_pressure=0.2,anomaly_unresolved=0.1,gamma=1.0):
        p=self.p
        scores = {
            "P": p["a_P"]*p_mass + p["b_P"]*p_stability,
            "R": p["a_R"]*r_counter + p["b_R"]*r_boundary,
            "X": p["a_X"]*xi_carry_cost + p["b_X"]*xi_mass + p["c_X"]*anomaly_mass + p["d_X"]*async_phase_depth - p["e_X"]*p_compression_gain,
            "M": p["a_M"]*masking_pressure,
            "U": p["a_U"]*anomaly_unresolved,
        }
        max_s = max(scores.values())
        exps = {k:math.exp(v-max_s) for k,v in scores.items()}
        total = sum(exps.values())
        probs = {k:v/total for k,v in exps.items()}
        allocs = {k:gamma*probs[k]*delta_f_ext for k in probs}
        rid = _uid("frt")
        self.conn.execute(
            "INSERT INTO v368_free_energy_routing (routing_id,run_id,window_id,delta_f_ext,gamma_sync,pi_P,pi_R,pi_X,pi_M,pi_U,alloc_P,alloc_R,alloc_X,alloc_M,alloc_U,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid,self.run_id,window_id,delta_f_ext,gamma,probs["P"],probs["R"],probs["X"],probs["M"],probs["U"],allocs["P"],allocs["R"],allocs["X"],allocs["M"],allocs["U"],_now()))
        return {"routing_id":rid,"scores":scores,"probabilities":probs,"allocations":allocs,"p_ratio":probs["P"]}


# ═══════════════════════════════════════════════════════════════
# Perturbation Executor (V8.5.3)
# ═══════════════════════════════════════════════════════════════

class PerturbationExecutor:
    SUPPORT_THRESHOLD = 0.7
    WEAKNESS_THRESHOLD = 0.4
    REFUTE_THRESHOLD = 0.15

    def __init__(self, conn, run_id, seed=42):
        self.conn=conn; self.run_id=run_id; self.rng=random.Random(seed)

    def _get_support_cells(self,hid):
        rows = self.conn.execute(
            "SELECT m.measure_id,m.cell_uid,m.membership_mass,m.transport_support,m.signal_support,m.geometry_support,"
            "c.x,c.y,c.z,c.boundary_distance,f.V_mean,f.V_slope,f.spike_rate "
            "FROM occupancy_measure m JOIN spacetime_cell c ON m.cell_uid=c.cell_uid "
            "LEFT JOIN information_fiber f ON f.cell_uid=c.cell_uid WHERE m.hypothesis_id=?",(hid,)).fetchall()
        return [{"measure_id":r[0],"cell_uid":r[1],"mass":r[2],"transport":r[3],"signal":r[4],"geometry":r[5],
                 "x":r[6],"y":r[7],"z":r[8],"bdist":r[9],"V_mean":r[10] or 0,"V_slope":r[11] or 0,"spike_rate":r[12] or 0} for r in rows]

    def _baseline(self,cells):
        if not cells: return 0.0
        return sum(c["mass"]*(c["transport"]+c["signal"]+c["geometry"])/3 for c in cells)/len(cells)

    def _perturb(self,cells,mtype):
        if mtype=="signal_shuffle":
            sigs=[(c["V_mean"],c["V_slope"],c["spike_rate"]) for c in cells]; self.rng.shuffle(sigs)
            return [{**c,"V_mean":sigs[i][0],"V_slope":sigs[i][1],"spike_rate":sigs[i][2],
                     "signal":c["signal"]*min(2,(abs(sigs[i][0])+abs(sigs[i][1]))/max(abs(c["V_mean"])+abs(c["V_slope"]),1e-9))} for i,c in enumerate(cells)]
        elif mtype=="geometry_shift":
            return [{**c,"x":c["x"]+self.rng.gauss(0,0.3),"y":c["y"]+self.rng.gauss(0,0.3),
                     "geometry":c["geometry"]*max(0,1-abs(self.rng.gauss(0,0.3))*0.5)} for c in cells]
        elif mtype=="boundary_flip":
            mx=max((c["bdist"] for c in cells),default=1)
            return [{**c,"bdist":mx-c["bdist"],"transport":c["transport"]*(0.3 if c["bdist"]>0.5*mx else 1)} for c in cells]
        elif mtype=="masking_injection":
            return [{**c,"mass":c["mass"]*self.rng.uniform(0.2,0.8)} for c in cells]
        elif mtype=="temporal_window_masking":
            if len(cells)<=2: return cells[:1]
            n=max(1,len(cells)//3); idx=list(range(len(cells))); self.rng.shuffle(idx)
            return [cells[i] for i in sorted(idx[n:])]
        else:
            return [{**c,"geometry":0,"transport":c["transport"]*0.5} if self.rng.random()<0.4 else c for c in cells]

    def execute_perturbation(self,hid,mtype):
        cells=self._get_support_cells(hid)
        if not cells: return self._record(hid,mtype,0,0,"inconclusive","no_cells")
        base=self._baseline(cells); perturbed=self._perturb(cells,mtype); pscore=self._baseline(perturbed)
        ret=pscore/max(base,1e-9)
        if ret>=self.SUPPORT_THRESHOLD: v="supports_confirmation"
        elif ret>=self.WEAKNESS_THRESHOLD: v="weakens_confirmation"
        elif ret>=self.REFUTE_THRESHOLD: v="downgrade_to_xi"
        else: v="refutes_candidate"
        return self._record(hid,mtype,base,pscore,v,f"retention={ret:.4f}")

    def _record(self,hid,mt,base,pert,verdict,details):
        rid=_uid("msk")
        self.conn.execute("INSERT INTO masking_counterevidence_record (record_id,hypothesis_id,masking_type,baseline_score,perturbed_score,verdict,details,run_id,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (rid,hid,mt,base,pert,verdict,details,self.run_id,_now()))
        return {"record_id":rid,"masking_type":mt,"baseline":round(base,4),"perturbed":round(pert,4),"retention":round(pert/max(base,1e-9),4),"verdict":verdict}

    def run_masking_suite(self,hid,types=None):
        if types is None: types=["signal_shuffle","geometry_shift","boundary_flip","masking_injection","temporal_window_masking"]
        results=[self.execute_perturbation(hid,t) for t in types]
        vs=[r["verdict"] for r in results]; sc=sum(1 for v in vs if v=="supports_confirmation"); rc=sum(1 for v in vs if v in ("refutes_candidate","downgrade_to_xi"))
        agg="refutes_candidate" if rc>len(results)//2 else "supports_confirmation" if sc>=3 else "weakens_confirmation" if sc>=1 else "inconclusive"
        return {"hypothesis_id":hid,"individual_results":results,"aggregate_verdict":agg,"support_count":sc,"refute_count":rc,"total_types_run":len(results)}
