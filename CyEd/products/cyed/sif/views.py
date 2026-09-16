"""
SIF provider endpoints: object collections, object-by-RefId, coverage report.

Request/response only. There is no zone registration, no event publication and
no consumer side — the coverage endpoint says so at runtime, because the most
damaging thing this module could do is let someone believe CyEd is SIF
certified on the strength of it.
"""

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import ADMIN, LEADERSHIP, IsStaff, has_any
from products.cyed.sif import encoding, mappers
from products.cyed.sif.models import SifRefId
from products.cyed.sif.refids import canonical, resolve_refid
from products.cyed.sif.serializers import SifRefIdSerializer

# How each SIF object type is sourced from CyEd.
SOURCES = {
    "StudentPersonal": lambda tenant: _students(tenant),
    "StudentSchoolEnrollment": lambda tenant: _students(tenant),
    "StaffPersonal": lambda tenant: _staff(tenant),
    "SchoolInfo": lambda tenant: _campuses(tenant),
    "StudentAttendance": lambda tenant: _attendance(tenant),
}


def _students(tenant_id):
    from products.cyed.sis.models import Student

    return Student.objects.filter(tenant_id=tenant_id).select_related("campus")


def _staff(tenant_id):
    from products.cyed.hr.models import Staff

    return Staff.objects.filter(tenant_id=tenant_id).select_related("campus")


def _campuses(tenant_id):
    from products.cyed.org.models import Campus

    return Campus.objects.filter(tenant_id=tenant_id)


def _attendance(tenant_id):
    from products.cyed.attendance.models import AttendanceMark

    return AttendanceMark.objects.filter(tenant_id=tenant_id).select_related(
        "student", "student__campus", "roll_call"
    )


