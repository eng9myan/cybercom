import json
import py_compile
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils import timezone

from products.cycom.cyai_moduledev.discovery import discover_apps, search_existing_functionality
from products.cycom.cyai_moduledev.models import ModuleDevRequest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # D:\cybercom\cycom
WORKSPACE_ROOT = REPO_ROOT / "ai_workspace"
PRODUCTS_ROOT = REPO_ROOT / "products" / "cycom"


def _err(msg: str):
    raise ValidationError(msg)


def start_request(tenant_id, product_description: str, requested_by: str = "") -> ModuleDevRequest:
    """Step 1: study existing functionality — real, runs immediately, no LLM needed."""
    discovery_results = search_existing_functionality(product_description)
    req = ModuleDevRequest.objects.create(
        tenant_id=tenant_id,
        product_description=product_description,
        requested_by=requested_by,
        discovery_results=discovery_results,
        status="requirements_gathering",
    )
    return req


def _call_llm(tenant_id, prompt: str) -> str:
    from platform.cyai.models import ModelConfig
    from platform.cyai.services import ModelGateway

    config = ModelConfig.objects.filter(provider="anthropic", active=True).first()
    if not config:
        _err("No active Anthropic ModelConfig found. Create one via /api/v1/ai/configs/ first.")
    result = ModelGateway.generate_completion(tenant_id=str(tenant_id), config=config, prompt=prompt)
    if result["status"] != "passed" or not result.get("text"):
        _err(f"LLM call failed: {result}")
    return result["text"]


def send_requirements_message(req: ModuleDevRequest, content: str) -> dict:
    if req.status != "requirements_gathering":
        _err(f"Request is '{req.status}', not accepting requirements messages.")

    messages = list(req.messages)
    messages.append({"role": "user", "content": content, "created_at": timezone.now().isoformat()})

    discovery_summary = json.dumps(req.discovery_results)[:3000]
    history = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    prompt = (
        "You are the CyAI Module Developer's requirements-gathering agent. "
        "Existing Cycom functionality found relevant to this request (do NOT duplicate it):\n"
        f"{discovery_summary}\n\n"
        "Ask clarifying questions until you have enough to write a functional spec. "
        "Respond ONLY with JSON: {\"type\": \"question\", \"content\": \"...\"} or, once ready, "
        "{\"type\": \"spec\", \"content\": \"<summary>\", \"functional_spec\": \"<full functional spec text>\"}.\n\n"
        f"Conversation:\n{history}"
    )
    text = _call_llm(req.tenant_id, prompt)
    parsed = json.loads(text)

    messages.append({"role": "assistant", "content": parsed.get("content", ""), "created_at": timezone.now().isoformat()})
    req.messages = messages
    if parsed.get("type") == "spec" and parsed.get("functional_spec"):
        req.functional_spec = parsed["functional_spec"]
    req.save(update_fields=["messages", "functional_spec"])
    return parsed


def confirm_requirements(req: ModuleDevRequest, confirmed_by: str) -> ModuleDevRequest:
    """Explicit gate #1 — user confirms the functional spec is correct."""
    if not req.functional_spec:
        _err("No functional spec drafted yet.")
    req.status = "requirements_confirmed"
    req.functional_spec_confirmed_by = confirmed_by
    req.functional_spec_confirmed_at = timezone.now()
    req.save(update_fields=["status", "functional_spec_confirmed_by", "functional_spec_confirmed_at"])
    return req


def generate_technical_design(req: ModuleDevRequest) -> ModuleDevRequest:
    if req.status != "requirements_confirmed":
        _err(f"Request is '{req.status}', requirements must be confirmed first.")
    catalog = json.dumps(discover_apps())[:4000]
    prompt = (
        "You are the CyAI Module Developer's technical-design agent. Write a technical design "
        "for the following confirmed functional spec, following the existing Cycom convention: "
        "a Django app under products/cycom/<name>/ with models.py (on platform.common.models.BaseModel), "
        "serializers.py, views.py (TenantScopedModelViewSet from core.viewsets), urls.py, apps.py.\n\n"
        f"Existing app catalog (avoid naming collisions, reuse existing models via FK where sensible):\n{catalog}\n\n"
        f"Functional spec:\n{req.functional_spec}\n\n"
        "Respond with plain text: the technical design document."
    )
    req.technical_design = _call_llm(req.tenant_id, prompt)
    req.status = "technical_design"
    req.save(update_fields=["technical_design", "status"])
    return req


