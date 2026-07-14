import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cycom-backend")))

import logging
from typing import Any, Dict
from fastapi import FastAPI, BackgroundTasks, Depends, Request, HTTPException, Security, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uuid
import shutil
from pydantic import BaseModel
from datetime import datetime

import hashlib
from db import engine, Base, AuditLog, get_tenant_session
from registry import AppRegistry
from bus import EventBus
import orchestrator
import setup
import rpc
from auth import JWTManager, get_current_user, RoleChecker
from sync import EdgeSyncManager
from typing import List
from fastapi.security import OAuth2PasswordRequestForm

from app.db.base import Base as BackendBase
# Import all models to ensure they are registered in BackendBase metadata
from app.models import (
    attendance, audit_log, company, crm, finance, fleet,
    helpdesk, hr, inventory, partner, payroll, pos,
    product, projects, purchase, recruitment, sales,
    sign, user, config_param
)

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cycom-kernel")

# Initialize database tables on start
Base.metadata.create_all(bind=engine)
BackendBase.metadata.create_all(bind=engine)

os.makedirs(r"D:\Cycom ERP\uploads", exist_ok=True)

app = FastAPI(
    title="Cycom Autonomous Micro-Kernel",
    description="Decoupled B2B ERP engine with CQRS event bus and JWT security",
    version="2026.2.0",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific B2B domains in staging/production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=r"D:\Cycom ERP\uploads"), name="uploads")


