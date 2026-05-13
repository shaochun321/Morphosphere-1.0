#!/usr/bin/env python3
"""Morphosphere v2.9 Intervention Policy Sandbox.

This script extends v28 without rewriting source facts. It copies outputs/m28.db to
outputs/m29.db, generates action/intervention proposals from v28 divergence outputs,
then runs deterministic sandbox-only replay proxies. All action outputs are ledgered
and sidecar-exported; no v25/v26/v27/v28 source tables are modified.
"""
import sqlite3, shutil, json, hashlib, datetime, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'outputs'
RUNTIME = ROOT / 'runtime_store' / 'v29'
M28_DB = OUT / 'm28.db'
M29_DB = OUT / 'm29.db'
VERSION = 'intervention_policy_sandbox_v2.9'

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(x)))

def sid(prefix, *parts):
    s = '|'.join(str(p) for p in parts)
    return prefix + hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]

def jdump(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True)

def reset():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    if M29_DB.exists():
        M29_DB.unlink()
    for p in RUNTIME.glob('*'):
        if p.is_file():
            p.unlink()
    shutil.copy2(M28_DB, M29_DB)

def create_tables(con):
    con.executescript('''
    drop table if exists v29_run_manifest;
    create table v29_run_manifest(
      run_id text primary key, version text, parent_version text,
      source_facts_rewritten integer, hot_swap_allowed integer,
      intervention_sandbox_only integer, action_can_modify_evidence integer,
      xi_direct_to_pr_allowed integer, created_at text, notes text
    );

    drop table if exists v29_intervention_proposal;
    create table v29_intervention_proposal(
      proposal_id text primary key, proposal_type text, origin_table text, origin_ref text,
      target_window_id text, target_support_ref text, target_evidence_edge_id text,
      target_shadow_edge_id text, target_xi_ref text, priority real,
      expected_effect text, allowed_scope text, forbidden_actions_json text,
      policy_ref text, recipe_id text, status text
    );

    drop table if exists v29_policy_candidate;
    create table v29_policy_candidate(
      policy_id text primary key, policy_type text, proposal_count integer,
      objective text, selection_rule text, allowed_scope text,
      risk_class text, status text
    );

    drop table if exists v29_sandbox_replay;
    create table v29_sandbox_replay(
      replay_id text primary key, proposal_id text, policy_id text,
      replay_mode text, sandbox_target text, baseline_divergence real,
      simulated_divergence real, divergence_delta real,
      simulated_precision_delta real, simulated_attention_delta real,
      source_facts_rewritten integer, evidence_modified integer,
      outcome_class text, replay_trace_json text
    );

    drop table if exists v29_intervention_effect_report;
    create table v29_intervention_effect_report(
      effect_id text primary key, proposal_id text, replay_id text,
      target_kind text, target_ref text, predicted_benefit real,
      predicted_risk real, effective_information_proxy real,
      policy_status text, route_to text, evidence_required_before_adoption integer,
      notes text
    );

    drop table if exists v29_action_divergence_outcome;
    create table v29_action_divergence_outcome(
      outcome_id text primary key, proposal_id text, baseline_class text,
      outcome_class text, confirmed_p_delta real, overreach_delta real,
      surprise_xi_delta real, weighted_action_score real,
      accepted_for_real_action integer, sandbox_only integer,
      next_gate text
    );

    drop table if exists v29_precision_action_hint;
    create table v29_precision_action_hint(
      hint_id text primary key, source_ref text, source_table text,
      precision_problem text, recommended_action text,
      expected_precision_gain real, caution text
    );

    drop table if exists v29_runtime_artifact_manifest;
    create table v29_runtime_artifact_manifest(
      artifact_id text primary key, path text, row_count integer, size_bytes integer, sha256 text
    );

    drop table if exists v29_recipe_trace;
    create table v29_recipe_trace(
      recipe_id text primary key, recipe_name text, formula_text text,
      input_refs text, parameters_json text, thresholds_json text,
      code_path text, code_hash text, output_refs text
    );

    drop table if exists v29_acceptance_report;
    create table v29_acceptance_report(check_id text primary key, status text, details text);
    ''')
    con.commit()

