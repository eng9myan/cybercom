from rest_framework import serializers

from products.cycom.forum.models import ForumReply, ForumThread


class ForumReplySerializer(serializers.ModelSerializer):
    """Staff moderation — full fields."""

    class Meta:
        model = ForumReply
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ForumThreadSerializer(serializers.ModelSerializer):
    """Staff moderation — full fields."""

    class Meta:
        model = ForumThread
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "slug", "created_at", "updated_at"]


class PublicReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumReply
        fields = ["id", "body", "author_name", "is_accepted", "created_at"]


class PublicThreadListSerializer(serializers.ModelSerializer):
    reply_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ForumThread
        fields = ["id", "title", "slug", "author_name", "is_pinned", "is_locked", "reply_count", "created_at"]


class PublicThreadDetailSerializer(serializers.ModelSerializer):
    replies = PublicReplySerializer(many=True, read_only=True)

    class Meta:
        model = ForumThread
        fields = ["id", "title", "slug", "body", "author_name", "is_pinned", "is_locked", "replies", "created_at"]


class PublicThreadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumThread
        fields = ["title", "body", "author_name", "author_email"]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title is required.")
        return value


class PublicReplyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumReply
        fields = ["body", "author_name", "author_email"]

    def validate_body(self, value):
        if not value.strip():
            raise serializers.ValidationError("Reply body is required.")
        return value
