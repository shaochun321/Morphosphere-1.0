from dataclasses import dataclass
from typing import List, Optional

@dataclass
class QuantityDefinition:
    quantity_id: str
    layer: str
    quantity_class: str
    unit_policy: str
    source_objects: List[str]
    allowed_targets: List[str]
    forbidden_targets: List[str]

class QuantityCatalog:
    """Loader and registry for data_contracts/quantity_catalog.yaml"""
    def __init__(self):
        self.quantities = {}

    def load(self, path: str):
        pass

    def is_allowed(self, quantity_id: str, target: str) -> bool:
        return True
