import json
import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.config import settings
from app.core.dependencies import get_current_company_id, get_current_user, require_permission
from app.db.session import get_db
from app.models.sign import SignRequest, SignTemplate
from app.models.user import User
from app.schemas.sign import SignRequestCreate, SignRequestResponse, SignTemplateResponse

router = APIRouter()

UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "sign"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB


def _safe_upload_path(original_filename: str) -> Path:
    suffix = Path(original_filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {suffix}")
    return UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"


@router.post("/templates", response_model=SignTemplateResponse)
async def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    fields_config: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sign.write")),
    company_id: int = Depends(get_current_company_id),
):
    path = _safe_upload_path(file.filename or "")
    body = await file.read()
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large")
    path.write_bytes(body)

    try:
        config_data = json.loads(fields_config)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="fields_config must be valid JSON")

    template = SignTemplate(
        company_id=company_id,
        name=name,
        file_path=str(path),
        fields_config=config_data,
        created_by_id=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    log_action(db, user=current_user, action="create", entity_type="SignTemplate", entity_id=template.id)
    return template


@router.get("/templates", response_model=List[SignTemplateResponse])
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sign.read")),
    company_id: int = Depends(get_current_company_id),
):
    return db.query(SignTemplate).filter(SignTemplate.company_id == company_id).all()


@router.post("/requests", response_model=SignRequestResponse)
def create_sign_request(
    request_in: SignRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sign.write")),
    company_id: int = Depends(get_current_company_id),
):
    template = (
        db.query(SignTemplate)
        .filter(SignTemplate.id == request_in.template_id, SignTemplate.company_id == company_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    sign_request = SignRequest(
        company_id=company_id,
        template_id=request_in.template_id,
        token=uuid.uuid4().hex,
        signers=request_in.signers,
        status="Sent",
        created_by_id=current_user.id,
    )
    db.add(sign_request)
    db.commit()
    db.refresh(sign_request)
    log_action(db, user=current_user, action="create", entity_type="SignRequest", entity_id=sign_request.id)
    return sign_request


@router.get("/requests", response_model=List[SignRequestResponse])
def list_sign_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sign.read")),
    company_id: int = Depends(get_current_company_id),
):
    return db.query(SignRequest).filter(SignRequest.company_id == company_id).all()


@router.get("/requests/{request_id}", response_model=SignRequestResponse)
def get_sign_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("sign.read")),
    company_id: int = Depends(get_current_company_id),
):
    obj = (
        db.query(SignRequest)
        .filter(SignRequest.id == request_id, SignRequest.company_id == company_id)
        .first()
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Signature request not found")
    return obj


# Public (token-gated) endpoints — no auth required, but token acts as bearer.
@router.get("/requests/public/{token}")
def get_public_sign_request(token: str, db: Session = Depends(get_db)):
    sr = db.query(SignRequest).filter(SignRequest.token == token).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Request not found or invalid token")
    template = db.query(SignTemplate).filter(SignTemplate.id == sr.template_id).first()
    return {"request": SignRequestResponse.model_validate(sr), "template": template and {
        "id": template.id, "name": template.name, "fields_config": template.fields_config
    }}


@router.post("/requests/public/{token}/sign")
def sign_document(token: str, signature_data: dict, db: Session = Depends(get_db)):
    sr = db.query(SignRequest).filter(SignRequest.token == token).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Request not found")
    sr.status = "Signed"
    db.commit()
    return {"message": "Document signed successfully", "status": sr.status}
