from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class TransformRegistration:
    transform_id: str
    category: str
    domain: List[str]
    codomain: List[str]
    quantity_class_map: Dict[str, List[str]]
    preserved_invariants: List[str]
    loss_budget: List[str]
    reversibility_class: str
    unit_policy: str
    forbidden_shortcuts: List[str] = field(default_factory=list)

class TransformRegistry:
    """Loader and registry for data_contracts/transform_registry.yaml"""
    def __init__(self):
        self.transforms = {}

    def load(self, path: str):
        pass

    def get_transform(self, transform_id: str) -> TransformRegistration:
        return self.transforms.get(transform_id)

    def validate_operation(self, transform_id: str, domain_objs: List[str], codomain_objs: List[str]) -> bool:
        # P01.5 Basic checking: Unregistered transforms should fail here
        if transform_id not in self.transforms:
            return False
        return True
