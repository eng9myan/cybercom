from rest_framework.routers import DefaultRouter
from .views import (
    DeploymentRecordViewSet, EnvironmentCheckViewSet, DeploymentStepViewSet,
    TenantProvisionViewSet, BackupRecordViewSet, HealthCheckSnapshotViewSet,
    UpgradeRecordViewSet,
)

router = DefaultRouter()
router.register("records", DeploymentRecordViewSet, basename="deployment-record")
router.register("environment-checks", EnvironmentCheckViewSet, basename="environment-check")
router.register("steps", DeploymentStepViewSet, basename="deployment-step")
router.register("tenant-provisions", TenantProvisionViewSet, basename="tenant-provision")
router.register("backups", BackupRecordViewSet, basename="backup-record")
router.register("health-snapshots", HealthCheckSnapshotViewSet, basename="health-snapshot")
router.register("upgrades", UpgradeRecordViewSet, basename="upgrade-record")

urlpatterns = router.urls