@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    """Global Security Audit Trail logger with cryptographic SHA-256 block chaining and JWT extraction."""
    method = request.method
    path = request.url.path
    response = await call_next(request)

    # Log any database state mutation action
    if method in ("POST", "PUT", "DELETE", "PATCH") and "/api/event" not in path and "/api/auth" not in path:
        # Extract user email from JWT Bearer token
        user_email = "anonymous@cycom.com"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = JWTManager.decode(token)
                user_email = payload.get("email", "anonymous@cycom.com")
            except Exception:
                pass

        # Extract tenant ID from request headers for dynamic shard routing
        tenant_id_str = request.headers.get("X-Tenant-ID", "1")
        try:
            tenant_id = int(tenant_id_str)
        except ValueError:
            tenant_id = 1

        db = get_tenant_session(tenant_id)
        try:
            # Query last audit entry for this tenant to retrieve the previous hash
            prev_entry = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).order_by(AuditLog.id.desc()).first()
            prev_hash = prev_entry.current_hash if prev_entry else "0"

            action = f"{method} {path}"
            details = f"HTTP Response: {response.status_code}"

            # Calculate SHA-256 block hash for this audit entry linked to the previous block
            payload_str = f"{prev_hash}|{user_email}|{action}|{details}"
            current_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

            log_entry = AuditLog(
                user_email=user_email,
                action=action,
                details=details,
                tenant_id=tenant_id,
                company_id=1,
                prev_hash=prev_hash,
                current_hash=current_hash
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Audit middleware failed to write to ledger: {str(e)}")
        finally:
            db.close()

    return response


app.include_router(orchestrator.router)
app.include_router(setup.router)
app.include_router(rpc.router)


class LoginPayload(BaseModel):
    email: str
    password: str


class SyncUploadPayload(BaseModel):
    edge_id: str
    batch: List[Dict[str, Any]]


class EventPayload(BaseModel):
    event_name: str
    payload: Dict[str, Any]


@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Exposes B2B JWT token generation."""
    email = form_data.username
    password = form_data.password
    # Simple simulated credential verify (extend with DB hashing)
    if email.endswith("@cycom.com") and password == "admin123":
        token = JWTManager.encode({"email": email, "role": "admin"})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": 1,
                "full_name": "Ahmad Masri",
                "email": email,
                "company_id": 1,
                "is_superuser": True
            }
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/api/auth/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    # Return user details corresponding to current_user token payload
    return {
        "id": 1,
        "full_name": "Ahmad Masri",
        "email": current_user.get("email", "admin@cycom.com"),
        "company_id": 1,
        "is_superuser": True
    }


@app.post("/api/sync/upload")
def sync_upload(payload: SyncUploadPayload, request: Request, user: dict = Security(get_current_user)):
    """Receives batch mutations uploaded by edge nodes using LWW resolution."""
    tenant_id_str = request.headers.get("X-Tenant-ID", "1")
    try:
        tenant_id = int(tenant_id_str)
    except ValueError:
        tenant_id = 1

    db = get_tenant_session(tenant_id)
    try:
        res = EdgeSyncManager.process_upward_sync(db, payload.edge_id, payload.batch, tenant_id, company_id=1)
        return res
    finally:
        db.close()


@app.get("/api/sync/download")
def sync_download(edge_id: str, last_sync_time: str, request: Request, user: dict = Security(get_current_user)):
    """Generates downward changes for edge nodes since specified timestamp."""
    tenant_id_str = request.headers.get("X-Tenant-ID", "1")
    try:
        tenant_id = int(tenant_id_str)
    except ValueError:
        tenant_id = 1

    db = get_tenant_session(tenant_id)
    try:
        try:
            last_timestamp = datetime.fromisoformat(last_sync_time.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ISO format for last_sync_time")

        res = EdgeSyncManager.generate_downward_delta(db, last_timestamp, tenant_id)
        return {"edge_id": edge_id, "delta": res}
    finally:
        db.close()


@app.post("/api/vendors/upload")
def upload_vendor_document(
    vendor_id: int = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    request: Request = Request,
    user: dict = Depends(get_current_user)
):
    tenant_id_str = request.headers.get("X-Tenant-ID", "1")
    try:
        tenant_id = int(tenant_id_str)
    except ValueError:
        tenant_id = 1

    upload_dir = r"D:\Cycom ERP\uploads\vendors"
    os.makedirs(upload_dir, exist_ok=True)

    safe_ext = os.path.splitext(file.filename)[1]
    if safe_ext.lower() not in [".pdf", ".png", ".jpg", ".jpeg", ".docx", ".doc", ".xls", ".xlsx"]:
        raise HTTPException(status_code=400, detail="Unsupported file format.")
    
    unique_filename = f"{uuid.uuid4()}{safe_ext}"
    storage_path = os.path.join(upload_dir, unique_filename)

    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    from apps.vendors.models import VendorDocument
    db = get_tenant_session(tenant_id)
    try:
        doc = VendorDocument(
            vendor_id=vendor_id,
            doc_type=doc_type,
            original_filename=file.filename,
            storage_path=f"/uploads/vendors/{unique_filename}",
            file_size_bytes=os.path.getsize(storage_path),
            mime_type=file.content_type,
            tenant_id=tenant_id,
            company_id=1
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return {"success": True, "document_id": doc.id, "storage_path": doc.storage_path}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    """Bootstrap dynamic applications on micro-kernel startup."""
    # Active apps loaded from environment configuration
    env_apps = os.getenv("ACTIVE_APPS", "finance,crm,inventory,hr").split(",")
    active_apps = [a.strip() for a in env_apps if a.strip()]

    logger.info(f"Micro-kernel booting. Active apps registry sequence: {active_apps}")
    AppRegistry.hot_load_apps(active_apps)
    
    # Re-run table creation for hot-loaded app models
    Base.metadata.create_all(bind=engine)
    BackendBase.metadata.create_all(bind=engine)


@app.post("/api/event")
async def post_headless_event(event: EventPayload, background_tasks: BackgroundTasks):
    """Headless Event Bridge for stand-alone CyShop (POS) and CyMed integrations."""
    logger.info(f"Headless Event Bridge received event: {event.event_name}")
    # Enqueue publishing task to prevent blocking external systems
    background_tasks.add_task(EventBus.publish, event.event_name, event.payload)
    return {"status": "queued", "event": event.event_name}


# --- ENTERPRISE GLOBAL PILLARS POC ---
from decimal import Decimal
from typing import Optional

class TaxRequest(BaseModel):
    amount: float
    vat_rate: Optional[float] = 0.16
    wht_rate: Optional[float] = 0.02
    apply_wht: Optional[bool] = False

class WorkflowRequest(BaseModel):
    rule: Dict[str, Any]
    context: Dict[str, Any]

class ReconcileRequest(BaseModel):
    bank_lines: List[Dict[str, Any]]
    open_invoices: List[Dict[str, Any]]

class VerifyAuditRequest(BaseModel):
    logs: List[Dict[str, Any]]

class ModuleInstallRequest(BaseModel):
    module_name: str
    github_repo: str
    branch: str

from tax_engine import TaxEngine
from workflow_engine import WorkflowEngine
from reconcile_engine import ReconcileEngine
from crypto_audit import CryptoAudit

@app.post("/api/enterprise/tax/calculate")
def calculate_tax(req: TaxRequest):
    res = TaxEngine.calculate_invoice_taxes(
        amount=Decimal(str(req.amount)),
        vat_rate=Decimal(str(req.vat_rate)),
        wht_rate=Decimal(str(req.wht_rate)),
        apply_wht=req.apply_wht
    )
    xml_data = TaxEngine.generate_jofotara_xml({
        "invoice_number": "INV-POC-999",
        "issue_date": "2026-07-14",
        "vat_amount": res["vat_amount"],
        "total_amount": res["total_amount"]
    })
    res["jofotara_xml"] = xml_data
    return res

@app.post("/api/enterprise/workflows/evaluate")
def evaluate_workflow(req: WorkflowRequest):
    matched = WorkflowEngine.evaluate_rule(req.rule, req.context)
    return {"matched": matched}

@app.post("/api/enterprise/reconcile")
def reconcile_transactions(req: ReconcileRequest):
    matches = ReconcileEngine.match_statement_lines(req.bank_lines, req.open_invoices)
    return {"matches": matches}

@app.post("/api/enterprise/audit/verify")
def verify_audit_ledger(req: VerifyAuditRequest):
    is_valid = CryptoAudit.verify_chain(req.logs)
    return {"chain_integrity_valid": is_valid}

@app.post("/api/modules/install")
def install_dynamic_module(req: ModuleInstallRequest):
    logger.info(f"Cycom.sh hot-load trigger: pulling {req.module_name} from branch {req.branch}...")
    from registry import LOADED_APPS
    if req.module_name not in LOADED_APPS:
        LOADED_APPS[req.module_name] = object()
    return {
        "success": True, 
        "module": req.module_name, 
        "status": "deployed", 
        "sandbox_url": f"http://localhost:3001/{req.module_name}-sandbox"
    }


@app.get("/api/kernel/status")
def kernel_status():
    """Return health check and loaded apps list."""
    return {
        "status": "online",
        "loaded_apps": AppRegistry.get_active_apps(),
    }
