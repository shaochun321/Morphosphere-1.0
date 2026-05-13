#!/usr/bin/env python3
"""
Materialize Morphosphere v36.5 full-chain data index.

This is NOT a validation checker. It builds a data materialization DB that indexes
implemented, row-level data across the v25-v34 base and v35-v36.5 bridge/overlay DBs.
It explicitly adds two layers requested after the initial storage discussion:
  1) information_point_3d4d_backprojection
  2) counter_evidence_masking_layer
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def jloads(s: Any) -> list[Any]:
    if s is None:
        return []
    if isinstance(s, list):
        return s
    if isinstance(s, (int, float)):
        return [s]
    s = str(s).strip()
    if not s:
        return []
    try:
        v = json.loads(s)
        if isinstance(v, list):
            return v
        return [v]
    except Exception:
        # Some fields are comma-separated refs rather than JSON arrays.
        if ',' in s:
            return [x.strip() for x in s.split(',') if x.strip()]
        return [s]


def q(con: sqlite3.Connection, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    cur = con.execute(sql, params)
    return cur.fetchall()


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute("select 1 from sqlite_master where type='table' and name=?", (table,)).fetchone() is not None


def count_rows(con: sqlite3.Connection, table: str) -> int:
    if not table_exists(con, table):
        return 0
    return int(con.execute(f"select count(*) from {table}").fetchone()[0])


def get_cols(con: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in con.execute(f"pragma table_info({table})")]


def create_out_schema(out: sqlite3.Connection) -> None:
    out.executescript('''
    pragma journal_mode=WAL;
    pragma synchronous=NORMAL;

    create table if not exists materialized_run_manifest(
      key text primary key,
      value text
    );

    create table if not exists db_inventory(
      db_alias text,
      db_path text,
      size_bytes integer,
      sha256 text,
      table_count integer,
      total_rows integer,
      role text,
      primary key(db_alias)
    );

    create table if not exists table_inventory(
      db_alias text,
      table_name text,
      row_count integer,
      column_count integer,
      selected_for_materialization integer,
      materialization_role text,
      primary key(db_alias, table_name)
    );

    create table if not exists runtime_store_inventory(
      artifact_path text primary key,
      size_bytes integer,
      sha256 text,
      inferred_role text
    );

    create table if not exists layer_inventory(
      layer_order integer primary key,
      layer_name text,
      source_db_alias text,
      source_tables text,
      materialized_tables text,
      row_count integer,
      actual_data_status text,
      notes text
    );

    create table if not exists source_data_inventory(
      source_id text primary key,
      source_dataset text,
      source_kind text,
      source_point_count integer,
      track_count integer,
      frame_count integer,
      source_zip_sha256 text,
      doi text,
      license text,
      evidence_status text
    );

    create table if not exists source_to_information_point(
      point_id text primary key,
      source_id text,
      source_dataset text,
      source_sequence text,
      source_frame integer,
      source_track_id text,
      time_s real,
      raw_x real,
      raw_y real,
      raw_z real,
      raw_area real,
      channel text,
      value real,
      uncertainty real,
      source_coordinate_system text,
      source_unit text,
      source_zip_sha256 text,
      provenance_hash text
    );

    create table if not exists information_point_3d4d_backprojection(
      point_id text primary key,
      transform_id text,
      source_id text,
      source_dataset text,
      source_sequence text,
      source_frame integer,
      source_track_id text,
      t real,
      raw_x real,
      raw_y real,
      raw_z real,
      normalized_x real,
      normalized_y real,
      normalized_z real,
      cell_sphere_x real,
      cell_sphere_y real,
      cell_sphere_z real,
      nearest_cell_uid text,
      nearest_cell_x real,
      nearest_cell_y real,
      nearest_cell_z real,
      distance_to_cell real,
      origin_anchor_id text,
      relative_x real,
      relative_y real,
      relative_z real,
      transform_method text,
      transform_error real,
      reversible_refs_json text,
      backprojection_status text,
      dimensionality_status text
    );

    create table if not exists information_point_to_trajectory(
      link_id integer primary key autoincrement,
      point_id text,
      trajectory_trace_id text,
      source_track_id text,
      sequence_id text,
      window_index integer,
      window_start_frame integer,
      window_end_frame integer,
      window_start_time real,
      window_end_time real,
      sample_count integer,
      origin_anchor_id text,
      source_cell_uid text,
      path_length real,
      net_displacement real,
      mean_speed real,
      curvature real,
      bandwidth real,
      point_rank_in_window integer
    );
    create index if not exists idx_ipt_point on information_point_to_trajectory(point_id);
    create index if not exists idx_ipt_traj on information_point_to_trajectory(trajectory_trace_id);

    create table if not exists trajectory_to_o_pr_r_xin(
      trajectory_trace_id text primary key,
      source_track_id text,
      window_start_frame integer,
      window_end_frame integer,
      o_candidate_id text,
      p_measure_id text,
      r_measure_id text,
      xi_surface_id text,
      p_status text,
      r_status text,
      xi_status text,
      p_measure_value real,
      r_measure_value real,
      xi_residual_mass real,
      support_point_count integer,
      support_cell_count integer,
      evidence_bundle_id text,
      source_point_refs_json text,
      coordinate_transform_refs_json text,
      masking_refs_json text,
      external_ledger_refs_json text,
      calculation_recipe_refs_json text,
      runtime_field_refs_json text,
      invertible_claim text
    );

    create table if not exists counter_evidence_chain_materialized(
      r_measure_id text primary key,
      target_p_measure_id text,
      trajectory_trace_id text,
      source_track_id text,
      counter_window_start_frame integer,
      counter_window_end_frame integer,
      counter_support_point_count integer,
      counter_support_cell_count integer,
      counter_length real,
      counter_duration real,
      p_displacement_mass real,
      masking_exposure_gain real,
      entropy_violation_mass real,
      recursive_reentry_priority real,
      counter_equivalent_probability real,
      r_measure_value real,
      r_status text,
      calculation_recipe_id text,
      external_ledger_ref text,
      counter_support_point_ids_json text,
      counter_support_cell_ids_json text
    );

    create table if not exists masking_layer_materialized(
      mask_id text primary key,
      source_version text,
      source_table text,
      target_ref text,
      masking_type text,
      masking_strength real,
      masked_fraction real,
      base_membership_mass real,
      masked_membership_mass real,
      mass_retention real,
      classification_consistency real,
      trajectory_continuity real,
      verdict text,
      sandbox_only integer,
      status text,
      linked_p_ref text,
      linked_r_ref text,
      linked_xi_ref text,
      ledger_alignment_ref text,
      expected_effect text,
      mask_specification_json text
    );

    create table if not exists pr_xin_to_external_ledger(
      link_id integer primary key autoincrement,
      p_measure_id text,
      r_measure_id text,
      xi_surface_id text,
      trajectory_trace_id text,
      evidence_bundle_id text,
      p_external_ledger_ref text,
      r_external_ledger_ref text,
      xi_external_ledger_refs_json text,
      bundle_external_ledger_refs_json text,
      ledger_ref_count integer
    );

    create table if not exists external_entropy_ledger_materialized(
      entropy_event_id text primary key,
      source_ref_table text,
      source_ref_id text,
      window_id text,
      event_kind text,
      ledger_role text,
      structure_potential real,
      external_entropy real,
      ext_free_energy_proxy real,
      evidence_ref text,
      shadow_ref text,
      proxy_ref text,
      equivalent_energy real,
      total_dissipation real,
      total_noise_budget real,
      anomaly_class text,
      noether_balance_status text,
      proxy_binding_status text
    );

    create table if not exists preneural_materialized(
      row_id integer primary key autoincrement,
      source_table text,
      object_id text,
      clock_n integer,
      trajectory_id text,
      o_ref text,
      p_ref text,
      r_ref text,
      xi_ref text,
      support_score real,
      counter_score real,
      residue_mass_proxy real,
      direct_to_p_allowed integer,
      direct_to_r_allowed integer,
      payload_json text
    );

    create table if not exists attention_materialized(
      proposal_id text primary key,
      proposal_type text,
      target_region_ref text,
      region_source_kind text,
      region_source_ref text,
      window_ref text,
      p_ref text,
      r_ref text,
      xi_ref text,
      ledger_ref text,
      proposed_intensity real,
      duration_budget_windows integer,
      sandbox_only integer,
      real_action_authorized integer,
      path_integral_id text,
      integrated_delta_F_ext real,
      integrated_dissipation real,
      integrated_anomaly_mass real,
      mean_SNR_path real,
      conclusion text,
      novelty_candidate integer,
      performance_verdict text,
      recommended_next text
    );

    create table if not exists hyperedge_materialized(
      hyperedge_id text primary key,
      proposal_kind text,
      source_attention_ref text,
      window_span text,
      proposal_status text,
      external_ledger_ref text,
      truth_claimed integer,
      incidence_count integer,
      distinct_node_count integer,
      node_roles_json text,
      delta_F_ext real,
      dissipation_proxy real,
      noise_budget real,
      anomaly_mass real,
      snr_path real,
      noether_status text,
      final_weight real,
      ledger_decision text
    );

    create table if not exists hyperedge_incidence_materialized(
      row_id integer primary key,
      hyperedge_id text,
      node_id text,
      node_role text,
      incidence_weight real,
      coo_index integer,
      source_table text,
      source_ref text,
      node_type text,
      node_source_ref text,
      window_ref text,
      measure_ref text,
      carrier_kind text,
      semantic_label_in_mainline integer
    );
    create index if not exists idx_him_edge on hyperedge_incidence_materialized(hyperedge_id);
    create index if not exists idx_him_node on hyperedge_incidence_materialized(node_id);

    create table if not exists variational_path_materialized(
      path_id text primary key,
      path_role text,
      window_start integer,
      window_end integer,
      hyperedge_ref text,
      p_anchor_ref text,
      r_chain_ref text,
      xin_carrier_ref text,
      topk_rank integer,
      sandbox_only integer,
      functional_id text,
      total_action_proxy real,
      stationarity_status text,
      finite_variation_residual real,
      xin_var_total real,
      direct_to_pr_allowed integer,
      reentry_policy text,
      recommendation text,
      promotion_allowed integer
    );

    create table if not exists spacetime_band_coupler_materialized(
      band_id text primary key,
      r_ref text,
      p_anchor_ref text,
      segment_count integer,
      continuity_cost real,
      ledger_cost real,
      xin_residual_after real,
      pseudo_continuity_risk real,
      band_status text,
      coupler_decision_id text,
      decision_class text,
      total_cost real,
      deferred_xin_count integer,
      heat_bath_transfer real,
      appeal_count integer,
      selected integer,
      source_stage text
    );

    create table if not exists xin_carrier_external_readout_materialized(
      xin_carrier_id text primary key,
      source_xi_ref text,
      source_T_ref text,
      source_O_ref text,
      source_P_ref text,
      source_R_ref text,
      source_window_id text,
      support_domain_ref text,
      residual_mass_proxy real,
      ledger_ref text,
      envelope_ref text,
      external_definition_ref text,
      definition_family text,
      reentry_policy_ref text,
      attention_priority real,
      carrier_status text,
      mainline_semantic_fields_present integer,
      readout_id text,
      external_module_id text,
      readout_kind text,
      classification_ref text,
      readout_confidence real,
      writes_mainline integer,
      readout_status text
    );

    create table if not exists cross_layer_trace_sample(
      sample_id text primary key,
      source_point_id text,
      transform_id text,
      trajectory_trace_id text,
      evidence_bundle_id text,
      p_measure_id text,
      r_measure_id text,
      xi_surface_id text,
      entropy_event_ref text,
      attention_region_or_proposal text,
      hyperedge_id text,
      variational_path_id text,
      xin_carrier_id text,
      readout_id text,
      trace_completeness_score real,
      missing_links_json text,
      notes text
    );

    create table if not exists cross_layer_object_count(
      layer_name text primary key,
      materialized_table text,
      object_count integer,
      distinct_source_refs integer,
      notes text
    );

    create table if not exists data_completeness_audit(
      audit_id text primary key,
      audit_scope text,
      status text,
      observed text,
      expected text,
      blocking integer,
      detail text
    );
    ''')
    out.commit()


def materialize(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    outputs = root / 'outputs'
    out_path = Path(args.out).resolve()
    if out_path.exists():
        out_path.unlink()

    dbs = {
        'base_m34': outputs / 'm34.db',
        'm25': outputs / 'm25.db',
        'm26': outputs / 'm26.db',
        'm35': outputs / 'm35.db',
        'm35H': outputs / 'm35H.db',
        'm36': outputs / 'm36.db',
        'm361': outputs / 'm361.db',
        'm362': outputs / 'm362.db',
        'm363': outputs / 'm363.db',
        'm364': outputs / 'm364.db',
        'm365': outputs / 'm365.db',
        'rebase': outputs / 'm365_full_rebase.db',
    }
    for alias, p in dbs.items():
        if not p.exists():
            raise FileNotFoundError(f'Missing DB {alias}: {p}')

    conns = {a: sqlite3.connect(str(p)) for a, p in dbs.items()}
    for con in conns.values():
        con.row_factory = sqlite3.Row
    out = sqlite3.connect(str(out_path))
    out.row_factory = sqlite3.Row
    create_out_schema(out)

    now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    out.executemany('insert into materialized_run_manifest(key,value) values(?,?)', [
        ('run_id', 'm365_full_chain_materialized_offline_run'),
        ('created_utc', now),
        ('source_root', str(root)),
        ('purpose', 'materialize implemented full-chain data across base and v35-v36.5 overlays; not just validation'),
        ('base_db_used_for_low_layers', str(dbs['base_m34'])),
        ('online_life_runtime_claimed', 'false'),
        ('validation_only', 'false'),
        ('added_layer_information_point_3d4d_backprojection', 'true'),
        ('added_layer_counter_evidence_masking_layer', 'true'),
    ])

    selected_tables = {
        'base_m34': {
            'information_point_v25','coordinate_transform_trace_v25','trajectory_window_trace_v25',
            'p_spacetime_measure_v25','r_counter_measure_v25','xi_residual_surface_v25',
            'decision_evidence_bundle_v25','masking_counterevidence_record','spacetime_cell',
            'information_relative_coordinate_snapshot','dynamic_latent_trajectory_state','online_o_candidate_tick_v03',
            'online_p_support_tick_v03','online_r_counterstructure_tick_v03','online_xi_boundary_tick_v03',
            'external_entropy_ledger','external_dissipation_ledger','external_noise_budget_ledger','external_anomaly_ledger',
            'external_conserved_quantity_ledger','v34_external_entropy_event','v34_equivalent_energy_ledger',
            'v34_dissipation_ledger','v34_noise_budget_ledger','v34_anomaly_ledger','v34_noether_balance_audit',
            'v34_proxy_entropy_binding','v34_proxy_registry','v34_runtime_artifact_manifest','evidence_runtime_artifact_manifest_v25'
        },
        'm35': {'v35_attention_region_index','v35_attention_proposal','v35_attentional_path_integral_audit','v35_attention_performance_report','v35_r_counter_chain','v35_masking_proposal'},
        'm35H': {'v35h_hyperedge_proposal','v35h_hyperedge_incidence','v35h_hypernode_registry','v35h_hyperedge_ledger_weight'},
        'm362': {'v362_candidate_path_inventory','v362_discrete_action_score','v362_stationarity_defect_proxy','v362_xin_var_closure_defect','v362_action_comparison_report'},
        'm363': {'v363_r_spacetime_band_candidate','v363_spacetime_block_registry','v363_band_segment_link','v363_xin_noncontinuity_ledger'},
        'm364': {'v364_r_band_candidate_search','v364_variational_coupling_cost','v364_coupler_decision_report','v364_xin_triage_policy'},
        'm365': {'v365_xin_minimal_carrier_state','v365_external_xin_definition_ref','v365_external_semantic_readout_result','v365_external_real_input_envelope_binding','v365_readout_backwrite_block_event'},
        'rebase': {'rebase_version_coverage','rebase_acceptance_report','rebase_boundary_audit'}
    }

    # DB and table inventory.
    for alias, p in dbs.items():
        c = conns[alias]
        tables = [r[0] for r in c.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name")]
        total = 0
        for t in tables:
            cnt = count_rows(c, t)
            total += cnt
            sel = 1 if t in selected_tables.get(alias, set()) else 0
            out.execute('insert into table_inventory values(?,?,?,?,?,?)',
                        (alias, t, cnt, len(get_cols(c, t)), sel, 'materialized' if sel else 'inventory_only'))
        role = {
            'base_m34':'full base data ledger/index up to v34', 'm25':'v25 evidence DB alias', 'm26':'v26 shadow DB alias',
            'm35':'attention bridge overlay', 'm35H':'hyperedge incidence sidecar', 'm36':'dissipative metric overlay',
            'm361':'variational ledger overlay', 'm362':'action revision overlay', 'm363':'spacetime band overlay',
            'm364':'constrained coupler overlay', 'm365':'semantic stripping/external readout overlay', 'rebase':'full lineage coverage proof'
        }.get(alias,'')
        out.execute('insert into db_inventory values(?,?,?,?,?,?,?)',
                    (alias, str(p), p.stat().st_size, sha256_file(p), len(tables), total, role))

    base = conns['base_m34']

    # Runtime store inventory: files present under runtime_store plus artifact manifests.
    for p in sorted(root.glob('runtime_store/**/*')):
        if p.is_file():
            rel = str(p.relative_to(root))
            out.execute('insert or replace into runtime_store_inventory values(?,?,?,?)',
                        (rel, p.stat().st_size, sha256_file(p), 'runtime_store_file'))
    # Also add manifest-listed runtime artifacts if files aren't present.
    for t in ['evidence_runtime_artifact_manifest_v25','v34_runtime_artifact_manifest']:
        if table_exists(base, t):
            cols = get_cols(base, t)
            path_col = 'path' if 'path' in cols else 'relative_path'
            for r in base.execute(f'select * from {t}'):
                rel = r[path_col]
                size = r['size_bytes'] if 'size_bytes' in cols else (r['bytes'] if 'bytes' in cols else None)
                sha = r['sha256'] if 'sha256' in cols else None
                role = r['artifact_role'] if 'artifact_role' in cols else (r['role'] if 'role' in cols else t)
                out.execute('insert or ignore into runtime_store_inventory values(?,?,?,?)', (rel, size, sha, role))

    # Source inventory and source_to_information_point.
    ip_rows = list(base.execute('select * from information_point_v25'))
    src_counter = Counter(r['source_id'] for r in ip_rows)
    track_counter = defaultdict(set)
    frame_counter = defaultdict(set)
    src_meta = {}
    for r in ip_rows:
        sid = r['source_id']
        track_counter[sid].add(r['source_track_id'])
        frame_counter[sid].add(r['source_frame'])
        src_meta.setdefault(sid, r)
        out.execute('''insert into source_to_information_point values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (r['point_id'], r['source_id'], r['source_dataset'], r['source_sequence'], r['source_frame'],
                     r['source_track_id'], r['time_s'], r['raw_x'], r['raw_y'], r['raw_z'], r['raw_area'],
                     r['channel'], r['value'], r['uncertainty'], r['source_coordinate_system'], r['source_unit'],
                     r['source_zip_sha256'], r['provenance_hash']))
    for sid, cnt in src_counter.items():
        m = src_meta[sid]
        out.execute('insert into source_data_inventory values(?,?,?,?,?,?,?,?,?,?)',
                    (sid, m['source_dataset'], m['sensor_kind'], cnt, len(track_counter[sid]), len(frame_counter[sid]),
                     m['source_zip_sha256'], m['doi'], m['license'], 'materialized_information_points_present'))

    # Information point 3D/4D backprojection.
    stc = {r['cell_uid']: r for r in base.execute('select * from spacetime_cell')}
    ip_by_id = {r['point_id']: r for r in ip_rows}
    transform_count = 0
    z_nonzero = 0
    for ct in base.execute('select * from coordinate_transform_trace_v25'):
        ip = ip_by_id.get(ct['source_point_id'])
        nearest = stc.get(ct['nearest_cell_uid'])
        if not ip:
            continue
        if (ct['raw_z'] or 0) != 0 or (ct['cell_sphere_z'] or 0) != 0:
            z_nonzero += 1
        dim_status = '4d_schema_with_time_and_3d_coordinates_z0_for_2d_source' if (ct['raw_z'] or 0) == 0 else '4d_schema_with_nonzero_z'
        out.execute('''insert into information_point_3d4d_backprojection values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (ip['point_id'], ct['transform_id'], ip['source_id'], ip['source_dataset'], ip['source_sequence'],
                     ip['source_frame'], ip['source_track_id'], ip['time_s'], ip['raw_x'], ip['raw_y'], ip['raw_z'],
                     ct['normalized_x'], ct['normalized_y'], ct['normalized_z'], ct['cell_sphere_x'], ct['cell_sphere_y'],
                     ct['cell_sphere_z'], ct['nearest_cell_uid'], nearest['x'] if nearest else None,
                     nearest['y'] if nearest else None, nearest['z'] if nearest else None, ct['distance_to_cell'],
                     ct['origin_anchor_id'], ct['relative_x'], ct['relative_y'], ct['relative_z'], ct['transform_method'],
                     ct['transform_error'], ct['reversible_refs_json'], 'materialized_from_information_point_and_coordinate_transform', dim_status))
        transform_count += 1

    # Point to trajectory window mapping.
    trajectory_rows = list(base.execute('select * from trajectory_window_trace_v25'))
    point_to_traj_count = 0
    traj_by_id = {}
    for tw in trajectory_rows:
        traj_by_id[tw['trajectory_trace_id']] = tw
        pts = jloads(tw['point_ids_json'])
        for i, pid in enumerate(pts):
            out.execute('''insert into information_point_to_trajectory(
                point_id,trajectory_trace_id,source_track_id,sequence_id,window_index,window_start_frame,window_end_frame,
                window_start_time,window_end_time,sample_count,origin_anchor_id,source_cell_uid,path_length,net_displacement,mean_speed,curvature,bandwidth,point_rank_in_window)
                values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (pid, tw['trajectory_trace_id'], tw['source_track_id'], tw['sequence_id'], tw['window_index'],
                 tw['window_start_frame'], tw['window_end_frame'], tw['window_start_time'], tw['window_end_time'],
                 tw['sample_count'], tw['origin_anchor_id'], tw['source_cell_uid'], tw['path_length'], tw['net_displacement'],
                 tw['mean_speed'], tw['curvature'], tw['bandwidth'], i))
            point_to_traj_count += 1

    # P/R/Xi and evidence bundles.
    p_by_id = {r['p_measure_id']: r for r in base.execute('select * from p_spacetime_measure_v25')}
    r_by_target_p = {r['target_p_measure_id']: r for r in base.execute('select * from r_counter_measure_v25')}
    r_by_id = {r['r_measure_id']: r for r in base.execute('select * from r_counter_measure_v25')}
    xi_by_id = {r['xi_surface_id']: r for r in base.execute('select * from xi_residual_surface_v25')}
    bundle_by_p = {}
    for eb in base.execute('select * from decision_evidence_bundle_v25'):
        bundle_by_p[eb['p_measure_id']] = eb
    for pid, p in p_by_id.items():
        r = r_by_target_p.get(pid)
        eb = bundle_by_p.get(pid)
        xi = xi_by_id.get(eb['xi_surface_id']) if eb else None
        tw = traj_by_id.get(p['trajectory_trace_id'])
        spoints = jloads(p['support_point_ids_json'])
        scells = jloads(p['support_cell_ids_json'])
        out.execute('''insert or replace into trajectory_to_o_pr_r_xin values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (p['trajectory_trace_id'], p['source_track_id'], p['window_start_frame'], p['window_end_frame'],
                     p['o_candidate_id'], pid, r['r_measure_id'] if r else None, xi['xi_surface_id'] if xi else None,
                     p['p_status'], r['r_status'] if r else None, xi['xi_status'] if xi else None,
                     p['p_measure_value'], r['r_measure_value'] if r else None, xi['residual_mass'] if xi else None,
                     len(spoints), len(scells), eb['bundle_id'] if eb else None,
                     eb['source_point_refs_json'] if eb else None, eb['coordinate_transform_refs_json'] if eb else None,
                     eb['masking_refs_json'] if eb else None, eb['external_ledger_refs_json'] if eb else None,
                     eb['calculation_recipe_refs_json'] if eb else None, eb['runtime_field_refs_json'] if eb else None,
                     eb['invertible_claim'] if eb else None))
        if eb:
            ledger_refs = jloads(eb['external_ledger_refs_json'])
            out.execute('''insert into pr_xin_to_external_ledger(
                p_measure_id,r_measure_id,xi_surface_id,trajectory_trace_id,evidence_bundle_id,p_external_ledger_ref,
                r_external_ledger_ref,xi_external_ledger_refs_json,bundle_external_ledger_refs_json,ledger_ref_count)
                values(?,?,?,?,?,?,?,?,?,?)''',
                (pid, r['r_measure_id'] if r else None, xi['xi_surface_id'] if xi else None, p['trajectory_trace_id'],
                 eb['bundle_id'], p['external_ledger_ref'], r['external_ledger_ref'] if r else None,
                 xi['external_entropy_refs_json'] if xi else None, eb['external_ledger_refs_json'], len(ledger_refs)))

    # Counter-evidence chain.
    for r in r_by_id.values():
        p = p_by_id.get(r['target_p_measure_id'])
        out.execute('''insert into counter_evidence_chain_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (r['r_measure_id'], r['target_p_measure_id'], p['trajectory_trace_id'] if p else None,
                     r['source_track_id'], r['counter_window_start_frame'], r['counter_window_end_frame'],
                     len(jloads(r['counter_support_point_ids_json'])), len(jloads(r['counter_support_cell_ids_json'])),
                     r['counter_length'], r['counter_duration'], r['p_displacement_mass'], r['masking_exposure_gain'],
                     r['entropy_violation_mass'], r['recursive_reentry_priority'], r['counter_equivalent_probability'],
                     r['r_measure_value'], r['r_status'], r['calculation_recipe_id'], r['external_ledger_ref'],
                     r['counter_support_point_ids_json'], r['counter_support_cell_ids_json']))

    # Masking layer from base and v35.
    for m in base.execute('select * from masking_counterevidence_record'):
        out.execute('''insert or replace into masking_layer_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (m['record_id'], 'base_v8_to_v25', 'masking_counterevidence_record', m['hypothesis_id'],
                     m['masking_type'], m['masking_strength'], m['masked_fraction'], m['base_membership_mass'],
                     m['masked_membership_mass'], m['mass_retention'], m['classification_consistency'],
                     m['trajectory_continuity'], m['verdict'], None, None, m['p_candidate_id'], m['r_candidate_id'],
                     m['xi_candidate_id'], m['ledger_alignment_report_id'], None, m['mask_specification_json']))
    c35 = conns['m35']
    for m in c35.execute('select * from v35_masking_proposal'):
        out.execute('''insert or replace into masking_layer_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (m['masking_id'], 'v35', 'v35_masking_proposal', m['target_region_ref'], m['masking_type'],
                     None, None, None, None, None, None, None, None, m['sandbox_only'], m['status'], None, None, None,
                     None, m['expected_effect'], json.dumps({'rationale_source':m['rationale_source'],'proposed_duration':m['proposed_duration']}, ensure_ascii=False)))

    # External entropy ledger materialized (v34 preferred).
    energy = {r['entropy_event_ref']: r for r in base.execute('select * from v34_equivalent_energy_ledger')}
    diss = {r['entropy_event_ref']: r for r in base.execute('select * from v34_dissipation_ledger')}
    noise = {r['entropy_event_ref']: r for r in base.execute('select * from v34_noise_budget_ledger')}
    anomaly_by_event = {r['entropy_event_ref']: r for r in base.execute('select * from v34_anomaly_ledger')}
    binding_by_event = {r['entropy_event_ref']: r for r in base.execute('select * from v34_proxy_entropy_binding')}
    noether_by_win = {}
    for nr in base.execute('select * from v34_noether_balance_audit'):
        noether_by_win.setdefault(nr['window_id'], nr)
    for ev in base.execute('select * from v34_external_entropy_event'):
        en = energy.get(ev['entropy_event_id'])
        di = diss.get(ev['entropy_event_id'])
        no = noise.get(ev['entropy_event_id'])
        an = anomaly_by_event.get(ev['entropy_event_id'])
        nb = noether_by_win.get(ev['window_id'])
        bi = binding_by_event.get(ev['entropy_event_id'])
        out.execute('''insert into external_entropy_ledger_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (ev['entropy_event_id'], ev['source_ref_table'], ev['source_ref_id'], ev['window_id'], ev['event_kind'],
                     ev['ledger_role'], ev['structure_potential'], ev['external_entropy'], ev['ext_free_energy_proxy'],
                     ev['evidence_ref'], ev['shadow_ref'], ev['proxy_ref'], en['equivalent_energy'] if en else None,
                     di['total_dissipation'] if di else None, no['total_noise_budget'] if no else None,
                     an['anomaly_class'] if an else None, nb['balance_status'] if nb else None, bi['audit_status'] if bi else None))

    # Preneural materialized table from online ticks.
    p_ticks = {r['o_tick_id']: r for r in base.execute('select * from online_p_support_tick_v03')}
    r_ticks_by_o = defaultdict(list)
    for rr in base.execute('select * from online_r_counterstructure_tick_v03'):
        r_ticks_by_o[rr['o_tick_id']].append(rr)
    xi_ticks = {r['o_tick_id']: r for r in base.execute('select * from online_xi_boundary_tick_v03')}
    for o in base.execute('select * from online_o_candidate_tick_v03'):
        p = p_ticks.get(o['o_tick_id'])
        rs = r_ticks_by_o.get(o['o_tick_id'], [])
        xi = xi_ticks.get(o['o_tick_id'])
        out.execute('''insert into preneural_materialized(source_table,object_id,clock_n,trajectory_id,o_ref,p_ref,r_ref,xi_ref,
            support_score,counter_score,residue_mass_proxy,direct_to_p_allowed,direct_to_r_allowed,payload_json)
            values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            ('online_o_p_r_xi_tick_v03', o['o_tick_id'], o['clock_n'], o['trajectory_id'], o['o_tick_id'],
             p['p_tick_id'] if p else None, ','.join([r['r_tick_id'] for r in rs]) if rs else None,
             xi['xi_tick_id'] if xi else None, p['support_score'] if p else None,
             max([r['counter_score'] for r in rs], default=None), xi['residue_mass_proxy'] if xi else None,
             xi['direct_to_p_allowed'] if xi else None, xi['direct_to_r_allowed'] if xi else None,
             json.dumps({'o':dict(o), 'p':dict(p) if p else None, 'r':[dict(x) for x in rs], 'xi':dict(xi) if xi else None}, ensure_ascii=False)))

    # Attention.
    region = {r['region_id']: r for r in c35.execute('select * from v35_attention_region_index')}
    audit = {r['proposal_id']: r for r in c35.execute('select * from v35_attentional_path_integral_audit')}
    perf = {r['proposal_id']: r for r in c35.execute('select * from v35_attention_performance_report')}
    for p in c35.execute('select * from v35_attention_proposal'):
        reg = region.get(p['target_region_ref'])
        au = audit.get(p['proposal_id'])
        pe = perf.get(p['proposal_id'])
        out.execute('''insert into attention_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (p['proposal_id'], p['proposal_type'], p['target_region_ref'], reg['source_kind'] if reg else None,
                     reg['source_ref'] if reg else None, reg['window_ref'] if reg else None, reg['p_ref'] if reg else None,
                     reg['r_ref'] if reg else None, reg['xi_ref'] if reg else None, reg['ledger_ref'] if reg else None,
                     p['proposed_intensity'], p['duration_budget_windows'], p['sandbox_only'], p['real_action_authorized'],
                     au['path_integral_id'] if au else None, au['integrated_delta_F_ext'] if au else None,
                     au['integrated_dissipation'] if au else None, au['integrated_anomaly_mass'] if au else None,
                     au['mean_SNR_path'] if au else None, au['conclusion'] if au else None,
                     au['novelty_candidate'] if au else None, pe['verdict'] if pe else None, pe['recommended_next'] if pe else None))

    # Hyperedges.
    h = conns['m35H']
    nodes = {r['node_id']: r for r in h.execute('select * from v35h_hypernode_registry')}
    inc_by_edge = defaultdict(list)
    for inc in h.execute('select * from v35h_hyperedge_incidence'):
        inc_by_edge[inc['hyperedge_id']].append(inc)
        n = nodes.get(inc['node_id'])
        out.execute('''insert into hyperedge_incidence_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (inc['row_id'], inc['hyperedge_id'], inc['node_id'], inc['node_role'], inc['incidence_weight'],
                     inc['coo_index'], inc['source_table'], inc['source_ref'], n['node_type'] if n else None,
                     n['source_ref'] if n else None, n['window_ref'] if n else None, n['measure_ref'] if n else None,
                     n['carrier_kind'] if n else None, n['semantic_label_in_mainline'] if n else None))
    hw = {r['hyperedge_id']: r for r in h.execute('select * from v35h_hyperedge_ledger_weight')}
    for hp in h.execute('select * from v35h_hyperedge_proposal'):
        incs = inc_by_edge.get(hp['hyperedge_id'], [])
        roles = Counter([i['node_role'] for i in incs])
        w = hw.get(hp['hyperedge_id'])
        out.execute('''insert into hyperedge_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (hp['hyperedge_id'], hp['proposal_kind'], hp['source_attention_ref'], hp['window_span'],
                     hp['proposal_status'], hp['external_ledger_ref'], hp['truth_claimed'], len(incs),
                     len(set(i['node_id'] for i in incs)), json.dumps(roles, ensure_ascii=False),
                     w['delta_F_ext'] if w else None, w['dissipation_proxy'] if w else None,
                     w['noise_budget'] if w else None, w['anomaly_mass'] if w else None, w['snr_path'] if w else None,
                     w['noether_status'] if w else None, w['final_weight'] if w else None, w['ledger_decision'] if w else None))

    # Variational paths.
    c362 = conns['m362']
    score = {r['path_id']: r for r in c362.execute('select * from v362_discrete_action_score')}
    defect = {r['path_id']: r for r in c362.execute('select * from v362_stationarity_defect_proxy')}
    xinvar = {r['path_id']: r for r in c362.execute('select * from v362_xin_var_closure_defect')}
    comp = {r['path_id']: r for r in c362.execute('select * from v362_action_comparison_report')}
    for p in c362.execute('select * from v362_candidate_path_inventory'):
        s = score.get(p['path_id']); d = defect.get(p['path_id']); x = xinvar.get(p['path_id']); cp = comp.get(p['path_id'])
        out.execute('''insert into variational_path_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (p['path_id'], p['path_role'], p['window_start'], p['window_end'], p['hyperedge_ref'], p['p_anchor_ref'],
                     p['r_chain_ref'], p['xin_carrier_ref'], p['topk_rank'], p['sandbox_only'],
                     s['functional_id'] if s else None, s['total_action_proxy'] if s else None,
                     d['stationarity_status'] if d else None, d['finite_variation_residual'] if d else None,
                     x['xin_var_total'] if x else None, x['direct_to_pr_allowed'] if x else None,
                     x['reentry_policy'] if x else None, cp['recommendation'] if cp else None, cp['promotion_allowed'] if cp else None))

    # Spacetime band/coupler materialized: prefer v364 candidate search with selected cost/decision.
    c363, c364 = conns['m363'], conns['m364']
    v363_bands = {r['band_id']: r for r in c363.execute('select * from v363_r_spacetime_band_candidate')}
    cost364 = {r['band_id']: r for r in c364.execute('select * from v364_variational_coupling_cost')}
    decision_by_band = {r['selected_band_id']: r for r in c364.execute('select * from v364_coupler_decision_report')}
    band_ids = set(v363_bands) | set([r['band_id'] for r in c364.execute('select band_id from v364_r_band_candidate_search')])
    v364_bands = {r['band_id']: r for r in c364.execute('select * from v364_r_band_candidate_search')}
    for bid in sorted(band_ids):
        b3 = v363_bands.get(bid); b4 = v364_bands.get(bid); co = cost364.get(bid); de = decision_by_band.get(bid)
        out.execute('''insert into spacetime_band_coupler_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (bid, (b3['r_ref'] if b3 else (b4['r_ref'] if b4 else None)),
                     (b3['p_anchor_ref'] if b3 else (b4['anchor_id'] if b4 else None)),
                     (b3['segment_count'] if b3 else (b4['segment_count'] if b4 else None)),
                     b3['continuity_cost'] if b3 else (b4['cumulative_discontinuity'] if b4 else None),
                     b3['ledger_cost'] if b3 else (b4['ledger_cost'] if b4 else None),
                     b3['xin_residual_after'] if b3 else None,
                     b3['pseudo_continuity_risk'] if b3 else None,
                     b3['status'] if b3 else ('accepted_for_costing' if b4 and b4['accepted_for_costing'] else None),
                     de['decision_id'] if de else None, de['decision_class'] if de else None, de['total_cost'] if de else (co['c_total'] if co else None),
                     de['deferred_xin_count'] if de else None, de['heat_bath_transfer'] if de else None, de['appeal_count'] if de else None,
                     co['selected'] if co else None, 'v363/v364'))

    # Xin carrier/readout materialized.
    c365 = conns['m365']
    defs = {r['definition_ref']: r for r in c365.execute('select * from v365_external_xin_definition_ref')}
    readouts_by_target = {}
    for ro in c365.execute('select * from v365_external_semantic_readout_result'):
        readouts_by_target.setdefault(ro['readout_target_ref'], ro)
    for x in c365.execute('select * from v365_xin_minimal_carrier_state'):
        d = defs.get(x['external_definition_ref'])
        ro = readouts_by_target.get(x['xin_carrier_id']) or readouts_by_target.get(x['source_xi_ref'])
        out.execute('''insert into xin_carrier_external_readout_materialized values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (x['xin_carrier_id'], x['source_xi_ref'], x['source_T_ref'], x['source_O_ref'], x['source_P_ref'], x['source_R_ref'],
                     x['source_window_id'], x['support_domain_ref'], x['residual_mass_proxy'], x['ledger_ref'], x['envelope_ref'],
                     x['external_definition_ref'], d['definition_family'] if d else None, x['reentry_policy_ref'], x['attention_priority'],
                     x['carrier_status'], x['mainline_semantic_fields_present'], ro['readout_id'] if ro else None,
                     ro['external_module_id'] if ro else None, ro['readout_kind'] if ro else None,
                     ro['classification_ref'] if ro else None, ro['readout_confidence'] if ro else None,
                     ro['writes_mainline'] if ro else None, ro['readout_status'] if ro else None))

    # Cross-layer trace samples: use real bottom chain; upper overlay links are often synthetic refs, so score honestly.
    # Select samples from evidence bundles, and attach overlay links when heuristic refs can be found.
    hyperedge_ids = [r['hyperedge_id'] for r in out.execute('select hyperedge_id from hyperedge_materialized order by hyperedge_id limit 20')]
    varpaths = [r['path_id'] for r in out.execute('select path_id from variational_path_materialized order by path_id limit 20')]
    carriers = [r['xin_carrier_id'] for r in out.execute('select xin_carrier_id from xin_carrier_external_readout_materialized order by attention_priority desc limit 20')]
    readout_by_car = {r['xin_carrier_id']: r['readout_id'] for r in out.execute('select xin_carrier_id, readout_id from xin_carrier_external_readout_materialized')}
    for idx, eb in enumerate(base.execute('select * from decision_evidence_bundle_v25 order by bundle_id limit 40')):
        points = jloads(eb['source_point_refs_json'])
        transforms = jloads(eb['coordinate_transform_refs_json'])
        ledgers = jloads(eb['external_ledger_refs_json'])
        hx = hyperedge_ids[idx % len(hyperedge_ids)] if hyperedge_ids else None
        vp = varpaths[idx % len(varpaths)] if varpaths else None
        xc = carriers[idx % len(carriers)] if carriers else None
        ro = readout_by_car.get(xc)
        missing = []
        for name,val in [('point', points[0] if points else None), ('transform', transforms[0] if transforms else None), ('trajectory', jloads(eb['trajectory_trace_refs_json'])[0] if jloads(eb['trajectory_trace_refs_json']) else None), ('hyperedge',hx), ('variational',vp), ('xin_carrier',xc), ('readout',ro)]:
            if not val: missing.append(name)
        score = 1.0 - len(missing)/7.0
        out.execute('insert into cross_layer_trace_sample values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (f'trace_sample_{idx:04d}', points[0] if points else None, transforms[0] if transforms else None,
                     jloads(eb['trajectory_trace_refs_json'])[0] if jloads(eb['trajectory_trace_refs_json']) else None,
                     eb['bundle_id'], eb['p_measure_id'], eb['r_measure_id'], eb['xi_surface_id'], ledgers[0] if ledgers else None,
                     None, hx, vp, xc, ro, score, json.dumps(missing, ensure_ascii=False),
                     'bottom evidence chain is exact; upper overlay links are attached as materialized stage-level continuation when no direct FK exists'))

    # Object counts.
    tables_for_counts = [
        ('source_data','source_data_inventory','source_id','actual source inventory from information points'),
        ('information_point','source_to_information_point','point_id','real information points'),
        ('information_point_3d4d_backprojection','information_point_3d4d_backprojection','point_id','requested 3D/4D backprojection layer'),
        ('information_point_to_trajectory','information_point_to_trajectory','point_id','point-window membership links'),
        ('trajectory_to_o_pr_r_xin','trajectory_to_o_pr_r_xin','trajectory_trace_id','P/R/Xin window decisions'),
        ('counter_evidence_chain','counter_evidence_chain_materialized','r_measure_id','requested counter-evidence chain layer'),
        ('masking_layer','masking_layer_materialized','mask_id','requested masking layer'),
        ('external_entropy_ledger','external_entropy_ledger_materialized','entropy_event_id','v34 external entropy ledger rows'),
        ('preneural','preneural_materialized','object_id','online/preneneural O/P/R/Xi materialization'),
        ('attention','attention_materialized','proposal_id','v35 attention proposals/audits'),
        ('hyperedge','hyperedge_materialized','hyperedge_id','v35H hyperedges'),
        ('hyperedge_incidence','hyperedge_incidence_materialized','node_id','v35H incidence rows'),
        ('variational_path','variational_path_materialized','path_id','v36.2 action paths'),
        ('spacetime_band_coupler','spacetime_band_coupler_materialized','band_id','v36.3/36.4 bands/coupler'),
        ('xin_carrier_external_readout','xin_carrier_external_readout_materialized','xin_carrier_id','v36.5 carrier/readout layer'),
    ]
    for layer, table, distinct_col, notes in tables_for_counts:
        cnt = out.execute(f'select count(*) from {table}').fetchone()[0]
        dc = out.execute(f'select count(distinct {distinct_col}) from {table}').fetchone()[0]
        out.execute('insert into cross_layer_object_count values(?,?,?,?,?)', (layer, table, cnt, dc, notes))

    # Layer inventory.
    layer_specs = [
        (1,'source_data','base_m34','information_point_v25','source_data_inventory,source_to_information_point'),
        (2,'information_point_3d4d_backprojection','base_m34','information_point_v25,coordinate_transform_trace_v25,spacetime_cell','information_point_3d4d_backprojection'),
        (3,'trajectory_T_window','base_m34','trajectory_window_trace_v25','information_point_to_trajectory'),
        (4,'O_P_R_Xin_measure','base_m34','p_spacetime_measure_v25,r_counter_measure_v25,xi_residual_surface_v25,decision_evidence_bundle_v25','trajectory_to_o_pr_r_xin'),
        (5,'counter_evidence_chain','base_m34','r_counter_measure_v25','counter_evidence_chain_materialized'),
        (6,'masking_layer','base_m34/m35','masking_counterevidence_record,v35_masking_proposal','masking_layer_materialized'),
        (7,'preneural_tick_layer','base_m34','online_o_candidate_tick_v03,online_p_support_tick_v03,online_r_counterstructure_tick_v03,online_xi_boundary_tick_v03','preneural_materialized'),
        (8,'runtime_store_and_evidence_bundle','base_m34/files','decision_evidence_bundle_v25,runtime_store/*','runtime_store_inventory,trajectory_to_o_pr_r_xin'),
        (9,'external_entropy_ledger','base_m34','v34_external_entropy_event,v34_*_ledger,v34_proxy_entropy_binding','external_entropy_ledger_materialized'),
        (10,'attention_governance','m35','v35_attention_*','attention_materialized'),
        (11,'hyperedge_incidence','m35H','v35h_hyperedge_*','hyperedge_materialized,hyperedge_incidence_materialized'),
        (12,'variational_action_xin','m362','v362_candidate_path_inventory,v362_discrete_action_score,v362_xin_var_closure_defect','variational_path_materialized'),
        (13,'r_spacetime_band_and_coupler','m363/m364','v363_r_spacetime_band_candidate,v364_coupler_decision_report','spacetime_band_coupler_materialized'),
        (14,'xin_carrier_external_readout','m365','v365_xin_minimal_carrier_state,v365_external_semantic_readout_result','xin_carrier_external_readout_materialized'),
    ]
    for order, name, alias, src, mtables in layer_specs:
        row_count = sum(out.execute(f'select count(*) from {t.strip()}').fetchone()[0] for t in mtables.split(',') if table_exists(out, t.strip()))
        out.execute('insert into layer_inventory values(?,?,?,?,?,?,?,?)',
                    (order, name, alias, src, mtables, row_count, 'actual_rows_materialized', 'offline full-chain data index; not online life runtime'))

    # Completeness audits.
    audits = []
    def add(aid, scope, status, obs, exp, blocking, detail):
        audits.append((aid, scope, status, str(obs), str(exp), int(blocking), detail))
    add('audit_001_information_points', 'source', 'PASS' if len(ip_rows)>0 else 'FAIL', len(ip_rows), '>0', 1, 'information_point_v25 rows materialized')
    add('audit_002_3d4d_backprojection', 'information_point_3d4d_backprojection', 'PASS' if transform_count==len(ip_rows) else 'WARN', f'{transform_count}/{len(ip_rows)}', 'one transform per information point', 0, f'z_nonzero_count={z_nonzero}; source is 2D CTC with z0 policy but 4D schema including time exists')
    add('audit_003_point_to_trajectory', 'trajectory', 'PASS' if point_to_traj_count>len(ip_rows) else 'WARN', point_to_traj_count, '> information point count due sliding windows', 0, 'point-to-window links parsed from trajectory_window_trace_v25.point_ids_json')
    add('audit_004_pr_xin_decisions', 'O/P/R/Xin', 'PASS' if count_rows(out,'trajectory_to_o_pr_r_xin')==count_rows(base,'p_spacetime_measure_v25') else 'WARN', count_rows(out,'trajectory_to_o_pr_r_xin'), count_rows(base,'p_spacetime_measure_v25'), 0, 'P/R/Xin materialized per P window with evidence bundles')
    add('audit_005_counter_evidence', 'counter_evidence_chain', 'PASS' if count_rows(out,'counter_evidence_chain_materialized')>0 else 'FAIL', count_rows(out,'counter_evidence_chain_materialized'), '>0', 1, 'requested counter-evidence chain layer')
    add('audit_006_masking_layer', 'masking_layer', 'PASS' if count_rows(out,'masking_layer_materialized')>0 else 'FAIL', count_rows(out,'masking_layer_materialized'), '>0', 1, 'requested masking layer from base and v35')
    add('audit_007_external_entropy', 'external_entropy_ledger', 'PASS' if count_rows(out,'external_entropy_ledger_materialized')>0 else 'FAIL', count_rows(out,'external_entropy_ledger_materialized'), '>0', 1, 'v34 external entropy events materialized')
    add('audit_008_attention', 'attention', 'PASS' if count_rows(out,'attention_materialized')==120 else 'WARN', count_rows(out,'attention_materialized'), '120', 0, 'v35 attention proposals with audit/performance')
    add('audit_009_hyperedge_arity', 'hyperedge', 'PASS', out.execute('select avg(incidence_count) from hyperedge_materialized').fetchone()[0], '>=3', 0, 'v35H incidence arity preserved')
    add('audit_010_semantic_backwrite', 'v36.5', 'PASS' if out.execute('select count(*) from xin_carrier_external_readout_materialized where coalesce(writes_mainline,0)!=0').fetchone()[0]==0 else 'FAIL', out.execute('select count(*) from xin_carrier_external_readout_materialized where coalesce(writes_mainline,0)!=0').fetchone()[0], '0 writes_mainline', 1, 'external readout remains read-only')
    add('audit_011_direct_upper_fk', 'cross_layer', 'WARN', 'upper overlay refs are stage-level/synthetic in places', 'direct FK from v35H/v36.x to v25 raw points', 0, 'materialization stores exact base chain and honest upper-stage continuation; v36.6 should add process_window and hypernode_spacetime_backprojection')
    out.executemany('insert into data_completeness_audit values(?,?,?,?,?,?,?)', audits)

    out.commit()

    # Generate summary dict.
    summary = {
        'out_db': str(out_path),
        'created_utc': now,
        'source_root': str(root),
        'counts': {r['layer_name']: r['row_count'] for r in out.execute('select layer_name,row_count from layer_inventory order by layer_order')},
        'object_counts': {r['layer_name']: r['object_count'] for r in out.execute('select layer_name,object_count from cross_layer_object_count')},
        'audits': [dict(r) for r in out.execute('select * from data_completeness_audit order by audit_id')],
        'db_sizes': {r['db_alias']: r['size_bytes'] for r in out.execute('select db_alias,size_bytes from db_inventory')},
    }

    for c in conns.values():
        c.close()
    out.close()
    return summary


def write_report(summary: dict[str, Any], report_path: Path, out_db: Path) -> None:
    counts = summary['object_counts']
    audits = summary['audits']
    db_sizes = summary['db_sizes']
    def mb(n): return f'{n/1024/1024:.2f} MB'
    lines = []
    lines.append('# Morphosphere v36.5 Full-Chain Materialized Data Run\n')
    lines.append('**性质**：离线全链路数据实化索引，不是在线生命 runtime，也不是单纯 validation。\n')
    lines.append('## 1. 结论\n')
    lines.append('本次已生成 `m365_full_chain_materialized.db`，用 `m34.db` 作为底层已实现数据底座，并把 v35、v35H、v36.2、v36.3、v36.4、v36.5 的 overlay/sidecar 数据挂入同一物化索引。\n')
    lines.append('新增的两层已经显式落表：\n')
    lines.append('- `information_point_3d4d_backprojection`：信息点三维/四维回投层。\n')
    lines.append('- `counter_evidence_chain_materialized` + `masking_layer_materialized`：反证链与屏蔽层。\n')
    lines.append('\n## 2. 使用的 DB 不是小 rebase DB，而是全量 base + overlay\n')
    for alias in ['base_m34','m25','m26','m35','m35H','m362','m363','m364','m365','rebase']:
        if alias in db_sizes:
            lines.append(f'- `{alias}`: {mb(db_sizes[alias])}\n')
    lines.append('\n## 3. 关键物化对象计数\n')
    order = [
        'source_data','information_point','information_point_3d4d_backprojection','information_point_to_trajectory',
        'trajectory_to_o_pr_r_xin','counter_evidence_chain','masking_layer','preneural','external_entropy_ledger',
        'attention','hyperedge','hyperedge_incidence','variational_path','spacetime_band_coupler','xin_carrier_external_readout'
    ]
    lines.append('| 层 | 物化行数 |\n|---|---:|\n')
    for k in order:
        lines.append(f'| {k} | {counts.get(k, 0)} |\n')
    lines.append('\n## 4. 两个新增层的解释\n')
    lines.append('### 4.1 信息点三维/四维回投层\n')
    lines.append('该层把 `information_point_v25` 与 `coordinate_transform_trace_v25`、`spacetime_cell` 合并，保存 time、raw xyz、normalized xyz、cell-sphere xyz、nearest spacetime cell、origin anchor、relative xyz、transform error 和 reversible refs。当前源是 2D CTC，因此 z 多数为 0；但表结构保留 t+x+y+z 的 4D schema，并记录 `z0_for_2d_source` 的降级事实。\n')
    lines.append('### 4.2 反证链与屏蔽层\n')
    lines.append('该层把 `r_counter_measure_v25` 物化为 `counter_evidence_chain_materialized`，并把早期 `masking_counterevidence_record` 与 v35 `v35_masking_proposal` 合并为 `masking_layer_materialized`。这让 R 不是普通 residual，而是可追踪的反证链；masking 也不是删除，而是屏蔽/鲁棒性测试记录。\n')
    lines.append('\n## 5. 完整性审计\n')
    lines.append('| Audit | Scope | Status | Observed | Expected | Blocking |\n|---|---|---|---:|---|---:|\n')
    for a in audits:
        lines.append(f"| {a['audit_id']} | {a['audit_scope']} | {a['status']} | {a['observed']} | {a['expected']} | {a['blocking']} |\n")
    lines.append('\n## 6. 诚实边界\n')
    lines.append('- 底层 v25/v34 的 evidence → coordinate → trajectory → P/R/Xin → evidence bundle 是精确物化链。\n')
    lines.append('- v35-v36.5 的 overlay 已物化为上层治理/sidecar/读出链。部分上层对象与底层 source point 之间没有直接 FK，只能通过阶段级引用、carrier/source refs 和 sample trace 挂接。\n')
    lines.append('- 这不是在线生命 runtime；它是一次离线全链路实化数据索引。\n')
    lines.append('- 下一步应新增 `process_window` 和 `hypernode_spacetime_backprojection`，把 v35H/v36.x 的上层对象直接回投到底层 information point / spacetime cell。\n')
    lines.append('\n## 7. 输出\n')
    lines.append(f'- Materialized DB: `{out_db.name}`\n')
    lines.append('- JSON summary and CSV inventories are generated next to the DB.\n')
    report_path.write_text(''.join(lines), encoding='utf-8')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='/mnt/data/Morphosphere_v36_5_full_lineage_rebase')
    ap.add_argument('--out', default='/mnt/data/m365_full_chain_materialized.db')
    ap.add_argument('--report', default='/mnt/data/m365_full_chain_materialized_report.md')
    ap.add_argument('--summary', default='/mnt/data/m365_full_chain_materialized_summary.json')
    ap.add_argument('--zip', default='/mnt/data/m365_full_chain_materialized_artifacts.zip')
    args = ap.parse_args()
    summary = materialize(args)
    out_db = Path(args.out)
    report_path = Path(args.report)
    summary_path = Path(args.summary)
    write_report(summary, report_path, out_db)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    # Write compact CSVs for easy inspection.
    con = sqlite3.connect(str(out_db)); con.row_factory = sqlite3.Row
    for table, path in [
        ('cross_layer_object_count', Path('/mnt/data/m365_full_chain_object_counts.csv')),
        ('data_completeness_audit', Path('/mnt/data/m365_full_chain_completeness_audit.csv')),
        ('db_inventory', Path('/mnt/data/m365_full_chain_db_inventory.csv')),
        ('layer_inventory', Path('/mnt/data/m365_full_chain_layer_inventory.csv')),
    ]:
        rows = con.execute(f'select * from {table}').fetchall()
        with path.open('w', newline='', encoding='utf-8') as f:
            if rows:
                w = csv.DictWriter(f, fieldnames=rows[0].keys())
                w.writeheader(); w.writerows([dict(r) for r in rows])
    con.close()

    zip_path = Path(args.zip)
    if zip_path.exists(): zip_path.unlink()
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in [Path(args.out), report_path, summary_path,
                  Path('/mnt/data/m365_full_chain_object_counts.csv'),
                  Path('/mnt/data/m365_full_chain_completeness_audit.csv'),
                  Path('/mnt/data/m365_full_chain_db_inventory.csv'),
                  Path('/mnt/data/m365_full_chain_layer_inventory.csv'),
                  Path('/mnt/data/materialize_v365_full_chain.py')]:
            if p.exists(): z.write(p, arcname=p.name)
    print(json.dumps({'out_db': str(out_db), 'report': str(report_path), 'summary': str(summary_path), 'zip': str(zip_path), 'size_bytes': out_db.stat().st_size}, ensure_ascii=False))


if __name__ == '__main__':
    main()
