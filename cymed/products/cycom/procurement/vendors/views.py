from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import VendorPerformance, VendorQualification
from .serializers import VendorPerformanceSerializer, VendorQualificationSerializer


class VendorQualificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = VendorQualification.objects.filter(tenant_id=tenant_id)
        vendor_id = request.query_params.get("vendor_id")
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)
        serializer = VendorQualificationSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = VendorQualificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorQualificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(VendorQualification, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        return Response(VendorQualificationSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = VendorQualificationSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = VendorQualificationSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VendorPerformanceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = VendorPerformance.objects.filter(tenant_id=tenant_id)
        vendor_id = request.query_params.get("vendor_id")
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)
        serializer = VendorPerformanceSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = VendorPerformanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorPerformanceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(VendorPerformance, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        return Response(VendorPerformanceSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = VendorPerformanceSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = VendorPerformanceSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
