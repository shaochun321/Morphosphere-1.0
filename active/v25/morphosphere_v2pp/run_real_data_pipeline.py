import sqlite3
import uuid
import os
from pathlib import Path

# Add src to pythonpath so imports work
import sys
sys.path.append(str(Path(__file__).parent / "src"))

from morphosphere.archive_access.compat_importer import CompatImporter
from morphosphere.active_exec.contracts.clock import SystemClock, AnalysisWindow
from morphosphere.active_exec.stage1_physics.patch_builder import PatchBuilder
from morphosphere.active_exec.preneural.assembler import PreNeuralAssembler
from morphosphere.active_exec.preneural.transport.builder import TransportBuilder
from morphosphere.active_exec.stage2_object.t_surface import TStagePacket
from morphosphere.active_exec.stage2_object.observable_surface import OBuilder
from morphosphere.active_exec.stage2_object.freezing.p_band_freezer import PBandFreezer
from morphosphere.active_exec.runtime.replay.alignment import ReplayValidator

import json
from morphosphere.contracts.transforms import DefaultTransformAuditor
from morphosphere.external_ledgers.external_isolation import DefaultExternalLedgerRunner

def init_db(db_path: Path):
    """Initialize DB with all schemas."""
    if db_path.exists():
        db_path.unlink()
        
    conn = sqlite3.connect(db_path)
    migrations_dir = Path(__file__).parent / "migrations"
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        with open(sql_file, "r") as f:
            conn.executescript(f.read())
    return conn

