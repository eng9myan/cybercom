from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AssetCategory, Depreciation, FixedAsset
from .serializers import AssetCategorySerializer, DepreciationSerializer, FixedAssetSerializer


class AssetCategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = AssetCategory.objects.filter(tenant_id=tenant_id)
        serializer = AssetCategorySerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = AssetCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssetCategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(AssetCategory, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        return Response(AssetCategorySerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = AssetCategorySerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = AssetCategorySerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FixedAssetListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = FixedAsset.objects.filter(tenant_id=tenant_id).select_related("category")
        serializer = FixedAssetSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = FixedAssetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FixedAssetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(FixedAsset, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        return Response(FixedAssetSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = FixedAssetSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = FixedAssetSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DepreciationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = Depreciation.objects.filter(tenant_id=tenant_id)
        asset_id = request.query_params.get("asset")
        if asset_id:
            qs = qs.filter(asset_id=asset_id)
        serializer = DepreciationSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = DepreciationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepreciationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(Depreciation, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        return Response(DepreciationSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = DepreciationSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = DepreciationSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
