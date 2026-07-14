# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, Role
from app.models.hr import Employee, Department, Position
from app.models.projects import Project, Task
from app.models.crm import Lead, Opportunity
from app.models.company import Company
from app.models.config_param import ConfigParameter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class RPCRequest(BaseModel):
    model: str
    method: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}


MOCK_COUNTRIES = [
    {"id": 1, "code": "JO", "name": "Jordan"},
    {"id": 2, "code": "AE", "name": "United Arab Emirates"},
    {"id": 3, "code": "SA", "name": "Saudi Arabia"},
    {"id": 4, "code": "EG", "name": "Egypt"},
    {"id": 5, "code": "US", "name": "United States"},
]

MOCK_CURRENCIES = [
    {"id": 1, "name": "JOD", "active": True},
    {"id": 2, "name": "AED", "active": True},
    {"id": 3, "name": "SAR", "active": True},
    {"id": 4, "name": "EGP", "active": True},
    {"id": 5, "name": "USD", "active": True},
]

MODEL_MAP = {
    "hr.employee": Employee,
    "hr.department": Department,
    "hr.position": Position,
    "project.project": Project,
    "project.task": Task,
    "crm.lead": Lead,
    "crm.opportunity": Opportunity,
    "res.users": User,
    "res.groups": Role,
    "res.company": Company,
    "ir.config_parameter": ConfigParameter,
}


def serialize_employee(emp: Employee, db: Session) -> dict:
    dept_name = ""
    if emp.department_id:
        dept = db.query(Department).filter(Department.id == emp.department_id).first()
        if dept:
            dept_name = dept.name

    job_title = "Unassigned"
    if emp.position_id:
        pos = db.query(Position).filter(Position.id == emp.position_id).first()
        if pos:
            job_title = pos.title

    manager_name = ""
    if emp.manager_id:
        mgr = db.query(Employee).filter(Employee.id == emp.manager_id).first()
        if mgr:
            manager_name = f"{mgr.first_name} {mgr.last_name}"

    return {
        "id": emp.id,
        "name": f"{emp.first_name} {emp.last_name}".strip() if (emp.first_name or emp.last_name) else "Unnamed",
        "work_email": emp.email or "",
        "work_phone": emp.phone or "",
        "work_location_id": [1, emp.location] if emp.location else False,
        "department_id": [emp.department_id, dept_name] if emp.department_id else False,
        "job_title": job_title,
        "create_date": emp.created_at.strftime("%Y-%m-%d %H:%M:%S") if emp.created_at else None,
        "parent_id": [emp.manager_id, manager_name] if emp.manager_id else False,
        "joined": emp.joined_date.strftime("%Y-%m-%d") if emp.joined_date else None,
        "bank": emp.bank or "N/A",
        "iban": emp.iban or "N/A",
        "portal_access": emp.portal_access,
        "single_device": emp.single_device or "N/A",
        "status": emp.status or "active",
    }


def serialize_task(t: Task, db: Session) -> dict:
    proj_name = "General"
    if t.project_id:
        proj = db.query(Project).filter(Project.id == t.project_id).first()
        if proj:
            proj_name = proj.name

    user_ids = []
    if t.assignee_id:
        user_ids = [t.assignee_id]

    return {
        "id": t.id,
        "name": t.title,
        "project_id": [t.project_id, proj_name] if t.project_id else False,
        "user_ids": user_ids,
        "allocated_hours": float(t.estimated_hours or 0.0),
        "planned_hours": float(t.estimated_hours or 0.0),
        "effective_hours": 0.0,
        "stage_id": [1, t.stage.replace("_", " ").title()] if t.stage else False,
        "state": t.stage or "todo",
    }


def serialize_lead(l: Lead, db: Session) -> dict:
    user_name = "Unassigned"
    if l.assigned_to_id:
        u = db.query(User).filter(User.id == l.assigned_to_id).first()
        if u:
            user_name = u.full_name

    return {
        "id": l.id,
        "name": l.name,
        "contact_name": l.contact_name or "",
        "email_from": l.contact_email or "",
        "phone": l.contact_phone or "",
        "expected_revenue": float(l.expected_revenue or 0.0),
        "stage_id": [1, l.stage.replace("_", " ").title()] if l.stage else False,
        "user_id": [l.assigned_to_id, user_name] if l.assigned_to_id else False,
    }


def serialize_generic(obj, db: Session) -> dict:
    row = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if val is not None:
            if hasattr(val, "strftime"):
                val = val.strftime("%Y-%m-%d %H:%M:%S")
            elif hasattr(val, "isoformat"):
                val = val.isoformat()
        row[col.name] = val
    return row


