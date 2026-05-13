from typing import Protocol, List, Any, Dict
from dataclasses import dataclass, field

@dataclass
class TransformationRecord:
    schema_version: str = "v7.0.0"
    run_id: str = ""
    stage_k_id: str = ""
    window_id: str = ""
    transform_id: str = ""
    domain_object_refs: List[str] = field(default_factory=list)
    codomain_object_refs: List[str] = field(default_factory=list)
    loss_metrics: Dict[str, float] = field(default_factory=dict)
    unit_policy_followed: bool = True

class TransformAuditor(Protocol):
    def record(self, transform_id: str, domain_objects: List[Any], codomain_objects: List[Any]) -> TransformationRecord:
        ...

class DefaultTransformAuditor:
    def record(self, transform_id: str, domain_objects: List[Any], codomain_objects: List[Any]) -> TransformationRecord:
        # Default implementation for P01.5
        # We capture the class names or strings provided as references
        domain_refs = [str(obj) if isinstance(obj, str) else obj.__class__.__name__ for obj in domain_objects]
        codomain_refs = [str(obj) if isinstance(obj, str) else obj.__class__.__name__ for obj in codomain_objects]
        return TransformationRecord(
            transform_id=transform_id,
            domain_object_refs=domain_refs,
            codomain_object_refs=codomain_refs
        )
