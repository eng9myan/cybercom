from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GoodsReceipt, GoodsReceiptLine, POLine, PurchaseOrder
from .serializers import (
    GoodsReceiptLineSerializer,
    GoodsReceiptSerializer,
    POLineSerializer,
    PurchaseOrderSerializer,
)


class PurchaseOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = PurchaseOrder.objects.filter(tenant_id=tenant_id)
        serializer = PurchaseOrderSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(PurchaseOrder, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        return Response(PurchaseOrderSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = PurchaseOrderSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = PurchaseOrderSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class POLineListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = POLine.objects.filter(tenant_id=tenant_id)
        po_id = request.query_params.get("po")
        if po_id:
            qs = qs.filter(po_id=po_id)
        serializer = POLineSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = POLineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class POLineDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(POLine, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        return Response(POLineSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = POLineSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = POLineSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoodsReceiptListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = GoodsReceipt.objects.filter(tenant_id=tenant_id)
        po_id = request.query_params.get("po")
        if po_id:
            qs = qs.filter(po_id=po_id)
        serializer = GoodsReceiptSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = GoodsReceiptSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoodsReceiptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(GoodsReceipt, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        return Response(GoodsReceiptSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = GoodsReceiptSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = GoodsReceiptSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoodsReceiptLineListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = GoodsReceiptLine.objects.filter(tenant_id=tenant_id)
        receipt_id = request.query_params.get("goods_receipt")
        if receipt_id:
            qs = qs.filter(goods_receipt_id=receipt_id)
        serializer = GoodsReceiptLineSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = GoodsReceiptLineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoodsReceiptLineDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(GoodsReceiptLine, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        return Response(GoodsReceiptLineSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = GoodsReceiptLineSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        serializer = GoodsReceiptLineSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
