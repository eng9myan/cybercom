"""Shared serializer bases."""

from rest_framework import serializers


class ReadOnlyModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer whose every field is read-only.

    Use for append-only or system-generated records (audit trails, approval
    steps, goods receipts) that must never be written directly over the API.

    Prefer this to `read_only_fields = fields`: when `fields = "__all__"` that
    idiom assigns a *string*, and DRF raises
    ``TypeError: The `read_only_fields` option must be a list or tuple``
    the first time the serializer builds its fields.
    """

    def get_fields(self):
        fields = super().get_fields()
        for field in fields.values():
            field.read_only = True
        return fields
