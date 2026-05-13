import json
from typing import List, Dict, Any

class V1Reader:
    """V1Reader: Reads legacy V1.7.1 JSON traces."""
    
    def read_trace(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Reads the full trace array from the JSON file.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
