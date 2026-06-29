from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from platform.cyai.models import GuardrailPolicy, InferenceLog, ModelConfig, PromptTemplate
from platform.cyai.serializers import (
    GuardrailPolicySerializer,
    InferenceLogSerializer,
    InferenceRequestSerializer,
    ModelConfigSerializer,
    PromptTemplateSerializer,
    RAGRequestSerializer,
)
from platform.cyai.services import ModelGateway, RAGService


class ModelConfigViewSet(viewsets.ModelViewSet):
    queryset = ModelConfig.objects.all().order_by("name")
    serializer_class = ModelConfigSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="generate")
    def generate_text(self, request, pk=None):
        config = self.get_object()
        serializer = InferenceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        res = ModelGateway.generate_completion(
            tenant_id=str(serializer.validated_data["tenant_id"]),
            config=config,
            prompt=serializer.validated_data["prompt"],
            variables=serializer.validated_data.get("variables"),
        )
        return Response(res, status=status.HTTP_200_OK)


class PromptTemplateViewSet(viewsets.ModelViewSet):
    queryset = PromptTemplate.objects.all().order_by("name")
    serializer_class = PromptTemplateSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="rag")
    def run_rag(self, request, pk=None):
        template = self.get_object()
        serializer = RAGRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Retrieve default ModelConfig for RAG execution
        config = ModelConfig.objects.filter(active=True).first()
        if not config:
            return Response(
                {"detail": "No active AI models configured"}, status=status.HTTP_400_BAD_REQUEST
            )

        res = RAGService.query_context_and_generate(
            tenant_id=str(serializer.validated_data["tenant_id"]),
            config=config,
            template=template,
            query=serializer.validated_data["query"],
            variables=serializer.validated_data["variables"],
        )
        return Response(res, status=status.HTTP_200_OK)


class GuardrailPolicyViewSet(viewsets.ModelViewSet):
    queryset = GuardrailPolicy.objects.all().order_by("name")
    serializer_class = GuardrailPolicySerializer
    permission_classes = [IsAuthenticated]


class InferenceLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InferenceLog.objects.all().order_by("-created_at")
    serializer_class = InferenceLogSerializer
    permission_classes = [IsAuthenticated]
