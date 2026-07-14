# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from sqlalchemy.orm import Session
from decimal import Decimal

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cycom-backend")))

from db import get_tenant_session
from auth import get_current_user

# Import all models from hot-plug apps
from apps.finance.models import Account, JournalEntry, JournalLine, Invoice, InvoiceLine, Payment, BankStatement, BankStatementLine
from apps.hr.models import Employee, Department, Position, Contract, Leave, Attendance, Payslip
from apps.crm.models import Lead, Opportunity, Activity, Partner, SaleOrder, SaleOrderLine
from apps.inventory.models import Product, Warehouse, StockLocation, StockQuant, StockMove, PurchaseOrder, PurchaseOrderLine
from apps.inventory.internal_orders import InternalOrder, InternalOrderLine, InternalOrderDiscrepancy
from apps.mrp.models import WorkCenter, BillOfMaterials, BillOfMaterialsLine, WorkOrder, ManufacturingOrder, Routing, RoutingStep
from apps.projects.models import Project, Task, Timesheet, Milestone, Budget
from app.models.payroll import OvertimeClaim, PayslipLine
from app.models.company import Company
from app.models.pos import PosSession, PosOrder, PosOrderLine, PosCashMove
# New CyCom-native models (resolves all mocking warnings)
from apps.vendors.models import Vendor, VendorDocument, VendorContact
from apps.procurement.models import (
    PurchaseRequest, PurchaseRequestLine,
    PurchaseOrder as CyPurchaseOrder, PurchaseOrderLine as CyPurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine, VendorBill
)
from apps.missing_models import (
    HelpdeskTicket, FleetVehicle, MaintenanceEquipment, MaintenanceRequest,
    KnowledgeArticle, PlanningSlot, QualityCheck, MarketingCampaign,
    SubscriptionContract, Expense, JobPosition, JobApplicant,
    FleetMaintenanceLog, FleetFuelLog
)

logger = logging.getLogger("cycom-rpc")
router = APIRouter(prefix="/api/rpc", tags=["RPC Layer"])

