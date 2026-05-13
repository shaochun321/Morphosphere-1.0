import sqlite3
import uuid
import os
import json
import math
from pathlib import Path
import sys

# Add src to pythonpath so imports work
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR / "src"))

# V37.0 Native Runtime Engines
from morphosphere.active_exec.runtime.spms.binding import SPMSBinder
from morphosphere.active_exec.runtime.spms.engines import ConfirmationGraphEngine, FreeEnergyRouter, PerturbationExecutor
from morphosphere.active_exec.runtime.xi.decay_engine import XiDecayEngine
from morphosphere.active_exec.runtime.spms.variational import VariationalXinEngine, InformationEnergyMetricEngine

def init_db(db_path: Path):
    """Initialize DB with all schemas."""
    if db_path.exists():
        db_path.unlink()
        
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    migrations_dir = BASE_DIR / "migrations"
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        try:
            with open(sql_file, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
        except sqlite3.OperationalError as e:
            print(f"Executescript failed in {sql_file.name}: {e}")
            raise
            
    conn.commit()
    return conn

# ── Data Adapter ──────────────────────────────────────────
class RealDataNode:
    def __init__(self, nid, cell_data):
        # Geometry
        self.position = cell_data.get("position", (math.cos(nid), math.sin(nid), 0.1*nid))
        self.surface_normal = cell_data.get("normal", (0, 0, 1))
        self.boundary_distance = cell_data.get("boundary_distance", 0.5)
        self.support_radius = cell_data.get("support_radius", 1.0)
        self.neighbor_ids = cell_data.get("neighbors", [(nid-1)%50, (nid+1)%50])
        self.source_patch_ids = [nid]
        
        # Signal mapping from legacy physics
        self.V_mean = cell_data.get("v_hair_cell", -60.0)
        self.V_slope = cell_data.get("dv_dt", 0.0)
        self.release_proxy = cell_data.get("neurotransmitter_release_rate", 0.0)
        self.afferent_current = cell_data.get("v_afferent", 0.0)
        self.spike_rate = cell_data.get("spike_rate", 10.0)
        self.spike_regularity = 0.8
        self.timing_precision = 0.9
        self.adaptation_state = cell_data.get("calcium_concentration", 0.1)

class RealDataSlice:
    def __init__(self, k, states):
        self.slice_id = f"real_slice_{k}"
        self.window_id = f"w_{k}"
        self.stage_k = k
        self.geometry_node_ids = list(range(len(states)))
        self.geometry_nodes = [RealDataNode(i, st) for i, st in enumerate(states)]
        self.signal_windows = self.geometry_nodes  # shared in this adapter

def generate_mock_trace(num_frames=5, num_cells=50):
    """Fallback generator if real JSON trace is missing."""
    frames = []
    for f in range(num_frames):
        cells = []
        for i in range(num_cells):
            cells.append({
                "v_hair_cell": -65.0 + 5.0 * math.sin(f + i*0.1),
                "neurotransmitter_release_rate": max(0, math.sin(f + i*0.1)),
                "calcium_concentration": 0.1 * f,
                "v_afferent": -70.0 + f,
                "position": (math.cos(i)*f, math.sin(i)*f, 0)
            })
        frames.append(cells)
    return frames

def main():
    print("Starting V37.0 Native Runtime Real Data E2E Pipeline...")
    trace_file = r"J:\Liying-cell\morphosphere_v1_run_output\cell_sphere\raw_manifold_trace.json"
    
    if os.path.exists(trace_file):
        print(f"Loading real legacy traces from {trace_file}")
        with open(trace_file, "r") as f:
            raw_frames = json.load(f)
    else:
        print(f"File not found: {trace_file}. Using synthetic mock trace for pipeline testing.")
        raw_frames = generate_mock_trace()

    # 1. Init DB
    db_path = Path("v37_real_data_run.db")
    conn = init_db(db_path)
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    
    # Register run in manifest to satisfy foreign keys
    conn.execute(
        "INSERT INTO run_manifest (run_id, rules_version, created_at) VALUES (?, ?, ?)", 
        (run_id, "v37.0", "2026-05-08T00:00:00Z")
    )
    conn.commit()
    
    print(f"Processing {len(raw_frames)} frames through Phase 1-6 native engines...")
    
    # 2. Setup V37 Native Engines
    spms_binder = SPMSBinder(conn, run_id=run_id, calibration_profile="real_data")
    conf_engine = ConfirmationGraphEngine(conn, run_id=run_id)
    xi_engine = XiDecayEngine(conn, run_id=run_id, decay_rate=0.2)
    router = FreeEnergyRouter(conn, run_id=run_id)
    executor = PerturbationExecutor(conn, run_id=run_id, seed=42)
    var_engine = VariationalXinEngine(conn, run_id=run_id)
    ie_engine = InformationEnergyMetricEngine(conn, run_id=run_id)
    
    all_maps = {}
    prev_uids = None
    
    for idx, frame_cells in enumerate(raw_frames):
        window_id = f"w_{idx}"
        
        # Phase 1: SPMS Binding
        slice_obj = RealDataSlice(idx, frame_cells)
        uid_map = spms_binder.bind_slice(slice_obj)
        all_maps[idx] = uid_map
        curr_uids = list(uid_map.values())
        
        # Create transport edges (OT mock) from prev frame
        if prev_uids:
            for i in range(min(len(prev_uids), len(curr_uids))):
                w = 0.5 + 0.3 * math.sin(0.2*i + idx)
                conn.execute(
                    "INSERT INTO transport_current_edge (edge_id,run_id,from_cell_uid,to_cell_uid,transport_weight,accepted,total_cost) VALUES (?,?,?,?,?,?,?)",
                    (f"tce_{idx}_{i}", run_id, prev_uids[i], curr_uids[i], w, 1, 0.1*i)
                )
        prev_uids = curr_uids
        conn.commit()
        
        # Phase 2: Confirmation Graph (Find structure candidates)
        if len(curr_uids) >= 10:
            h_strong = spms_binder.bind_hypothesis("P_candidate", idx, curr_uids[:5], 0.8)
            conf_engine.attempt_transition(h_strong, "PR_candidate", force=True)
            
            # Phase 5: Perturbation Masking (Validate structure)
            executor.run_masking_suite(h_strong)
        
        # Phase 3: Xi Decay Dynamics (Unexplained residuals)
        xi_noise = xi_engine.create_xi_from_residual(f"h_noise_{idx}", "stochastic_noise", 0.5)
        xi_engine.step_window(window_k=idx)
        
        # Phase 4: Free-Energy Routing
        router.route_delta_f(
            delta_f_ext=5.0+idx, window_id=window_id,
            p_mass=0.5, p_stability=0.4, r_counter=0.3, r_boundary=0.2,
            xi_carry_cost=0.35, xi_mass=0.4, anomaly_mass=0.15,
            async_phase_depth=0.2, p_compression_gain=0.25, masking_pressure=0.3, anomaly_unresolved=0.15
        )
        
        # Phase 6: Variational Xin & Information Energy Metric
        for uid in curr_uids[:5]:  # Compute variational state for top 5 cells
            var_engine.process_cell(uid, window_id)
            
        if len(curr_uids) >= 2:
            ie_engine.compute_pairwise(curr_uids[0], curr_uids[1])
            
        conn.commit()
        
        if idx % 10 == 0:
            print(f"Processed frame {idx}/{len(raw_frames)}")
            
    print("Pipeline finished successfully!")
    print(f"Results saved to {db_path.absolute()}")
    
    # Verify in DB
    cnt_cells = conn.execute("SELECT COUNT(*) FROM spacetime_cell").fetchone()[0]
    cnt_trans = conn.execute("SELECT COUNT(*) FROM transport_current_edge").fetchone()[0]
    cnt_sv = conn.execute("SELECT COUNT(*) FROM v361_variational_state_vector").fetchone()[0]
    cnt_masks = conn.execute("SELECT COUNT(*) FROM masking_counterevidence_record").fetchone()[0]
    
    print(f"DB Output:")
    print(f"  Cells: {cnt_cells}")
    print(f"  Transport edges: {cnt_trans}")
    print(f"  Masking evals: {cnt_masks}")
    print(f"  Variational states: {cnt_sv}")
    
    conn.close()

if __name__ == "__main__":
    main()
