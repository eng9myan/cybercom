"""
Discovery Engine — real, static (AST-based, never imports/executes) scan of
every existing products/cycom/<app>/ Django app: model classes, their
fields, and registered URL routes. This is what "study existing Cycom
functionality" and "search for existing functionality before creating a new
feature" actually run against — a real catalog, not something the LLM has
to guess at or hallucinate.
"""

import ast
from pathlib import Path

PRODUCTS_ROOT = Path(__file__).resolve().parent.parent  # .../products/cycom


def _extract_models_from_file(models_path: Path) -> dict:
    if not models_path.exists():
        return {}
    tree = ast.parse(models_path.read_text(encoding="utf-8"))
    models = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = [b.id for b in node.bases if isinstance(b, ast.Name)]
        if not any(b in ("BaseModel", "PlatformModel") for b in base_names):
            continue
        fields = []
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Call):
                    fields.append(target.id)
        models[node.name] = fields
    return models


def _extract_url_prefixes(urls_path: Path) -> list[str]:
    if not urls_path.exists():
        return []
    tree = ast.parse(urls_path.read_text(encoding="utf-8"))
    prefixes = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "register"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            prefixes.append(node.args[0].value)
    return prefixes


def discover_apps() -> dict:
    """Returns {app_name: {"models": {ModelName: [fields]}, "url_prefixes": [...]}}"""
    catalog = {}
    for app_dir in sorted(PRODUCTS_ROOT.iterdir()):
        if not app_dir.is_dir() or app_dir.name.startswith("_") or app_dir.name.startswith("."):
            continue
        models_file = app_dir / "models.py"
        urls_file = app_dir / "urls.py"
        if not models_file.exists():
            continue
        catalog[app_dir.name] = {
            "models": _extract_models_from_file(models_file),
            "url_prefixes": _extract_url_prefixes(urls_file),
        }
    return catalog


_STOPWORDS = {
    "i", "a", "an", "the", "to", "for", "of", "and", "or", "want", "need",
    "module", "feature", "track", "some", "that", "with", "new", "build",
    "create", "is", "are", "be", "this", "it", "on", "in",
}


def search_existing_functionality(query: str) -> list[dict]:
    """Word-level search over the discovered catalog — the concrete
    mechanism behind "search for existing functionality before creating a
    new feature". Matches individual meaningful query words against app
    names, model names, and field names (a whole-sentence substring match
    would almost never hit anything real)."""
    query_words = {w for w in query.lower().split() if w not in _STOPWORDS and len(w) > 2}
    if not query_words:
        return []

    catalog = discover_apps()
    matches = []
    for app_name, app_data in catalog.items():
        for model_name, fields in app_data["models"].items():
            haystack = f"{app_name} {model_name} {' '.join(fields)}".lower()
            hit_words = {w for w in query_words if w in haystack or w.rstrip("s") in haystack}
            if hit_words:
                matches.append(
                    {"app": app_name, "model": model_name, "fields": fields, "matched_on": sorted(hit_words)}
                )
    return matches
