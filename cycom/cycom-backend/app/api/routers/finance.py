from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import crud
from app.core.audit import log_action
from app.core.dependencies import get_current_company_id, require_permission
from app.db.session import get_db
from app.models.finance import (
    Account,
    BankStatementLine,
    Journal,
    JournalEntry,
    JournalLine,
)
from app.models.user import User
from app.schemas.finance import (
    AccountCreate,
    AccountResponse,
    BankStatementLineCreate,
    BankStatementLineResponse,
    JournalCreate,
    JournalEntryCreate,
    JournalEntryResponse,
    JournalEntryUpdate,
    JournalResponse,
)

router = APIRouter()


def _next_entry_ref(db: Session, cid: int, date_: datetime) -> str:
    n = db.query(JournalEntry).filter(JournalEntry.company_id == cid).count() + 1
    return f"MOVE/{date_.year}/{date_.month:02d}/{n:04d}"


def _next_statement_ref(db: Session, cid: int) -> str:
    n = db.query(BankStatementLine).filter(BankStatementLine.company_id == cid).count() + 1
    return f"STMT-TX-{n:04d}"


# ---------- Accounts ----------
@router.get("/accounts", response_model=List[AccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Account, cid, limit=500)


@router.post("/accounts", response_model=AccountResponse)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, Account, cid, payload.model_dump(), created_by_id=user.id)


# ---------- Journals ----------
@router.get("/journals", response_model=List[JournalResponse])
def list_journals(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.read")),
    cid: int = Depends(get_current_company_id),
):
    return crud.list_for_company(db, Journal, cid)


@router.post("/journals", response_model=JournalResponse)
def create_journal(
    payload: JournalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.write")),
    cid: int = Depends(get_current_company_id),
):
    return crud.create_for_company(db, Journal, cid, payload.model_dump(), created_by_id=user.id)


# ---------- Journal entries ----------
@router.get("/entries", response_model=List[JournalEntryResponse])
def list_entries(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.read")),
    cid: int = Depends(get_current_company_id),
):
    return (
        db.query(JournalEntry)
        .filter(JournalEntry.company_id == cid)
        .order_by(JournalEntry.date.desc(), JournalEntry.id.desc())
        .limit(500)
        .all()
    )


@router.post("/entries", response_model=JournalEntryResponse)
def create_entry(
    payload: JournalEntryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.write")),
    cid: int = Depends(get_current_company_id),
):
    debit_total = sum((l.debit for l in payload.lines), Decimal("0"))
    credit_total = sum((l.credit for l in payload.lines), Decimal("0"))
    if debit_total != credit_total:
        raise HTTPException(
            status_code=400, detail=f"Entry not balanced: debit {debit_total} != credit {credit_total}"
        )

    entry = JournalEntry(
        company_id=cid,
        reference=_next_entry_ref(db, cid, payload.date),
        journal_id=payload.journal_id,
        date=payload.date,
        partner_id=payload.partner_id,
        description=payload.description,
        debit_total=debit_total,
        credit_total=credit_total,
        status="Draft",
        created_by_id=user.id,
    )
    db.add(entry)
    db.flush()

    for line in payload.lines:
        db.add(
            JournalLine(
                company_id=cid,
                entry_id=entry.id,
                account_id=line.account_id,
                debit=line.debit,
                credit=line.credit,
                label=line.label,
            )
        )

    db.commit()
    db.refresh(entry)
    log_action(db, user=user, action="create", entity_type="JournalEntry", entity_id=entry.id)
    return entry


@router.put("/entries/{obj_id}", response_model=JournalEntryResponse)
def update_entry(
    obj_id: int,
    payload: JournalEntryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.write")),
    cid: int = Depends(get_current_company_id),
):
    obj = crud.get_for_company(db, JournalEntry, cid, obj_id)
    if payload.status:
        if payload.status not in ("Draft", "Posted"):
            raise HTTPException(status_code=400, detail="Invalid status")
        obj.status = payload.status
    if payload.reconciled is not None:
        obj.reconciled = payload.reconciled
    obj.updated_by_id = user.id
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/entries/bulk-draft")
def bulk_set_draft(
    ids: List[int],
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.write")),
    cid: int = Depends(get_current_company_id),
):
    rows = (
        db.query(JournalEntry)
        .filter(JournalEntry.company_id == cid, JournalEntry.id.in_(ids))
        .all()
    )
    for r in rows:
        r.status = "Draft"
        r.reconciled = False
    db.commit()
    return {"updated": len(rows)}


# ---------- Bank reconciliation ----------
@router.get("/bank-lines", response_model=List[BankStatementLineResponse])
def list_bank_lines(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.read")),
    cid: int = Depends(get_current_company_id),
):
    return (
        db.query(BankStatementLine).filter(BankStatementLine.company_id == cid).all()
    )


@router.post("/bank-lines", response_model=BankStatementLineResponse)
def add_bank_line(
    payload: BankStatementLineCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.write")),
    cid: int = Depends(get_current_company_id),
):
    line = BankStatementLine(
        company_id=cid,
        reference=_next_statement_ref(db, cid),
        journal_id=payload.journal_id,
        date=payload.date,
        label=payload.label,
        amount=payload.amount,
        created_by_id=user.id,
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


@router.post("/reconcile/auto")
def auto_reconcile(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("accounting.write")),
    cid: int = Depends(get_current_company_id),
):
    """Match unreconciled bank lines to journal entries by absolute amount."""
    lines = (
        db.query(BankStatementLine)
        .filter(BankStatementLine.company_id == cid, BankStatementLine.matched_entry_id.is_(None))
        .all()
    )
    matches = 0
    for line in lines:
        target = abs(line.amount)
        entry = (
            db.query(JournalEntry)
            .filter(
                JournalEntry.company_id == cid,
                JournalEntry.reconciled.is_(False),
                ((JournalEntry.debit_total == target) | (JournalEntry.credit_total == target)),
            )
            .first()
        )
        if entry:
            line.matched_entry_id = entry.id
            entry.reconciled = True
            matches += 1
    db.commit()
    log_action(db, user=user, action="reconcile", entity_type="Finance", changes={"matches": matches})
    return {"matches": matches}