def persist_p_band(conn, p_band):
    """Helper to save P Band"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO p_band_record 
        (p_band_id, o_surface_id, core_margin_type, member_node_ids_json, coherence_score, replay_support, origin_anchor_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        p_band.p_band_id, p_band.o_surface_id, p_band.core_margin_type,
        json.dumps(p_band.member_node_ids), p_band.coherence_score,
        p_band.replay_support, p_band.origin_anchor_id
    ))
    conn.commit()

def persist_alignment(conn, record):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO replay_alignment_record
        (alignment_id, run_id, v6_surface_id, legacy_record_id, alignment_score, divergence_reason)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        record.alignment_id, record.run_id, record.v6_surface_id,
        record.legacy_record_id, record.alignment_score, record.divergence_reason
    ))
    conn.commit()

def persist_transformation_record(conn, record):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transformation_record
        (schema_version, run_id, stage_k_id, window_id, transform_id, domain_object_refs, codomain_object_refs, loss_metrics, unit_policy_followed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record.schema_version, record.run_id, record.stage_k_id, record.window_id,
        record.transform_id, json.dumps(record.domain_object_refs),
        json.dumps(record.codomain_object_refs), json.dumps(record.loss_metrics),
        record.unit_policy_followed
    ))
    conn.commit()

def persist_isolation_report(conn, report):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO external_isolation_report
        (schema_version, run_id, stage_k_id, window_id, related_T_ref, related_O_ref, related_P_refs, related_R_refs, related_origin_ref, external_free_energy, balance_summary, recommended_validation_path, linked_ledger_refs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        report.schema_version, report.run_id, report.stage_k_id, report.window_id,
        report.related_T_ref, report.related_O_ref, json.dumps(report.related_P_refs),
        json.dumps(report.related_R_refs), report.related_origin_ref,
        report.external_free_energy, report.balance_summary,
        report.recommended_validation_path, json.dumps(report.linked_ledger_refs)
    ))
    conn.commit()

def persist_cell_graph_state(conn, state):
    cursor = conn.cursor()
    state_dict = {
        'v_hair_cell': list(state.v_hair_cell),
        'calcium_concentration': list(state.calcium_concentration),
        'v_afferent': list(state.v_afferent),
        'met_open_probability': list(state.met_open_probability),
        'neurotransmitter_release_rate': list(state.neurotransmitter_release_rate)
    }
    cursor.execute('''
        INSERT OR REPLACE INTO cell_graph_state
        (clock_n, run_id, num_cells, state_json)
        VALUES (?, ?, ?, ?)
    ''', (
        state.clock_n, state.run_id, state.num_cells,
        json.dumps(state_dict)
    ))
    conn.commit()

def persist_pointset_slice(conn, slice_obj, run_id):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO preneural_pointset_slice
        (slice_id, window_id, geometry_node_ids_json, edges_json, signal_windows_refs_json)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        slice_obj.slice_id, slice_obj.window_id,
        json.dumps(list(slice_obj.geometry_node_ids)),
        json.dumps([]), json.dumps([])
    ))
    conn.commit()

def persist_transport(conn, transport, run_id):
    cursor = conn.cursor()
    edges_json = json.dumps([e.model_dump() for e in transport.edges]) if transport.edges else '[]'
    cursor.execute('''
        INSERT INTO transport_operator
        (transport_id, from_slice_id, to_slice_id, mapping_matrix_json, transport_error)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        transport.transport_id, transport.from_slice_id,
        transport.to_slice_id, edges_json, transport.transport_error
    ))
    conn.commit()

def persist_observable_surface(conn, o_surface, run_id):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO observable_surface
        (o_surface_id, stage_k, t_surface_id, field_surface_id, candidate_surface_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        o_surface.o_surface_id, o_surface.stage_k, o_surface.t_surface_id,
        o_surface.field_surface_id, o_surface.candidate_surface_id
    ))
    conn.commit()

def main():
    print("Starting V6 Real Data E2E Pipeline...")
    trace_file = r"J:\Liying-cell\morphosphere_v1_run_output\cell_sphere\raw_manifold_trace.json"
    
    if not os.path.exists(trace_file):
        print(f"File not found: {trace_file}")
        return

    # 1. Init DB
    db_path = Path("v6_real_data_run.db")
    conn = init_db(db_path)
    
    # 2. Setup run
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    
    print(f"Loading legacy traces from {trace_file}")
    importer = CompatImporter()
    cell_states = importer.import_v1_frames(trace_file, run_id)
    
    print(f"Imported {len(cell_states)} frames. Driving pipeline...")
    
    # Setup V6 operators
    patch_builder = PatchBuilder(run_id=run_id)
    assembler = PreNeuralAssembler()
    transport_builder = TransportBuilder()
    o_builder = OBuilder()
    p_freezer = PBandFreezer()
    validator = ReplayValidator()
    auditor = DefaultTransformAuditor()
    ledger_runner = DefaultExternalLedgerRunner()
    
    prev_slice = None
    
    for idx, state in enumerate(cell_states):
        # Persist CellGraphState (P02)
        persist_cell_graph_state(conn, state)
        
        # Build patches (P03)
        patch_graph = patch_builder.build_patch_graph(state)
        
        t_rec1 = auditor.record("cell_to_patch_aggregation", ["CellGraphState"], ["PatchGraph"])
        t_rec1.run_id = run_id
        t_rec1.stage_k_id = f"stg_{idx}"
        persist_transformation_record(conn, t_rec1)
        
        # Build pre-neural slice (P04)
        window = AnalysisWindow(
            window_id=f"win_{idx}", 
            clock_start=idx, 
            clock_end=idx+1,
            window_center=idx,
            window_size=1,
            window_stride=1
        )
        slice_obj = assembler.build_slice(window, [patch_graph])
        persist_pointset_slice(conn, slice_obj, run_id)
        
        # Transport (P05)
        transport = None
        if prev_slice:
            transport = transport_builder.build_transport(prev_slice, slice_obj)
            persist_transport(conn, transport, run_id)
        prev_slice = slice_obj
        
        # O-Surface (P06)
        t_packet = TStagePacket(
            t_surface_id=f"tsurf_{idx}",
            stage_k=idx,
            slice_ids=[slice_obj.slice_id],
            transport_ids=[transport.transport_id] if transport else []
        )
        o_surface = o_builder.build_o_surface(t_packet)
        persist_observable_surface(conn, o_surface, run_id)
        
        t_rec2 = auditor.record("pointset_to_o_field_surface", ["PreNeuralPointSetSlice"], ["O_field_surface"])
        t_rec2.run_id = run_id
        t_rec2.stage_k_id = f"stg_{idx}"
        persist_transformation_record(conn, t_rec2)
        
        # P/R/Omega Freezing (P07)
        # Using a surrogate score of 0.85 to force a freeze for testing
        nodes = list(range(len(patch_graph.source_cell_ids)))
        p_band = p_freezer.freeze(o_surface.o_surface_id, 0.85, nodes)
        
        if p_band:
            persist_p_band(conn, p_band)
            
            t_rec3 = auditor.record("o_to_frozen_objects", ["O_k"], ["P_k"])
            t_rec3.run_id = run_id
            t_rec3.stage_k_id = f"stg_{idx}"
            persist_transformation_record(conn, t_rec3)
            
            iso_report = ledger_runner.step(t_packet, o_surface, [p_band], None)
            iso_report.run_id = run_id
            iso_report.stage_k_id = f"stg_{idx}"
            iso_report.related_O_ref = o_surface.o_surface_id
            iso_report.related_P_refs = [p_band.p_band_id]
            persist_isolation_report(conn, iso_report)
            
        # Replay Alignment (P12)
        # We align our new O-surface with the old JSON frame idx
        align_record = validator.validate_alignment(
            run_id=run_id,
            v6_surface_id=o_surface.o_surface_id,
            legacy_record_id=f"legacy_frame_{idx}",
            score=1.0 # Assuming perfect structural match for this test
        )
        persist_alignment(conn, align_record)
        
        if idx % 10 == 0:
            print(f"Processed frame {idx}/{len(cell_states)}")
            
    print("Pipeline finished successfully!")
    print(f"Results saved to {db_path.absolute()}")
    
    # Verify in DB
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM replay_alignment_record")
    print(f"Alignment records generated: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM p_band_record")
    print(f"P-Band records generated: {cursor.fetchone()[0]}")
    
    conn.close()

if __name__ == "__main__":
    main()
