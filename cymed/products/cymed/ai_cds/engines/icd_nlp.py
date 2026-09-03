"""
ICD-11 NLP suggestion engine.

Baseline: text search across platform.terminology Concept store for ICD-11.
Upgrade: replace `_baseline_lookup` with a fine-tuned clinical NLP model
(BioBERT / GatorTron / mBERT) hosted behind an inference endpoint.
"""
from __future__ import annotations

from django.apps import apps

from ..models import ICDCodeSuggestion


class ICDNLPEngine:
    model_version = "cymed-icd11-baseline-v1"

    def _terminology(self):
        try:
            return apps.get_model("terminology", "Concept")
        except LookupError:
            return None

    def _baseline_lookup(self, text: str, limit: int = 5) -> list[dict]:
        """Very simple substring match over ICD-11 concepts + display."""
        Concept = self._terminology()
        if not Concept:
            return []
        # Extract candidate keywords (nouns > 4 chars)
        keywords = [w.strip(".,;:") for w in text.split() if len(w) > 4]
        if not keywords:
            return []
        qs = Concept.objects.filter(code_system__code="icd11")
        matches = []
        for kw in keywords[:8]:
            hits = qs.filter(display__icontains=kw)[:limit]
            for h in hits:
                matches.append({
                    "icd11": h.code,
                    "label": h.display,
                    "confidence": 0.6,        # placeholder
                    "matched_term": kw,
                })
        # Deduplicate by icd11
        seen = {}
        for m in matches:
            if m["icd11"] not in seen:
                seen[m["icd11"]] = m
        return list(seen.values())[:limit]

    def suggest(self, *, encounter_id: str, source_text: str,
                 limit: int = 5) -> dict:
        suggestions = self._baseline_lookup(source_text, limit=limit)
        rec = ICDCodeSuggestion.objects.create(
            encounter_id=encounter_id,
            source_text=source_text[:5000],
            suggestions=suggestions,
            model_version=self.model_version,
        )
        return {"id": str(rec.id), "suggestions": suggestions,
                "model_version": self.model_version}
