from rest_framework import serializers

from core.serializers import ReadOnlyModelSerializer

from products.cyed.security.models import LoginAttempt, MfaEnrollment, SecurityEvent


class MfaEnrollmentSerializer(ReadOnlyModelSerializer):
    """
    Administrative view of an enrolment.

    `secret` is excluded by field list, not merely marked read-only: a field
    that is never declared cannot be leaked by a future change that flips a
    flag. The shared secret leaves the server exactly once, at enrolment.
    """

    backup_codes_remaining = serializers.IntegerField(source="unused_backup_code_count",
                                                      read_only=True)

    class Meta:
        model = MfaEnrollment
        fields = [
            "id", "tenant_id", "user_email", "label", "confirmed", "confirmed_at",
            "last_verified_at", "backup_codes_remaining", "created_at", "updated_at",
        ]


class SecurityEventSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = SecurityEvent
        fields = "__all__"


class LoginAttemptSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = LoginAttempt
        fields = "__all__"
