from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Account, JournalEntry, JournalLine
from .serializers import AccountSerializer, JournalEntrySerializer, JournalLineSerializer


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------

class AccountListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = Account.objects.filter(tenant_id=tenant_id).order_by("code")
        serializer = AccountSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(Account, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        return Response(AccountSerializer(obj).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = AccountSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = AccountSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# JournalEntry
# ---------------------------------------------------------------------------

class JournalEntryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = (
            JournalEntry.objects
            .filter(tenant_id=tenant_id)
            .prefetch_related("lines__account")
            .order_by("-entry_date", "-created_at")
        )
        serializer = JournalEntrySerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = JournalEntrySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JournalEntryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(JournalEntry, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        return Response(JournalEntrySerializer(obj).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = JournalEntrySerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = JournalEntrySerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# JournalLine
# ---------------------------------------------------------------------------

class JournalLineListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        queryset = (
            JournalLine.objects
            .filter(tenant_id=tenant_id)
            .select_related("journal", "account")
            .order_by("journal__entry_date", "created_at")
        )
        serializer = JournalLineSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        serializer = JournalLineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(tenant_id=tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JournalLineDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_object(self, pk, tenant_id):
        return get_object_or_404(JournalLine, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        return Response(JournalLineSerializer(obj).data)

    def put(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = JournalLineSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        serializer = JournalLineSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        tenant_id = getattr(request, "tenant_id", None)
        obj = self._get_object(pk, tenant_id)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
