"""
Website Public APIs — Views.
All endpoints: unauthenticated (IsPublicEndpoint), rate-limited, audit-logged.
OpenAPI annotations via drf-spectacular @extend_schema.
"""
import time

from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .audit import log_website_request, log_lead_event
from .models import (
    ProductListing, Industry, CaseStudy,
    DemoRequest, ContactMessage, PartnerListing, PartnerApplication,
    DocumentationSection, DocumentationItem, NewsletterSubscription, NewsletterStatus,
)
from .permissions import IsPublicEndpoint
from .serializers import (
    ProductListingListSerializer, ProductListingDetailSerializer,
    IndustryListSerializer, IndustryDetailSerializer,
    CaseStudyListSerializer, CaseStudyDetailSerializer,
    PartnerListingSerializer,
    DocumentationSectionSerializer, DocumentationSectionDetailSerializer, DocumentationItemSerializer,
    DemoRequestCreateSerializer, DemoRequestResponseSerializer,
    ContactMessageCreateSerializer, ContactMessageResponseSerializer,
    PartnerApplicationCreateSerializer, PartnerApplicationResponseSerializer,
    NewsletterSubscribeSerializer,
)
from .throttling import (
    PublicReadThrottle, DemoRequestThrottle,
    ContactThrottle, PartnerApplicationThrottle, NewsletterThrottle,
)


# ---------------------------------------------------------------------------
# Mixin: request timing + logging
# ---------------------------------------------------------------------------

class AuditMixin:
    """Attach start_time on dispatch; log on finalize_response."""

    def initial(self, request, *args, **kwargs):
        request._start_time = time.monotonic()
        super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        log_website_request(
            request,
            endpoint=request.path,
            status_code=response.status_code,
            resource_type=getattr(self, "_resource_type", ""),
            resource_id=getattr(self, "_resource_id", ""),
            start_time=getattr(request, "_start_time", None),
        )
        return response


# ---------------------------------------------------------------------------
# Health / Status
# ---------------------------------------------------------------------------

@extend_schema(
    tags=["Public Health"],
    summary="Website API health check",
    description="Returns the operational status of the public website APIs.",
    responses={
        200: OpenApiResponse(description="API is operational"),
    },
)
class PublicHealthView(AuditMixin, APIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    _resource_type = "health"

    def get(self, request):
        return Response({
            "status": "ok",
            "service": "cybercom-website-api",
            "version": "v1",
            "endpoints": [
                "/api/v1/public/products/",
                "/api/v1/public/industries/",
                "/api/v1/public/case-studies/",
                "/api/v1/public/partners/",
                "/api/v1/public/documentation/",
                "/api/v1/public/demo-request/",
                "/api/v1/public/contact/",
            ],
        })


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        tags=["Public Products"],
        summary="List published products",
        description=(
            "Returns all published CyberCom product listings. "
            "Filter by `category` or `is_featured=true` for homepage use."
        ),
        parameters=[
            OpenApiParameter("category", OpenApiTypes.STR, description="Filter by product category"),
            OpenApiParameter("is_featured", OpenApiTypes.BOOL, description="Featured products only"),
            OpenApiParameter("search", OpenApiTypes.STR, description="Search name or tagline"),
        ],
        responses={200: ProductListingListSerializer(many=True)},
    )
)
class ProductListView(AuditMixin, ListAPIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    serializer_class = ProductListingListSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "tagline", "short_description"]
    ordering_fields = ["sort_order", "name"]
    ordering = ["sort_order"]
    _resource_type = "product_listing"

    def get_queryset(self):
        qs = ProductListing.objects.filter(is_published=True, parent_product__isnull=True)
        if category := self.request.query_params.get("category"):
            qs = qs.filter(category=category)
        if self.request.query_params.get("is_featured", "").lower() == "true":
            qs = qs.filter(is_featured=True)
        return qs


