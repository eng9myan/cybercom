from rest_framework.response import Response
from rest_framework.views import APIView

from .services import verify_at_checkin, verify_before_appointment


class VerifyBeforeAppointmentView(APIView):
    def post(self, request):
        return Response(verify_before_appointment(
            appointment_id=request.data["appointment_id"],
            policy_id=request.data["policy_id"],
            service_code=request.data["service_code"],
            provider_tenant_id=request.data["provider_tenant_id"],
        ))


class VerifyAtCheckinView(APIView):
    def post(self, request):
        return Response(verify_at_checkin(
            appointment_id=request.data["appointment_id"],
            policy_id=request.data["policy_id"],
            service_code=request.data["service_code"],
            provider_tenant_id=request.data["provider_tenant_id"],
        ))
