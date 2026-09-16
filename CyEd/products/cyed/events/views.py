from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.events import excursions
from products.cyed.events.models import Event, EventParticipation
from products.cyed.events.serializers import EventParticipationSerializer, EventSerializer
from products.cyed.governance.access import (
    IsStaff,
    _email,
    is_staff,
    scope_queryset_by_student,
    visible_student_ids,
)


class EventViewSet(TenantScopedModelViewSet):
    queryset = Event.objects.select_related("staff_in_charge").all()
    serializer_class = EventSerializer

    def get_permissions(self):
        return [IsAuthenticatedViaClaims()] if self.action in ("list", "retrieve") else [IsStaff()]

    @action(detail=True, methods=["post"])
    def invite(self, request, pk=None):
        """
        Add students, raising the permission form and the charge together.

        Body: ``{"students": [uuid], "class_section": "<uuid>"}`` — an explicit
        list or everyone in a class.

        One action rather than two so a family gets a single job instead of a
        form and an invoice arriving days apart.
        """
        event = self.get_object()
        student_ids = request.data.get("students") or []
        if request.data.get("class_section"):
            from products.cyed.sis.models import Enrolment

            student_ids = list(
                Enrolment.objects.filter(
                    tenant_id=request.tenant_id,
                    class_section_id=request.data["class_section"],
                    status="active",
                ).values_list("student_id", flat=True)
            )
        if not student_ids:
            return Response(
                {"detail": "Give a list of students or a class section."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            created = excursions.invite(
                event, student_ids=student_ids, issued_by=_email(request)
            )
        except excursions.ExcursionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(
            {"invited": len(created), "already_invited": len(student_ids) - len(created)},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def readiness(self, request, pk=None):
        """
        Who is cleared, and precisely what is missing for everyone else.

        "Not ready" alone sends an office worker back through three systems;
        each row here names what is outstanding.
        """
        return Response(excursions.readiness(self.get_object()))

    @action(detail=True, methods=["get"])
    def roll(self, request, pk=None):
        """
        The roll a supervising teacher takes off site, with medical plans in
        full — a teacher in a car park needs the steps, not a link to them.
        """
        return Response(excursions.excursion_roll(self.get_object()))

    @action(detail=True, methods=["get"], url_path="chase-list")
    def chase_list(self, request, pk=None):
        """Families to contact about unreturned permissions, past the deadline."""
        return Response(excursions.chase_list(self.get_object()))


class EventParticipationViewSet(TenantScopedModelViewSet):
    """Families confirm/decline (and give consent for) their own child; staff manage all."""

    queryset = EventParticipation.objects.select_related("event", "student").all()
    serializer_class = EventParticipationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="student_id")
        event = self.request.query_params.get("event")
        if event:
            qs = qs.filter(event_id=event)
        return qs

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """
        A family says yes.

        Does not clear the child on its own — the permission still has to be
        signed and the fee settled. Saying so in the response stops a parent
        believing they are done when a form is still outstanding.
        """
        participation = self.get_object()
        visible = visible_student_ids(request, request.tenant_id)
        if visible is not None and participation.student_id not in visible:
            return Response({"detail": "That is not your child."},
                            status=status.HTTP_403_FORBIDDEN)

        excursions.confirm(
            participation,
            responded_by=_email(request),
            emergency_contact=request.data.get("emergency_contact", ""),
        )
        return Response({
            **self.get_serializer(participation).data,
            "cleared": participation.is_cleared(),
            "still_needed": [] if participation.is_cleared() else [
                item for item, done in (
                    ("permission not signed", participation.is_consented()),
                    ("fee unpaid", participation.is_paid()),
                ) if not done
            ],
        })

    @action(detail=True, methods=["post"], url_path="waive-fee", permission_classes=[IsStaff])
    def waive_fee(self, request, pk=None):
        """
        A child whose family cannot pay still goes.

        Recorded as a decision so the readiness list can tell "the school
        decided this" from "nobody has chased this family".
        """
        try:
            participation = excursions.waive_fee(
                self.get_object(), reason=request.data.get("reason", ""), actor=_email(request)
            )
        except excursions.ExcursionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(participation).data)
