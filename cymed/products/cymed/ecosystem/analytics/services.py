"""Service layer for the CyMed ecosystem analytics sub-app."""
from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import (
    AnalyticsExport,
    AnalyticsSnapshot,
    Dashboard,
    DashboardWidget,
)


@transaction.atomic
def snapshot_patient_flow(
    *,
    tenant_id: uuid.UUID | None,
    snapshot_date: Any,
) -> AnalyticsSnapshot:
    # Hook: real aggregation runs in a downstream ETL job; this is a placeholder.
    payload = {
        "visits": 0,
        "admissions": 0,
        "discharges": 0,
        "telehealth": 0,
    }
    snapshot, _ = AnalyticsSnapshot.objects.update_or_create(
        tenant_id=tenant_id,
        snapshot_date=snapshot_date,
        kind=AnalyticsSnapshot.Kind.PATIENT_FLOW,
        defaults={"payload": payload, "generated_at": timezone.now()},
    )
    return snapshot


@transaction.atomic
def snapshot_revenue(
    *,
    tenant_id: uuid.UUID | None,
    snapshot_date: Any,
) -> AnalyticsSnapshot:
    # Hook: real aggregation runs in a downstream ETL job; this is a placeholder.
    payload = {
        "gross": 0,
        "net": 0,
        "cash": 0,
        "insurance": 0,
        "ar_outstanding": 0,
    }
    snapshot, _ = AnalyticsSnapshot.objects.update_or_create(
        tenant_id=tenant_id,
        snapshot_date=snapshot_date,
        kind=AnalyticsSnapshot.Kind.REVENUE,
        defaults={"payload": payload, "generated_at": timezone.now()},
    )
    return snapshot


@transaction.atomic
def snapshot_referral_network(
    *,
    tenant_id: uuid.UUID | None,
    snapshot_date: Any,
) -> AnalyticsSnapshot:
    # Hook: real aggregation runs in a downstream ETL job; this is a placeholder.
    payload = {
        "in_counts_by_target_kind": {},
        "out_counts_by_target_kind": {},
        "top_sources": [],
        "top_destinations": [],
    }
    snapshot, _ = AnalyticsSnapshot.objects.update_or_create(
        tenant_id=tenant_id,
        snapshot_date=snapshot_date,
        kind=AnalyticsSnapshot.Kind.REFERRAL_NETWORK,
        defaults={"payload": payload, "generated_at": timezone.now()},
    )
    return snapshot


@transaction.atomic
def snapshot_provider_utilisation(
    *,
    tenant_id: uuid.UUID | None,
    snapshot_date: Any,
) -> AnalyticsSnapshot:
    # Hook: real aggregation runs in a downstream ETL job; this is a placeholder.
    payload = {
        "providers": [],
        "average_utilisation": 0,
        "capacity_hours": 0,
        "booked_hours": 0,
    }
    snapshot, _ = AnalyticsSnapshot.objects.update_or_create(
        tenant_id=tenant_id,
        snapshot_date=snapshot_date,
        kind=AnalyticsSnapshot.Kind.PROVIDER_UTILISATION,
        defaults={"payload": payload, "generated_at": timezone.now()},
    )
    return snapshot


@transaction.atomic
def create_dashboard(
    *,
    tenant_id: uuid.UUID | None,
    code: str,
    title: str,
    title_ar: str = "",
    audience: str,
    layout: dict | None = None,
    shared_with_tenant_ids: list | None = None,
) -> Dashboard:
    dashboard = Dashboard.objects.create(
        tenant_id=tenant_id,
        code=code,
        title=title,
        title_ar=title_ar,
        audience=audience,
        layout=layout or {},
        shared_with_tenant_ids=shared_with_tenant_ids or [],
    )
    return dashboard


@transaction.atomic
def add_widget(
    *,
    dashboard_id: uuid.UUID,
    kind: str,
    title: str,
    data_source: str,
    params: dict | None = None,
    position: int = 0,
) -> DashboardWidget:
    dashboard = Dashboard.objects.get(pk=dashboard_id)
    widget = DashboardWidget.objects.create(
        dashboard=dashboard,
        position=position,
        kind=kind,
        title=title,
        data_source=data_source,
        params=params or {},
    )
    return widget


@transaction.atomic
def queue_export(
    *,
    tenant_id: uuid.UUID | None,
    requested_by_profile_id: uuid.UUID | None,
    kind: str,
    filter_payload: dict,
) -> AnalyticsExport:
    export = AnalyticsExport.objects.create(
        tenant_id=tenant_id,
        requested_by_profile_id=requested_by_profile_id,
        kind=kind,
        filter_payload=filter_payload or {},
        status=AnalyticsExport.Status.QUEUED,
    )
    return export


@transaction.atomic
def complete_export(
    *,
    export_id: uuid.UUID,
    file_url: str,
) -> AnalyticsExport:
    export = AnalyticsExport.objects.get(pk=export_id)
    export.status = AnalyticsExport.Status.COMPLETED
    export.file_url = file_url
    export.completed_at = timezone.now()
    export.error_message = ""
    export.save(
        update_fields=[
            "status",
            "file_url",
            "completed_at",
            "error_message",
        ]
    )
    return export


@transaction.atomic
def fail_export(
    *,
    export_id: uuid.UUID,
    error_message: str,
) -> AnalyticsExport:
    export = AnalyticsExport.objects.get(pk=export_id)
    export.status = AnalyticsExport.Status.FAILED
    export.error_message = error_message
    export.completed_at = timezone.now()
    export.save(
        update_fields=[
            "status",
            "error_message",
            "completed_at",
        ]
    )
    return export