# Mapping frontend model names to SQLAlchemy model classes
MODEL_MAP = {
    "hr.employee": Employee,
    "hr.department": Department,
    "hr.position": Position,
    "hr.contract": Contract,
    "hr.leave": Leave,
    "hr.attendance": Attendance,
    "hr.payslip": Payslip,
    "hr.payslip.line": PayslipLine,
    "hr.attendance.overtime": OvertimeClaim,
    
    "finance.account": Account,
    "finance.journal_entry": JournalEntry,
    "finance.journal_line": JournalLine,
    "finance.invoice": Invoice,
    "finance.invoice_line": InvoiceLine,
    "finance.payment": Payment,
    "finance.bank_statement": BankStatement,
    "finance.bank_statement_line": BankStatementLine,
    
    "account.move": JournalEntry,
    "account.bank.statement.line": BankStatementLine,
    
    "crm.lead": Lead,
    "crm.opportunity": Opportunity,
    "crm.activity": Activity,
    "crm.partner": Partner,
    "crm.sale_order": SaleOrder,
    "crm.sale_order_line": SaleOrderLine,
    "sale.order": SaleOrder,
    
    "inventory.warehouse": Warehouse,
    "inventory.location": StockLocation,
    "inventory.product": Product,
    "inventory.quant": StockQuant,
    "inventory.stock_move": StockMove,
    "inventory.purchase_order": PurchaseOrder,
    "inventory.purchase_order_line": PurchaseOrderLine,
    "purchase.order": PurchaseOrder,
    
    "mrp.work_center": WorkCenter,
    "mrp.bom": BillOfMaterials,
    "mrp.bom_line": BillOfMaterialsLine,
    "mrp.work_order": WorkOrder,
    "mrp.manufacturing_order": ManufacturingOrder,
    
    "project.project": Project,
    "project.task": Task,
    "project.timesheet": Timesheet,
    "project.milestone": Milestone,
    "project.budget": Budget,
    
    "res.company": Company,
    "pos.session": PosSession,
    "pos.order": PosOrder,
    "pos.order.line": PosOrderLine,
    "pos.cash_move": PosCashMove,

    # ── Vendor Management ───────────────────────────────────────────────────
    "cy.vendor": Vendor,
    "res.partner": Vendor,                       # Legacy compatibility mapping
    "cy.vendor.document": VendorDocument,
    "cy.vendor.contact": VendorContact,

    # ── Procurement ─────────────────────────────────────────────────────────
    "cy.purchase.request": PurchaseRequest,
    "cy.purchase.request.line": PurchaseRequestLine,
    "cy.purchase.order": CyPurchaseOrder,
    "cy.purchase.order.line": CyPurchaseOrderLine,
    "cy.goods.receipt": GoodsReceipt,
    "cy.goods.receipt.line": GoodsReceiptLine,
    "cy.vendor.bill": VendorBill,
    "account.move.vendor": VendorBill,            # Legacy compatibility mapping for vendor bills

    # ── Internal Orders (Branch → Warehouse) ────────────────────────────────
    "cy.internal.order": InternalOrder,
    "cy.internal.order.line": InternalOrderLine,
    "cy.internal.order.discrepancy": InternalOrderDiscrepancy,

    # ── Helpdesk ────────────────────────────────────────────────────────────
    "helpdesk.ticket": HelpdeskTicket,
    "cy.helpdesk.ticket": HelpdeskTicket,

    # ── Fleet ────────────────────────────────────────────────────────────────
    "fleet.vehicle": FleetVehicle,
    "cy.fleet.vehicle": FleetVehicle,
    "cy.fleet.maintenance": FleetMaintenanceLog,
    "cy.fleet.fuel": FleetFuelLog,

    # ── Maintenance ──────────────────────────────────────────────────────────
    "maintenance.equipment": MaintenanceEquipment,
    "maintenance.request": MaintenanceRequest,
    "cy.maintenance.request": MaintenanceRequest,

    # ── Knowledge ────────────────────────────────────────────────────────────
    "knowledge.article": KnowledgeArticle,
    "cy.knowledge.article": KnowledgeArticle,

    # ── Planning ─────────────────────────────────────────────────────────────
    "planning.slot": PlanningSlot,
    "cy.planning.slot": PlanningSlot,

    # ── Quality ──────────────────────────────────────────────────────────────
    "quality.check": QualityCheck,
    "cy.quality.check": QualityCheck,

    # ── Marketing ────────────────────────────────────────────────────────────
    "mass.mailing": MarketingCampaign,
    "cy.marketing.campaign": MarketingCampaign,

    # ── Subscriptions ────────────────────────────────────────────────────────
    "subscription.contract": SubscriptionContract,
    "cy.subscription.contract": SubscriptionContract,

    # ── Expenses ─────────────────────────────────────────────────────────────
    "hr.expense": Expense,
    "cy.expense": Expense,

    # ── Recruitment ──────────────────────────────────────────────────────────
    "hr.applicant": JobApplicant,
    "cy.job.applicant": JobApplicant,
    "cy.job.position": JobPosition,

    # ── Product alias (already mapped, add frontend alias) ───────────────────
    "product.product": Product,
    "product.template": Product,
    "stock.quant": StockQuant,
    "stock.picking": StockMove,
    "stock.location": StockLocation,
    "stock.warehouse": Warehouse,
}


def resolve_m2o(table_name: str, record_id: int, db: Session) -> Optional[str]:
    from sqlalchemy import text
    try:
        if table_name == "hr_employees":
            row = db.execute(text("SELECT first_name, last_name FROM hr_employees WHERE id = :id"), {"id": record_id}).fetchone()
            if row:
                return f"{row[0]} {row[1]}".strip()
        else:
            for col in ["name", "title", "code", "label"]:
                try:
                    row = db.execute(text(f"SELECT {col} FROM {table_name} WHERE id = :id"), {"id": record_id}).fetchone()
                    if row:
                        return str(row[0])
                except Exception:
                    continue
    except Exception:
        pass
    return None


