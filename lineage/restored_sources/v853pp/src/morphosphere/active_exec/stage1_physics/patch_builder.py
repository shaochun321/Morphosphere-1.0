from typing import List, Dict
from ..contracts.clock import SystemClock
from .cell_graph_state import CellGraphState, PatchGraph

class PatchBuilder:
    """PatchBuilder: Transforms CellGraphState into PatchGraph."""
    
    def __init__(self, run_id: str):
        self.run_id = run_id

    def build_patch_graph(self, cell_state: CellGraphState) -> PatchGraph:
        """
        Builds a PatchGraph from CellGraphState.
        Currently implements a 1:1 surrogate mapping or a simple aggregation.
        """
        # For P03, we simulate a simple aggregation where pairs of cells form a patch
        num_patches = max(1, cell_state.num_cells // 2)
        
        source_cell_ids: Dict[int, List[int]] = {}
        patch_weights: Dict[int, List[float]] = {}
        v_afferent_aggregated: List[float] = []

        for p_id in range(num_patches):
            # Assign cell 2*p_id and 2*p_id + 1 to patch p_id
            c1 = 2 * p_id
            c2 = min(2 * p_id + 1, cell_state.num_cells - 1)
            source_cell_ids[p_id] = [c1, c2] if c1 != c2 else [c1]
            
            # Simple averaging
            if c1 != c2:
                patch_weights[p_id] = [0.5, 0.5]
                if cell_state.v_afferent:
                    v_agg = 0.5 * cell_state.v_afferent[c1] + 0.5 * cell_state.v_afferent[c2]
                else:
                    v_agg = 0.0
            else:
                patch_weights[p_id] = [1.0]
                if cell_state.v_afferent:
                    v_agg = cell_state.v_afferent[c1]
                else:
                    v_agg = 0.0
            v_afferent_aggregated.append(v_agg)

        return PatchGraph(
            clock_n=cell_state.clock_n,
            num_patches=num_patches,
            source_cell_ids=source_cell_ids,
            patch_weights=patch_weights,
            v_afferent_aggregated=v_afferent_aggregated
        )
