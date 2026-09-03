"""DRF serializers for credentialing models."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    CredentialDocument,
    CredentialingApplication,
    LicenseVerification,
    PrivilegeGrant,
)


class CredentialingApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CredentialingApplication
        fields = "__all__"


class CredentialDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CredentialDocument
        fields = "__all__"


class LicenseVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseVerification
        fields = "__all__"


class PrivilegeGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivilegeGrant
        fields = "__all__"
