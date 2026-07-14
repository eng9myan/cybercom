from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, Date, Boolean

from app.db.base import BaseEntity


class Account(BaseEntity):
    __tablename__ = "fin_accounts"
    code = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)  # asset|liability|equity|income|expense
    parent_id = Column(Integer, ForeignKey("fin_accounts.id"), nullable=True)


class Journal(BaseEntity):
    __tablename__ = "fin_journals"
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    journal_type = Column(String, nullable=False)  # bank|cash|sale|purchase|general


class JournalEntry(BaseEntity):
    __tablename__ = "fin_journal_entries"
    reference = Column(String, unique=True, index=True, nullable=False)  # e.g. MOVE/2026/06/001
    journal_id = Column(Integer, ForeignKey("fin_journals.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    description = Column(String, nullable=True)
    status = Column(String, default="Draft", nullable=False)  # Draft|Posted
    reconciled = Column(Boolean, default=False, nullable=False)
    debit_total = Column(Numeric(14, 2), default=0, nullable=False)
    credit_total = Column(Numeric(14, 2), default=0, nullable=False)


class JournalLine(BaseEntity):
    __tablename__ = "fin_journal_lines"
    entry_id = Column(Integer, ForeignKey("fin_journal_entries.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("fin_accounts.id"), nullable=False)
    debit = Column(Numeric(14, 2), default=0, nullable=False)
    credit = Column(Numeric(14, 2), default=0, nullable=False)
    label = Column(String, nullable=True)


class BankStatementLine(BaseEntity):
    __tablename__ = "fin_bank_statement_lines"
    reference = Column(String, unique=True, index=True, nullable=False)
    journal_id = Column(Integer, ForeignKey("fin_journals.id"), nullable=False)
    date = Column(Date, nullable=False)
    label = Column(String, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    matched_entry_id = Column(Integer, ForeignKey("fin_journal_entries.id"), nullable=True)
