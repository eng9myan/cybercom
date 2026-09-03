"""Resource registry — maps FHIR resource type name → mapper instance."""
from __future__ import annotations

from typing import Protocol


class ResourceMapper(Protocol):
    resource_type: str            # e.g. 'Patient'
    django_model: type            # e.g. core.patients.Patient

    def to_fhir(self, obj) -> dict: ...
    def from_fhir(self, data: dict): ...
    def search(self, params: dict): ...


_registry: dict[str, ResourceMapper] = {}


def register(mapper: ResourceMapper):
    _registry[mapper.resource_type] = mapper


def get_mapper(resource_type: str) -> ResourceMapper:
    if resource_type not in _registry:
        raise KeyError(f"Unknown FHIR resource: {resource_type}")
    return _registry[resource_type]


def all_types() -> list[str]:
    return sorted(_registry.keys())
