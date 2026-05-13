"""Canonical v8.5.3 perturbation definitions.

These are validation instruments only. They do not make biological claims and do
not update scientific thresholds.
"""
PERTURBATIONS = {
    "signal_shuffle": {
        "target_metric": "relation_normalized_entropy",
        "expected_direction": "increase",
        "meaning": "destroys local signal ordering and should raise relation uncertainty",
    },
    "geometry_shift": {
        "target_metric": "mean_geometry_cost",
        "expected_direction": "increase",
        "meaning": "shifts support geometry and should raise transport geometry cost",
    },
    "boundary_flip": {
        "target_metric": "rejected_transport_fraction",
        "expected_direction": "increase",
        "meaning": "introduces boundary mismatch and should increase rejection pressure",
    },
    "masking_injection": {
        "target_metric": "mean_o_support_score",
        "expected_direction": "decrease",
        "meaning": "adds counterevidence and should reduce O support",
    },
    "xi_pressure_injection": {
        "target_metric": "xi_quarantine_pressure",
        "expected_direction": "increase",
        "meaning": "adds residual pressure and should increase quarantine/decay pressure",
    },
}
