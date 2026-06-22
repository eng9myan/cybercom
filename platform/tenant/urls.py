"""
CyberCom Multi-Tenant Framework — URL Router.
Base: /api/v1/tenants/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from platform.tenant import views

router = DefaultRouter()
router.register(r"", views.TenantViewSet, basename="tenant")
router.register(r"profiles", views.TenantProfileViewSet, basename="tenant-profile")
router.register(r"configurations", views.TenantConfigurationViewSet, basename="tenant-configuration")
router.register(r"brandings", views.TenantBrandingViewSet, basename="tenant-branding")
router.register(r"subscriptions", views.TenantSubscriptionViewSet, basename="tenant-subscription")
router.register(r"licenses", views.TenantLicenseViewSet, basename="tenant-license")
router.register(r"environments", views.TenantEnvironmentViewSet, basename="tenant-environment")
router.register(r"regions", views.TenantRegionViewSet, basename="tenant-region")
router.register(r"deployment-profiles", views.TenantDeploymentProfileViewSet, basename="tenant-deployment-profile")
router.register(r"feature-flags", views.TenantFeatureFlagViewSet, basename="tenant-feature-flag")
router.register(r"domains", views.TenantDomainViewSet, basename="tenant-domain")
router.register(r"sso", views.TenantSSOConfigurationViewSet, basename="tenant-sso")
router.register(r"storage-policies", views.TenantStoragePolicyViewSet, basename="tenant-storage-policy")
router.register(r"retention-policies", views.TenantRetentionPolicyViewSet, basename="tenant-retention-policy")
router.register(r"compliance", views.TenantComplianceProfileViewSet, basename="tenant-compliance")
router.register(r"audit-configurations", views.TenantAuditConfigurationViewSet, basename="tenant-audit-configuration")

urlpatterns = [
    path("healthz/", views.tenant_health, name="tenant-health"),
    path("metrics", views.tenant_metrics, name="tenant-metrics"),
    path("", include(router.urls)),
]
