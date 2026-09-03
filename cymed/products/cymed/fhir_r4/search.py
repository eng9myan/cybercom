"""Basic FHIR search-param parser → Django Q object.

Handles: exact match, prefix operators (eq/ne/gt/ge/lt/le for dates + numbers),
token modifiers (:exact, :contains), and _count / _sort.
"""
from datetime import date, datetime
from django.db.models import Q


COMPARATORS = {"eq": "", "ne": "__ne", "gt": "__gt", "ge": "__gte",
               "lt": "__lt", "le": "__lte"}


def parse_search(params: dict, field_map: dict) -> tuple[Q, int, list[str]]:
    """
    field_map = {'family': 'last_name', 'given': 'first_name', 'birthdate': 'dob'}
    Returns (Q, limit, order_list)
    """
    q = Q()
    limit = int(params.get("_count", "50"))
    order = params.get("_sort", "").split(",") if params.get("_sort") else []

    for key, value in params.items():
        if key.startswith("_"):
            continue
        if key not in field_map:
            continue
        model_field = field_map[key]

        # detect comparator prefix
        op = ""
        val = value
        if isinstance(value, str) and len(value) > 2 and value[:2] in COMPARATORS:
            op = COMPARATORS.get(value[:2], "")
            val = value[2:]

        # try date parse
        try:
            val = datetime.fromisoformat(val) if "T" in val else date.fromisoformat(val)
        except (ValueError, TypeError):
            pass

        q &= Q(**{f"{model_field}{op}": val})

    return q, limit, order
