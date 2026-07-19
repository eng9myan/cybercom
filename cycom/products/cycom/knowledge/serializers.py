from rest_framework import serializers

from products.cycom.knowledge.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate_parent(self, value):
        if value and self.instance and value.id == self.instance.id:
            raise serializers.ValidationError("An article cannot be its own parent.")
        return value
