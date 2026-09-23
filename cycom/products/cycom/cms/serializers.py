from rest_framework import serializers

from products.cycom.cms.models import CONTAINER_BLOCK_TYPES, Page, PageBlock
from products.cycom.cms.services import build_block_tree


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "slug", "created_at", "updated_at"]


class PageBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageBlock
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        block_type = attrs.get("block_type", getattr(self.instance, "block_type", None))
        page = attrs.get("page", getattr(self.instance, "page", None))

        if parent is not None:
            if parent.page_id != page.id:
                raise serializers.ValidationError({"parent": "Parent block must belong to the same page."})
            if parent.block_type not in CONTAINER_BLOCK_TYPES:
                raise serializers.ValidationError({"parent": f"'{parent.block_type}' cannot contain child blocks."})
            if block_type in CONTAINER_BLOCK_TYPES:
                raise serializers.ValidationError(
                    {"block_type": "A section/columns block cannot be nested inside another block."}
                )
        return attrs


class PageTreeSerializer(serializers.ModelSerializer):
    """Full page + its nested block tree, for the builder canvas and the
    public renderer alike."""

    blocks = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "title", "slug", "meta_description", "is_published", "is_homepage", "blocks"]

    def get_blocks(self, page):
        return build_block_tree(page)