@router.post("")
@router.post("/")
def rpc_call(
    payload: RPCRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = payload.model
    method = payload.method
    args = payload.args
    kwargs = payload.kwargs

    logger.info(f"RPC call: model={model}, method={method}, args={args}, kwargs={kwargs}")

    # 1) Handle mock models
    if model == "res.country":
        if method == "search_read":
            domain = args[0] if len(args) > 0 else []
            code_filter = None
            for term in domain:
                if isinstance(term, list) and term[0] == "code" and term[1] == "=":
                    code_filter = term[2].upper()
            if code_filter:
                return [c for c in MOCK_COUNTRIES if c["code"] == code_filter]
            return MOCK_COUNTRIES
        raise HTTPException(status_code=400, detail=f"Method {method} not supported for res.country")

    if model == "res.currency":
        if method == "search_read":
            domain = args[0] if len(args) > 0 else []
            name_filter = None
            for term in domain:
                if isinstance(term, list) and term[0] == "name" and term[1] == "=":
                    name_filter = term[2].upper()
            if name_filter:
                return [c for c in MOCK_CURRENCIES if c["name"] == name_filter]
            return MOCK_CURRENCIES
        elif method == "write":
            return True
        raise HTTPException(status_code=400, detail=f"Method {method} not supported for res.currency")

    # 2) Handle settings (ir.config_parameter)
    if model == "ir.config_parameter":
        if method == "set_param":
            if len(args) < 2:
                raise HTTPException(status_code=400, detail="Missing key or value for set_param")
            key, val = args[0], args[1]
            param = db.query(ConfigParameter).filter(ConfigParameter.key == key).first()
            if param:
                param.value = str(val)
            else:
                param = ConfigParameter(key=key, value=str(val))
                db.add(param)
            db.commit()
            return True
        elif method == "get_param":
            key = args[0] if len(args) > 0 else kwargs.get("key")
            param = db.query(ConfigParameter).filter(ConfigParameter.key == key).first()
            return param.value if param else kwargs.get("default", False)
        elif method == "search_read":
            params = db.query(ConfigParameter).all()
            return [{"id": p.key, "key": p.key, "value": p.value} for p in params]
        raise HTTPException(status_code=400, detail=f"Method {method} not supported for ir.config_parameter")

    # 3) Check if model is mapped
    if model not in MODEL_MAP:
        raise HTTPException(status_code=400, detail=f"Model {model} is not supported in the clean-room translation layer")

    model_class = MODEL_MAP[model]

    # Helper function to map filters
    def apply_filters(query, domain):
        if not domain:
            return query
        for term in domain:
            if isinstance(term, list) and len(term) == 3:
                field, op, val = term

                # Check column mapping
                sql_field = field
                if field == "active" and hasattr(model_class, "is_active"):
                    sql_field = "is_active"

                if hasattr(model_class, sql_field):
                    col = getattr(model_class, sql_field)
                    if op == "=":
                        query = query.filter(col == val)
                    elif op == "!=":
                        query = query.filter(col != val)
                    elif op == "in":
                        query = query.filter(col.in_(val))
                    elif op == "not in":
                        query = query.filter(~col.in_(val))
                    elif op in ("like", "ilike"):
                        query = query.filter(col.ilike(f"%{val}%"))
        return query

    company_id = current_user.company_id or 1

    # 4) Method dispatch
    if method == "search_read":
        domain = args[0] if len(args) > 0 else []
        limit = kwargs.get("limit", 200)
        offset = kwargs.get("offset", 0)

        query = db.query(model_class)
        if hasattr(model_class, "is_active"):
            query = query.filter(model_class.is_active == True)
        if hasattr(model_class, "company_id") and model != "res.company":
            query = query.filter(model_class.company_id == company_id)

        query = apply_filters(query, domain)

        if hasattr(model_class, "id"):
            query = query.order_by(model_class.id.desc())

        records = query.offset(offset).limit(limit).all()

        serialized = []
        for r in records:
            if model == "hr.employee":
                serialized.append(serialize_employee(r, db))
            elif model == "project.task":
                serialized.append(serialize_task(r, db))
            elif model == "crm.lead":
                serialized.append(serialize_lead(r, db))
            else:
                serialized.append(serialize_generic(r, db))
        return serialized

    elif method == "create":
        if len(args) < 1:
            raise HTTPException(status_code=400, detail="Missing values dictionary for create")
        vals = args[0]

        mapped_vals = {}
        for k, v in vals.items():
            if model == "hr.employee":
                if k == "name":
                    parts = v.strip().split(" ", 1)
                    mapped_vals["first_name"] = parts[0]
                    mapped_vals["last_name"] = parts[1] if len(parts) > 1 else ""
                elif k == "work_email":
                    mapped_vals["email"] = v
                elif k == "work_phone":
                    mapped_vals["phone"] = v
                elif k == "work_location_id":
                    mapped_vals["location"] = v[1] if isinstance(v, list) else v
                elif k == "department_id":
                    mapped_vals["department_id"] = v[0] if isinstance(v, list) else v
                elif k == "job_title":
                    pos = db.query(Position).filter(Position.title == v).first()
                    if not pos:
                        pos = Position(title=v, company_id=company_id)
                        db.add(pos)
                        db.commit()
                        db.refresh(pos)
                    mapped_vals["position_id"] = pos.id
                else:
                    mapped_vals[k] = v
            elif model == "project.task":
                if k == "name":
                    mapped_vals["title"] = v
                elif k == "allocated_hours" or k == "planned_hours":
                    mapped_vals["estimated_hours"] = v
                else:
                    mapped_vals[k] = v
            elif model == "crm.lead":
                if k == "email_from":
                    mapped_vals["contact_email"] = v
                elif k == "phone":
                    mapped_vals["contact_phone"] = v
                else:
                    mapped_vals[k] = v
            else:
                mapped_vals[k] = v

        if hasattr(model_class, "company_id") and "company_id" not in mapped_vals:
            mapped_vals["company_id"] = company_id
        if hasattr(model_class, "created_by_id"):
            mapped_vals["created_by_id"] = current_user.id

        if model == "res.company":
            if "code" not in mapped_vals:
                mapped_vals["code"] = mapped_vals.get("name", "COMP").upper().replace(" ", "_")[:10]
            if "short_name" not in mapped_vals:
                mapped_vals["short_name"] = mapped_vals.get("name", "Company")

        new_obj = model_class(**mapped_vals)
        db.add(new_obj)
        db.commit()
        db.refresh(new_obj)
        return new_obj.id

    elif method == "write":
        if len(args) < 2:
            raise HTTPException(status_code=400, detail="Missing ids list or values dict for write")
        ids, vals = args[0], args[1]

        if isinstance(ids, int):
            ids = [ids]

        for obj_id in ids:
            obj = db.query(model_class).filter(model_class.id == obj_id).first()
            if not obj:
                continue

            for k, v in vals.items():
                sql_k = k
                if model == "hr.employee":
                    if k == "name":
                        parts = v.strip().split(" ", 1)
                        obj.first_name = parts[0]
                        obj.last_name = parts[1] if len(parts) > 1 else ""
                        continue
                    elif k == "work_email":
                        obj.email = v
                        continue
                    elif k == "work_phone":
                        obj.phone = v
                        continue
                elif model == "project.task":
                    if k == "name":
                        obj.title = v
                        continue
                    elif k == "stage_id":
                        stage_name = v[1] if isinstance(v, list) else v
                        s = str(stage_name).lower()
                        if "done" in s or "closed" in s:
                            obj.stage = "done"
                        elif "review" in s or "test" in s:
                            obj.stage = "review"
                        elif "progress" in s or "working" in s:
                            obj.stage = "in_progress"
                        else:
                            obj.stage = "todo"
                        continue
                elif model == "crm.lead":
                    if k == "stage_id":
                        stage_name = v[1] if isinstance(v, list) else v
                        s = str(stage_name).lower()
                        if "qualified" in s:
                            obj.stage = "qualified"
                        elif "proposal" in s:
                            obj.stage = "proposal"
                        elif "won" in s:
                            obj.stage = "won"
                        elif "lost" in s:
                            obj.stage = "lost"
                        else:
                            obj.stage = "new"
                        continue

                if hasattr(obj, sql_k):
                    setattr(obj, sql_k, v)

            if hasattr(obj, "updated_by_id"):
                obj.updated_by_id = current_user.id
            db.commit()
        return True

    elif method == "unlink":
        if len(args) < 1:
            raise HTTPException(status_code=400, detail="Missing ids list for unlink")
        ids = args[0]
        if isinstance(ids, int):
            ids = [ids]

        for obj_id in ids:
            obj = db.query(model_class).filter(model_class.id == obj_id).first()
            if not obj:
                continue
            if hasattr(obj, "is_active"):
                obj.is_active = False
            else:
                db.delete(obj)
        db.commit()
        return True

    raise HTTPException(status_code=400, detail=f"Method {method} not implemented for {model}")