@extend_schema(
    tags=["Public Products"],
    summary="Get product detail by slug",
    responses={200: ProductListingDetailSerializer, 404: OpenApiResponse(description="Not found")},
)
class ProductDetailView(AuditMixin, RetrieveAPIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    serializer_class = ProductListingDetailSerializer
    lookup_field = "slug"
    _resource_type = "product_listing"

    def get_queryset(self):
        return ProductListing.objects.filter(is_published=True).prefetch_related("sub_products")

    def get_object(self):
        obj = super().get_object()
        self._resource_id = str(obj.id)
        return obj


# ---------------------------------------------------------------------------
# Industries
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        tags=["Public Industries"],
        summary="List published industries",
        parameters=[
            OpenApiParameter("is_featured", OpenApiTypes.BOOL, description="Featured industries only"),
        ],
        responses={200: IndustryListSerializer(many=True)},
    )
)
class IndustryListView(AuditMixin, ListAPIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    serializer_class = IndustryListSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "short_description"]
    ordering = ["sort_order"]
    _resource_type = "industry"

    def get_queryset(self):
        qs = Industry.objects.filter(is_published=True)
        if self.request.query_params.get("is_featured", "").lower() == "true":
            qs = qs.filter(is_featured=True)
        return qs


@extend_schema(
    tags=["Public Industries"],
    summary="Get industry detail by slug",
    responses={200: IndustryDetailSerializer, 404: OpenApiResponse(description="Not found")},
)
class IndustryDetailView(AuditMixin, RetrieveAPIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    serializer_class = IndustryDetailSerializer
    lookup_field = "slug"
    _resource_type = "industry"

    def get_queryset(self):
        return Industry.objects.filter(is_published=True).prefetch_related("relevant_products")

    def get_object(self):
        obj = super().get_object()
        self._resource_id = str(obj.id)
        return obj


# ---------------------------------------------------------------------------
# Case Studies
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        tags=["Public Case Studies"],
        summary="List published case studies",
        parameters=[
            OpenApiParameter("industry", OpenApiTypes.STR, description="Filter by industry slug"),
            OpenApiParameter("is_featured", OpenApiTypes.BOOL),
            OpenApiParameter("country", OpenApiTypes.STR),
        ],
        responses={200: CaseStudyListSerializer(many=True)},
    )
)
class CaseStudyListView(AuditMixin, ListAPIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    serializer_class = CaseStudyListSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "customer_name", "summary"]
    ordering = ["-published_at"]
    _resource_type = "case_study"

    def get_queryset(self):
        qs = CaseStudy.objects.filter(is_published=True).select_related("industry")
        if industry_slug := self.request.query_params.get("industry"):
            qs = qs.filter(industry__slug=industry_slug)
        if self.request.query_params.get("is_featured", "").lower() == "true":
            qs = qs.filter(is_featured=True)
        if country := self.request.query_params.get("country"):
            qs = qs.filter(country__iexact=country)
        return qs


