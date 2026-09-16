from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from products.cyed.governance.access import IsStaff
from products.cyed.school.models import get_profile
from products.cyed.school.serializers import SchoolProfileSerializer


class SchoolProfileView(APIView):
    """
    GET  /api/v1/school/profile/  → the tenant's school profile (any user).
    PATCH                          → update name/address/contact (staff only).
    """

    def get_permissions(self):
        return [IsStaff()] if self.request.method == "PATCH" else [IsAuthenticatedViaClaims()]

    def _tenant(self, request):
        return getattr(request, "tenant_id", None)

    def get(self, request):
        if self._tenant(request) is None:
            return Response({"detail": "A tenant context is required."}, status=status.HTTP_400_BAD_REQUEST)
        profile = get_profile(self._tenant(request))
        return Response(SchoolProfileSerializer(profile).data)

    def patch(self, request):
        profile = get_profile(self._tenant(request))
        serializer = SchoolProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SchoolLogoView(APIView):
    """
    POST /api/v1/school/logo/  (multipart 'logo') → upload the school logo (staff).
    GET                         → serve the logo bytes.
    JPEG is recommended (it embeds into the report-card PDF).
    """

    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        return [IsStaff()] if self.request.method == "POST" else [IsAuthenticatedViaClaims()]

    def post(self, request):
        tenant = getattr(request, "tenant_id", None)
        if tenant is None:
            return Response({"detail": "A tenant context is required."}, status=status.HTTP_400_BAD_REQUEST)
        f = request.FILES.get("logo")
        if not f:
            return Response({"detail": "Attach a 'logo' file."}, status=status.HTTP_400_BAD_REQUEST)
        content_type = (f.content_type or "").lower()
        if content_type not in ("image/jpeg", "image/jpg", "image/png"):
            return Response({"detail": "Logo must be JPEG or PNG (JPEG recommended)."},
                            status=status.HTTP_400_BAD_REQUEST)
        profile = get_profile(tenant)
        profile.logo_bytes = f.read()
        profile.logo_content_type = "image/jpeg" if "jp" in content_type else content_type
        profile.save(update_fields=["logo_bytes", "logo_content_type", "updated_at"])
        return Response({"detail": "Logo uploaded.", "content_type": profile.logo_content_type,
                         "embeddable": profile.logo_content_type == "image/jpeg"})

    def get(self, request):
        profile = get_profile(getattr(request, "tenant_id", None))
        if not profile.has_logo:
            raise Http404("No logo set.")
        return HttpResponse(bytes(profile.logo_bytes), content_type=profile.logo_content_type or "image/jpeg")
