from rest_framework import serializers

from products.cyed.library.models import Book, LibraryPolicy, Loan, get_policy


class LibraryPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryPolicy
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "copies_available", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data.setdefault("copies_available", validated_data.get("copies_total", 1))
        return super().create(validated_data)


class LoanSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    book_title = serializers.CharField(source="book.title", read_only=True)
    days_overdue = serializers.SerializerMethodField()
    outstanding_fine = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = "__all__"
        # `due_on` is set from policy, and every fine field moves through an
        # action — a fine that could be PATCHed to zero is not a fine.
        read_only_fields = [
            "id", "tenant_id", "status", "returned_on", "created_at", "updated_at",
            "due_on", "fine_amount", "fine_waived", "fine_waived_by",
            "fine_waive_reason", "renewed_count",
        ]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip() if obj.student_id else ""

    def get_days_overdue(self, obj) -> int:
        return obj.days_overdue()

    def get_outstanding_fine(self, obj) -> str:
        return str(obj.outstanding_fine(get_policy(obj.tenant_id)))
