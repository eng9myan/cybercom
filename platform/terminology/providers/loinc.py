from typing import Any, Dict, List, Optional
from platform.terminology.providers.base import TerminologyProvider

class LOINCProvider(TerminologyProvider):
    """
    Terminology provider for LOINC (Logical Observation Identifiers Names and Codes).
    Supports laboratory measurements, clinical observations, and mappings to other standards.
    """
    OBSERVATIONS = {
        "2339-0": {
            "display": "Glucose [Mass/volume] in Blood",
            "class": "CHEM",
            "system": "Bld",
            "scale": "Qn",
            "definition": "Quantitative measurement of glucose mass concentration in blood.",
            "synonyms": ["Blood Glucose", "GLU", "Blood Sugar"],
            "mappings": {"snomed": "365812005"}
        },
        "4544-3": {
            "display": "Hemoglobin A1c [Fraction] in Blood",
            "class": "HEM/BC",
            "system": "Bld",
            "scale": "Qn",
            "definition": "Quantitative measurement of HbA1c fraction in blood.",
            "synonyms": ["HbA1c", "Glycated hemoglobin", "Glycohemoglobin", "A1c"],
            "mappings": {"snomed": "365825000"}
        },
        "29463-7": {
            "display": "Body weight",
            "class": "CLIN",
            "system": "Patient",
            "scale": "Qn",
            "definition": "Quantitative measurement of patient body weight.",
            "synonyms": ["Weight", "Body mass", "Wt"],
            "mappings": {"snomed": "27113001"}
        },
        "8867-4": {
            "display": "Heart rate",
            "class": "CLIN",
            "system": "Pt",
            "scale": "Qn",
            "definition": "Heart rate measured in beats per minute.",
            "synonyms": ["Pulse", "Heart beats", "HR"],
            "mappings": {"snomed": "364075005"}
        }
    }

    def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        results = []
        q = query.lower()
        
        for code, details in self.OBSERVATIONS.items():
            matches_synonym = any(q in s.lower() for s in details["synonyms"])
            if q in code.lower() or q in details["display"].lower() or q in details["definition"].lower() or matches_synonym:
                results.append({"code": code, "display": details["display"], "type": "observation"})
                if len(results) >= limit:
                    return results
        return results

    def lookup(self, code: str, **kwargs) -> Optional[Dict[str, Any]]:
        if code in self.OBSERVATIONS:
            details = self.OBSERVATIONS[code]
            return {
                "code": code,
                "display": details["display"],
                "class": details["class"],
                "system": details["system"],
                "scale": details["scale"],
                "definition": details["definition"]
            }
        return None

    def validate(self, code: str, **kwargs) -> bool:
        return code in self.OBSERVATIONS

    def translate(self, code: str, target_system: str, **kwargs) -> Optional[Dict[str, Any]]:
        target_system = target_system.lower()
        if code in self.OBSERVATIONS:
            mappings = self.OBSERVATIONS[code]["mappings"]
            if target_system in mappings:
                return {
                    "code": mappings[target_system],
                    "system": target_system.upper(),
                    "relationship": "equivalent"
                }
        return None

    def expand(self, value_set: str, filter_str: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        results = []
        if "vital" in value_set.lower():
            for code in ["8867-4", "29463-7"]:
                results.append({"code": code, "display": self.OBSERVATIONS[code]["display"]})
        elif "chemistry" in value_set.lower() or "lab" in value_set.lower():
            for code in ["2339-0", "4544-3"]:
                results.append({"code": code, "display": self.OBSERVATIONS[code]["display"]})
        else:
            for code, details in self.OBSERVATIONS.items():
                results.append({"code": code, "display": details["display"]})
                
        if filter_str:
            f = filter_str.lower()
            results = [r for r in results if f in r["code"].lower() or f in r["display"].lower()]
        return results

    def get_children(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        # Flat structure for LOINC in this mock
        return []

    def get_parents(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        if code in self.OBSERVATIONS:
            category = self.OBSERVATIONS[code]["class"]
            return [{"code": category, "display": f"LOINC Class {category}"}]
        return []

    def get_synonyms(self, code: str, **kwargs) -> List[str]:
        if code in self.OBSERVATIONS:
            return self.OBSERVATIONS[code]["synonyms"]
        return []

    def get_mappings(self, code: str, target_system: str, **kwargs) -> List[Dict[str, Any]]:
        translated = self.translate(code, target_system)
        return [translated] if translated else []

    def get_version(self) -> str:
        return "2.77"
