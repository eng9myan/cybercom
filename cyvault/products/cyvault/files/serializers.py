from rest_framework import serializers

from products.cyvault.files.models import FileObject


class FileObjectSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = FileObject
        fields = [
            "id",
            "tenant_id",
            "file",
            "download_url",
            "original_filename",
            "content_type",
            "size_bytes",
            "checksum_sha256",
            "category",
            "linked_model",
            "linked_id",
            "uploaded_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tenant_id",
            "download_url",
            "content_type",
            "size_bytes",
            "checksum_sha256",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"file": {"write_only": True}}

    def get_download_url(self, obj: FileObject) -> str | None:
        if not obj.file:
            return None
        return obj.file.url

    def create(self, validated_data):
        upload = validated_data["file"]
        validated_data.setdefault("original_filename", upload.name)
        validated_data["content_type"] = getattr(upload, "content_type", "") or ""
        validated_data["size_bytes"] = upload.size
        instance = FileObject(**validated_data)
        instance.file = upload
        instance.save()
        instance.checksum_sha256 = instance.compute_checksum()
        instance.save(update_fields=["checksum_sha256"])
        return instance
