from rest_framework import serializers

from products.cycom.project.models import Project, Task, TimesheetEntry
from products.cycom.project.scheduling import would_create_cycle


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True, default="")

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate_depends_on(self, value):
        """Refuse a dependency that would make the graph unschedulable.
        Rejected at save time rather than at render time, so a cycle can
        never be stored and then break the Gantt for everyone who opens it."""
        if not value:
            return value
        if self.instance is not None:
            if any(dep.pk == self.instance.pk for dep in value):
                raise serializers.ValidationError("A task cannot depend on itself.")
            if would_create_cycle(self.instance, [d.pk for d in value]):
                raise serializers.ValidationError(
                    "These dependencies would create a cycle -- the resulting "
                    "schedule would have no valid task order."
                )
        return value


class TimesheetEntrySerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source="task.name", read_only=True, default="")

    class Meta:
        model = TimesheetEntry
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
