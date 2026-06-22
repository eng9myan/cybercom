from typing import Any, Dict, List, Optional
from platform.terminology.providers.base import TerminologyProvider

class SNOMEDProvider(TerminologyProvider):
    """
    Terminology provider for SNOMED CT (Systematized Nomenclature of Medicine Clinical Terms).
    Supports clinical concepts, synonyms, hierarchies, and ICD-11 mappings.
    """
    CONCEPTS = {
        "111553001": {
            "display": "Type 1 diabetes mellitus (disorder)",
            "definition": "A type 1 diabetes mellitus disorder characterized by autoimmune destruction of beta cells.",
            "parents": ["73211009"],
            "children": [],
            "synonyms": ["Type 1 diabetes", "Juvenile onset diabetes mellitus", "Autoimmune diabetes"],
            "relationships": {"finding_site": "113331007", "associated_morphology": "56200009"}
        },
        "44054006": {
            "display": "Type 2 diabetes mellitus (disorder)",
            "definition": "A type 2 diabetes mellitus disorder characterized by resistance to insulin action.",
            "parents": ["73211009"],
            "children": [],
            "synonyms": ["Type 2 diabetes", "NIDDM", "Adult-onset diabetes mellitus"],
            "relationships": {"finding_site": "113331007", "associated_morphology": "56200009"}
        },
        "239720000": {
            "display": "Osteoarthritis of hip (disorder)",
            "definition": "Degenerative joint disease affecting the hip joint.",
            "parents": ["394659003"],
            "children": [],
            "synonyms": ["Coxarthrosis", "Degenerative arthritis of hip"],
            "relationships": {"finding_site": "24184005"}
        },
        "371038006": {
            "display": "Osteoarthritis of knee (disorder)",
            "definition": "Degenerative joint disease affecting the knee joint.",
            "parents": ["394659003"],
            "children": [],
            "synonyms": ["Gonarthrosis", "Degenerative arthritis of knee"],
            "relationships": {"finding_site": "45271004"}
        },
        "73211009": {
            "display": "Diabetes mellitus (disorder)",
            "definition": "A metabolic disorder characterized by chronic hyperglycemia.",
            "parents": ["138875005"],
            "children": ["111553001", "44054006"],
            "synonyms": ["Sugar diabetes", "Diabetes"],
            "relationships": {}
        }
    }

    SNOMED_TO_ICD11 = {
        "111553001": "1B10.0",
        "44054006": "1B10.1",
        "239720000": "FA80",
        "371038006": "FA81",
    }

    def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        results = []
        q = query.lower()
        
        for code, details in self.CONCEPTS.items():
            matches_synonym = any(q in s.lower() for s in details["synonyms"])
            if q in code.lower() or q in details["display"].lower() or q in details["definition"].lower() or matches_synonym:
                results.append({"code": code, "display": details["display"], "type": "concept"})
                if len(results) >= limit:
                    return results
        return results

    def lookup(self, code: str, **kwargs) -> Optional[Dict[str, Any]]:
        if code in self.CONCEPTS:
            details = self.CONCEPTS[code]
            return {
                "code": code,
                "display": details["display"],
                "definition": details["definition"],
                "relationships": details["relationships"]
            }
        return None

    def validate(self, code: str, **kwargs) -> bool:
        return code in self.CONCEPTS

    def translate(self, code: str, target_system: str, **kwargs) -> Optional[Dict[str, Any]]:
        target_system = target_system.lower()
        if target_system in ("icd11", "icd-11"):
            if code in self.SNOMED_TO_ICD11:
                icd11_code = self.SNOMED_TO_ICD11[code]
                return {"code": icd11_code, "system": "ICD-11", "relationship": "equivalent"}
        return None

    def expand(self, value_set: str, filter_str: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        results = []
        if "diabetes" in value_set.lower():
            for code in ["111553001", "44054006"]:
                results.append({"code": code, "display": self.CONCEPTS[code]["display"]})
        else:
            for code, details in self.CONCEPTS.items():
                results.append({"code": code, "display": details["display"]})
                
        if filter_str:
            f = filter_str.lower()
            results = [r for r in results if f in r["code"].lower() or f in r["display"].lower()]
        return results

    def get_children(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        if code in self.CONCEPTS:
            children = self.CONCEPTS[code].get("children", [])
            return [{"code": c, "display": self.CONCEPTS[c]["display"]} for c in children]
        return []

    def get_parents(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        if code in self.CONCEPTS:
            parents = self.CONCEPTS[code].get("parents", [])
            return [{"code": p, "display": self.CONCEPTS.get(p, {}).get("display", f"Parent {p}")} for p in parents]
        return []

    def get_synonyms(self, code: str, **kwargs) -> List[str]:
        if code in self.CONCEPTS:
            return self.CONCEPTS[code].get("synonyms", [])
        return []

    def get_mappings(self, code: str, target_system: str, **kwargs) -> List[Dict[str, Any]]:
        translated = self.translate(code, target_system)
        return [translated] if translated else []

    def get_version(self) -> str:
        return "2025.01.31-snomed"
