"""
Data migration: seeds the CyMed feature flag registry.
"""

import uuid

from django.db import migrations

PLATFORM_TENANT = uuid.UUID("00000000-0000-0000-0000-000000000001")

FLAGS = [
    # Clinic — Starter
    {
        "code": "clinic.appointments",
        "name": "Appointments",
        "scope": "edition",
        "module": "clinic.appointments",
        "default": True,
    },
    {
        "code": "clinic.reception",
        "name": "Reception",
        "scope": "edition",
        "module": "clinic.reception",
        "default": True,
    },
    {
        "code": "clinic.queue",
        "name": "Queue Management",
        "scope": "edition",
        "module": "clinic.queues",
        "default": True,
    },
    {
        "code": "clinic.consultation",
        "name": "Consultations",
        "scope": "edition",
        "module": "clinic.consultations",
        "default": True,
    },
    {
        "code": "clinic.telemedicine",
        "name": "Telemedicine",
        "scope": "edition",
        "module": "clinic.telemedicine",
        "default": True,
    },
    # Clinic — Professional
    {
        "code": "clinic.specialty_templates",
        "name": "Specialty Templates",
        "scope": "edition",
        "module": "clinic.specialties",
        "default": False,
    },
    {
        "code": "clinic.advanced_scheduling",
        "name": "Advanced Scheduling",
        "scope": "edition",
        "module": "clinic.appointments",
        "default": False,
    },
    {
        "code": "clinic.referral_management",
        "name": "Referral Management",
        "scope": "edition",
        "module": "clinic.referrals",
        "default": False,
    },
    {
        "code": "clinic.insurance_verification",
        "name": "Insurance Verification",
        "scope": "edition",
        "module": "clinic.insurance_bridge",
        "default": False,
    },
    # Clinic — Enterprise
    {
        "code": "clinic.multi_clinic",
        "name": "Multi-Clinic",
        "scope": "edition",
        "module": "clinic.reception",
        "default": False,
    },
    {
        "code": "clinic.enterprise_reporting",
        "name": "Enterprise Reporting",
        "scope": "edition",
        "module": "clinic.consultations",
        "default": False,
    },
    {
        "code": "clinic.advanced_workforce",
        "name": "Advanced Workforce",
        "scope": "edition",
        "module": "clinic.specialties",
        "default": False,
    },
    {
        "code": "clinic.advanced_analytics",
        "name": "Advanced Analytics",
        "scope": "edition",
        "module": "clinic.consultations",
        "default": False,
    },
    {
        "code": "clinic.multi_organization",
        "name": "Multi-Organization",
        "scope": "edition",
        "module": "clinic.reception",
        "default": False,
    },
    # Hospital — Community
    {
        "code": "hospital.adt",
        "name": "Admission/Discharge/Transfer",
        "scope": "edition",
        "module": "hospital.adt",
        "default": True,
    },
    {
        "code": "hospital.bed_management",
        "name": "Bed Management",
        "scope": "edition",
        "module": "hospital.bed_management",
        "default": True,
    },
    {
        "code": "hospital.emergency",
        "name": "Emergency Department",
        "scope": "edition",
        "module": "hospital.emergency",
        "default": True,
    },
    {
        "code": "hospital.inpatient",
        "name": "Inpatient Care",
        "scope": "edition",
        "module": "hospital.inpatient",
        "default": True,
    },
    {
        "code": "hospital.nursing",
        "name": "Nursing",
        "scope": "edition",
        "module": "hospital.nursing",
        "default": True,
    },
    {
        "code": "hospital.discharge",
        "name": "Discharge Management",
        "scope": "edition",
        "module": "hospital.discharge",
        "default": True,
    },
    # Hospital — Enterprise
    {
        "code": "hospital.icu",
        "name": "Intensive Care Unit",
        "scope": "edition",
        "module": "hospital.icu",
        "default": False,
    },
    {
        "code": "hospital.operating_room",
        "name": "Operating Room",
        "scope": "edition",
        "module": "hospital.operating_room",
        "default": False,
    },
    {
        "code": "hospital.anesthesia",
        "name": "Anesthesia",
        "scope": "edition",
        "module": "hospital.anesthesia",
        "default": False,
    },
    {
        "code": "hospital.maternity",
        "name": "Maternity / Obstetrics",
        "scope": "edition",
        "module": "hospital.maternity",
        "default": False,
    },
    {
        "code": "hospital.transfer_center",
        "name": "Transfer Center",
        "scope": "edition",
        "module": "hospital.transfer_center",
        "default": False,
    },
    {
        "code": "hospital.capacity_management",
        "name": "Capacity Management",
        "scope": "edition",
        "module": "hospital.capacity_management",
        "default": False,
    },
    # Hospital — Medical City
    {
        "code": "hospital.clinical_command_center",
        "name": "Clinical Command Center",
        "scope": "edition",
        "module": "hospital.clinical_command_center",
        "default": False,
    },
    {
        "code": "hospital.multi_hospital",
        "name": "Multi-Hospital",
        "scope": "edition",
        "module": "hospital.adt",
        "default": False,
    },
    {
        "code": "hospital.academic_center",
        "name": "Academic / Teaching Center",
        "scope": "edition",
        "module": "hospital.inpatient",
        "default": False,
    },
    {
        "code": "hospital.regional_network",
        "name": "Regional Health Network",
        "scope": "edition",
        "module": "hospital.capacity_management",
        "default": False,
    },
    # Government features
    {
        "code": "platform.government_cloud",
        "name": "Government Cloud Deployment",
        "scope": "government",
        "module": "",
        "default": False,
    },
    {
        "code": "platform.air_gapped",
        "name": "Air-Gapped Deployment",
        "scope": "government",
        "module": "",
        "default": False,
    },
    {
        "code": "platform.white_label",
        "name": "White Label",
        "scope": "edition",
        "module": "",
        "default": False,
    },
    # Beta flags
    {
        "code": "cyai.clinical_decision_support",
        "name": "AI Clinical Decision Support",
        "scope": "beta",
        "module": "",
        "default": False,
    },
    {
        "code": "cyai.predictive_analytics",
        "name": "AI Predictive Analytics",
        "scope": "beta",
        "module": "",
        "default": False,
    },
]


def seed_flags(apps, schema_editor):
    FeatureFlag = apps.get_model("commercial_feature_flags", "FeatureFlag")
    for f in FLAGS:
        FeatureFlag.objects.get_or_create(
            code=f["code"],
            defaults={
                "id": uuid.uuid4(),
                "tenant_id": PLATFORM_TENANT,
                "name": f["name"],
                "scope": f["scope"],
                "module_code": f["module"],
                "default_enabled": f["default"],
            },
        )


def unseed_flags(apps, schema_editor):
    FeatureFlag = apps.get_model("commercial_feature_flags", "FeatureFlag")
    FeatureFlag.objects.filter(code__in=[f["code"] for f in FLAGS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("commercial_feature_flags", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_flags, unseed_flags),
    ]
