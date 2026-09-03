"""CapabilityStatement generator — describes what /fhir/R4 supports."""
from django.utils import timezone

from .registry import all_types


def capability_statement() -> dict:
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": timezone.now().isoformat(),
        "publisher": "CyMed Healthcare Systems",
        "kind": "instance",
        "software": {"name": "CyMed FHIR R4", "version": "1.0.0"},
        "implementation": {"description": "CyMed clinical + billing FHIR R4 server"},
        "fhirVersion": "4.0.1",
        "format": ["application/fhir+json"],
        "rest": [{
            "mode": "server",
            "resource": [
                {
                    "type": t,
                    "interaction": [
                        {"code": "read"}, {"code": "search-type"},
                        {"code": "create"}, {"code": "update"},
                    ],
                    "searchParam": [],   # populated from mapper._search_map in future
                }
                for t in all_types()
            ],
            "security": {
                "cors": True,
                "service": [{"coding": [{"code": "OAuth"}]}],
            },
        }],
    }
