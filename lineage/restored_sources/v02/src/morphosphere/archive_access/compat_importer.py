from typing import Dict, Any, List
from ..active_exec.stage1_physics.cell_graph_state import CellGraphState
from .v1_reader import V1Reader

class CompatImporter:
    """CompatImporter: Translates legacy data into V6 compliant contracts."""
    
    def __init__(self):
        self.v1_reader = V1Reader()
        
    def import_v1_frames(self, file_path: str, run_id: str) -> List[CellGraphState]:
        """
        Imports V1 trace array and returns a list of V6 CellGraphStates.
        Since raw_manifold_trace.json only has macro variables (shell_energy, etc.),
        we mock the micro-cells mapping logic here for the V6 physics core.
        """
        traces = self.v1_reader.read_trace(file_path)
        states = []
        
        for idx, frame in enumerate(traces):
            # Deriving num_cells from shell_count as a naive projection mapping
            shell_count = frame.get("shell_count", 1)
            # Suppose each shell layer maps to 10 simulated cells in the V6 core
            num_cells = shell_count * 10
            
            # Using shell energy to approximate afferent voltage distributions
            base_v = -70.0
            v_afferent = []
            boundaries = frame.get("shell_boundary", [])
            for boundary in boundaries:
                energy = boundary.get("shell_energy", 0.0)
                # Spread the energy across the 10 cells in this shell
                shell_v = base_v + energy
                v_afferent.extend([shell_v] * 10)
            
            # Padding if boundaries list was shorter than expected
            while len(v_afferent) < num_cells:
                v_afferent.append(base_v)
                
            state = CellGraphState(
                clock_n=idx,
                run_id=run_id,
                num_cells=num_cells,
                v_hair_cell=[-65.0] * num_cells,
                calcium_concentration=[0.0] * num_cells,
                v_afferent=v_afferent,
                met_open_probability=[0.0] * num_cells,
                neurotransmitter_release_rate=[0.0] * num_cells
            )
            states.append(state)
            
        return states
