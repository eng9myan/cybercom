# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Import Base and MultiTenantMixin from core-kernel
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from db import Base, MultiTenantMixin


class Account(Base, MultiTenantMixin):
    """Clean-room financial chart of accounts."""
    __tablename__ = "fin_accounts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # asset | liability | equity | revenue | expense
    is_active = Column(Boolean, default=True, nullable=False)


class JournalEntry(Base, MultiTenantMixin):
    """Financial Journal Entries representing dual-entry transactions."""
    __tablename__ = "fin_journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    narration = Column(String, nullable=True)
    status = Column(String, default="draft")  # draft | posted


class JournalLine(Base, MultiTenantMixin):
    """Individual debit/credit lines of a financial journal entry."""
    __tablename__ = "fin_journal_lines"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("fin_journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("fin_accounts.id"), nullable=False)
    debit = Column(Numeric(14, 2), default=0.0, nullable=False)
    credit = Column(Numeric(14, 2), default=0.0, nullable=False)


# =========================================================================
#   INVOICES, PAYMENTS & RECONCILIATION
# =========================================================================

class Invoice(Base, MultiTenantMixin):
    """Customer Invoices and Vendor Bills."""
    __tablename__ = "fin_invoices"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True, nullable=False)
    partner_id = Column(Integer, nullable=False, index=True)  # Link to crm_partners
    type = Column(String, nullable=False)  # customer | vendor
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    amount_untaxed = Column(Numeric(14, 2), default=0.0, nullable=False)
    amount_tax = Column(Numeric(14, 2), default=0.0, nullable=False)
    amount_total = Column(Numeric(14, 2), default=0.0, nullable=False)
    status = Column(String, default="draft")  # draft | open | paid | cancel


class InvoiceLine(Base, MultiTenantMixin):
    """Individual items billed in an Invoice."""
    __tablename__ = "fin_invoice_lines"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("fin_invoices.id"), nullable=False)
    product_id = Column(Integer, nullable=False, index=True)  # Link to inv_products
    name = Column(String, nullable=False)
    qty = Column(Numeric(12, 4), default=1.0, nullable=False)
    price_unit = Column(Numeric(14, 2), default=0.0, nullable=False)
    tax_percent = Column(Numeric(5, 2), default=0.0, nullable=False)  # e.g., 16.0 for Jordan VAT
    price_subtotal = Column(Numeric(14, 2), default=0.0, nullable=False)


class Payment(Base, MultiTenantMixin):
    """Customer and Vendor cash/bank payments."""
    __tablename__ = "fin_payments"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True, nullable=False)
    invoice_id = Column(Integer, ForeignKey("fin_invoices.id"), nullable=True)
    partner_id = Column(Integer, nullable=False, index=True)
    amount = Column(Numeric(14, 2), default=0.0, nullable=False)
    date = Column(Date, nullable=False)
    payment_method = Column(String, nullable=False)  # bank | cash
    status = Column(String, default="posted")  # draft | posted | cancel


class BankStatement(Base, MultiTenantMixin):
    """Periodic bank accounts statements."""
    __tablename__ = "fin_bank_statements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    starting_balance = Column(Numeric(14, 2), default=0.0, nullable=False)
    ending_balance = Column(Numeric(14, 2), default=0.0, nullable=False)
    status = Column(String, default="draft")  # draft | validated


class BankStatementLine(Base, MultiTenantMixin):
    """Individual transactions reported inside a Bank Statement."""
    __tablename__ = "fin_bank_statement_lines"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("fin_bank_statements.id"), nullable=False)
    date = Column(Date, nullable=False)
    name = Column(String, nullable=False)  # Memo/Reference
    amount = Column(Numeric(14, 2), default=0.0, nullable=False)
    partner_id = Column(Integer, nullable=True)
    is_reconciled = Column(Boolean, default=False, nullable=False)


# =========================================================================
#   CARBON & ESG LEDGER (Scope 1, 2, and 3 Emissions Double-Entry Ledger)
# =========================================================================

class CarbonAccount(Base, MultiTenantMixin):
    """Parallel ledger accounts for greenhouse gas emissions (in metric tonnes of CO2e)."""
    __tablename__ = "esg_carbon_accounts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    scope = Column(Integer, nullable=False)  # 1 (Direct), 2 (Indirect energy), 3 (Value chain)
    emission_type = Column(String, nullable=False)  # fuel | electricity | logistics | waste


class CarbonJournalEntry(Base, MultiTenantMixin):
    """Double-entry Carbon Journal to track and audit offset ledger entries."""
    __tablename__ = "esg_carbon_journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    ref_financial_entry_id = Column(Integer, ForeignKey("fin_journal_entries.id"), nullable=True)
    description = Column(String, nullable=True)


class CarbonJournalLine(Base, MultiTenantMixin):
    """Debit/Credit emissions lines. Debit = emissions release, Credit = carbon offset."""
    __tablename__ = "esg_carbon_journal_lines"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("esg_carbon_journal_entries.id"), nullable=False)
    carbon_account_id = Column(Integer, ForeignKey("esg_carbon_accounts.id"), nullable=False)
    debit_co2e = Column(Numeric(12, 4), default=0.0, nullable=False)  # Emissions generated
    credit_co2e = Column(Numeric(12, 4), default=0.0, nullable=False)  # Offsets / removals applied
