from django.utils import timezone
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    ClinicListing,
    ClinicSpecialty,
    HospitalListing,
    ImagingCenterListing,
    LaboratoryListing,
    PharmacyListing,
    ProviderReview,
)
from .serializers import (
    ClinicListingSerializer,
    ClinicSpecialtySerializer,
    HospitalListingSerializer,
    ImagingCenterListingSerializer,
    LaboratoryListingSerializer,
    PharmacyListingSerializer,
    ProviderReviewSerializer,
)


class HospitalListingViewSet(viewsets.ModelViewSet):
    serializer_class = HospitalListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "name_ar", "city", "country", "slug"]
    ordering_fields = [
        "created_at",
        "name",
        "city",
        "rating_average",
        "review_count",
        "is_featured",
    ]
    ordering = ["-is_featured", "-rating_average"]

    def get_queryset(self):
        qs = HospitalListing.objects.filter(tenant_id=self.request.tenant_id)
        city = self.request.query_params.get("city")
        is_published = self.request.query_params.get("is_published")
        is_featured = self.request.query_params.get("is_featured")
        accepts_insurance = self.request.query_params.get("accepts_insurance")
        if city:
            qs = qs.filter(city__iexact=city)
        if is_published is not None:
            qs = qs.filter(is_published=is_published.lower() == "true")
        if is_featured is not None:
            qs = qs.filter(is_featured=is_featured.lower() == "true")
        if accepts_insurance is not None:
            qs = qs.filter(accepts_insurance=accepts_insurance.lower() == "true")
        return qs

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        hospital = self.get_object()
        hospital.is_published = True
        hospital.save(update_fields=["is_published", "updated_at"])
        return Response({"status": "Hospital listing published."})

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        hospital = self.get_object()
        hospital.is_published = False
        hospital.save(update_fields=["is_published", "updated_at"])
        return Response({"status": "Hospital listing unpublished."})


class ClinicListingViewSet(viewsets.ModelViewSet):
    serializer_class = ClinicListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "name_ar", "city", "country", "primary_specialty", "slug"]
    ordering_fields = [
        "created_at",
        "name",
        "city",
        "rating_average",
        "review_count",
        "is_featured",
    ]
    ordering = ["-is_featured", "-rating_average"]

    def get_queryset(self):
        qs = ClinicListing.objects.filter(tenant_id=self.request.tenant_id)
        city = self.request.query_params.get("city")
        primary_specialty = self.request.query_params.get("primary_specialty")
        is_published = self.request.query_params.get("is_published")
        telemedicine = self.request.query_params.get("telemedicine_available")
        home_visit = self.request.query_params.get("home_visit_available")
        if city:
            qs = qs.filter(city__iexact=city)
        if primary_specialty:
            qs = qs.filter(primary_specialty__iexact=primary_specialty)
        if is_published is not None:
            qs = qs.filter(is_published=is_published.lower() == "true")
        if telemedicine is not None:
            qs = qs.filter(telemedicine_available=telemedicine.lower() == "true")
        if home_visit is not None:
            qs = qs.filter(home_visit_available=home_visit.lower() == "true")
        return qs

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        clinic = self.get_object()
        clinic.is_published = True
        clinic.save(update_fields=["is_published", "updated_at"])
        return Response({"status": "Clinic listing published."})

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        clinic = self.get_object()
        clinic.is_published = False
        clinic.save(update_fields=["is_published", "updated_at"])
        return Response({"status": "Clinic listing unpublished."})


class ClinicSpecialtyViewSet(viewsets.ModelViewSet):
    serializer_class = ClinicSpecialtySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "name_ar", "code", "snomed_code"]
    ordering_fields = ["display_order", "name", "created_at"]
    ordering = ["display_order", "name"]

    def get_queryset(self):
        qs = ClinicSpecialty.objects.filter(tenant_id=self.request.tenant_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs


class LaboratoryListingViewSet(viewsets.ModelViewSet):
    serializer_class = LaboratoryListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "name_ar", "city", "country", "slug"]
    ordering_fields = ["created_at", "name", "city"]
    ordering = ["name"]

    def get_queryset(self):
        qs = LaboratoryListing.objects.filter(tenant_id=self.request.tenant_id)
        city = self.request.query_params.get("city")
        is_published = self.request.query_params.get("is_published")
        home_collection = self.request.query_params.get("home_collection")
        if city:
            qs = qs.filter(city__iexact=city)
        if is_published is not None:
            qs = qs.filter(is_published=is_published.lower() == "true")
        if home_collection is not None:
            qs = qs.filter(home_collection=home_collection.lower() == "true")
        return qs


class ImagingCenterListingViewSet(viewsets.ModelViewSet):
    serializer_class = ImagingCenterListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "name_ar", "city", "country", "slug"]
    ordering_fields = ["created_at", "name", "city"]
    ordering = ["name"]

    def get_queryset(self):
        qs = ImagingCenterListing.objects.filter(tenant_id=self.request.tenant_id)
        city = self.request.query_params.get("city")
        is_published = self.request.query_params.get("is_published")
        if city:
            qs = qs.filter(city__iexact=city)
        if is_published is not None:
            qs = qs.filter(is_published=is_published.lower() == "true")
        return qs


class PharmacyListingViewSet(viewsets.ModelViewSet):
    serializer_class = PharmacyListingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "name_ar", "city", "country", "slug"]
    ordering_fields = ["created_at", "name", "city"]
    ordering = ["name"]

    def get_queryset(self):
        qs = PharmacyListing.objects.filter(tenant_id=self.request.tenant_id)
        city = self.request.query_params.get("city")
        is_published = self.request.query_params.get("is_published")
        home_delivery = self.request.query_params.get("home_delivery")
        is_24_hours = self.request.query_params.get("is_24_hours")
        if city:
            qs = qs.filter(city__iexact=city)
        if is_published is not None:
            qs = qs.filter(is_published=is_published.lower() == "true")
        if home_delivery is not None:
            qs = qs.filter(home_delivery=home_delivery.lower() == "true")
        if is_24_hours is not None:
            qs = qs.filter(is_24_hours=is_24_hours.lower() == "true")
        return qs


class ProviderReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "review_text"]
    ordering_fields = ["created_at", "rating", "visit_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = ProviderReview.objects.filter(tenant_id=self.request.tenant_id)
        provider_type = self.request.query_params.get("provider_type")
        provider_listing_id = self.request.query_params.get("provider_listing_id")
        is_published = self.request.query_params.get("is_published")
        if provider_type:
            qs = qs.filter(provider_type=provider_type)
        if provider_listing_id:
            qs = qs.filter(provider_listing_id=provider_listing_id)
        if is_published is not None:
            qs = qs.filter(is_published=is_published.lower() == "true")
        return qs

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        review = self.get_object()
        review.is_published = True
        review.moderated_at = timezone.now()
        review.save(update_fields=["is_published", "moderated_at", "updated_at"])
        return Response({"status": "Review approved and published."})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        review = self.get_object()
        review.is_published = False
        review.moderated_at = timezone.now()
        review.save(update_fields=["is_published", "moderated_at", "updated_at"])
        return Response({"status": "Review rejected."})
