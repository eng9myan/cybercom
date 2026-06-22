from typing import Any, Dict, List, Optional
from platform.terminology.providers.base import TerminologyProvider

class ICFProvider(TerminologyProvider):
    """
    Terminology provider for WHO ICF (International Classification of Functioning, Disability and Health).
    Supports functional assessments, disability classifications, and patient functioning models.
    """
    CLASSIFICATIONS = {
        "d450": {
            "display": "Walking",
            "component": "Activities and Participation",
            "definition": "Moving along a surface on foot, step by step, so that one foot is always on the ground.",
            "synonyms": ["Ambulating", "Foot travel", "Steps"],
            "mappings": {"whodas": "WHODAS-D4.1"}
        },
        "b152": {
            "display": "Emotional functions",
            "component": "Body Functions",
            "definition": "Mental functions related to the feeling and affect components of physical and psychological processes.",
            "synonyms": ["Affect", "Emotions", "Feeling state"],
            "mappings": {"whodas": "WHODAS-D1.3"}
        },
        "s730": {
            "display": "Structure of upper extremity",
            "component": "Body Structures",
            "definition": "The structural composition of the shoulder, arm, hand and fingers.",
            "synonyms": ["Upper limbs", "Arm anatomy"],
            "mappings": {}
        },
        "e1101": {
            "display": "Drugs",
            "component": "Environmental Factors",
            "definition": "Any natural or synthetic substance that can affect functioning.",
            "synonyms": ["Medications", "Pharmaceuticals", "Substances"],
            "mappings": {}
        }
    }

    def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        results = []
        q = query.lower()
        
        for code, details in self.CLASSIFICATIONS.items():
            matches_synonym = any(q in s.lower() for s in details["synonyms"])
            if q in code.lower() or q in details["display"].lower() or q in details["definition"].lower() or matches_synonym:
                results.append({"code": code, "display": details["display"], "type": "functioning_model"})
                if len(results) >= limit:
                    return results
        return results

    def lookup(self, code: str, **kwargs) -> Optional[Dict[str, Any]]:
        if code in self.CLASSIFICATIONS:
            details = self.CLASSIFICATIONS[code]
            return {
                "code": code,
                "display": details["display"],
                "component": details["component"],
                "definition": details["definition"]
            }
        return None

    def validate(self, code: str, **kwargs) -> bool:
        return code in self.CLASSIFICATIONS

    def translate(self, code: str, target_system: str, **kwargs) -> Optional[Dict[str, Any]]:
        target_system = target_system.lower()
        if code in self.CLASSIFICATIONS:
            mappings = self.CLASSIFICATIONS[code]["mappings"]
            if target_system in mappings:
                return {
                    "code": mappings[target_system],
                    "system": target_system.upper(),
                    "relationship": "equivalent"
                }
        return None

    def expand(self, value_set: str, filter_str: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        results = []
        for code, details in self.CLASSIFICATIONS.items():
            results.append({"code": code, "display": details["display"]})
                
        if filter_str:
            f = filter_str.lower()
            results = [r for r in results if f in r["code"].lower() or f in r["display"].lower()]
        return results

    def get_children(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        return []

    def get_parents(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        if code in self.CLASSIFICATIONS:
            component = self.CLASSIFICATIONS[code]["component"]
            return [{"code": component.lower().replace(" ", "_"), "display": f"ICF Component: {component}"}]
        return []

    def get_synonyms(self, code: str, **kwargs) -> List[str]:
        if code in self.CLASSIFICATIONS:
            return self.CLASSIFICATIONS[code]["synonyms"]
        return []

    def get_mappings(self, code: str, target_system: str, **kwargs) -> List[Dict[str, Any]]:
        translated = self.translate(code, target_system)
        return [translated] if translated else []

    def get_version(self) -> str:
        return "2001-icf"
