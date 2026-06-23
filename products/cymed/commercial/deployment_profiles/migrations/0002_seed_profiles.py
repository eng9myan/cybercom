"""
Data migration: seeds the standard CyMed deployment profiles and their capabilities.
"""
from django.db import migrations
import uuid

PLATFORM_TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")

PROFILES = [
    {
        "code": "saas",
        "name": "CyMed SaaS",
        "profile_type": "saas",
        "requires_offline_license": False,
        "supports_auto_update": True,
        "supports_telemetry": True,
        "requires_government_clearance": False,
        "capabilities": ["online_activation", "auto_update", "telemetry", "cloud_backup", "multi_tenant"],
    },
    {
        "code": "private_cloud",
        "name": "Private Cloud",
        "profile_type": "private_cloud",
        "requires_offline_license": False,
        "supports_auto_update": True,
        "supports_telemetry": True,
        "requires_government_clearance": False,
        "capabilities": ["online_activation", "auto_update", "telemetry", "local_backup"],
    },
    {
        "code": "government_cloud",
        "name": "Government Cloud",
        "profile_type": "government_cloud",
        "requires_offline_license": True,
        "supports_auto_update": False,
        "supports_telemetry": False,
        "requires_government_clearance": True,
        "capabilities": ["offline_activation", "manual_update", "local_backup", "fips_compliance"],
    },
    {
        "code": "hybrid",
        "name": "Hybrid Deployment",
        "profile_type": "hybrid",
        "requires_offline_license": False,
        "supports_auto_update": True,
        "supports_telemetry": True,
        "requires_government_clearance": False,
        "capabilities": ["online_activation", "auto_update", "telemetry", "local_backup", "cloud_sync"],
    },
    {
        "code": "air_gapped",
        "name": "Air-Gapped",
        "profile_type": "air_gapped",
        "requires_offline_license": True,
        "supports_auto_update": False,
        "supports_telemetry": False,
        "requires_government_clearance": True,
        "capabilities": ["offline_activation", "manual_update", "local_backup", "fips_compliance", "data_sovereignty"],
    },
]


def seed_profiles(apps, schema_editor):
    DeploymentProfile = apps.get_model("commercial_deployment_profiles", "DeploymentProfile")
    DeploymentCapability = apps.get_model("commercial_deployment_profiles", "DeploymentCapability")

    for p in PROFILES:
        profile, _ = DeploymentProfile.objects.get_or_create(
            code=p["code"],
            defaults={
                "id": uuid.uuid4(),
                "tenant_id": PLATFORM_TENANT,
                "name": p["name"],
                "profile_type": p["profile_type"],
                "requires_offline_license": p["requires_offline_license"],
                "supports_auto_update": p["supports_auto_update"],
                "supports_telemetry": p["supports_telemetry"],
                "requires_government_clearance": p["requires_government_clearance"],
            },
        )
        for cap in p["capabilities"]:
            DeploymentCapability.objects.get_or_create(
                profile=profile,
                capability_code=cap,
                defaults={
                    "id": uuid.uuid4(),
                    "tenant_id": PLATFORM_TENANT,
                    "is_supported": True,
                },
            )


def unseed_profiles(apps, schema_editor):
    DeploymentProfile = apps.get_model("commercial_deployment_profiles", "DeploymentProfile")
    DeploymentProfile.objects.filter(code__in=[p["code"] for p in PROFILES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("commercial_deployment_profiles", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_profiles, unseed_profiles),
    ]