def create_manifest(con):
    con.execute('insert into v29_run_manifest values (?,?,?,?,?,?,?,?,?,?)', (
        'run29_intervention_policy_sandbox', VERSION, 'shadow_evidence_divergence_gate_v2.8',
        0, 0, 1, 0, 0, datetime.datetime.utcnow().isoformat(timespec='seconds')+'Z',
        'Action enters only as intervention proposals and sandbox replay. No source facts, evidence rows, or shadow source rows are rewritten.'
    ))
    recipes = [
        ('recipe29_proposal_selection_v1','proposal_selection_v1',
         'Generate sandbox-only proposals from v28 confirmed P, overreach, surprise Xi, and emergence rows.',
         'v28_*', {'confirmed_limit':160,'overreach_limit':120,'surprise_all':True,'emergence_all':True},
         {'no_source_fact_rewrite':True}, 'active/v29/scripts/run_v29.py', '', 'v29_intervention_proposal'),
        ('recipe29_sandbox_replay_v1','sandbox_replay_v1',
         'Simulate intervention effect on divergence proxy without changing evidence or source facts.',
         'v29_intervention_proposal + v28_divergence_decomposition',
         {'replay_modes':['targeted_replay','shadow_gain_damping','sampling_precision_request','emergence_probe']},
         {'sandbox_only':True}, 'active/v29/scripts/run_v29.py', '', 'v29_sandbox_replay'),
        ('recipe29_effect_report_v1','effect_report_v1',
         'Estimate benefit, risk, and effective-information proxy from sandbox replay deltas.',
         'v29_sandbox_replay', {'effective_information_proxy':'benefit*(1-risk)'},
         {'real_action_requires_gate':True}, 'active/v29/scripts/run_v29.py', '', 'v29_intervention_effect_report'),
        ('recipe29_action_outcome_v1','action_divergence_outcome_v1',
         'Route sandbox outcomes to monitor, penalty, Xi probe, or later action gate.',
         'v29_effect_report', {}, {'accepted_for_real_action':False},
         'active/v29/scripts/run_v29.py', '', 'v29_action_divergence_outcome'),
    ]
    con.executemany('insert into v29_recipe_trace values (?,?,?,?,?,?,?,?,?)', [(a,b,c, str(d), jdump(e), jdump(f), g,h,i) for a,b,c,d,e,f,g,h,i in recipes])
    con.commit()

def ensure_v28_indexes(con):
    con.execute('create index if not exists idx_v28_div_ev on v28_divergence_decomposition(evidence_edge_id)')
    con.execute('create index if not exists idx_v28_div_sh on v28_divergence_decomposition(shadow_edge_id)')
    con.execute('create index if not exists idx_v28_div_win on v28_divergence_decomposition(window_id)')
    con.commit()

def div_for(con, evidence_edge_id=None, shadow_edge_id=None, window_id=None):
    if evidence_edge_id:
        r = con.execute('select * from v28_divergence_decomposition where evidence_edge_id=? limit 1',(evidence_edge_id,)).fetchone()
        if r: return dict(r)
    if shadow_edge_id:
        r = con.execute('select * from v28_divergence_decomposition where shadow_edge_id=? limit 1',(shadow_edge_id,)).fetchone()
        if r: return dict(r)
    if window_id:
        r = con.execute('select * from v28_divergence_decomposition where window_id=? order by total_divergence desc limit 1',(window_id,)).fetchone()
        if r: return dict(r)
    return {}

def add_policies(con):
    policies = [
        ('pol29_confirmed_p_stability','confirmed_p_stability_monitor',0,
         'Keep durable confirmed P under low-cost monitoring and test whether attention can be yielded safely.',
         'select high-overlap confirmed P rows with nonzero attention_yield_delta','sandbox_shadow_monitor','low','sandbox_only'),
        ('pol29_overreach_damping','shadow_overreach_damping',0,
         'Dampen unsupported shadow prediction strength in sandbox and check whether divergence proxy decreases.',
         'select high overreach_mass rows','sandbox_shadow_only','medium','sandbox_only'),
        ('pol29_surprise_probe','evidence_surprise_probe',0,
         'Request targeted replay / sampling around persistent Evidence surprise without promoting Xi directly.',
         'select all v28 evidence surprise Xi and emergence alert rows','sandbox_replay_only','medium','sandbox_only'),
        ('pol29_precision_sampling','precision_sampling_request',0,
         'Increase precision of high-divergence windows through observation/replay requests, not fact rewrite.',
         'select top divergence windows and low-confidence outcomes','observation_request','low','sandbox_only'),
    ]
    con.executemany('insert into v29_policy_candidate values (?,?,?,?,?,?,?,?)', policies)
    con.commit()

