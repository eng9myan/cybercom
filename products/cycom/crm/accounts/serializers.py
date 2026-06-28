from rest_framework import serializers
from .models import CRMAccount, AccountContact


class CRMAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CRMAccount
        fields = [
            "id", "account_number", "name", "name_ar", "account_type",
            "industry", "phone", "email", "address", "country",
            "assigned_to_id", "annual_revenue", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AccountContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountContact
        fields = [
            "id", "account", "first_name", "last_name", "title",
            "email", "phone", "is_primary", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
