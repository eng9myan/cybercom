from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import log_action
from app.core.dependencies import get_current_superuser, get_current_user
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter()


@router.post("/", response_model=CompanyResponse)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    if db.query(Company).filter(Company.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Company code already exists")
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    log_action(db, user=current_user, action="create", entity_type="Company", entity_id=company.id)
    return company


@router.get("/", response_model=List[CompanyResponse])
def list_companies(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.is_superuser:
        return db.query(Company).all()
    return db.query(Company).filter(Company.id == current_user.company_id).all()


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if not current_user.is_superuser and company.id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    db.commit()
    db.refresh(company)
    log_action(db, user=current_user, action="update", entity_type="Company", entity_id=company.id)
    return company
