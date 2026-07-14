from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import crud
from app.core.audit import log_action
from app.core.dependencies import get_current_company_id, get_current_user, require_permission
from app.db.session import get_db
from app.models.hr import Contract, Department, Employee, LeaveRequest, LeaveType, Position
from app.models.user import User
from app.schemas.hr import (
    ContractCreate,
    ContractResponse,
    ContractUpdate,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveRequestUpdate,
    LeaveTypeCreate,
    LeaveTypeResponse,
    PositionCreate,
    PositionResponse,
    PositionUpdate,
)

router = APIRouter()


# ---------- Departments ----------
@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Department, cid)


@router.post("/departments", response_model=DepartmentResponse)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    obj = crud.create_for_company(db, Department, cid, payload.model_dump(), created_by_id=user.id)
    log_action(db, user=user, action="create", entity_type="Department", entity_id=obj.id)
    return obj


@router.put("/departments/{obj_id}", response_model=DepartmentResponse)
def update_department(
    obj_id: int,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, Department, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )


@router.delete("/departments/{obj_id}")
def delete_department(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    crud.soft_delete_for_company(db, Department, cid, obj_id)
    return {"ok": True}


# ---------- Positions ----------
@router.get("/positions", response_model=List[PositionResponse])
def list_positions(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Position, cid)


@router.post("/positions", response_model=PositionResponse)
def create_position(
    payload: PositionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, Position, cid, payload.model_dump(), created_by_id=user.id)


@router.put("/positions/{obj_id}", response_model=PositionResponse)
def update_position(
    obj_id: int,
    payload: PositionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, Position, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )


# ---------- Employees ----------
@router.get("/employees", response_model=List[EmployeeResponse])
def list_employees(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Employee, cid, limit=500)


@router.get("/employees/{obj_id}", response_model=EmployeeResponse)
def get_employee(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.get_for_company(db, Employee, cid, obj_id)


@router.post("/employees", response_model=EmployeeResponse)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    obj = crud.create_for_company(db, Employee, cid, payload.model_dump(), created_by_id=user.id)
    log_action(db, user=user, action="create", entity_type="Employee", entity_id=obj.id)
    return obj


@router.put("/employees/{obj_id}", response_model=EmployeeResponse)
def update_employee(
    obj_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    obj = crud.update_for_company(
        db, Employee, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )
    log_action(db, user=user, action="update", entity_type="Employee", entity_id=obj.id)
    return obj


@router.delete("/employees/{obj_id}")
def delete_employee(
    obj_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    crud.soft_delete_for_company(db, Employee, cid, obj_id)
    log_action(db, user=user, action="delete", entity_type="Employee", entity_id=obj_id)
    return {"ok": True}


# ---------- Contracts ----------
@router.get("/contracts", response_model=List[ContractResponse])
def list_contracts(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Contract, cid)


@router.post("/contracts", response_model=ContractResponse)
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, Contract, cid, payload.model_dump(), created_by_id=user.id)


@router.put("/contracts/{obj_id}", response_model=ContractResponse)
def update_contract(
    obj_id: int,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.update_for_company(
        db, Contract, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )


# ---------- Leave ----------
@router.get("/leave-types", response_model=List[LeaveTypeResponse])
def list_leave_types(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, LeaveType, cid)


@router.post("/leave-types", response_model=LeaveTypeResponse)
def create_leave_type(
    payload: LeaveTypeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, LeaveType, cid, payload.model_dump(), created_by_id=user.id)


@router.get("/leave-requests", response_model=List[LeaveRequestResponse])
def list_leave_requests(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, LeaveRequest, cid)


@router.post("/leave-requests", response_model=LeaveRequestResponse)
def create_leave_request(
    payload: LeaveRequestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(
        db, LeaveRequest, cid, {**payload.model_dump(), "status": "submitted"}, created_by_id=user.id
    )


@router.put("/leave-requests/{obj_id}", response_model=LeaveRequestResponse)
def update_leave_request(
    obj_id: int,
    payload: LeaveRequestUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("hr.write")),
    cid: int = Depends(get_current_company_id),
):
    obj = crud.update_for_company(
        db, LeaveRequest, cid, obj_id, payload.model_dump(exclude_unset=True), updated_by_id=user.id
    )
    if payload.status == "approved":
        obj.approved_by_id = user.id
        db.commit()
        db.refresh(obj)
    return obj
