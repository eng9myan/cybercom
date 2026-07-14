from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DeliveryCompany, DeliveryJob, Driver, Vehicle
from .serializers import (
    DeliveryCompanySerializer,
    DeliveryJobSerializer,
    DriverSerializer,
    VehicleSerializer,
)
from .services import DispatchEngine, InvalidJobTransitionError, NoEligibleDriverError, transition_job


class DeliveryCompanyViewSet(viewsets.ModelViewSet):
    queryset = DeliveryCompany.objects.all()
    serializer_class = DeliveryCompanySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def apply_to_network(self, request, pk=None):
        company = self.get_object()
        company.apply_to_network()
        return Response(self.get_serializer(company).data)

    @action(detail=True, methods=["post"])
    def suspend_network_membership(self, request, pk=None):
        company = self.get_object()
        company.suspend_network_membership()
        return Response(self.get_serializer(company).data)


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [IsAuthenticated]


class DeliveryJobViewSet(viewsets.ModelViewSet):
    queryset = DeliveryJob.objects.all()
    serializer_class = DeliveryJobSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def dispatch_nearest(self, request, pk=None):
        job = self.get_object()
        try:
            job = DispatchEngine().assign_nearest(job)
        except NoEligibleDriverError as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        job = self.get_object()
        try:
            job = transition_job(job, request.data.get("to_status"))
        except InvalidJobTransitionError as exc:
            return Response({"detail": str(exc)}, status=400)
        if job.status in ("delivered", "failed", "cancelled"):
            DispatchEngine().release_driver(job)
        return Response(self.get_serializer(job).data)
