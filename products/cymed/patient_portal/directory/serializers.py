from rest_framework import serializers
from .models import (
    HospitalListing,
    ClinicListing,
    ClinicSpecialty,
    LaboratoryListing,
    ImagingCenterListing,
    PharmacyListing,
    ProviderReview,
)


class HospitalListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalListing
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'rating_average', 'review_count']


class ClinicListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicListing
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'rating_average', 'review_count']


class ClinicSpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicSpecialty
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LaboratoryListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaboratoryListing
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ImagingCenterListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingCenterListing
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PharmacyListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyListing
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProviderReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderReview
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_published', 'moderated_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
