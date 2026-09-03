"""Auto ICD-10 + CPT coding from a clinic SOAP note.

Thin façade over rcm.engines.AutoCodingEngine. Provides a single POST endpoint
suitable for wiring into the clinic SOAP form's "suggest codes" button.
"""
from rest_framework.response import Response
from rest_framework.views import APIView


class SuggestCodesView(APIView):
    def post(self, request):
        try:
            from products.cymed.rcm.engines import AutoCodingEngine
        except ImportError:
            return Response({"error": "rcm app unavailable"}, status=500)
        return Response(AutoCodingEngine().code_encounter(
            encounter_id=request.data["encounter_id"],
            clinical_text=request.data.get("clinical_text", ""),
            procedures_text=request.data.get("procedures_text", ""),
        ))