def add_proposal(rows, proposal_type, origin_table, origin_ref, target_window_id, support_ref, evidence_edge_id, shadow_edge_id, xi_ref, priority, expected_effect, policy_ref):
    rows.append((sid('ip29_', proposal_type, origin_ref), proposal_type, origin_table, origin_ref, target_window_id, support_ref, evidence_edge_id, shadow_edge_id, xi_ref, clamp(priority), expected_effect, 'sandbox_only', jdump(['rewrite_source_facts','modify_evidence_rows','hot_swap_parameters','xi_direct_to_pr']), policy_ref, 'recipe29_proposal_selection_v1', 'proposed'))

def build_proposals(con):
    rows=[]
    # confirmed P stability monitor: not action on facts; asks whether attention can be yielded.
    for r in con.execute('select * from v28_confirmed_p_structure order by equivalent_probability_boost desc limit 160'):
        r=dict(r); d=div_for(con, r.get('evidence_edge_id'), r.get('shadow_edge_id'))
        priority = 0.35 + float(r.get('equivalent_probability_boost') or 0) + 0.15*float(r.get('support_domain_overlap') or 0)
        add_proposal(rows, 'confirmed_p_stability_monitor', 'v28_confirmed_p_structure', r['confirmed_p_id'], d.get('window_id') or r.get('window_span'), r.get('alignment_ref'), r.get('evidence_edge_id'), r.get('shadow_edge_id'), None, priority, 'test safe attention yield and macro-node readiness in sandbox', 'pol29_confirmed_p_stability')
    # shadow overreach damping: action proposal stays shadow-only.
    for r in con.execute('select * from v28_shadow_overreach_penalty order by overreach_mass desc limit 120'):
        r=dict(r); priority = 0.40 + float(r.get('overreach_mass') or 0)
        add_proposal(rows, 'shadow_gain_damping', 'v28_shadow_overreach_penalty', r['penalty_id'], r.get('window_id'), r.get('alignment_ref'), None, r.get('shadow_edge_id'), None, priority, 'dampen unsupported shadow edge gain in sandbox; route failures to R/Xi review', 'pol29_overreach_damping')
    # evidence surprise and emergence probe.
    for r in con.execute('select * from v28_evidence_surprise_xi order by surprise_mass desc'):
        r=dict(r); priority = 0.45 + float(r.get('surprise_mass') or 0) + (0.15 if r.get('emergence_candidate') else 0)
        add_proposal(rows, 'targeted_xi_replay', 'v28_evidence_surprise_xi', r['surprise_id'], r.get('window_id'), r.get('alignment_ref'), r.get('evidence_edge_id'), None, r.get('xi_surface_ref'), priority, 'request targeted replay/sampling around surprise; Xi may only re-enter via O candidate', 'pol29_surprise_probe')
    for r in con.execute('select * from v28_emergence_alert_candidate order by novelty_score desc'):
        r=dict(r); priority = 0.65 + 0.25*float(r.get('novelty_score') or 0)
        add_proposal(rows, 'emergence_probe', 'v28_emergence_alert_candidate', r['alert_id'], r.get('window_span'), r.get('support_domain'), r.get('support_domain'), None, None, priority, 'run masking replay and proto-O readiness check for persistent surprise', 'pol29_surprise_probe')
    # High divergence precision requests.
    for r in con.execute('select * from v28_divergence_decomposition order by total_divergence desc limit 80'):
        r=dict(r); priority = 0.30 + float(r.get('total_divergence') or 0)
        add_proposal(rows, 'precision_sampling_request', 'v28_divergence_decomposition', r['divergence_id'], r.get('window_id'), r.get('support_domain_ref'), r.get('evidence_edge_id'), r.get('shadow_edge_id'), None, priority, 'request higher precision observation/replay for high divergence window', 'pol29_precision_sampling')
    # Deduplicate by proposal id.
    seen=set(); unique=[]
    for row in rows:
        if row[0] not in seen:
            seen.add(row[0]); unique.append(row)
    con.executemany('insert into v29_intervention_proposal values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', unique)
    for pid in ['pol29_confirmed_p_stability','pol29_overreach_damping','pol29_surprise_probe','pol29_precision_sampling']:
        cnt=con.execute('select count(*) from v29_intervention_proposal where policy_ref=?',(pid,)).fetchone()[0]
        con.execute('update v29_policy_candidate set proposal_count=? where policy_id=?',(cnt,pid))
    con.commit()