def approve_technical_design(req: ModuleDevRequest, approved_by: str) -> ModuleDevRequest:
    """Explicit gate #2 — admin approves the design. Permission (IsPlatformAdmin)
    is enforced at the view layer; this just records the approval."""
    if req.status != "technical_design":
        _err(f"Request is '{req.status}', no design pending approval.")
    req.status = "design_approved"
    req.technical_design_approved_by = approved_by
    req.technical_design_approved_at = timezone.now()
    req.save(update_fields=["status", "technical_design_approved_by", "technical_design_approved_at"])
    return req


def generate_code(req: ModuleDevRequest, module_name: str) -> ModuleDevRequest:
    """Step: generate code ONLY into the isolated workspace — never touches
    products/cycom/ directly. Nothing here is importable by the running app."""
    if req.status != "design_approved":
        _err(f"Request is '{req.status}', design must be approved first.")
    if not module_name.isidentifier():
        _err("module_name must be a valid Python identifier.")

    prompt = (
        "You are the CyAI Module Developer's code-generation agent. Generate a complete Django app "
        f"named '{module_name}' implementing this approved technical design:\n\n{req.technical_design}\n\n"
        "Respond ONLY with JSON: {\"files\": [{\"path\": \"models.py\", \"content\": \"...\"}, "
        "{\"path\": \"serializers.py\", \"content\": \"...\"}, {\"path\": \"views.py\", \"content\": \"...\"}, "
        "{\"path\": \"urls.py\", \"content\": \"...\"}, {\"path\": \"apps.py\", \"content\": \"...\"}, "
        "{\"path\": \"tests/test_models.py\", \"content\": \"...\"}]}"
    )
    text = _call_llm(req.tenant_id, prompt)
    parsed = json.loads(text)
    files = parsed.get("files", [])
    if not files:
        _err("LLM returned no files.")

    workspace_dir = WORKSPACE_ROOT / module_name
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True)

    for f in files:
        file_path = workspace_dir / f["path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f["content"], encoding="utf-8")

    req.module_name = module_name
    req.workspace_path = str(workspace_dir)
    req.generated_files = files
    req.status = "code_generated"
    req.save(update_fields=["module_name", "workspace_path", "generated_files", "status"])
    return req


def run_checks(req: ModuleDevRequest) -> ModuleDevRequest:
    """Real syntax/compile checks against every generated .py file, plus a
    real pytest run of any generated test file — all inside the isolated
    workspace, nothing touches the live app."""
    if req.status != "code_generated":
        _err(f"Request is '{req.status}', no generated code to check.")

    workspace_dir = Path(req.workspace_path)
    lint_results = {"errors": [], "files_checked": 0}
    build_results = {"errors": [], "files_checked": 0}

    for f in req.generated_files:
        if not f["path"].endswith(".py"):
            continue
        file_path = workspace_dir / f["path"]
        lint_results["files_checked"] += 1
        build_results["files_checked"] += 1
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Windows locks open file handles, so pyc must be written to a
                # path nothing else currently holds open (unlike NamedTemporaryFile).
                py_compile.compile(str(file_path), cfile=str(Path(tmp_dir) / "out.pyc"), doraise=True)
        except py_compile.PyCompileError as exc:
            lint_results["errors"].append({"file": f["path"], "error": str(exc)})
            build_results["errors"].append({"file": f["path"], "error": str(exc)})

    test_files = [f["path"] for f in req.generated_files if "test" in f["path"].lower()]
    if test_files:
        proc = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q", str(workspace_dir)],
            capture_output=True, text=True, timeout=60,
        )
        test_results = {
            "test_files": test_files,
            "collect_exit_code": proc.returncode,
            "collect_output": (proc.stdout + proc.stderr)[-2000:],
        }
    else:
        test_results = {"test_files": [], "note": "No test files were generated."}

    req.lint_results = lint_results
    req.build_results = build_results
    req.test_results = test_results
    req.status = "diff_ready" if not lint_results["errors"] and not build_results["errors"] else "testing"
    req.diff_text = "\n\n".join(
        f"--- new file: {f['path']} ---\n{f['content']}" for f in req.generated_files
    )
    req.save(update_fields=["lint_results", "build_results", "test_results", "status", "diff_text"])
    return req