class SifObjectView(APIView):
    """
    ``GET /api/v1/sif/objects/<ObjectType>/`` — a SIF collection.

    ``?format=xml`` for the XML binding (the default a zone would expect),
    ``?format=json`` for the JSON binding. Paged with ``?limit=&offset=``
    because a full StudentAttendance collection for a year is large enough to
    matter.

    Staff-only: these payloads carry student PII in bulk.
    """

    permission_classes = [IsStaff]

    def get(self, request, object_type):
        spec = mappers.OBJECTS.get(object_type)
        if spec is None:
            return Response(
                {
                    "detail": f"Unknown SIF object '{object_type}'.",
                    "supported": sorted(mappers.OBJECTS),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            limit = min(int(request.query_params.get("limit", 100)), 1000)
            offset = int(request.query_params.get("offset", 0))
        except ValueError:
            return Response({"detail": "limit and offset must be whole numbers."},
                            status=status.HTTP_400_BAD_REQUEST)

        queryset = SOURCES[object_type](request.tenant_id)
        total = queryset.count()
        rows = list(queryset[offset:offset + limit])
        objects = [spec["mapper"](row) for row in rows]

        if request.query_params.get("format", "xml") == "json":
            return Response({
                "object": object_type,
                "total": total,
                "limit": limit,
                "offset": offset,
                spec["collection"]: [encoding.to_json(o) for o in objects],
                # Repeated on every response, not buried in a separate report:
                # a consumer reading only this payload still learns what is
                # missing from it.
                "cyed:gaps": spec["gaps"],
            })

        xml = encoding.collection_to_xml(spec["collection"], object_type, objects)
        response = HttpResponse(xml, content_type="application/xml")
        response["X-CyEd-SIF-Total"] = str(total)
        response["X-CyEd-SIF-Conformance"] = "uncertified-provider"
        return response


class SifObjectByRefIdView(APIView):
    """
    ``GET /api/v1/sif/refid/<uuid>/`` — resolve a RefId back to its object.

    The question a consumer asks when reconciling: "what is this identifier you
    sent me?" Answering it requires no knowledge of how the RefId was derived.
    """

    permission_classes = [IsStaff]

    def get(self, request, refid):
        row = resolve_refid(request.tenant_id, refid)
        if row is None:
            return Response({"detail": "No object in this school carries that RefId."},
                            status=status.HTTP_404_NOT_FOUND)

        spec = mappers.OBJECTS.get(row.object_type)
        if spec is None:
            return Response({"detail": f"RefId maps to unsupported object '{row.object_type}'."},
                            status=status.HTTP_501_NOT_IMPLEMENTED)

        obj = _reload_object(request.tenant_id, row)
        if obj is None:
            # The registry outlives the row it pointed at — deliberately, since
            # a RefId must never be reused. Say so rather than 404ing, which a
            # consumer would read as "never existed".
            return Response(
                {
                    "refid": canonical(row.refid),
                    "object": row.object_type,
                    "detail": (
                        "This RefId was issued but the underlying record no longer "
                        "exists. The RefId is retired and will never be reassigned."
                    ),
                    "source": row.source_description,
                },
                status=status.HTTP_410_GONE,
            )

        if request.query_params.get("format", "json") == "xml":
            return HttpResponse(
                encoding.to_xml(row.object_type, spec["mapper"](obj)),
                content_type="application/xml",
            )
        return Response({
            "refid": canonical(row.refid),
            "object": row.object_type,
            row.object_type: encoding.to_json(spec["mapper"](obj)),
        })


def _reload_object(tenant_id, row):
    """
    Fetch the CyEd record a registry row points at, or None if it is gone.

    Uses `source_local_id`, which is the real row id even for derived objects
    whose `local_id` is a hash — so this is a single indexed fetch rather than
    a scan that re-derives hashes looking for a match.
    """
    from products.cyed.attendance.models import AttendanceMark
    from products.cyed.hr.models import Staff
    from products.cyed.org.models import Campus
    from products.cyed.sis.models import Student

    key = row.source_local_id or row.local_id
    lookup = {
        "StudentPersonal": Student,
        "StudentSchoolEnrollment": Student,
        "StaffPersonal": Staff,
        "SchoolInfo": Campus,
        "StudentAttendance": AttendanceMark,
    }.get(row.object_type)
    if lookup is None:
        return None

    queryset = lookup.objects.filter(tenant_id=tenant_id, id=key)
    if lookup is Student:
        queryset = queryset.select_related("campus")
    elif lookup is AttendanceMark:
        queryset = queryset.select_related("student", "student__campus", "roll_call")
    return queryset.first()


class SifCoverageView(APIView):
    """
    ``GET /api/v1/sif/coverage/`` — what this module does and does not do.

    This report, not a conformance badge, is what an auditor should be given.
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        return Response({
            "conformance": "uncertified-provider",
            "disclaimer": (
                "CyEd implements a SIF AU v3.x data mapping layer and a stable RefId "
                "registry. It is NOT a certified SIF Zone integration and must not be "
                "described as SIF certified."
            ),
            "implemented": {
                "objects": sorted(mappers.OBJECTS),
                "bindings": ["xml", "json"],
                "refids": "RFC 4122 UUIDs, minted once and stable for the life of the object",
                "pattern": "request/response provider",
            },
            "not_implemented": [
                "SIF Zone registration and Environment provisioning "
                "(/environments, /requestsConnector, /queues, /subscriptions)",
                "Event publication and subscription (CREATE/UPDATE/DELETE onto a zone topic)",
                "Delayed (asynchronous) message exchange and queue semantics",
                "SIF conformance certification against a jurisdiction's test harness",
                "Consumer-side ingestion — CyEd provides objects, it does not consume them",
            ],
            "element_gaps": {
                name: spec["gaps"] for name, spec in sorted(mappers.OBJECTS.items())
            },
            "refids_issued": SifRefId.objects.filter(tenant_id=request.tenant_id).count(),
        })


class SifRefIdViewSet(TenantScopedModelViewSet):
    """
    The RefId registry, read-only.

    Minting happens as a side effect of emitting an object; exposing create or
    update here would let a RefId be changed after a consumer had keyed off it,
    which is the one thing a RefId must never do.
    """

    queryset = SifRefId.objects.all()
    serializer_class = SifRefIdSerializer
    permission_classes = [IsStaff]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("object_type"):
            qs = qs.filter(object_type=params["object_type"])
        if params.get("local_id"):
            qs = qs.filter(local_id=params["local_id"])
        return qs
