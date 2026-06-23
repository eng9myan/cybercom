from rest_framework import serializers
from .models import HistologyCase, TissueBlock, Slide, SlideReview, HistologyDiagnosis

class HistologyDiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistologyDiagnosis
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class SlideReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlideReview
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class SlideSerializer(serializers.ModelSerializer):
    reviews = SlideReviewSerializer(many=True, read_only=True)
    class Meta:
        model = Slide
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class TissueBlockSerializer(serializers.ModelSerializer):
    slides = SlideSerializer(many=True, read_only=True)
    class Meta:
        model = TissueBlock
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class HistologyCaseSerializer(serializers.ModelSerializer):
    blocks = TissueBlockSerializer(many=True, read_only=True)
    class Meta:
        model = HistologyCase
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "case_number"]
