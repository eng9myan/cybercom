from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class _M(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AccountBase(BaseModel):
    code: str
    name: str
    account_type: str
    parent_id: Optional[int] = None


class AccountCreate(AccountBase):
    pass


class AccountResponse(_M, AccountBase):
    id: int
    company_id: int


class JournalBase(BaseModel):
    name: str
    code: str
    journal_type: str


class JournalCreate(JournalBase):
    pass


class JournalResponse(_M, JournalBase):
    id: int
    company_id: int


class JournalLineCreate(BaseModel):
    account_id: int
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    label: Optional[str] = None


class JournalLineResponse(_M):
    id: int
    account_id: int
    debit: Decimal
    credit: Decimal
    label: Optional[str] = None


class JournalEntryCreate(BaseModel):
    journal_id: int
    date: date
    partner_id: Optional[int] = None
    description: Optional[str] = None
    lines: List[JournalLineCreate]


class JournalEntryUpdate(BaseModel):
    status: Optional[str] = None
    reconciled: Optional[bool] = None


class JournalEntryResponse(_M):
    id: int
    reference: str
    company_id: int
    journal_id: int
    date: date
    partner_id: Optional[int] = None
    description: Optional[str] = None
    status: str
    reconciled: bool
    debit_total: Decimal
    credit_total: Decimal


class BankStatementLineCreate(BaseModel):
    journal_id: int
    date: date
    label: str
    amount: Decimal


class BankStatementLineResponse(_M):
    id: int
    reference: str
    company_id: int
    journal_id: int
    date: date
    label: str
    amount: Decimal
    matched_entry_id: Optional[int] = None
