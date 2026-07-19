from rest_framework import serializers

from products.cycom.todo.models import Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "done_at"]
