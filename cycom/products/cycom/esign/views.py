from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.throttling import PublicWriteRateThrottle
from core.viewsets import TenantScopedModelViewSet
from products.cycom.esign.models import SignRequest, SignTemplate
from products.cycom.esign.serializers import (
    SignRequestPublicSerializer,
    SignRequestSerializer,
    SignTemplatePublicSerializer,
    SignTemplateSerializer,
)


class SignTemplateViewSet(TenantScopedModelViewSet):
    # Frontend (app/sign/templates/page.tsx) treats the list response as a
    # bare array (`.filter`, `.length`) — the project-wide default
    # PageNumberPagination would wrap it in {count,next,previous,results}
    # and break every list call here.
    pagination_class = None
    queryset = SignTemplate.objects.all()
    serializer_class = SignTemplateSerializer


class SignRequestViewSet(TenantScopedModelViewSet):
    pagination_class = None
    queryset = SignRequest.objects.select_related("template").all()
    serializer_class = SignRequestSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def public_sign_detail(request, token):
    """
    Unauthenticated by design — the token itself (32 random bytes, url-safe)
    is the credential, same as any e-signature portal link. No tenant
    scoping applies here: the request is looked up globally by token.
    """
    try:
        sign_request = SignRequest.objects.select_related("template").get(token=token)
    except SignRequest.DoesNotExist:
        return Response({"detail": "Signature request not found or link expired."}, status=404)

    if sign_request.status == "Sent":
        sign_request.status = "Viewed"
        sign_request.viewed_at = timezone.now()
        sign_request.save(update_fields=["status", "viewed_at", "updated_at"])

    return Response(
        {
            "request": SignRequestPublicSerializer(sign_request).data,
            "template": SignTemplatePublicSerializer(sign_request.template).data,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PublicWriteRateThrottle])
def public_sign_submit(request, token):
    try:
        sign_request = SignRequest.objects.get(token=token)
    except SignRequest.DoesNotExist:
        return Response({"detail": "Signature request not found or link expired."}, status=404)

    if sign_request.status == "Signed":
        return Response({"detail": "This document has already been signed."}, status=400)

    signature = request.data.get("signature")
    if not signature:
        return Response({"detail": "signature is required."}, status=status.HTTP_400_BAD_REQUEST)

    # signed_at is server time, not the client-supplied dateSigned — a
    # signature timestamp has to be trustworthy, and the client clock isn't.
    sign_request.signature = signature
    sign_request.status = "Signed"
    sign_request.signed_at = timezone.now()
    sign_request.save(update_fields=["signature", "status", "signed_at", "updated_at"])

    return Response({"status": "Signed", "token": sign_request.token})
