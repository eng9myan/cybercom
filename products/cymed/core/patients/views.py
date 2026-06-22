from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from products.cymed.core.patients.models import Patient, PatientMergeHistory
from products.cymed.core.patients.serializers import (
    PatientSerializer, PatientMergeSerializer, PatientUnmergeSerializer
)
from products.cymed.core.patients.services import PatientService

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.filter(is_deleted=False)
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Enforce tenant isolation scoping
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    @action(detail=False, methods=["post"])
    def search(self, request):
        """MPI Cross-Organization & Fuzzy Duplicate Search."""
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")
        dob = request.data.get("dob")
        national_id = request.data.get("national_id")
        passport_number = request.data.get("passport_number")

        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return Response({"detail": "Tenant context required"}, status=status.HTTP_400_BAD_REQUEST)

        matches = PatientService.detect_duplicates(
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            tenant_id=tenant_id,
            national_id=national_id,
            passport_number=passport_number
        )

        serializer = self.get_serializer(matches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def merge(self, request):
        """Merge patient endpoint."""
        ser = PatientMergeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return Response({"detail": "Tenant context required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            history = PatientService.merge_patients(
                source_id=ser.validated_data["source_patient_id"],
                target_id=ser.validated_data["target_patient_id"],
                tenant_id=tenant_id,
                merged_by=str(request.user)
            )
            return Response({
                "detail": "Patients merged successfully",
                "merge_history_id": str(history.id)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def unmerge(self, request):
        """Unmerge patient endpoint."""
        ser = PatientUnmergeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return Response({"detail": "Tenant context required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            PatientService.unmerge_patients(
                history_id=ser.validated_data["merge_history_id"],
                tenant_id=tenant_id,
                unmerged_by=str(request.user)
            )
            return Response({"detail": "Patients unmerged successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
