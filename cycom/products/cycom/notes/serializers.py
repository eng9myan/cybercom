from rest_framework import serializers

from products.cycom.notes.models import Note


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
