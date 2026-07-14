from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Bill, BillLine, Vendor, VendorPayment
from .serializers import (
    BillLineSerializer,
    BillSerializer,
    VendorPaymentSerializer,
    VendorSerializer,
)

# ---------------------------------------------------------------------------
# Vendor
# ---------------------------------------------------------------------------


class VendorListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = Vendor.objects.filter(tenant_id=tenant_id).order_by("vendor_code")
        return Response(VendorSerializer(queryset, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(Vendor, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        return Response(VendorSerializer(self._get_object(pk, tenant_id)).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = VendorSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = VendorSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        self._get_object(pk, tenant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Bill
# ---------------------------------------------------------------------------


class BillListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = (
            Bill.objects.filter(tenant_id=tenant_id)
            .select_related("vendor")
            .prefetch_related("lines")
            .order_by("-bill_date", "-created_at")
        )
        return Response(BillSerializer(queryset, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = BillSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BillDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(Bill, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        return Response(BillSerializer(self._get_object(pk, tenant_id)).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = BillSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = BillSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        self._get_object(pk, tenant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# BillLine
# ---------------------------------------------------------------------------


class BillLineListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = (
            BillLine.objects.filter(tenant_id=tenant_id)
            .select_related("bill__vendor")
            .order_by("bill__bill_date", "created_at")
        )
        return Response(BillLineSerializer(queryset, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = BillLineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BillLineDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(BillLine, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        return Response(BillLineSerializer(self._get_object(pk, tenant_id)).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = BillLineSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = BillLineSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        self._get_object(pk, tenant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# VendorPayment
# ---------------------------------------------------------------------------


class VendorPaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = (
            VendorPayment.objects.filter(tenant_id=tenant_id)
            .select_related("vendor", "bill")
            .order_by("-payment_date", "-created_at")
        )
        return Response(VendorPaymentSerializer(queryset, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = VendorPaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorPaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(VendorPayment, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        return Response(VendorPaymentSerializer(self._get_object(pk, tenant_id)).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = VendorPaymentSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = VendorPaymentSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        self._get_object(pk, tenant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
