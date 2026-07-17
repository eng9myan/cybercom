"""
Validates and executes a report query_spec against the REPORTABLE_MODELS
whitelist. This is the only path from a query_spec (LLM-drafted or
hand-written) to a real database query — every field/filter/aggregate is
checked against the registry first, so an LLM can never reach a model,
field, or relation it wasn't explicitly whitelisted for.
"""

from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Sum

from products.cycom.cyai_reports.registry import REPORTABLE_MODELS

_ALLOWED_FILTER_SUFFIXES = ("__gte", "__lte", "__gt", "__lt", "__icontains", "__in")
_AGGREGATE_FUNCS = {"sum": Sum, "count": Count, "avg": Avg}


def _strip_suffix(field: str) -> str:
    for suffix in _ALLOWED_FILTER_SUFFIXES:
        if field.endswith(suffix):
            return field[: -len(suffix)]
    return field


def validate_spec(spec: dict) -> dict:
    model_key = spec.get("model")
    if model_key not in REPORTABLE_MODELS:
        raise ValidationError(f"'{model_key}' is not a reportable model.")
    registry = REPORTABLE_MODELS[model_key]

    filters = spec.get("filters", {}) or {}
    for field in filters:
        base_field = _strip_suffix(field)
        if base_field not in registry["filter_fields"]:
            raise ValidationError(f"Field '{field}' is not filterable on '{model_key}'.")

    aggregate = spec.get("aggregate")
    if aggregate:
        if aggregate not in _AGGREGATE_FUNCS:
            raise ValidationError(f"Unknown aggregate '{aggregate}'.")
        agg_field = spec.get("aggregate_field")
        if aggregate != "count" and agg_field not in registry["aggregate_fields"]:
            raise ValidationError(f"Field '{agg_field}' is not aggregatable on '{model_key}'.")

    group_by = spec.get("group_by")
    if group_by and group_by not in registry["filter_fields"] | registry["fields"]:
        raise ValidationError(f"Field '{group_by}' cannot be grouped on '{model_key}'.")

    fields = spec.get("fields", [])
    for field in fields:
        if field not in registry["fields"]:
            raise ValidationError(f"Field '{field}' is not selectable on '{model_key}'.")

    limit = spec.get("limit", 100)
    if not isinstance(limit, int) or limit < 1 or limit > 500:
        raise ValidationError("limit must be an integer between 1 and 500.")

    return spec


def execute_spec(spec: dict, tenant_id) -> dict:
    validate_spec(spec)
    registry = REPORTABLE_MODELS[spec["model"]]
    qs = registry["model"].objects.filter(tenant_id=tenant_id)

    filters = spec.get("filters", {}) or {}
    if filters:
        qs = qs.filter(**filters)

    aggregate = spec.get("aggregate")
    group_by = spec.get("group_by")

    if aggregate and group_by:
        agg_fn = _AGGREGATE_FUNCS[aggregate]
        agg_expr = agg_fn("id") if aggregate == "count" else agg_fn(spec["aggregate_field"])
        rows = list(qs.values(group_by).annotate(result=agg_expr).order_by(group_by))
        return {"type": "grouped", "group_by": group_by, "rows": rows}

    if aggregate:
        agg_fn = _AGGREGATE_FUNCS[aggregate]
        agg_expr = agg_fn("id") if aggregate == "count" else agg_fn(spec["aggregate_field"])
        result = qs.aggregate(result=agg_expr)
        return {"type": "aggregate", "result": result["result"]}

    fields = spec.get("fields") or list(registry["fields"])
    limit = spec.get("limit", 100)
    rows = list(qs.values(*fields)[:limit])
    return {"type": "rows", "rows": rows, "count": len(rows)}
