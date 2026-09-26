"""
Hooks the automation engine onto the whitelisted source models.

pre_save snapshots the watched fields' old values so a "changed to" condition
has something to compare against; post_save evaluates the rules. Only fields
listed in registry.py are snapshotted -- this is not a generic audit trail.
"""
from __future__ import annotations

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from products.cycom.automation.engine import run_rules_for
from products.cycom.automation.registry import AUTOMATION_SOURCES

# instance pk -> {field_path: old value}, populated in pre_save, consumed and
# cleared in post_save of the same save() call.
_PREVIOUS: dict[str, dict] = {}


def _key(instance) -> str:
    return f"{instance.__class__.__name__}:{instance.pk}"


def _source_key_for(model) -> str | None:
    for key, cfg in AUTOMATION_SOURCES.items():
        if cfg["model"] is model:
            return key
    return None


def _make_pre_save(source_key: str, paths: list[str]):
    def handler(sender, instance, **kwargs):
        if instance.pk is None or instance._state.adding:
            return
        old = sender.objects.filter(pk=instance.pk).values(*paths).first()
        if old:
            _PREVIOUS[_key(instance)] = dict(old)

    return handler


def _make_post_save(source_key: str):
    def handler(sender, instance, created, **kwargs):
        previous = _PREVIOUS.pop(_key(instance), None)
        run_rules_for(
            instance,
            source_key=source_key,
            event="created" if created else "updated",
            previous=previous,
        )

    return handler


def connect():
    for source_key, cfg in AUTOMATION_SOURCES.items():
        model = cfg["model"]
        paths = sorted({path for _lbl, path, _t in cfg["fields"].values()})
        pre_save.connect(
            _make_pre_save(source_key, paths),
            sender=model,
            weak=False,
            dispatch_uid=f"automation_pre_{source_key}",
        )
        post_save.connect(
            _make_post_save(source_key),
            sender=model,
            weak=False,
            dispatch_uid=f"automation_post_{source_key}",
        )