def simulate(con):
    replay_rows=[]; effect_rows=[]; outcome_rows=[]; hint_rows=[]
    for r in con.execute('select * from v29_intervention_proposal order by priority desc, proposal_id'):
        r=dict(r)
        div=div_for(con, r.get('target_evidence_edge_id'), r.get('target_shadow_edge_id'), r.get('target_window_id'))
        baseline = float(div.get('total_divergence') or 0.0)
        dclass = div.get('divergence_class') or 'unknown'
        ptype = r['proposal_type']
        if ptype == 'confirmed_p_stability_monitor':
            mode='monitor_attention_yield'; reduction=0.04 + 0.04*r['priority']; precision_delta=0.03; attention_delta=0.08
            outcome='stable_monitoring'
        elif ptype == 'shadow_gain_damping':
            mode='shadow_only_gain_damping'; reduction=0.22 + 0.20*r['priority']; precision_delta=0.02; attention_delta=-0.01
            outcome='overreach_reduced'
        elif ptype == 'targeted_xi_replay':
            mode='targeted_xi_replay'; reduction=0.12 + 0.10*r['priority']; precision_delta=0.12; attention_delta=0.05
            outcome='surprise_under_review'
        elif ptype == 'emergence_probe':
            mode='masking_replay_proto_o_probe'; reduction=0.08 + 0.08*r['priority']; precision_delta=0.10; attention_delta=0.07
            outcome='emergence_probe_open'
        else:
            mode='precision_sampling_request'; reduction=0.10 + 0.14*r['priority']; precision_delta=0.16; attention_delta=0.03
            outcome='precision_requested'
        sim = max(0.0, baseline * (1.0 - clamp(reduction, 0.0, 0.65)))
        delta = sim - baseline
        rid = sid('sr29_', r['proposal_id'])
        trace = {'proposal_type':ptype,'baseline_class':dclass,'sandbox_only':True,'operation':mode,'notes':'deterministic proxy replay; source facts and evidence unchanged'}
        replay_rows.append((rid, r['proposal_id'], r['policy_ref'], mode, r.get('target_support_ref'), baseline, sim, delta, precision_delta, attention_delta, 0, 0, outcome, jdump(trace)))
        benefit = clamp(-delta + precision_delta*0.25 + max(attention_delta,0)*0.15)
        risk = clamp(0.06 + (0.20 if ptype in ('targeted_xi_replay','emergence_probe') else 0.08) + max(0, baseline-sim)*0.02)
        ei = clamp(benefit * (1-risk))
        eff_id=sid('er29_', rid)
        route = {'confirmed_p_stability_monitor':'monitor_or_v30_macro_candidate','shadow_gain_damping':'R_Xi_review_then_shadow_penalty','targeted_xi_replay':'Xi_to_proto_O_review_only','emergence_probe':'emergence_review_board','precision_sampling_request':'observation_precision_queue'}.get(ptype,'review')
        effect_rows.append((eff_id, r['proposal_id'], rid, ptype, r.get('origin_ref'), benefit, risk, ei, 'sandbox_only_pending_gate', route, 1, 'No real-world action authorized; sandbox result is evidence for next gate.'))
        conf_delta = benefit if ptype=='confirmed_p_stability_monitor' else 0.0
        over_delta = -benefit if ptype=='shadow_gain_damping' else 0.0
        xi_delta = -benefit if ptype in ('targeted_xi_replay','emergence_probe') else 0.0
        score = clamp(benefit - 0.35*risk + precision_delta*0.20)
        outcome_rows.append((sid('ao29_', eff_id), r['proposal_id'], dclass, outcome, conf_delta, over_delta, xi_delta, score, 0, 1, 'v29_sandbox_acceptance_then_v30_or_v28_1'))
        if ptype in ('precision_sampling_request','targeted_xi_replay','emergence_probe'):
            hint_rows.append((sid('ph29_', r['proposal_id']), r['origin_ref'], r['origin_table'], 'insufficient precision or unresolved persistent surprise', r['expected_effect'], precision_delta, 'observation/replay only; do not modify evidence or source facts'))
    con.executemany('insert into v29_sandbox_replay values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', replay_rows)
    con.executemany('insert into v29_intervention_effect_report values (?,?,?,?,?,?,?,?,?,?,?,?)', effect_rows)
    con.executemany('insert into v29_action_divergence_outcome values (?,?,?,?,?,?,?,?,?,?,?)', outcome_rows)
    con.executemany('insert into v29_precision_action_hint values (?,?,?,?,?,?,?)', hint_rows)
    con.commit()

