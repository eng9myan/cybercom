from rest_framework import serializers

from .models import (
    DependentProfile,
    FamilyAccessPermission,
    FamilyGroup,
    FamilyMember,
)


class FamilyGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyGroup
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class DependentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DependentProfile
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class FamilyMemberDetailSerializer(serializers.ModelSerializer):
    """Family member with nested dependent profile."""

    dependent_profile = DependentProfileSerializer(read_only=True)

    class Meta:
        model = FamilyMember
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class FamilyGroupDetailSerializer(serializers.ModelSerializer):
    """Family group with nested members."""

    members = FamilyMemberDetailSerializer(many=True, read_only=True)

    class Meta:
        model = FamilyGroup
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class FamilyAccessPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyAccessPermission
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "revoked_at", "revoked_by"]
