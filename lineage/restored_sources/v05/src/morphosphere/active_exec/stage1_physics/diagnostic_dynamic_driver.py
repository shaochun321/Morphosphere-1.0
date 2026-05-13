"""V8.5 Patch v1.1 T1: Diagnostic Dynamic Driver.

Label: diagnostic_dynamic_driver
NOT: final hair-cell biophysics, validated MET physiology, scientific model.

Per-cell sinusoidal MET stimulus with random phase offset produces
time-varying, nonuniform information_fiber values.
"""
import numpy as np

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

class DiagnosticDynamicDriver:
    """Produces time-varying heterogeneous cell signals for diagnostic runs."""

    def __init__(self, num_cells, A=0.1, omega=2*np.pi*10, dt=0.01, seed=42):
        rng = np.random.RandomState(seed)
        self.num_cells = num_cells
        self.A = A
        self.omega = omega
        self.dt = dt
        self.phase_offsets = rng.uniform(0, 2*np.pi, num_cells)
        self.V_hair = np.full(num_cells, -65.0)
        self.V_hair_prev = np.full(num_cells, -65.0)
        self.g_MET = 1.0
        self.E_MET = 0.0
        self.g_leak = 0.1
        self.E_leak = -65.0
        self.C_m = 1.0

    def step(self, clock_n):
        """Advance one timestep. Returns dict of per-cell signal arrays."""
        self.V_hair_prev = self.V_hair.copy()
        stimulus = self.A * np.sin(self.omega * clock_n * self.dt + self.phase_offsets)
        met_open = np.clip(0.5 + 0.4 * np.tanh(stimulus), 0.1, 0.9)
        I_MET = self.g_MET * met_open * (self.V_hair - self.E_MET)
        I_leak = self.g_leak * (self.V_hair - self.E_leak)
        dV = (-I_leak - I_MET) / self.C_m
        self.V_hair = self.V_hair + self.dt * dV
        release = 0.001 * sigmoid((self.V_hair + 50.0) / 5.0)
        V_aff = -70.0 + 30.0 * release
        spike_rate = 50.0 * np.maximum(0.0, (V_aff + 60.0) / 10.0)
        spike_reg = 1.0 / (1.0 + np.abs(spike_rate - 50.0) / 25.0)
        timing_prec = 0.01 * spike_reg
        V_slope = (self.V_hair - self.V_hair_prev) / self.dt
        return {
            "V_mean": self.V_hair.copy(),
            "V_slope": V_slope,
            "release_proxy": release,
            "afferent_current": V_aff,
            "spike_rate": spike_rate,
            "spike_regularity": spike_reg,
            "timing_precision": timing_prec,
            "adaptation_state": np.full(self.num_cells, 0.5),
            "met_open": met_open,
        }
