from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import crud
from app.core.audit import log_action
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.attendance import (
    AttendancePunch,
    BiometricDevice,
    EmployeeSchedule,
    ShiftPlan,
)
from app.models.user import User
from app.schemas.attendance import (
    BiometricDeviceCreate,
    BiometricDeviceResponse,
    BiometricDeviceUpdate,
    PunchCreate,
    PunchResponse,
    ScheduleCreate,
    ScheduleResponse,
    ShiftPlanCreate,
    ShiftPlanResponse,
)

router = APIRouter()


# ---------- Devices ----------
@router.get("/devices", response_model=List[BiometricDeviceResponse])
def list_devices(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, BiometricDevice, cid)


@router.post("/devices", response_model=BiometricDeviceResponse)
def create_device(
    payload: BiometricDeviceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.write")),
    cid: int = Depends(get_current_company_id),
):
    obj = crud.create_for_company(
        db, BiometricDevice, cid, payload.model_dump(), created_by_id=user.id
    )
    log_action(db, user=user, action="create", entity_type="BiometricDevice", entity_id=obj.id)
    return obj


@router.put("/devices/{obj_id}", response_model=BiometricDeviceResponse)
def update_device(
    obj_id: int,
    payload: BiometricDeviceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, BiometricDevice, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )


@router.post("/devices/{obj_id}/sync", response_model=BiometricDeviceResponse)
def sync_device(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.write")),
    cid: int = Depends(get_current_company_id),
):
    obj = crud.get_for_company(db, BiometricDevice, cid, obj_id)
    obj.last_synced_at = datetime.now(timezone.utc)
    obj.status = "Online"
    db.commit()
    db.refresh(obj)
    log_action(db, user=user, action="sync", entity_type="BiometricDevice", entity_id=obj.id)
    return obj


# ---------- Punches ----------
@router.get("/punches", response_model=List[PunchResponse])
def list_punches(
    employee_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.read")),
    cid: int = Depends(get_current_company_id),
):
    q = db.query(AttendancePunch).filter(
        AttendancePunch.company_id == cid, AttendancePunch.is_active.is_(True)
    )
    if employee_id:
        q = q.filter(AttendancePunch.employee_id == employee_id)
    return q.order_by(AttendancePunch.punch_at.desc()).limit(500).all()


@router.post("/punches", response_model=PunchResponse)
def create_punch(
    payload: PunchCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(
        db, AttendancePunch, cid, payload.model_dump(), created_by_id=user.id
    )


@router.post("/punches/correct", response_model=PunchResponse)
def submit_correction(
    payload: PunchCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.write")),
    cid: int = Depends(get_current_company_id),
):
    if not payload.correction_reason:
        raise HTTPException(status_code=400, detail="Correction reason required")
    data = payload.model_dump()
    data["is_correction"] = "yes"
    obj = crud.create_for_company(db, AttendancePunch, cid, data, created_by_id=user.id)
    log_action(db, user=user, action="correct", entity_type="AttendancePunch", entity_id=obj.id)
    return obj


# ---------- Shift plans ----------
@router.get("/shift-plans", response_model=List[ShiftPlanResponse])
def list_shift_plans(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, ShiftPlan, cid)


@router.post("/shift-plans", response_model=ShiftPlanResponse)
def create_shift_plan(
    payload: ShiftPlanCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, ShiftPlan, cid, payload.model_dump(), created_by_id=user.id)


# ---------- Schedules ----------
@router.get("/schedules", response_model=List[ScheduleResponse])
def list_schedules(
    employee_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.read")),
    cid: int = Depends(get_current_company_id),
):
    q = db.query(EmployeeSchedule).filter(
        EmployeeSchedule.company_id == cid, EmployeeSchedule.is_active.is_(True)
    )
    if employee_id:
        q = q.filter(EmployeeSchedule.employee_id == employee_id)
    return q.all()


@router.post("/schedules", response_model=ScheduleResponse)
def create_schedule(
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("attendance.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(
        db, EmployeeSchedule, cid, payload.model_dump(), created_by_id=user.id
    )
