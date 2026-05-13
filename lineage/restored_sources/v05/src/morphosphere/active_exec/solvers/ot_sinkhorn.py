import numpy as np

class OptimalTransportPilot:
    """
    High-Order Optimal Transport Solver Skeleton (Sinkhorn-Knopp).
    Uses entropic regularization to solve the discrete optimal transport problem.
    """
    def __init__(self, reg=0.1, numItermax=1000, stopThr=1e-9):
        self.reg = reg
        self.numItermax = numItermax
        self.stopThr = stopThr

    def solve(self, a: np.ndarray, b: np.ndarray, M: np.ndarray) -> np.ndarray:
        """
        Solve the regularized OT problem.
        a: Source distribution (1D array)
        b: Target distribution (1D array)
        M: Cost matrix (2D array)
        Returns the transport matrix (Coupling matrix).
        """
        a = np.asarray(a, dtype=np.float64)
        b = np.asarray(b, dtype=np.float64)
        M = np.asarray(M, dtype=np.float64)

        dim_a = a.shape[0]
        dim_b = b.shape[0]

        if M.shape != (dim_a, dim_b):
            raise ValueError("Cost matrix M must have shape (len(a), len(b))")

        K = np.exp(-M / self.reg)
        u = np.ones(dim_a) / dim_a
        v = np.ones(dim_b) / dim_b

        for _ in range(self.numItermax):
            u_prev = u
            v = b / np.dot(K.T, u)
            u = a / np.dot(K, v)

            if np.any(np.isnan(u)) or np.any(np.isnan(v)):
                # Numerical instability, break early
                break

            if np.linalg.norm(u - u_prev) < self.stopThr:
                break

        return np.diag(u).dot(K).dot(np.diag(v))
