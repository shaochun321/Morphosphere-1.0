from typing import Dict, Any

class V2Reader:
    """V2Reader: Reads V2 numpy/pickle matrices."""
    
    def read_matrix(self, file_path: str) -> Dict[str, Any]:
        """
        Mock implementation for reading V2 matrix objects.
        """
        return {
            "version": "2.0",
            "num_patches": 5,
            "v_afferent": [-70.0] * 5
        }