def serialize_generic(obj, db: Session) -> dict:
    """Fallback generic serializer converting SQLAlchemy objects to JSON dicts with legacy compatibility mappings."""
    res = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, Decimal):
            res[col.name] = float(val)
        elif hasattr(val, "isoformat"):
            res[col.name] = val.isoformat()
        else:
            res[col.name] = val

        # Handle Many2One / Foreign Key relationship formatting dynamically
        if col.name.endswith("_id") and val is not None:
            resolved = False
            for fk in col.foreign_keys:
                table_name = fk.column.table.name
                name_val = resolve_m2o(table_name, val, db)
                if name_val is not None:
                    res[col.name] = [val, name_val]
                    resolved = True
                    break
            if not resolved:
                res[col.name] = [val, f"Record #{val}"]

    # Add name computed field for list widgets
    if "name" not in res:
        res["name"] = getattr(obj, "title", getattr(obj, "number", getattr(obj, "code", f"Record #{obj.id}")))

    # --- Legacy Compatibility Mappings ---
    model_name = obj.__class__.__name__.lower()
    
    # 1. Leave model compatibility (hr_leaves)
    if "leave" in model_name:
        leave_type = getattr(obj, "leave_type", "annual")
        res["holiday_status_id"] = [1, leave_type.capitalize() + " Leave"]
        res["number_of_days"] = float(getattr(obj, "days", 0))
        res["date_from"] = getattr(obj, "start_date", "").isoformat() if hasattr(getattr(obj, "start_date", None), "isoformat") else str(getattr(obj, "start_date", ""))
        res["date_to"] = getattr(obj, "end_date", "").isoformat() if hasattr(getattr(obj, "end_date", None), "isoformat") else str(getattr(obj, "end_date", ""))
        status = getattr(obj, "status", "draft")
        if status == "approved":
            res["state"] = "validate"
        elif status == "rejected":
            res["state"] = "refuse"
        else:
            res["state"] = "confirm"

    # 2. Payslip model compatibility (hr_payslips)
    elif "payslip" in model_name:
        period = getattr(obj, "period", "2026-07")
        res["date_from"] = f"{period}-01"
        res["date_to"] = f"{period}-30"
        res["net_wage"] = float(getattr(obj, "net", 0))
        status = getattr(obj, "status", "draft")
        res["state"] = "done" if status == "posted" else "draft"

    # 3. OvertimeClaim model compatibility (payroll_overtime_claims)
    elif "overtimeclaim" in model_name:
        res["duration"] = float(getattr(obj, "hours", 0))
        status = getattr(obj, "status", "pending")
        res["state"] = "validated" if status == "approved" else "refused" if status == "rejected" else "draft"

    return res


def serialize_employee(emp: Employee, db: Session) -> dict:
    dept_name = ""
    if emp.department_id:
        dept = db.query(Department).filter(Department.id == emp.department_id).first()
        dept_name = dept.name if dept else ""

    job_title = "Unassigned"
    if emp.position_id:
        pos = db.query(Position).filter(Position.id == emp.position_id).first()
        job_title = pos.title if pos else "Unassigned"

    return {
        "id": emp.id,
        "name": f"{emp.first_name} {emp.last_name}".strip() if (emp.first_name or emp.last_name) else "Unnamed",
        "work_email": emp.email or "",
        "work_phone": emp.phone or "",
        "work_location_id": [1, emp.location] if emp.location else False,
        "department_id": [emp.department_id, dept_name] if emp.department_id else False,
        "job_title": job_title,
        "joined": emp.joined_date.isoformat() if emp.joined_date else None,
        "bank": emp.bank or "N/A",
        "iban": emp.iban or "N/A",
        "status": emp.status or "active",
    }


def serialize_task(t: Task, db: Session) -> dict:
    proj_name = "General"
    if t.project_id:
        proj = db.query(Project).filter(Project.id == t.project_id).first()
        proj_name = proj.name if proj else "General"

    return {
        "id": t.id,
        "name": t.title,
        "description": t.description or "",
        "project_id": [t.project_id, proj_name],
        "stage": t.stage,
        "priority": t.priority,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "estimated_hours": float(t.estimated_hours),
    }


