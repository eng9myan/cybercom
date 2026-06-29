from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from platform.cydata.models import (
    CDCPipelineLog,
    DataAsset,
    DataLineage,
    DataQualityRule,
    MasterDataMap,
)
from platform.cydata.serializers import (
    CDCPipelineLogSerializer,
    DataAssetSerializer,
    DataLineageSerializer,
    DataQualityEvaluateRequestSerializer,
    DataQualityRuleSerializer,
    MasterDataMapSerializer,
    MasterDataMatchRequestSerializer,
)
from platform.cydata.services import CDCPipelineClient, DataQualityEngine, MasterDataReconciler


class DataAssetViewSet(viewsets.ModelViewSet):
    queryset = DataAsset.objects.all().order_by("name")
    serializer_class = DataAssetSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="evaluate")
    def evaluate_quality(self, request, pk=None):
        asset = self.get_object()
        serializer = DataQualityEvaluateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        res = DataQualityEngine.evaluate_asset(
            asset=asset, records=serializer.validated_data["records"]
        )
        return Response(res, status=status.HTTP_200_OK)


class DataLineageViewSet(viewsets.ModelViewSet):
    queryset = DataLineage.objects.all().order_by("-updated_at")
    serializer_class = DataLineageSerializer
    permission_classes = [IsAuthenticated]


class DataQualityRuleViewSet(viewsets.ModelViewSet):
    queryset = DataQualityRule.objects.all().order_by("asset", "column_name")
    serializer_class = DataQualityRuleSerializer
    permission_classes = [IsAuthenticated]


class MasterDataMapViewSet(viewsets.ModelViewSet):
    queryset = MasterDataMap.objects.all().order_by("entity_type", "golden_record_id")
    serializer_class = MasterDataMapSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="match")
    def match_record(self, request):
        serializer = MasterDataMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mapping = MasterDataReconciler.match_and_link(
            entity_type=serializer.validated_data["entity_type"],
            source_system=serializer.validated_data["source_system"],
            source_id=serializer.validated_data["source_id"],
            matching_fields=serializer.validated_data["matching_fields"],
        )
        return Response(MasterDataMapSerializer(mapping).data, status=status.HTTP_200_OK)


class CDCPipelineLogViewSet(viewsets.ModelViewSet):
    queryset = CDCPipelineLog.objects.all().order_by("-synced_at")
    serializer_class = CDCPipelineLogSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="sync")
    def sync_records(self, request):
        tenant_id = request.data.get("tenant_id")
        table_name = request.data.get("table_name")
        records_count = request.data.get("records_count", 0)

        if not tenant_id or not table_name:
            return Response(
                {"detail": "tenant_id and table_name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log = CDCPipelineClient.trigger_cdc_sync(
            tenant_id=tenant_id, table_name=table_name, records_count=int(records_count)
        )
        return Response(CDCPipelineLogSerializer(log).data, status=status.HTTP_201_CREATED)
