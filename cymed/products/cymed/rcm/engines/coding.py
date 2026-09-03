"""Auto ICD-10/CPT coding from clinical notes.

Delegates ICD-11 NLP to ai_cds engine; maps ICD-11 → ICD-10 via terminology
ConceptMap. CPT codes come from a procedure keyword dictionary.
"""
from __future__ import annotations


class AutoCodingEngine:
    def __init__(self):
        try:
            from products.cymed.ai_cds.engines import ICDNLPEngine
            self.icd_engine = ICDNLPEngine()
        except ImportError:
            self.icd_engine = None

    def code_encounter(self, *, encounter_id: str, clinical_text: str,
                       procedures_text: str = "") -> dict:
        icd11 = []
        if self.icd_engine and clinical_text:
            r = self.icd_engine.suggest(encounter_id=encounter_id,
                                          source_text=clinical_text, limit=5)
            icd11 = r.get("suggestions", [])

        icd10 = self._map_icd11_to_icd10(icd11)
        cpt = self._extract_cpt(procedures_text or clinical_text)

        return {
            "encounter_id": encounter_id,
            "icd11_suggestions": icd11,
            "icd10_suggestions": icd10,
            "cpt_suggestions": cpt,
        }

    def _map_icd11_to_icd10(self, icd11_list: list[dict]) -> list[dict]:
        """Best-effort ICD-11 → ICD-10 via platform.terminology ConceptMap."""
        try:
            from django.apps import apps
            ConceptMap = apps.get_model("terminology", "ConceptMap")
        except (LookupError, Exception):
            return []
        out = []
        for i in icd11_list:
            m = ConceptMap.objects.filter(source_code=i.get("icd11"),
                                            source_system__code="icd11",
                                            target_system__code="icd10").first()
            if m:
                out.append({"icd10": m.target_code, "label": m.target_display,
                            "from_icd11": i.get("icd11")})
        return out

    _CPT_KEYWORDS = {
        # Extremely minimal starter dictionary — replace with commercial coder set
        "office visit level 3": "99213",
        "office visit level 4": "99214",
        "chest x-ray": "71046",
        "ecg": "93000",
        "cbc": "85025",
        "basic metabolic panel": "80048",
        "lipid panel": "80061",
        "hba1c": "83036",
        "urinalysis": "81003",
        "immunization admin": "90471",
    }

    def _extract_cpt(self, text: str) -> list[dict]:
        text = (text or "").lower()
        out = []
        for kw, cpt in self._CPT_KEYWORDS.items():
            if kw in text:
                out.append({"cpt": cpt, "matched": kw, "confidence": 0.7})
        return out