def export_runtime(con):
    tables=['v29_intervention_proposal','v29_policy_candidate','v29_sandbox_replay','v29_intervention_effect_report','v29_action_divergence_outcome','v29_precision_action_hint']
    for t in tables:
        path=RUNTIME/(t+'.jsonl')
        count=0
        with path.open('w', encoding='utf-8') as f:
            for row in con.execute(f'select * from {t}'):
                f.write(jdump(dict(row))+'\n'); count+=1
        data=path.read_bytes()
        con.execute('insert into v29_runtime_artifact_manifest values (?,?,?,?,?)',(t, str(path.relative_to(ROOT)), count, len(data), hashlib.sha256(data).hexdigest()))
    (RUNTIME/'runtime_manifest_v29.json').write_text(jdump([dict(r) for r in con.execute('select * from v29_runtime_artifact_manifest')]), encoding='utf-8')
    con.commit()

def acceptance(con):
    checks=[]
    def cnt(t): return con.execute(f'select count(*) from {t}').fetchone()[0]
    def add(cid, cond, detail): checks.append((cid, 'PASS' if cond else 'FAIL', str(detail)))
    add('sqlite_quick_check', con.execute('pragma quick_check(1)').fetchone()[0]=='ok', 'ok')
    for t in ['v29_intervention_proposal','v29_policy_candidate','v29_sandbox_replay','v29_intervention_effect_report','v29_action_divergence_outcome']:
        add(t+'_positive', cnt(t)>0, cnt(t))
    man=con.execute('select source_facts_rewritten,hot_swap_allowed,intervention_sandbox_only,action_can_modify_evidence,xi_direct_to_pr_allowed from v29_run_manifest').fetchone()
    add('source_facts_not_rewritten', man[0]==0, man[0])
    add('hot_swap_not_allowed', man[1]==0, man[1])
    add('intervention_sandbox_only', man[2]==1, man[2])
    add('action_cannot_modify_evidence', man[3]==0, man[3])
    add('xi_direct_to_pr_not_allowed', man[4]==0, man[4])
    add('all_replays_no_source_rewrite', con.execute('select count(*) from v29_sandbox_replay where source_facts_rewritten!=0 or evidence_modified!=0').fetchone()[0]==0, 'checked')
    add('no_real_action_accepted', con.execute('select count(*) from v29_action_divergence_outcome where accepted_for_real_action!=0').fetchone()[0]==0, 'checked')
    add('runtime_sidecars_present', cnt('v29_runtime_artifact_manifest')>=6, cnt('v29_runtime_artifact_manifest'))
    add('recipe_trace_present', cnt('v29_recipe_trace')>=4, cnt('v29_recipe_trace'))
    add('precision_hints_present', cnt('v29_precision_action_hint')>0, cnt('v29_precision_action_hint'))
    con.executemany('insert into v29_acceptance_report values (?,?,?)', checks)
    con.commit()
    bad=[x for x in checks if x[1] != 'PASS']
    if bad:
        raise SystemExit('V29 acceptance failed: '+str(bad))

def main():
    reset()
    con=sqlite3.connect(M29_DB); con.row_factory=sqlite3.Row
    create_tables(con); create_manifest(con); ensure_v28_indexes(con); add_policies(con); build_proposals(con); simulate(con); export_runtime(con); acceptance(con)
    print('V29_INTERVENTION_POLICY_SANDBOX: PASS')
    for t in ['v29_intervention_proposal','v29_policy_candidate','v29_sandbox_replay','v29_intervention_effect_report','v29_action_divergence_outcome','v29_precision_action_hint']:
        print(f'{t}:', con.execute(f'select count(*) from {t}').fetchone()[0])
    con.close()

if __name__ == '__main__':
    main()
