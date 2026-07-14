from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantRegisterView, TenantViewSet, TenantSettingsViewSet, CompanyViewSet,
    BranchViewSet, DepartmentViewSet, WarehousePlaceholderViewSet, CostCenterPlaceholderViewSet
)

router = DefaultRouter()
router.register('info', TenantViewSet, basename='tenant-info')
router.register('settings', TenantSettingsViewSet, basename='tenant-settings')
router.register('companies', CompanyViewSet, basename='company')
router.register('branches', BranchViewSet, basename='branch')
router.register('departments', DepartmentViewSet, basename='department')
router.register('warehouses', WarehousePlaceholderViewSet, basename='warehouse')
router.register('cost-centers', CostCenterPlaceholderViewSet, basename='cost-center')

urlpatterns = [
    path('register/', TenantRegisterView.as_view(), name='tenant-register'),
    path('', include(router.urls)),
]
