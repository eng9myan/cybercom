from rest_framework import serializers

from .models import EphemeralEnvironment


class EphemeralEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EphemeralEnvironment
        fields = [
            "id", "name", "tenant", "app", "git_ref", "status", "public_ip",
            "terraform_instance_id", "error_message", "requested_by",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "public_ip", "terraform_instance_id",
            "error_message", "requested_by", "created_at", "updated_at",
        ]
