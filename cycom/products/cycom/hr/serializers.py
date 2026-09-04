from rest_framework import serializers

from products.cycom.hr.models import Contract, Employee


class EmployeeSerializer(serializers.ModelSerializer):
    # email / phone are EncryptedText (BinaryField storage); DRF would otherwise
    # base64-encode them. The field hands us plain text on read / write.
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=50)

    class Meta:
        model = Employee
        fields = [
            "id", "tenant_id", "employee_number", "first_name", "last_name",
            "email", "phone", "job_title", "department", "hire_date", "status",
            "marital", "spouse_employed", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ContractSerializer(serializers.ModelSerializer):
    hourly_rate = serializers.DecimalField(max_digits=12, decimal_places=4, read_only=True)

    class Meta:
        model = Contract
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
