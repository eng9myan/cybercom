from rest_framework import serializers

from .models import (
    CareTeam,
    CareTeamMember,
    CareTeamAssignment,
    CareTeamRole,
    CoverageSchedule,
)


class CareTeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareTeamMember
        fields = '__all__'


class CareTeamAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareTeamAssignment
        fields = '__all__'


class CoverageScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverageSchedule
        fields = '__all__'


class CareTeamSerializer(serializers.ModelSerializer):
    members = CareTeamMemberSerializer(many=True, read_only=True)
    patient_assignments = CareTeamAssignmentSerializer(many=True, read_only=True)
    coverage_schedules = CoverageScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = CareTeam
        fields = '__all__'


class CareTeamRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareTeamRole
        fields = '__all__'
