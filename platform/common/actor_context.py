"""
Ambient actor context — the current user id for audit columns.

Set once per request (by the tenant-isolation middleware, from the JWT `sub`
claim) and per Celery task (by `@tenant_task`), read by `BaseModel.save()` to
fill `created_by` on insert and `updated_by` on every write
(canonical-data-model-v1.md §1.2).

Unset context is fine — the columns are nullable. This is best-effort audit
metadata, not an isolation control (that's `tenant_context`).
"""
from __future__ import annotations

import contextlib
import uuid
from contextvars import ContextVar

_current_actor: ContextVar[object | None] = ContextVar("cybercom_current_actor", default=None)


def _coerce(value):
    """Accept a UUID, a uuid string, or None. Anything unparseable -> None
    (a malformed `sub` claim must not break a write)."""
    if value is None or isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def set_current_actor(user_id) -> None:
    _current_actor.set(_coerce(user_id))


def get_current_actor():
    return _current_actor.get()


def clear_current_actor() -> None:
    _current_actor.set(None)


@contextlib.contextmanager
def actor_context(user_id):
    """`with actor_context(user_id): ...` — for jobs, tests, backfills."""
    token = _current_actor.set(_coerce(user_id))
    try:
        yield
    finally:
        _current_actor.reset(token)