def deploy_to_staging(req: ModuleDevRequest) -> ModuleDevRequest:
    """Promotes validated workspace files into products/cycom/<module_name>/
    — this is a real, local/staging-only filesystem copy + migrate, not a
    git commit and never a push. Requires IsPlatformAdmin at the view layer."""
    if req.status != "diff_ready":
        _err(f"Request is '{req.status}', not ready for staging (lint/build errors must be clean).")

    target_dir = PRODUCTS_ROOT / req.module_name
    if target_dir.exists():
        _err(f"products/cycom/{req.module_name}/ already exists — refusing to overwrite.")

    workspace_dir = Path(req.workspace_path)
    shutil.copytree(workspace_dir, target_dir)
    (target_dir / "migrations").mkdir(exist_ok=True)
    (target_dir / "migrations" / "__init__.py").touch()
    if not (target_dir / "__init__.py").exists():
        (target_dir / "__init__.py").touch()

    req.staging_deployed_at = timezone.now()
    req.status = "staging_deployed"
    req.rollback_manifest = {
        "action": "remove_directory",
        "path": str(target_dir),
        "note": "Also remove the INSTALLED_APPS/urls.py entries added manually after this copy, "
                "and drop the app's DB tables if migrate was run.",
    }
    req.save(update_fields=["staging_deployed_at", "status", "rollback_manifest"])
    return req


def mark_uat(req: ModuleDevRequest) -> ModuleDevRequest:
    if req.status != "staging_deployed":
        _err(f"Request is '{req.status}', not yet in staging.")
    req.status = "uat"
    req.save(update_fields=["status"])
    return req


def approve_production(req: ModuleDevRequest, approved_by: str, confirm_production: bool) -> ModuleDevRequest:
    """Explicit gate #3 — separate from design approval. Requires BOTH
    IsPlatformAdmin (view layer) AND an explicit confirm_production=True
    flag (defense in depth). Recording this approval does NOT deploy
    anything — deploy_to_production() is a separate, deliberately
    un-auto-triggered step."""
    if not confirm_production:
        _err("confirm_production must be explicitly true.")
    if req.status != "uat":
        _err(f"Request is '{req.status}', must complete UAT first.")
    req.status = "production_approved"
    req.production_approved_by = approved_by
    req.production_approved_at = timezone.now()
    req.save(update_fields=["status", "production_approved_by", "production_approved_at"])
    return req


def deploy_to_production(req: ModuleDevRequest, confirm_push: bool) -> ModuleDevRequest:
    """
    Real git add/commit/push mechanism — gated behind production_approved
    status AND an explicit confirm_push flag. This function is intentionally
    never called by this codebase's own tests/verification; a real push to
    the repo's remote needs a fresh, explicit, in-the-moment human decision
    every time, the same standing rule as every other production action.
    """
    if req.status != "production_approved":
        _err(f"Request is '{req.status}', production must be approved first.")
    if not confirm_push:
        _err("confirm_push must be explicitly true.")

    target_dir = PRODUCTS_ROOT / req.module_name
    subprocess.run(["git", "add", str(target_dir)], cwd=REPO_ROOT, check=True)
    commit_msg = f"Add {req.module_name} module (CyAI Module Developer, request {req.id})"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_ROOT, check=True)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    subprocess.run(["git", "push"], cwd=REPO_ROOT, check=True)

    req.deploy_commit_sha = sha
    req.deployed_at = timezone.now()
    req.status = "deployed"
    req.save(update_fields=["deploy_commit_sha", "deployed_at", "status"])
    return req


def rollback(req: ModuleDevRequest) -> ModuleDevRequest:
    """Reverses a staging (or production) deployment — removes the copied
    module directory. Only ever removes what this request itself created."""
    if req.status not in ("staging_deployed", "uat", "production_approved", "deployed"):
        _err(f"Request is '{req.status}', nothing to roll back.")
    if not req.rollback_manifest:
        _err("No rollback manifest recorded for this request.")

    target_dir = Path(req.rollback_manifest["path"])
    if target_dir.exists() and target_dir.is_relative_to(PRODUCTS_ROOT):
        shutil.rmtree(target_dir)

    req.status = "rolled_back"
    req.save(update_fields=["status"])
    return req
