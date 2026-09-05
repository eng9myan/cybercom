"""
Flavor engine (blueprint N) — loads the vertical-flavor registry and
individual flavor packs into VerticalFlavor / LayoutTemplate rows, and
gates a tenant's enabled flavor set against it.

Two sources, two tiers (N.1, N.9):
  - flavor-registry.yaml   the full ~55-entry catalog (the ambition). Every
                            entry becomes a VerticalFlavor row even before a
                            real pack exists — status stays "engine_only"
                            ("expressible via config/Studio, no pack yet").
  - *.flavor.yaml packs    a buildable definition (N.4) for a flavor that has
                            graduated past "expressible" — validated against
                            flavor.schema.yaml, merged into the matching
                            VerticalFlavor.definition, and used to populate
                            that flavor's LayoutTemplate rows.

`sync_registry()` / `sync_packs()` are idempotent — safe to call on every
deploy (see the `load_flavor_registry` management command) or on demand via
`VerticalFlavorViewSet.sync`.
"""
from __future__ import annotations

import datetime
import glob
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from django.db import transaction

from platform.canonical.models import LayoutTemplate, VerticalFlavor, VerticalFlavorStatus

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "docs" / "blueprint" / "schemas" / "flavor-registry.yaml"
DEFAULT_SCHEMA_PATH = REPO_ROOT / "docs" / "blueprint" / "schemas" / "flavor.schema.yaml"
DEFAULT_PACKS_GLOB = str(
    REPO_ROOT / "docs" / "blueprint" / "schemas" / "examples" / "*.flavor.yaml"
)

# flavor-registry.yaml spells the status "engine-only" (hyphen); the model's
# TextChoices value is "engine_only" (underscore, a valid Python identifier).
_STATUS_ALIASES = {"engine-only": VerticalFlavorStatus.ENGINE_ONLY}


class FlavorError(Exception):
    """Base class for flavor-engine errors."""


class FlavorNotFoundError(FlavorError):
    def __init__(self, key: str):
        super().__init__(f"No registered flavor with key '{key}'.")
        self.key = key


class FlavorValidationError(FlavorError):
    """A flavor pack failed validation against flavor.schema.yaml."""

    def __init__(self, path: Any, errors: list[str]):
        super().__init__(f"{path}: {'; '.join(errors)}")
        self.path = path
        self.errors = errors


def _normalize_status(raw: str) -> str:
    return _STATUS_ALIASES.get(raw, raw.replace("-", "_"))


def _slug_from_pascal(name: str) -> str:
    """'RetailFlavour' -> 'retail'; 'ConvenienceFuelForecourtFlavour' ->
    'convenience_fuel_forecourt'. Only used when a pack has no matching
    registry entry yet — the registry key otherwise always wins."""
    base = name[: -len("Flavour")] if name.endswith("Flavour") else name
    out: list[str] = []
    for i, ch in enumerate(base):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


@transaction.atomic
def sync_registry(registry_path: str | Path | None = None) -> dict[str, int]:
    """Upsert one VerticalFlavor row per flavor-registry.yaml entry."""
    path = Path(registry_path or DEFAULT_REGISTRY_PATH)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    created = updated = 0
    seen_keys: set[str] = set()
    for family, entries in (data.get("families") or {}).items():
        for entry in entries:
            key = entry["key"]
            seen_keys.add(key)
            status = _normalize_status(entry.get("status", "engine-only"))
            registry_meta = {
                "family": family,
                "wave": entry.get("wave"),
                "core_plus": entry.get("core_plus", []),
                "ext": entry.get("ext", False),
                "resolves_to": entry.get("resolves_to"),
                "note": entry.get("note", ""),
            }
            existing = VerticalFlavor.objects.filter(key=key).first()
            definition = {**(existing.definition if existing else {}), "registry": registry_meta}
            obj, was_created = VerticalFlavor.objects.update_or_create(
                key=key,
                defaults={"name": entry["name"], "status": status, "definition": definition},
            )
            created += int(was_created)
            updated += int(not was_created)

    return {"created": created, "updated": updated, "total": len(seen_keys)}


