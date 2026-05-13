# Legacy V2 Reference

`morphosphere_v2` remains in the archive as a reference implementation, not as an automatically installed dependency of the mainline.

## Legacy strengths to preserve

Future convergence work should review and selectively migrate or adapterize:

- `morphosphere_v2/src/morphosphere/core/cell_graph_state.py`
- `morphosphere_v2/src/morphosphere/core/integrator.py`
- `morphosphere_v2/src/morphosphere/core/dynamics.py`
- `morphosphere_v2/src/morphosphere/preneural/patch_graph.py`
- `morphosphere_v2/src/morphosphere/preneural/preneural_slice.py`
- `morphosphere_v2/src/morphosphere/trajectory/transport.py`
- `morphosphere_v2/src/morphosphere/trajectory/decomposition.py`

## Non-destructive rule

Do not delete the legacy directory until the physical cell graph, electromechanical integrator, patch-afferent graph, and preneural slice crosswalk have been represented in the mainline.

## Import rule

Do not install `morphosphere_v2` and `morphosphere_v2pp` into the same environment. Both expose the import package name `morphosphere`.
