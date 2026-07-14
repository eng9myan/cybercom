from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import crud
from app.core.audit import log_action
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.payroll import (
    OvertimeClaim,
    Payslip,
    PayrollDeduction,
    SalaryStructure,
)
from app.models.user import User
from app.schemas.payroll import (
    OvertimeClaimCreate,
    OvertimeClaimResponse,
    OvertimeClaimUpdate,
    PayrollDeductionCreate,
    PayrollDeductionResponse,
    PayslipApprove,
    PayslipGenerateRequest,
    PayslipResponse,
    SalaryStructureCreate,
    SalaryStructureResponse,
)

router = APIRouter()


# ---------- Salary structures ----------
@router.get("/structures", response_model=List[SalaryStructureResponse])
def list_structures(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, SalaryStructure, cid)


@router.post("/structures", response_model=SalaryStructureResponse)
def create_structure(
    payload: SalaryStructureCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(
        db, SalaryStructure, cid, payload.model_dump(), created_by_id=user.id
    )


# ---------- Deductions ----------
@router.get("/deductions", response_model=List[PayrollDeductionResponse])
def list_deductions(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, PayrollDeduction, cid)


@router.post("/deductions", response_model=PayrollDeductionResponse)
def create_deduction(
    payload: PayrollDeductionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(
        db, PayrollDeduction, cid, payload.model_dump(), created_by_id=user.id
    )


# ---------- Overtime ----------
@router.get("/overtime", response_model=List[OvertimeClaimResponse])
def list_overtime(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, OvertimeClaim, cid)


@router.post("/overtime", response_model=OvertimeClaimResponse)
def create_overtime(
    payload: OvertimeClaimCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(
        db, OvertimeClaim, cid, payload.model_dump(), created_by_id=user.id
    )


@router.put("/overtime/{obj_id}", response_model=OvertimeClaimResponse)
def update_overtime(
    obj_id: int,
    payload: OvertimeClaimUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.write")),
    cid: int = Depends(get_current_company_id),
):
    obj = crud.update_for_company(
        db, OvertimeClaim, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )
    if payload.status == "approved":
        obj.approved_by_id = user.id
        db.commit()
        db.refresh(obj)
    return obj


# ---------- Payslips ----------
WORKING_HOURS_PER_MONTH = Decimal("176")


def _lateness_deduction(minutes: int, hourly_rate: Decimal) -> Decimal:
    if minutes <= 15:
        return Decimal("0")
    if minutes <= 30:
        return Decimal("0.5") * hourly_rate
    if minutes <= 60:
        return hourly_rate
    return Decimal("2") * hourly_rate


@router.post("/payslips/generate", response_model=PayslipResponse)
def generate_payslip(
    payload: PayslipGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.write")),
    cid: int = Depends(get_current_company_id),
):
    hourly = payload.base_salary / WORKING_HOURS_PER_MONTH
    ot_amount = (payload.overtime_hours * hourly * Decimal("1.5")).quantize(Decimal("0.01"))
    lateness = _lateness_deduction(payload.lateness_minutes, hourly).quantize(Decimal("0.01"))
    net = (
        payload.base_salary
        + ot_amount
        + payload.allowances
        - lateness
        - payload.other_deductions
    ).quantize(Decimal("0.01"))

    payslip = Payslip(
        company_id=cid,
        employee_id=payload.employee_id,
        period=payload.period,
        base_salary=payload.base_salary,
        overtime_amount=ot_amount,
        allowances=payload.allowances,
        lateness_deduction=lateness,
        other_deductions=payload.other_deductions,
        net_salary=net,
        status="Draft",
        created_by_id=user.id,
    )
    db.add(payslip)
    db.commit()
    db.refresh(payslip)
    log_action(db, user=user, action="generate", entity_type="Payslip", entity_id=payslip.id)
    return payslip


@router.get("/payslips", response_model=List[PayslipResponse])
def list_payslips(
    employee_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.read")),
    cid: int = Depends(get_current_company_id),
):
    q = db.query(Payslip).filter(Payslip.company_id == cid, Payslip.is_active.is_(True))
    if employee_id:
        q = q.filter(Payslip.employee_id == employee_id)
    return q.order_by(Payslip.id.desc()).all()


@router.get("/payslips/{obj_id}", response_model=PayslipResponse)
def get_payslip(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.get_for_company(db, Payslip, cid, obj_id)


@router.put("/payslips/{obj_id}/status", response_model=PayslipResponse)
def approve_payslip(
    obj_id: int,
    payload: PayslipApprove,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("payroll.write")),
    cid: int = Depends(get_current_company_id),
):
    if payload.status not in ("Approved", "Paid", "Draft"):
        raise HTTPException(status_code=400, detail="Invalid status")
    obj = crud.get_for_company(db, Payslip, cid, obj_id)
    obj.status = payload.status
    obj.updated_by_id = user.id
    db.commit()
    db.refresh(obj)
    log_action(db, user=user, action=payload.status.lower(), entity_type="Payslip", entity_id=obj.id)
    return obj