def _stringify_dates(value: Any) -> Any:
    """YAML's implicit timestamp tag parses an unquoted `2026-09-04` into a
    `datetime.date`/`datetime.datetime`, which is neither valid JSON (for
    jsonschema's `type: string`) nor natively storable in a plain JSONField.
    Recursively coerce those to ISO-8601 strings before validating or
    persisting a pack."""
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _stringify_dates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_stringify_dates(v) for v in value]
    return value


def _validate_pack(data: dict, schema: dict) -> list[str]:
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    return [f"{'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]


@transaction.atomic
def sync_packs(
    packs_glob: str | None = None, schema_path: str | Path | None = None
) -> dict[str, Any]:
    """Validate every *.flavor.yaml pack against flavor.schema.yaml, then
    merge its full definition into the matching VerticalFlavor row (matched
    by its PascalCase `flavor` name against the registry's `name`) and
    replace that flavor's LayoutTemplate rows. A pack with no matching
    registry entry creates one. Raises FlavorValidationError on the first
    invalid pack — a bad pack must not partially land."""
    schema = yaml.safe_load(Path(schema_path or DEFAULT_SCHEMA_PATH).read_text(encoding="utf-8"))

    loaded: list[tuple[Path, dict]] = []
    for file_path in sorted(glob.glob(packs_glob or DEFAULT_PACKS_GLOB)):
        p = Path(file_path)
        pack = _stringify_dates(yaml.safe_load(p.read_text(encoding="utf-8")) or {})
        errors = _validate_pack(pack, schema)
        if errors:
            raise FlavorValidationError(p, errors)
        loaded.append((p, pack))

    synced: list[str] = []
    for _p, pack in loaded:
        pascal_name = pack["flavor"]
        existing = VerticalFlavor.objects.filter(name=pascal_name).first()
        key = existing.key if existing else _slug_from_pascal(pascal_name)
        definition = {**(existing.definition if existing else {}), "pack": pack}

        obj, _created = VerticalFlavor.objects.update_or_create(
            key=key,
            defaults={
                "name": pascal_name,
                "version": pack["version"],
                "feature_flag": pack.get("feature_flag", ""),
                "definition": definition,
            },
        )

        LayoutTemplate.objects.filter(flavor_key=obj.key).delete()
        for lt in pack.get("layout_templates", []):
            LayoutTemplate.objects.create(
                flavor_key=obj.key,
                name=lt["name"],
                route=lt.get("route", ""),
                slots=lt.get("slots", {}),
            )
        synced.append(obj.key)

    return {"packs_synced": len(synced), "keys": synced}


def list_flavors(status: str | None = None):
    qs = VerticalFlavor.objects.all()
    if status:
        qs = qs.filter(status=status)
    return qs


def get_flavor(key: str) -> VerticalFlavor:
    try:
        return VerticalFlavor.objects.get(key=key)
    except VerticalFlavor.DoesNotExist:
        raise FlavorNotFoundError(key) from None


def is_valid_key(key: str) -> bool:
    return VerticalFlavor.objects.filter(key=key).exists()


def enable_for_tenant(tenant: Any, key: str) -> Any:
    """Add `key` to `tenant.flavor_set` (idempotent). `tenant` is duck-typed —
    any object with a JSON `flavor_set` list field and a `save_if_unchanged`
    method (platform.tenant.models.Tenant). Raises FlavorNotFoundError if
    `key` isn't a registered flavor."""
    get_flavor(key)  # validates — raises FlavorNotFoundError if unknown
    current = list(tenant.flavor_set or [])
    if key not in current:
        current.append(key)
        tenant.flavor_set = current
        tenant.save_if_unchanged(fields=["flavor_set"])
    return tenant


def disable_for_tenant(tenant: Any, key: str) -> Any:
    """Remove `key` from `tenant.flavor_set` (idempotent, no error if absent
    or unknown — disabling is always safe)."""
    current = list(tenant.flavor_set or [])
    if key in current:
        current.remove(key)
        tenant.flavor_set = current
        tenant.save_if_unchanged(fields=["flavor_set"])
    return tenant
