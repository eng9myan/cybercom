from rest_framework import serializers

from products.cycom.blog.models import BlogPost


class BlogPostSerializer(serializers.ModelSerializer):
    """Admin/authenticated CRUD — full fields."""

    class Meta:
        model = BlogPost
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "slug", "published_at", "created_at", "updated_at"]


class PublicBlogPostListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ["id", "title", "slug", "excerpt", "cover_image_url", "author_name", "published_at"]


class PublicBlogPostDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ["id", "title", "slug", "content", "cover_image_url", "author_name", "published_at"]