@extend_schema(
    tags=["Public Case Studies"],
    summary="Get case study detail by slug",
    responses={200: CaseStudyDetailSerializer, 404: OpenApiResponse(description="Not found")},
)
class CaseStudyDetailView(AuditMixin, RetrieveAPIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    serializer_class = CaseStudyDetailSerializer
    lookup_field = "slug"
    _resource_type = "case_study"

    def get_queryset(self):
        return CaseStudy.objects.filter(is_published=True).select_related("industry").prefetch_related("products")

    def get_object(self):
        obj = super().get_object()
        self._resource_id = str(obj.id)
        return obj


# ---------------------------------------------------------------------------
# Partners
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        tags=["Public Partners"],
        summary="List published partner directory",
        parameters=[
            OpenApiParameter("partner_type", OpenApiTypes.STR),
            OpenApiParameter("country", OpenApiTypes.STR),
            OpenApiParameter("is_featured", OpenApiTypes.BOOL),
        ],
        responses={200: PartnerListingSerializer(many=True)},
    )
)
class PartnerListView(AuditMixin, ListAPIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    serializer_class = PartnerListingSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["company_name", "description"]
    ordering = ["sort_order", "company_name"]
    _resource_type = "partner_listing"

    def get_queryset(self):
        qs = PartnerListing.objects.filter(is_published=True)
        if ptype := self.request.query_params.get("partner_type"):
            qs = qs.filter(partner_type=ptype)
        if country := self.request.query_params.get("country"):
            qs = qs.filter(countries__contains=[country])
        if self.request.query_params.get("is_featured", "").lower() == "true":
            qs = qs.filter(is_featured=True)
        return qs


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        tags=["Public Documentation"],
        summary="List documentation sections",
        parameters=[
            OpenApiParameter("product", OpenApiTypes.STR, description="Filter by product slug"),
        ],
        responses={200: DocumentationSectionSerializer(many=True)},
    )
)
class DocumentationSectionListView(AuditMixin, ListAPIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    serializer_class = DocumentationSectionSerializer
    ordering = ["sort_order"]
    _resource_type = "doc_section"

    def get_queryset(self):
        qs = DocumentationSection.objects.filter(is_published=True).select_related("product")
        if product_slug := self.request.query_params.get("product"):
            qs = qs.filter(product__slug=product_slug)
        return qs


@extend_schema(
    tags=["Public Documentation"],
    summary="Get documentation section with items",
    responses={200: DocumentationSectionDetailSerializer, 404: OpenApiResponse(description="Not found")},
)
class DocumentationSectionDetailView(AuditMixin, RetrieveAPIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    serializer_class = DocumentationSectionDetailSerializer
    lookup_field = "slug"
    _resource_type = "doc_section"

    def get_queryset(self):
        return DocumentationSection.objects.filter(is_published=True).prefetch_related(
            "items"
        ).select_related("product")

    def get_object(self):
        obj = super().get_object()
        self._resource_id = str(obj.id)
        return obj


@extend_schema(
    tags=["Public Documentation"],
    summary="Search documentation items",
    parameters=[
        OpenApiParameter("q", OpenApiTypes.STR, required=True, description="Search query"),
        OpenApiParameter("product", OpenApiTypes.STR, description="Filter by product slug"),
        OpenApiParameter("content_type", OpenApiTypes.STR, description="Filter by content type"),
    ],
    responses={200: DocumentationItemSerializer(many=True)},
)
class DocumentationSearchView(AuditMixin, APIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    _resource_type = "doc_search"

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query or len(query) < 2:
            return Response(
                {"detail": "Search query must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = DocumentationItem.objects.filter(is_published=True).select_related("section__product")
        qs = qs.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(tags__contains=[query]))

        if product_slug := request.query_params.get("product"):
            qs = qs.filter(section__product__slug=product_slug)
        if content_type := request.query_params.get("content_type"):
            qs = qs.filter(content_type=content_type)

        qs = qs[:20]
        serializer = DocumentationItemSerializer(qs, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})


# ---------------------------------------------------------------------------
# Demo Request
# ---------------------------------------------------------------------------

@extend_schema(
    tags=["Public Lead Generation"],
    summary="Submit a demo request",
    description=(
        "Captures a demo request lead from cy-com.com. "
        "Rate limited to 5 requests per hour per IP. "
        "Returns a reference number for tracking."
    ),
    request=DemoRequestCreateSerializer,
    responses={
        201: DemoRequestResponseSerializer,
        400: OpenApiResponse(description="Validation error"),
        429: OpenApiResponse(description="Rate limit exceeded"),
    },
)
class DemoRequestCreateView(AuditMixin, APIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [DemoRequestThrottle]
    _resource_type = "demo_request"

    def post(self, request):
        serializer = DemoRequestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            log_website_request(
                request,
                endpoint=request.path,
                status_code=400,
                resource_type="demo_request",
                error_detail=str(serializer.errors),
                start_time=getattr(request, "_start_time", None),
            )
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        demo = serializer.save(
            ip_address=_get_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        self._resource_id = str(demo.id)

        log_lead_event(
            request,
            action="create",
            resource_type="demo_request",
            resource_id=str(demo.id),
            details={"reference_number": demo.reference_number, "company": demo.company},
        )

        response_serializer = DemoRequestResponseSerializer(demo)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Public Lead Generation"],
    summary="Get demo request status by reference number",
    responses={
        200: DemoRequestResponseSerializer,
        404: OpenApiResponse(description="Not found"),
    },
)
class DemoRequestStatusView(AuditMixin, APIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    _resource_type = "demo_request"

    def get(self, request, reference_number: str):
        try:
            demo = DemoRequest.objects.get(reference_number=reference_number.upper())
        except DemoRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self._resource_id = str(demo.id)
        serializer = DemoRequestResponseSerializer(demo)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

@extend_schema(
    tags=["Public Lead Generation"],
    summary="Submit a contact message",
    request=ContactMessageCreateSerializer,
    responses={
        201: ContactMessageResponseSerializer,
        400: OpenApiResponse(description="Validation error"),
        429: OpenApiResponse(description="Rate limit exceeded"),
    },
)
class ContactCreateView(AuditMixin, APIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [ContactThrottle]
    _resource_type = "contact_message"

    def post(self, request):
        serializer = ContactMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.save(
            ip_address=_get_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        self._resource_id = str(message.id)

        log_lead_event(
            request,
            action="create",
            resource_type="contact_message",
            resource_id=str(message.id),
            details={"ticket_number": message.ticket_number, "department": message.department},
        )

        response_serializer = ContactMessageResponseSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Public Lead Generation"],
    summary="Get contact ticket status",
    responses={
        200: ContactMessageResponseSerializer,
        404: OpenApiResponse(description="Not found"),
    },
)
class ContactStatusView(AuditMixin, APIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PublicReadThrottle]
    _resource_type = "contact_message"

    def get(self, request, ticket_number: str):
        try:
            msg = ContactMessage.objects.get(ticket_number=ticket_number.upper())
        except ContactMessage.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self._resource_id = str(msg.id)
        return Response(ContactMessageResponseSerializer(msg).data)


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

@extend_schema(
    tags=["Public Lead Generation"],
    summary="Subscribe to newsletter",
    request=NewsletterSubscribeSerializer,
    responses={
        200: OpenApiResponse(description="Already subscribed or confirmed"),
        201: OpenApiResponse(description="Subscribed successfully"),
        400: OpenApiResponse(description="Validation error"),
    },
)
class NewsletterSubscribeView(AuditMixin, APIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [NewsletterThrottle]
    _resource_type = "newsletter"

    def post(self, request):
        serializer = NewsletterSubscribeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        source = serializer.validated_data.get("source", "")

        obj, created = NewsletterSubscription.objects.get_or_create(
            email=email,
            defaults={
                "source": source,
                "gdpr_consent": serializer.validated_data["gdpr_consent"],
                "ip_address": _get_ip(request),
                "status": NewsletterStatus.PENDING,
            },
        )

        if not created and obj.status == NewsletterStatus.UNSUBSCRIBED:
            obj.status = NewsletterStatus.PENDING
            obj.source = source
            obj.save(update_fields=["status", "source", "updated_at"])

        http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {"status": obj.status, "message": "Thank you for subscribing!"},
            status=http_status,
        )


# ---------------------------------------------------------------------------
# Partner Application
# ---------------------------------------------------------------------------

@extend_schema(
    tags=["Public Partners"],
    summary="Submit a partner program application",
    request=PartnerApplicationCreateSerializer,
    responses={
        201: PartnerApplicationResponseSerializer,
        400: OpenApiResponse(description="Validation error"),
        429: OpenApiResponse(description="Rate limit exceeded"),
    },
)
class PartnerApplicationCreateView(AuditMixin, APIView):
    permission_classes = [IsPublicEndpoint]
    throttle_classes = [PartnerApplicationThrottle]
    _resource_type = "partner_application"

    def post(self, request):
        serializer = PartnerApplicationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        application = serializer.save(
            ip_address=_get_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )
        self._resource_id = str(application.id)

        log_lead_event(
            request,
            action="create",
            resource_type="partner_application",
            resource_id=str(application.id),
            details={
                "reference_number": application.reference_number,
                "company_name": application.company_name,
                "partner_type": application.partner_type,
            },
        )

        response_serializer = PartnerApplicationResponseSerializer(application)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
