"""
Two doors onto the same threads:

  /api/v1/messages/threads/      care team (staff roles) — every thread of the tenant
  /api/v1/messages/my/threads/   the signed-in patient — only their own threads

Both are tenant-scoped by the project-wide filter; the patient door is
additionally narrowed to the caller's own Patient record.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from platform.api.permissions import IsAuthenticatedClinicalStaff, IsAuthenticatedPatient, actor
from platform.canonical import events as canonical_events
from products.cymed.core.messaging.models import Message, MessageThread
from products.cymed.core.messaging.serializers import (
    NewThreadSerializer,
    ReplySerializer,
    ThreadDetailSerializer,
    ThreadSerializer,
)
from products.cymed.core.patients.models import Patient


def _author(request) -> str:
    return actor(request)


@transaction.atomic
def _post(thread, sender_type, sender, body):
    msg = Message.objects.create(tenant_id=thread.tenant_id, thread=thread,
                                 sender_type=sender_type, sender=sender, body=body)
    thread.last_message_at = msg.created_at
    if thread.status == "closed" and sender_type == "patient":
        thread.status = "open"  # a patient writing back reopens it
    thread.save(update_fields=["last_message_at", "status", "updated_at"])
    canonical_events.emit(
        event_type="cymed.message.created", aggregate_type="MessageThread",
        aggregate_id=thread.id, tenant_id=thread.tenant_id,
        # No body in the event: notification fan-out must not carry PHI.
        payload={"thread_id": str(thread.id), "patient_id": str(thread.patient_id),
                 "sender_type": sender_type, "assigned_to": thread.assigned_to},
    )
    return msg


class _ThreadViewSetBase(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = MessageThread.objects.all()
    me = "staff"
    other_side = "patient"
    filterset_fields = ["status", "category"]

    def get_serializer_class(self):
        return ThreadDetailSerializer if self.action == "retrieve" else ThreadSerializer

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "other_side": self.other_side}

    def retrieve(self, request, *args, **kwargs):
        thread = self.get_object()
        # Opening a thread marks the other side's messages read.
        thread.messages.filter(sender_type=self.other_side, read_at__isnull=True).update(read_at=timezone.now())
        return Response(self.get_serializer(thread).data)

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        thread = self.get_object()
        ser = ReplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        msg = _post(thread, self.me, _author(request), ser.validated_data["body"])
        return Response({"id": str(msg.id), "created_at": msg.created_at}, status=status.HTTP_201_CREATED)


class StaffThreadViewSet(_ThreadViewSetBase):
    permission_classes = [IsAuthenticatedClinicalStaff]
    filterset_fields = ["status", "category", "patient", "assigned_to"]

    def create(self, request):
        ser = NewThreadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        patient = Patient.objects.filter(id=data.get("patient"), tenant_id=request.tenant_id).first()
        if patient is None:
            return Response({"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)
        thread = MessageThread.objects.create(tenant_id=request.tenant_id, patient=patient,
                                              subject=data["subject"], category=data["category"],
                                              assigned_to=_author(request))
        _post(thread, "staff", _author(request), data["body"])
        return Response(ThreadSerializer(thread, context=self.get_serializer_context()).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        thread = self.get_object()
        thread.assigned_to = str(request.data.get("assigned_to", ""))[:255]
        thread.save(update_fields=["assigned_to", "updated_at"])
        return Response(ThreadSerializer(thread, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        thread = self.get_object()
        thread.status = "closed"
        thread.save(update_fields=["status", "updated_at"])
        return Response(ThreadSerializer(thread, context=self.get_serializer_context()).data)


class PatientThreadViewSet(_ThreadViewSetBase):
    permission_classes = [IsAuthenticatedPatient]
    me = "patient"
    other_side = "staff"

    def _patient(self):
        from products.cymed.patient_portal.models import PatientPortalProfile

        profile = (PatientPortalProfile.objects
                   .filter(tenant_id=self.request.tenant_id, user_id=self.request.user.id)
                   .select_related("patient").first())
        return profile.patient if profile else None

    def get_queryset(self):
        patient = self._patient()
        if patient is None:
            return MessageThread.objects.none()
        return super().get_queryset().filter(patient=patient)

    def create(self, request):
        patient = self._patient()
        if patient is None:
            return Response({"detail": "No patient record for this account."}, status=status.HTTP_403_FORBIDDEN)
        ser = NewThreadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        thread = MessageThread.objects.create(tenant_id=patient.tenant_id, patient=patient,
                                              subject=data["subject"], category=data["category"])
        _post(thread, "patient", _author(request), data["body"])
        return Response(ThreadSerializer(thread, context=self.get_serializer_context()).data,
                        status=status.HTTP_201_CREATED)
