from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from .models import Tenant, TenantSettings, Company, Branch, Department, WarehousePlaceholder, CostCenterPlaceholder
from .serializers import (
    TenantSerializer, TenantSettingsSerializer, CompanySerializer, BranchSerializer,
    DepartmentSerializer, WarehousePlaceholderSerializer, CostCenterPlaceholderSerializer
)
from apps.identity.models import User, Role, RoleAssignment, UserProfile

class TenantRegisterView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        name = request.data.get("name")
        subdomain = request.data.get("subdomain")
        email = request.data.get("email")
        username = request.data.get("username")
        password = request.data.get("password")

        if not all([name, subdomain, email, username, password]):
            return Response(
                {"error": "All fields are required (name, subdomain, email, username, password)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Tenant.objects.filter(subdomain=subdomain).exists():
            return Response(
                {"error": "Subdomain is already registered"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username is already registered"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Create Tenant
        tenant = Tenant.objects.create(name=name, subdomain=subdomain)

        # 2. Create TenantSettings
        TenantSettings.objects.create(tenant=tenant)

        # 3. Create default Company
        company = Company.objects.create(
            tenant_id=tenant.id,
            name=f"{name} Corp",
            legal_name=name
        )

        # 4. Create default Branch
        branch = Branch.objects.create(
            tenant_id=tenant.id,
            company=company,
            name="Amman HQ",
            address="Amman, Jordan"
        )

        # 5. Create default Roles
        admin_role, _ = Role.objects.get_or_create(
            code="ADMIN",
            name="Administrator",
            tenant_id=tenant.id
        )
        Role.objects.get_or_create(
            code="CASHIER",
            name="POS Cashier",
            tenant_id=tenant.id
        )

        # 6. Create User
        user = User.objects.create(
            username=username,
            email=email,
            tenant_id=tenant.id
        )
        user.set_password(password)
        user.save()

        # Create Profile
        UserProfile.objects.create(user=user, tenant_id=tenant.id)

        # 7. Assign Admin role to User at Branch
        RoleAssignment.objects.create(
            tenant_id=tenant.id,
            user=user,
            role=admin_role,
            branch=branch
        )

        return Response({
            "message": "Tenant provisioned successfully",
            "tenant_id": tenant.id,
            "company_id": company.id,
            "branch_id": branch.id,
            "user_id": user.id
        }, status=status.HTTP_201_CREATED)

class TenantViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TenantSerializer

    def get_queryset(self):
        return Tenant.objects.filter(id=self.request.tenant_id)

class TenantSettingsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TenantSettingsSerializer

    def get_queryset(self):
        return TenantSettings.objects.filter(tenant_id=self.request.tenant_id)

class CompanyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CompanySerializer

    def get_queryset(self):
        return Company.objects.filter(tenant_id=self.request.tenant_id)

class BranchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BranchSerializer

    def get_queryset(self):
        return Branch.objects.filter(tenant_id=self.request.tenant_id)

class DepartmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        return Department.objects.filter(tenant_id=self.request.tenant_id)

class WarehousePlaceholderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WarehousePlaceholderSerializer

    def get_queryset(self):
        return WarehousePlaceholder.objects.filter(tenant_id=self.request.tenant_id)

class CostCenterPlaceholderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CostCenterPlaceholderSerializer

    def get_queryset(self):
        return CostCenterPlaceholder.objects.filter(tenant_id=self.request.tenant_id)
