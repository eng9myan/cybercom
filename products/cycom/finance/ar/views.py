from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Customer, Invoice, InvoiceLine, Payment, ARAgingBucket
from .serializers import (
    CustomerSerializer,
    InvoiceSerializer,
    InvoiceLineSerializer,
    PaymentSerializer,
    ARAgingBucketSerializer,
)


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------

class CustomerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = Customer.objects.filter(tenant_id=tenant_id).order_by("customer_code")
        return Response(CustomerSerializer(queryset, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(Customer, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        return Response(CustomerSerializer(self._get_object(pk, tenant_id)).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = CustomerSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = CustomerSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        self._get_object(pk, tenant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Invoice
# ---------------------------------------------------------------------------

class InvoiceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = (
            Invoice.objects
            .filter(tenant_id=tenant_id)
            .select_related("customer")
            .prefetch_related("lines")
            .order_by("-invoice_date", "-created_at")
        )
        return Response(InvoiceSerializer(queryset, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = InvoiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvoiceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(Invoice, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        return Response(InvoiceSerializer(self._get_object(pk, tenant_id)).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = InvoiceSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = InvoiceSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        self._get_object(pk, tenant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# InvoiceLine
# ---------------------------------------------------------------------------

class InvoiceLineListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = (
            InvoiceLine.objects
            .filter(tenant_id=tenant_id)
            .select_related("invoice__customer")
            .order_by("invoice__invoice_date", "created_at")
        )
        return Response(InvoiceLineSerializer(queryset, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = InvoiceLineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvoiceLineDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(InvoiceLine, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        return Response(InvoiceLineSerializer(self._get_object(pk, tenant_id)).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = InvoiceLineSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = InvoiceLineSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        self._get_object(pk, tenant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class PaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = (
            Payment.objects
            .filter(tenant_id=tenant_id)
            .select_related("customer", "invoice")
            .order_by("-payment_date", "-created_at")
        )
        return Response(PaymentSerializer(queryset, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(Payment, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        return Response(PaymentSerializer(self._get_object(pk, tenant_id)).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = PaymentSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = PaymentSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        self._get_object(pk, tenant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# ARAgingBucket
# ---------------------------------------------------------------------------

class ARAgingBucketListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = (
            ARAgingBucket.objects
            .filter(tenant_id=tenant_id)
            .select_related("customer")
            .order_by("customer__customer_code", "bucket_label")
        )
        return Response(ARAgingBucketSerializer(queryset, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = ARAgingBucketSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ARAgingBucketDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(ARAgingBucket, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        return Response(ARAgingBucketSerializer(self._get_object(pk, tenant_id)).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = ARAgingBucketSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = ARAgingBucketSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        self._get_object(pk, tenant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