@router.post("")
@router.post("/")
def rpc_call(request: Request, payload: Dict[str, Any], user: dict = Security(get_current_user)):
    """Dynamic RPC query and mutation dispatcher."""
    # Resolve the tenant ID for dynamic sharding
    tenant_id_str = request.headers.get("X-Tenant-ID", "1")
    try:
        tenant_id = int(tenant_id_str)
    except ValueError:
        tenant_id = 1

    db = get_tenant_session(tenant_id)
    try:
        model = payload.get("model")
        method = payload.get("method")
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})

        logger.info(f"RPC dispatch: model={model}, method={method}, tenant={tenant_id}")

        if model not in MODEL_MAP:
            # Dynamic mock handler for compatibility metadata and unregistered setup models
            if method == "search_read":
                domain = args[0] if len(args) > 0 else []
                if model == "res.country":
                    return [{"id": 1, "code": "JO", "name": "Jordan"}, {"id": 2, "code": "SA", "name": "Saudi Arabia"}]
                elif model == "res.currency":
                    return [{"id": 1, "name": "JOD", "code": "JOD", "active": True}, {"id": 2, "name": "SAR", "code": "SAR", "active": True}]
                elif model == "ir.module.module":
                    name_val = "l10n_jo"
                    for term in domain:
                        if isinstance(term, list) and term[0] == "name":
                            name_val = term[2]
                    return [{"id": 1, "name": name_val, "state": "installed", "shortdesc": "Jordanian Chart of Accounts"}]
                elif model == "account.tax":
                    return [
                        {"id": 1, "name": "Standard Sales Tax (16%)", "amount": 16.0, "type_tax_use": "sale"},
                        {"id": 2, "name": "Standard Purchase Tax (16%)", "amount": 16.0, "type_tax_use": "purchase"}
                    ]
                logger.warning(f"Mocking search_read for unregistered model '{model}'")
                return []
            elif method == "create":
                logger.warning(f"Mocking create for unregistered model '{model}'")
                return 99
            elif method in ["write", "unlink", "button_immediate_install", "set_param"]:
                logger.warning(f"Mocking {method} for unregistered model '{model}'")
                return True
            raise HTTPException(status_code=400, detail=f"Model '{model}' is not registered.")

        model_class = MODEL_MAP[model]

        if method == "search_read":
            domain = args[0] if len(args) > 0 else []
            limit = kwargs.get("limit", 200)
            offset = kwargs.get("offset", 0)

            query = db.query(model_class)
            if hasattr(model_class, "tenant_id"):
                query = query.filter(model_class.tenant_id == tenant_id)

            # Apply basic filters
            for term in domain:
                if isinstance(term, list) and len(term) == 3:
                    field, op, val = term
                    if hasattr(model_class, field):
                        col = getattr(model_class, field)
                        if op == "=":
                            query = query.filter(col == val)
                        elif op == "in":
                            query = query.filter(col.in_(val))

            records = query.offset(offset).limit(limit).all()

            serialized = []
            for r in records:
                if model == "hr.employee":
                    serialized.append(serialize_employee(r, db))
                elif model == "project.task":
                    serialized.append(serialize_task(r, db))
                else:
                    serialized.append(serialize_generic(r, db))
            return serialized

        elif method == "create":
            if len(args) < 1:
                raise HTTPException(status_code=400, detail="Missing values dictionary.")
            vals = args[0]
            
            # Map frontend names to core models
            mapped_vals = {}
            from sqlalchemy import Date, DateTime
            from datetime import datetime
            for k, v in vals.items():
                if k in model_class.__table__.columns:
                    col_type = model_class.__table__.columns[k].type
                    if isinstance(v, str) and v:
                        if isinstance(col_type, Date):
                            try:
                                v = datetime.strptime(v, "%Y-%m-%d").date()
                            except ValueError:
                                pass
                        elif isinstance(col_type, DateTime):
                            try:
                                v = datetime.fromisoformat(v)
                            except ValueError:
                                try:
                                    v = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    pass

                if model == "hr.employee" and k == "name":
                    parts = v.strip().split(" ", 1)
                    mapped_vals["first_name"] = parts[0]
                    mapped_vals["last_name"] = parts[1] if len(parts) > 1 else ""
                elif model == "project.task" and k == "name":
                    mapped_vals["title"] = v
                else:
                    mapped_vals[k] = v

            if hasattr(model_class, "tenant_id"):
                mapped_vals["tenant_id"] = tenant_id
            if hasattr(model_class, "company_id") and "company_id" not in mapped_vals:
                mapped_vals["company_id"] = 1

            new_obj = model_class(**mapped_vals)
            db.add(new_obj)
            db.commit()
            db.refresh(new_obj)
            return new_obj.id

        elif method == "write":
            if len(args) < 2:
                raise HTTPException(status_code=400, detail="Missing id or write values.")
            obj_id, vals = args[0], args[1]
            obj_ids = obj_id if isinstance(obj_id, list) else [obj_id]

            query = db.query(model_class).filter(model_class.id.in_(obj_ids))
            if hasattr(model_class, "tenant_id"):
                query = query.filter(model_class.tenant_id == tenant_id)
            records = query.all()
            
            from sqlalchemy import Date, DateTime
            from datetime import datetime
            for r in records:
                for k, v in vals.items():
                    if hasattr(r, k):
                        if k in model_class.__table__.columns:
                            col_type = model_class.__table__.columns[k].type
                            if isinstance(v, str) and v:
                                if isinstance(col_type, Date):
                                    try:
                                        v = datetime.strptime(v, "%Y-%m-%d").date()
                                    except ValueError:
                                        pass
                                elif isinstance(col_type, DateTime):
                                    try:
                                        v = datetime.fromisoformat(v)
                                    except ValueError:
                                        try:
                                            v = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
                                        except ValueError:
                                            pass
                        setattr(r, k, v)
            db.commit()
            return True

        elif method == "unlink":
            obj_ids = args[0] if isinstance(args[0], list) else [args[0]]
            query = db.query(model_class).filter(model_class.id.in_(obj_ids))
            if hasattr(model_class, "tenant_id"):
                query = query.filter(model_class.tenant_id == tenant_id)
            query.delete(synchronize_session=False)
            db.commit()
            return True

        elif method == "bulk_import":
            if len(args) < 1:
                raise HTTPException(status_code=400, detail="Missing bulk import items list.")
            items = args[0]
            if not isinstance(items, list):
                raise HTTPException(status_code=400, detail="Bulk import items must be a list.")

            imported_count = 0
            if model == "hr.employee":
                for item in items:
                    emp_no = item.get("employee_no")
                    if not emp_no:
                        continue
                    fullname = item.get("name", "").strip()
                    parts = fullname.split(" ", 1)
                    first_name = parts[0]
                    last_name = parts[1] if len(parts) > 1 else ""

                    dept_id = None
                    dept_name = item.get("department")
                    if dept_name:
                        dept = db.query(Department).filter(Department.name == dept_name).first()
                        if not dept:
                            dept = Department(name=dept_name, tenant_id=tenant_id)
                            db.add(dept)
                            db.commit()
                            db.refresh(dept)
                        dept_id = dept.id

                    pos_id = None
                    job_title = item.get("role") or item.get("job_title")
                    if job_title:
                        pos = db.query(Position).filter(Position.title == job_title).first()
                        if not pos:
                            pos = Position(title=job_title, department_id=dept_id, tenant_id=tenant_id)
                            db.add(pos)
                            db.commit()
                            db.refresh(pos)
                        pos_id = pos.id

                    emp = db.query(Employee).filter(Employee.employee_no == emp_no).first()
                    if emp:
                        emp.first_name = first_name
                        emp.last_name = last_name
                        emp.email = item.get("email")
                        emp.phone = item.get("phone")
                        emp.location = item.get("location")
                        emp.department_id = dept_id
                        emp.position_id = pos_id
                        emp.grade = item.get("grade", "N/A")
                        emp.bank = item.get("bank", "N/A")
                        emp.iban = item.get("iban", "N/A")
                    else:
                        emp = Employee(
                            employee_no=emp_no,
                            first_name=first_name,
                            last_name=last_name,
                            email=item.get("email"),
                            phone=item.get("phone"),
                            location=item.get("location"),
                            department_id=dept_id,
                            position_id=pos_id,
                            grade=item.get("grade", "N/A"),
                            bank=item.get("bank", "N/A"),
                            iban=item.get("iban", "N/A"),
                            tenant_id=tenant_id
                        )
                        db.add(emp)
                    imported_count += 1
                db.commit()
                return {"success": True, "imported_count": imported_count}

            elif model in ["inventory.product", "product.product", "product.template"]:
                for item in items:
                    code = item.get("code")
                    if not code:
                        continue
                    prod = db.query(Product).filter(Product.code == code).first()
                    if prod:
                        prod.name = item.get("name", prod.name)
                        prod.barcode = item.get("barcode", prod.barcode)
                        prod.uom = item.get("uom", prod.uom)
                        prod.category = item.get("category", prod.category)
                        prod.cost = item.get("cost", prod.cost)
                        prod.price = item.get("price", prod.price)
                    else:
                        prod = Product(
                            name=item.get("name", "Unnamed Product"),
                            code=code,
                            barcode=item.get("barcode"),
                            uom=item.get("uom", "unit"),
                            category=item.get("category"),
                            cost=item.get("cost", 0.0),
                            price=item.get("price", 0.0),
                            tenant_id=tenant_id
                        )
                        db.add(prod)
                    imported_count += 1
                db.commit()
                return {"success": True, "imported_count": imported_count}

            elif model in ["account.move", "finance.journal_entry"]:
                from datetime import datetime
                entries_by_ref = {}
                for item in items:
                    ref = item.get("reference") or item.get("entry_reference")
                    if not ref:
                        continue
                    if ref not in entries_by_ref:
                        entries_by_ref[ref] = {
                            "reference": ref,
                            "date": item.get("date"),
                            "description": item.get("description") or "Imported Journal Entry",
                            "lines": []
                        }
                    entries_by_ref[ref]["lines"].append({
                        "account_code": item.get("account_code"),
                        "debit": float(item.get("debit") or 0.0),
                        "credit": float(item.get("credit") or 0.0)
                    })

                for ref, entry_data in entries_by_ref.items():
                    debit_total = sum(l["debit"] for l in entry_data["lines"])
                    credit_total = sum(l["credit"] for l in entry_data["lines"])
                    if abs(debit_total - credit_total) > 0.001:
                        raise HTTPException(status_code=400, detail=f"Journal Entry {ref} is unbalanced: Debits ({debit_total}) must equal Credits ({credit_total}).")

                    date_val = datetime.utcnow()
                    if entry_data["date"]:
                        try:
                            date_val = datetime.strptime(str(entry_data["date"]), "%Y-%m-%d")
                        except Exception:
                            pass

                    entry = db.query(JournalEntry).filter(JournalEntry.number == ref).first()
                    if entry:
                        entry.date = date_val
                        entry.narration = entry_data["description"]
                        db.query(JournalLine).filter(JournalLine.entry_id == entry.id).delete()
                    else:
                        entry = JournalEntry(
                            number=ref,
                            date=date_val,
                            narration=entry_data["description"],
                            status="draft",
                            tenant_id=tenant_id,
                            company_id=1
                        )
                        db.add(entry)
                        db.commit()
                        db.refresh(entry)

                    for line_item in entry_data["lines"]:
                        ac_code = line_item["account_code"]
                        account = db.query(Account).filter(Account.code == ac_code).first()
                        if not account:
                            account = Account(code=ac_code, name=f"Account {ac_code}", type="asset", tenant_id=tenant_id, company_id=1)
                            db.add(account)
                            db.commit()
                            db.refresh(account)

                        line = JournalLine(
                            entry_id=entry.id,
                            account_id=account.id,
                            debit=Decimal(str(line_item["debit"])),
                            credit=Decimal(str(line_item["credit"])),
                            tenant_id=tenant_id,
                            company_id=1
                        )
                        db.add(line)
                    imported_count += 1
                db.commit()
                return {"success": True, "imported_count": imported_count}

            else:
                raise HTTPException(status_code=400, detail=f"Bulk import not supported for '{model}'")

        elif method == "submit_for_review":
            if len(args) < 1:
                raise HTTPException(status_code=400, detail="Missing record ID.")
            record_id = args[0]
            obj = db.query(model_class).filter(model_class.id == record_id).first()
            if not obj:
                raise HTTPException(status_code=404, detail="Record not found.")
            if hasattr(obj, "approval_status"):
                obj.approval_status = "submitted"
            elif hasattr(obj, "state"):
                obj.state = "submitted"
            db.commit()
            return True

        elif method == "allocate_items":
            if len(args) < 2:
                raise HTTPException(status_code=400, detail="Missing arguments (order_id, allocations).")
            order_id = args[0]
            allocations = args[1]
            
            order = db.query(InternalOrder).filter(InternalOrder.id == order_id).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found.")
            
            for line_id_str, alloc_qty in allocations.items():
                line = db.query(InternalOrderLine).filter(InternalOrderLine.id == int(line_id_str)).first()
                if line:
                    line.allocated_qty = Decimal(str(alloc_qty))
                    line.line_state = "allocated"
            
            order.state = "allocated"
            db.commit()
            return True

        elif method == "dispatch_order":
            if len(args) < 1:
                raise HTTPException(status_code=400, detail="Missing order ID.")
            order_id = args[0]
            
            order = db.query(InternalOrder).filter(InternalOrder.id == order_id).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found.")
            
            from datetime import datetime
            for line in db.query(InternalOrderLine).filter(InternalOrderLine.order_id == order_id).all():
                line.shipped_qty = line.allocated_qty
                line.line_state = "shipped"
            
            order.state = "dispatched"
            order.dispatched_at = datetime.utcnow()
            db.commit()
            return True

        elif method == "receive_order":
            if len(args) < 2:
                raise HTTPException(status_code=400, detail="Missing arguments (order_id, receipts).")
            order_id = args[0]
            receipts = args[1]
            
            order = db.query(InternalOrder).filter(InternalOrder.id == order_id).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found.")
            
            from datetime import datetime
            has_discrepancy = False
            for line_id_str, data in receipts.items():
                line = db.query(InternalOrderLine).filter(InternalOrderLine.id == int(line_id_str)).first()
                if line:
                    rec_qty = Decimal(str(data.get("received_qty", 0)))
                    line.received_qty = rec_qty
                    line.line_state = "received"
                    
                    diff = line.shipped_qty - rec_qty
                    if diff > 0:
                        has_discrepancy = True
                        disc = InternalOrderDiscrepancy(
                            order_id=order_id,
                            line_id=line.id,
                            shipped_qty=line.shipped_qty,
                            received_qty=rec_qty,
                            difference_qty=diff,
                            reason=data.get("reason", "Shortage"),
                            investigation_status="open",
                            tenant_id=tenant_id,
                            company_id=1
                        )
                        db.add(disc)
            
            order.state = "partially_received" if has_discrepancy else "received"
            order.received_at = datetime.utcnow()
            db.commit()
            return True

        elif method == "approve":
            if len(args) < 1:
                raise HTTPException(status_code=400, detail="Missing record ID.")
            record_id = args[0]
            obj = db.query(model_class).filter(model_class.id == record_id).first()
            if not obj:
                raise HTTPException(status_code=404, detail="Record not found.")

            from datetime import datetime
            if model in ["cy.vendor", "res.partner"]:
                obj.approval_status = "approved"
                obj.approved_at = datetime.utcnow()
                obj.approved_by_id = user.get("uid") or 1
            elif model in ["cy.purchase.order", "purchase.order"]:
                obj.state = "purchase"
                obj.approved_at = datetime.utcnow()
                obj.approved_by_id = user.get("uid") or 1
            elif model == "cy.internal.order":
                obj.state = "approved"
            else:
                if hasattr(obj, "approval_status"):
                    obj.approval_status = "approved"
                elif hasattr(obj, "state"):
                    obj.state = "approved"
            db.commit()
            return True

        elif method == "reject":
            if len(args) < 1:
                raise HTTPException(status_code=400, detail="Missing record ID.")
            record_id = args[0]
            reason = args[1] if len(args) > 1 else ""
            obj = db.query(model_class).filter(model_class.id == record_id).first()
            if not obj:
                raise HTTPException(status_code=404, detail="Record not found.")

            if model in ["cy.vendor", "res.partner"]:
                obj.approval_status = "rejected"
                obj.rejection_reason = reason
            elif model in ["cy.purchase.order", "purchase.order"]:
                obj.state = "cancel"
                obj.notes = (obj.notes or "") + f"\nRejected: {reason}"
            elif model == "cy.internal.order":
                obj.state = "cancelled"
            db.commit()
            return True

        else:
            raise HTTPException(status_code=400, detail=f"RPC method '{method}' not implemented.")

    except Exception as e:
        db.rollback()
        logger.error(f"RPC Execution Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
