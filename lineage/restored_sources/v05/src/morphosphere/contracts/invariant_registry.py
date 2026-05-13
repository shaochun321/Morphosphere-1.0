from dataclasses import dataclass
from typing import List

@dataclass
class InvariantDefinition:
    invariant_id: str
    description: str
    applies_to: List[str]
    violation_severity: str

class InvariantRegistry:
    """Loader and registry for data_contracts/invariant_registry.yaml"""
    def __init__(self):
        self.invariants = {}

    def load(self, path: str):
        pass
