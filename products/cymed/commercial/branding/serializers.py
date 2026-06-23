from rest_framework import serializers
from products.cymed.commercial.branding.models import (
    Brand, BrandTheme, BrandAsset, BrandDomain, BrandLocalization
)


class BrandThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandTheme
        fields = "__all__"


class BrandAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandAsset
        fields = "__all__"


class BrandDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandDomain
        fields = "__all__"


class BrandLocalizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandLocalization
        fields = "__all__"


class BrandSerializer(serializers.ModelSerializer):
    theme = BrandThemeSerializer(read_only=True)
    assets = BrandAssetSerializer(many=True, read_only=True)
    domains = BrandDomainSerializer(many=True, read_only=True)
    localizations = BrandLocalizationSerializer(many=True, read_only=True)

    class Meta:
        model = Brand
        fields = "__all__"
