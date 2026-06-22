from typing import Any, Dict, List, Optional
from platform.terminology.providers.base import TerminologyProvider

class FHIRTerminologyProvider(TerminologyProvider):
    """
    Terminology provider implementing FHIR terminology services standard.
    Exposes CodeSystem, ValueSet, and ConceptMap functionalities ($lookup, $expand, $validate-code, $translate, $subsumes).
    """
    MOCK_VALUE_SETS = {
        "http://hl7.org/fhir/ValueSet/administrative-gender": [
            {"code": "male", "display": "Male", "system": "http://hl7.org/fhir/administrative-gender"},
            {"code": "female", "display": "Female", "system": "http://hl7.org/fhir/administrative-gender"},
            {"code": "other", "display": "Other", "system": "http://hl7.org/fhir/administrative-gender"},
            {"code": "unknown", "display": "Unknown", "system": "http://hl7.org/fhir/administrative-gender"}
        ]
    }

    MOCK_CODE_SYSTEMS = {
        "http://hl7.org/fhir/administrative-gender": {
            "male": {"display": "Male", "definition": "Male gender"},
            "female": {"display": "Female", "definition": "Female gender"},
            "other": {"display": "Other", "definition": "Other gender"},
            "unknown": {"display": "Unknown", "definition": "Unknown gender"}
        }
    }

    MOCK_CONCEPT_MAPS = {
        "http://hl7.org/fhir/ConceptMap/gender-translation": {
            "male": {"code": "M", "display": "Male", "system": "http://terminology.hl7.org/CodeSystem/v3-AdministrativeGender"},
            "female": {"code": "F", "display": "Female", "system": "http://terminology.hl7.org/CodeSystem/v3-AdministrativeGender"}
        }
    }

    def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        results = []
        q = query.lower()
        
        # Search mock CodeSystem concepts
        for cs_url, concepts in self.MOCK_CODE_SYSTEMS.items():
            for code, details in concepts.items():
                if q in code.lower() or q in details["display"].lower() or q in details["definition"].lower():
                    results.append({"code": code, "display": details["display"], "system": cs_url})
                    if len(results) >= limit:
                        return results
        return results

    def lookup(self, code: str, **kwargs) -> Optional[Dict[str, Any]]:
        # FHIR $lookup operation
        system = kwargs.get("system", "http://hl7.org/fhir/administrative-gender")
        if system in self.MOCK_CODE_SYSTEMS:
            concepts = self.MOCK_CODE_SYSTEMS[system]
            if code in concepts:
                details = concepts[code]
                return {
                    "name": "administrative-gender",
                    "version": "4.0.1",
                    "display": details["display"],
                    "definition": details["definition"],
                    "system": system,
                    "code": code
                }
        return None

    def validate(self, code: str, **kwargs) -> bool:
        # FHIR $validate-code operation
        system = kwargs.get("system", "http://hl7.org/fhir/administrative-gender")
        value_set = kwargs.get("value_set")
        
        if value_set:
            if value_set in self.MOCK_VALUE_SETS:
                concepts = self.MOCK_VALUE_SETS[value_set]
                return any(c["code"] == code for c in concepts)
            return False
            
        if system in self.MOCK_CODE_SYSTEMS:
            return code in self.MOCK_CODE_SYSTEMS[system]
        return False

    def translate(self, code: str, target_system: str, **kwargs) -> Optional[Dict[str, Any]]:
        # FHIR $translate operation
        concept_map = kwargs.get("concept_map", "http://hl7.org/fhir/ConceptMap/gender-translation")
        if concept_map in self.MOCK_CONCEPT_MAPS:
            mappings = self.MOCK_CONCEPT_MAPS[concept_map]
            if code in mappings:
                details = mappings[code]
                return {
                    "code": details["code"],
                    "display": details["display"],
                    "system": details["system"],
                    "relationship": "equivalent"
                }
        return None

    def expand(self, value_set: str, filter_str: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        # FHIR $expand operation
        if value_set in self.MOCK_VALUE_SETS:
            concepts = self.MOCK_VALUE_SETS[value_set]
            if filter_str:
                f = filter_str.lower()
                concepts = [c for c in concepts if f in c["code"].lower() or f in c["display"].lower()]
            return concepts
        return []

    def subsumes(self, code_a: str, code_b: str, **kwargs) -> str:
        # FHIR $subsumes operation: tests if code_a subsumes code_b (parent/child relationship)
        # Returns: "subsumes", "subsumed-by", "equivalent", or "not-subsumed"
        if code_a == code_b:
            return "equivalent"
            
        # Mock subsumption check
        if code_a == "parent-concept" and code_b == "child-concept":
            return "subsumes"
        elif code_a == "child-concept" and code_b == "parent-concept":
            return "subsumed-by"
        return "not-subsumed"

    def get_children(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        if code == "parent-concept":
            return [{"code": "child-concept", "display": "Child Concept"}]
        return []

    def get_parents(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        if code == "child-concept":
            return [{"code": "parent-concept", "display": "Parent Concept"}]
        return []

    def get_synonyms(self, code: str, **kwargs) -> List[str]:
        return []

    def get_mappings(self, code: str, target_system: str, **kwargs) -> List[Dict[str, Any]]:
        translated = self.translate(code, target_system, **kwargs)
        return [translated] if translated else []

    def get_version(self) -> str:
        return "R4-4.0.1"
