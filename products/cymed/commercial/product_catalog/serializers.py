from rest_framework import serializers

from products.cymed.commercial.product_catalog.models import (
    ProductFeatureMatrix,
    ProductLicenseMapping,
    ProductVersion,
)


class ProductVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVersion
        fields = "__all__"


class ProductLicenseMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductLicenseMapping
        fields = "__all__"


class ProductFeatureMatrixSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFeatureMatrix
        fields = "__all__"
