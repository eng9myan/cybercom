from django.db.models import Avg, Count, Sum
from rest_framework.exceptions import ValidationError

from products.cycom.reporting.registry import REPORT_SOURCES

_AGG_CLASSES = {"sum": Sum, "avg": Avg}


def run_report(report, tenant_id):
    """Execute a SavedReport's pivot and return
    [{"label": <dimension value>, "value": <aggregated number>}, ...].

    `dimension`/`measure` never reach the ORM as raw strings — both are
    resolved through REPORT_SOURCES first, so an invalid or malicious key
    fails closed with a ValidationError rather than probing model fields.
    """
    source_cfg = REPORT_SOURCES.get(report.source)
    if source_cfg is None:
        raise ValidationError(f"Unknown report source '{report.source}'.")

    dim_entry = source_cfg["dimensions"].get(report.dimension)
    measure_entry = source_cfg["measures"].get(report.measure)
    if dim_entry is None:
        raise ValidationError(f"Unknown dimension '{report.dimension}' for source '{report.source}'.")
    if measure_entry is None:
        raise ValidationError(f"Unknown measure '{report.measure}' for source '{report.source}'.")

    _, dim_field = dim_entry
    _, measure_field = measure_entry

    qs = source_cfg["model"].objects.filter(tenant_id=tenant_id)

    if measure_field is None or report.aggregation == "count":
        rows = qs.values(dim_field).annotate(value=Count("id")).order_by(dim_field)
    else:
        agg_cls = _AGG_CLASSES.get(report.aggregation, Sum)
        rows = qs.values(dim_field).annotate(value=agg_cls(measure_field)).order_by(dim_field)

    return [
        {
            "label": str(row[dim_field]) if row[dim_field] not in (None, "") else "(none)",
            "value": float(row["value"]) if row["value"] is not None else 0,
        }
        for row in rows
    ]
