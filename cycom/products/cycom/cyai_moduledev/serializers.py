from rest_framework import serializers

from products.cycom.cyai_moduledev.models import ModuleDevRequest


class ModuleDevRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleDevRequest
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "status", "discovery_results", "messages", "functional_spec",
            "functional_spec_confirmed_by", "functional_spec_confirmed_at", "technical_design",
            "technical_design_approved_by", "technical_design_approved_at", "module_name",
            "workspace_path", "generated_files", "lint_results", "build_results", "test_results",
            "diff_text", "staging_deployed_at", "production_approved_by", "production_approved_at",
            "deployed_at", "deploy_commit_sha", "rollback_manifest", "rejection_reason",
            "created_at", "updated_at",
        ]


class StartRequestSerializer(serializers.Serializer):
    product_description = serializers.CharField()


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField()


class GenerateCodeSerializer(serializers.Serializer):
    module_name = serializers.CharField()


class ApproveProductionSerializer(serializers.Serializer):
    confirm_production = serializers.BooleanField()


class DeployProductionSerializer(serializers.Serializer):
    confirm_push = serializers.BooleanField()
