"""
Automation actions.

Each action only touches what registry.py explicitly allows: `set_field`
writes only to a source's `writable` map (never a status column with real
transition logic behind it, never tenant_id), and the rest create their own
records rather than mutating someone else's.

An unknown action type, or one naming a field outside the whitelist, is
skipped and reported in the run log -- never silently ignored, never raised
into the business write that triggered the rule.
"""
from __future__ import annotations

from django.core.mail import send_mail

from products.cycom.automation.registry import resolve_field
from products.cycom.project.models import Task as ProjectTask
from products.cycom.todo.models import Task as TodoItem


def _render(template: str, instance) -> str:
    """Tiny {field} substitution against the triggering record. Unknown
    placeholders are left as-is rather than raising -- a typo in a message
    template shouldn't fail the whole rule."""
    out = template or ""
    for attr in ("name", "number", "status", "stage", "subject", "customer_name", "priority"):
        value = getattr(instance, attr, None)
        if value is not None:
            out = out.replace("{" + attr + "}", str(value))
    return out


def _set_field(action, instance, source_key) -> str:
    field_key = action.get("field")
    resolved = resolve_field(source_key, field_key, writable=True)
    if not resolved:
        return f"set_field skipped: '{field_key}' is not a writable field on {source_key}"
    _label, path, _ftype = resolved
    value = action.get("value")
    setattr(instance, path, value)
    instance.save(update_fields=[path, "updated_at"])
    return f"set {path} = {value}"


def _create_task(action, instance, _source_key) -> str:
    name = _render(action.get("name") or "Automation task", instance)
    task = ProjectTask.objects.create(
        tenant_id=instance.tenant_id,
        name=name,
        description=_render(action.get("description") or "", instance),
        assignee=action.get("assignee") or "",
        priority=action.get("priority") or "normal",
    )
    return f"created project task {task.pk} '{name}'"


def _create_todo(action, instance, _source_key) -> str:
    """A to-do assigned to a person, linked back to the record that
    triggered it (todo.Task already carries linked_model/linked_id)."""
    title = _render(action.get("title") or "Automation follow-up", instance)
    item = TodoItem.objects.create(
        tenant_id=instance.tenant_id,
        title=title,
        description=_render(action.get("description") or "", instance),
        assignee=action.get("assignee") or "",
        linked_model=instance.__class__.__name__,
        linked_id=instance.pk,
    )
    return f"created to-do {item.pk} '{title}'"


def _send_email(action, instance, _source_key) -> str:
    to = [a.strip() for a in (action.get("to") or "").split(",") if a.strip()]
    if not to:
        return "send_email skipped: no recipient"
    subject = _render(action.get("subject") or "Cycom automation", instance)
    body = _render(action.get("body") or "", instance)
    send_mail(subject, body, None, to, fail_silently=False)
    return f"emailed {', '.join(to)}"


HANDLERS = {
    "set_field": _set_field,
    "create_task": _create_task,
    "create_todo": _create_todo,
    "send_email": _send_email,
}


def execute_all(rule, instance, source_key: str) -> str:
    results = []
    for action in rule.actions or []:
        handler = HANDLERS.get(action.get("type"))
        if not handler:
            results.append(f"unknown action type '{action.get('type')}'")
            continue
        results.append(handler(action, instance, source_key))
    return "; ".join(results)
