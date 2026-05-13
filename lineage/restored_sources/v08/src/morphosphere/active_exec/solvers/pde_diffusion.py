import numpy as np

class PDESolverPilot:
    """
    PDE Solver Skeleton (Explicit Finite Difference / Heat Diffusion).
    Simulates simple diffusion on a graph or point cloud using graph Laplacian.
    """
    def __init__(self, dt=0.01, num_steps=10):
        self.dt = dt
        self.num_steps = num_steps

    def compute_laplacian(self, adjacency: np.ndarray) -> np.ndarray:
        """
        Compute the unnormalized graph Laplacian.
        L = D - A
        """
        degrees = np.sum(adjacency, axis=1)
        D = np.diag(degrees)
        return D - adjacency

    def diffuse(self, initial_field: np.ndarray, adjacency: np.ndarray) -> np.ndarray:
        """
        Perform heat diffusion: du/dt = -L u
        Using explicit Euler: u(t+dt) = u(t) - dt * L * u(t)
        """
        L = self.compute_laplacian(adjacency)
        u = initial_field.copy()

        for _ in range(self.num_steps):
            du = -np.dot(L, u)
            u = u + self.dt * du

        return u
