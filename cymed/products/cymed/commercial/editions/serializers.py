from rest_framework import serializers

from products.cymed.commercial.editions.models import (
    EditionFeature,
    EditionLimit,
    EditionModule,
    ProductCatalogEntry,
    ProductEdition,
)


class ProductCatalogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCatalogEntry
        fields = "__all__"


class EditionFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditionFeature
        fields = "__all__"


class EditionLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditionLimit
        fields = "__all__"


class EditionModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditionModule
        fields = "__all__"


class ProductEditionSerializer(serializers.ModelSerializer):
    features = EditionFeatureSerializer(many=True, read_only=True)
    limits = EditionLimitSerializer(many=True, read_only=True)
    modules = EditionModuleSerializer(many=True, read_only=True)

    class Meta:
        model = ProductEdition
        fields = "__all__"
