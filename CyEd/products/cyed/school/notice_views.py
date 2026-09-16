"""
Daily notices.

Kept in its own module rather than added to `views.py`, which holds the
school-profile singleton views and uses a different base class.
"""

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import (
    PARENT,
    STUDENT,
    IsStaff,
    _email,
    has_any,
    is_staff,
    visible_student_ids,
)
from products.cyed.school.models import Notice
from products.cyed.school.serializers import NoticeSerializer


class NoticeViewSet(TenantScopedModelViewSet):
    """
    The noticeboard. Everyone reads what is addressed to them; staff post.
    """

    queryset = Notice.objects.select_related("campus").all()
    serializer_class = NoticeSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "today"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        # An unpublished notice is a draft; only staff see drafts.
        if not is_staff(self.request):
            qs = qs.filter(is_published=True)
        if params.get("audience"):
            qs = qs.filter(audience__in=[params["audience"], "all"])
        if params.get("campus"):
            qs = qs.filter(campus_id=params["campus"])
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id, posted_by=_email(self.request))

    @action(detail=False, methods=["get"])
    def today(self, request):
        """
        What is on the board right now, for whoever is asking.

        Audience and year level are applied here rather than left to the
        client: a Year 9 excursion notice filling a Year 7 student's screen is
        how a noticeboard becomes something people scroll past.
        """
        on = request.query_params.get("date") or timezone.localdate()
        if isinstance(on, str):
            from django.utils.dateparse import parse_date

            parsed = parse_date(on)
            if parsed is None:
                return Response({"detail": "date must be YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)
            on = parsed

        audience = self._audience_for(request)
        year_levels = self._year_levels_for(request)

        rows = []
        for notice in self.get_queryset():
            if not notice.is_active(on):
                continue
            if audience and notice.audience not in ("all", audience):
                continue
            # A notice for specific years is shown when any of the reader's
            # own year levels match — a parent with children in 7 and 10 needs
            # both, not one chosen arbitrarily.
            if year_levels and not any(notice.applies_to_year(y) for y in year_levels):
                continue
            rows.append(notice)

        # Urgent first, then newest — the order they should be read in.
        priority = {"urgent": 0, "important": 1, "normal": 2}
        rows.sort(key=lambda n: (priority.get(n.priority, 9), -n.starts_on.toordinal()))
        return Response({
            "date": on.isoformat(),
            "count": len(rows),
            "results": self.get_serializer(rows, many=True).data,
        })

    def _audience_for(self, request):
        """Which audience bucket this caller falls into, or None for staff."""
        if has_any(request, STUDENT):
            return "students"
        if has_any(request, PARENT):
            return "parents"
        if is_staff(request):
            return "staff"
        return None

    def _year_levels_for(self, request):
        """
        The year levels relevant to this reader.

        Staff see everything, so this is empty for them. A family sees the year
        levels of the children they can see.
        """
        if is_staff(request):
            return []
        visible = visible_student_ids(request, request.tenant_id)
        if not visible:
            return []
        from products.cyed.sis.models import Student

        return list(
            Student.objects.filter(
                tenant_id=request.tenant_id, id__in=visible
            ).values_list("year_level", flat=True)
        )
