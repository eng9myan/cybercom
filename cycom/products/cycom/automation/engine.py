"""
Automation rule evaluation.

Everything a rule names (source, condition field, action target) is resolved
through registry.py, so a crafted rule can't reach a model or attribute that
wasn't explicitly exposed. A rule that names something unknown fails closed
(condition evaluates False / action is skipped and logged), never raises into
the caller's save().
"""
from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from django.db.models import F
from django.utils import timezone

from products.cycom.automation import actions as action_impl
from products.cycom.automation.models import AutomationRule, AutomationRun
from products.cycom.automation.registry import OPERATORS, resolve_field, source_config

logger = logging.getLogger("cycom.automation")

# Set by signals.py while a rule's own actions are being applied, so a rule
# that writes to a watched field can't retrigger itself (or another rule)
# into an endless save loop.
_SUPPRESS = set()


def suppress_key(instance) -> str:
    return f"{instance.__class__.__name__}:{instance.pk}"


def _as_number(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def evaluate_condition(condition: dict, source_key: str, instance, previous: dict | None) -> bool:
    field_key = condition.get("field")
    operator = condition.get("operator")
    expected = condition.get("value")

    resolved = resolve_field(source_key, field_key)
    if not resolved or operator not in OPERATORS:
        return False
    _label, path, ftype = resolved
    _op_label, numeric_only = OPERATORS[operator]

    actual = getattr(instance, path, None)

    if operator == "changed_to":
        # Only meaningful on an update where we captured the pre-save value.
        if previous is None or path not in previous:
            return False
        return str(previous[path]) != str(actual) and str(actual) == str(expected)

    if numeric_only:
        if ftype != "number":
            return False
        a, b = _as_number(actual), _as_number(expected)
        if a is None or b is None:
            return False
        return {
            "gt": a > b, "gte": a >= b, "lt": a < b, "lte": a <= b,
        }[operator]

    a_str, b_str = str(actual if actual is not None else ""), str(expected if expected is not None else "")
    if operator == "eq":
        return a_str == b_str
    if operator == "ne":
        return a_str != b_str
    if operator == "contains":
        return b_str.lower() in a_str.lower()
    return False


def rule_matches(rule: AutomationRule, instance, previous: dict | None) -> bool:
    conditions = rule.conditions or []
    if not conditions:
        return True  # "always, on this event" is a legitimate rule
    return all(evaluate_condition(c, rule.trigger_source, instance, previous) for c in conditions)


def run_rules_for(instance, source_key: str, event: str, previous: dict | None = None) -> None:
    """Evaluate every active rule for this source. Never raises -- an
    automation failure must not roll back the business write that triggered
    it; it's recorded as a failed AutomationRun instead."""
    key = suppress_key(instance)
    if key in _SUPPRESS:
        return

    tenant_id = getattr(instance, "tenant_id", None)
    if tenant_id is None:
        return

    rules = AutomationRule.objects.filter(
        tenant_id=tenant_id, trigger_source=source_key, is_active=True,
    )
    for rule in rules:
        if rule.trigger_event != "created_or_updated" and rule.trigger_event != event:
            continue
        try:
            if not rule_matches(rule, instance, previous):
                AutomationRun.objects.create(
                    tenant_id=tenant_id, rule=rule, record_id=str(instance.pk),
                    event=event, status="skipped",
                )
                continue
            _SUPPRESS.add(key)
            try:
                detail = action_impl.execute_all(rule, instance, source_key)
            finally:
                _SUPPRESS.discard(key)
            AutomationRun.objects.create(
                tenant_id=tenant_id, rule=rule, record_id=str(instance.pk),
                event=event, status="matched", detail=detail,
            )
            AutomationRule.objects.filter(pk=rule.pk).update(
                run_count=F("run_count") + 1, last_run_at=timezone.now(),
            )
        except Exception as exc:  # noqa: BLE001 -- see docstring
            logger.exception("automation rule %s failed", rule.pk)
            AutomationRun.objects.create(
                tenant_id=tenant_id, rule=rule, record_id=str(instance.pk),
                event=event, status="failed", detail=str(exc)[:2000],
            )
