from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccountContact, CRMAccount
from .serializers import AccountContactSerializer, CRMAccountSerializer


class CRMAccountListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = CRMAccount.objects.filter(tenant_id=getattr(request, "tenant_id", None))
        return Response(CRMAccountSerializer(qs, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        s = CRMAccountSerializer(data=request.data)
        if s.is_valid():
            s.save(tenant_id=tenant_id)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class CRMAccountDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(CRMAccount, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        return Response(
            CRMAccountSerializer(self.get_object(pk, getattr(request, "tenant_id", None))).data
        )

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        s = CRMAccountSerializer(obj, data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        s = CRMAccountSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self.get_object(pk, getattr(request, "tenant_id", None)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountContactListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = AccountContact.objects.filter(tenant_id=getattr(request, "tenant_id", None))
        return Response(AccountContactSerializer(qs, many=True).data)

    def post(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        s = AccountContactSerializer(data=request.data)
        if s.is_valid():
            s.save(tenant_id=tenant_id)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountContactDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, tenant_id):
        return get_object_or_404(AccountContact, pk=pk, tenant_id=tenant_id)

    def get(self, request, pk):
        return Response(
            AccountContactSerializer(self.get_object(pk, getattr(request, "tenant_id", None))).data
        )

    def put(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        s = AccountContactSerializer(obj, data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, getattr(request, "tenant_id", None))
        s = AccountContactSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        self.get_object(pk, getattr(request, "tenant_id", None)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
