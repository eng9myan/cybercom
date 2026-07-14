# -*- coding: utf-8 -*-
from decimal import Decimal
import logging
from sqlalchemy.orm import Session
from apps.hr.models import Employee, Contract
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core-kernel")))
from apps.finance.models import JournalEntry, JournalLine, Account

logger = logging.getLogger("cycom-payroll")


class PayrollEngine:
    """Core B2B payroll engine calculating deductions and posting ledger provisions."""

    @staticmethod
    def calculate_payslip(contract: Contract, country_code: str) -> dict:
        """Computes net pay, social security deductions, and income tax brackets."""
        base = Decimal(str(contract.base_salary))

        # 1. Social Security / Pension Deductions (2026 rates)
        # Jordan (JO): Employee pays 7.5%, Employer pays 14.25%
        # Saudi Arabia (SA): Employee GOSI 9.75%, Employer GOSI 11.75%
        if country_code == "JO":
            employee_ss = base * Decimal("0.075")
            employer_ss = base * Decimal("0.1425")
        elif country_code == "SA":
            employee_ss = base * Decimal("0.0975")
            employer_ss = base * Decimal("0.1175")
        else:
            employee_ss = base * Decimal("0.05")
            employer_ss = base * Decimal("0.10")

        # 2. Income Tax brackets (Jordanian Tax Law brackets simulation)
        # Exempt up to 750 JOD/month. 5% on next 416 JOD, 10% on next 416, 15% thereafter.
        taxable_income = base - employee_ss
        income_tax = Decimal("0.0")

        if country_code == "JO":
            if taxable_income > 750:
                rem = taxable_income - 750
                # Tier 1: 5% (up to 416 JOD)
                t1 = min(rem, Decimal("416.0"))
                income_tax += t1 * Decimal("0.05")
                rem -= t1
                # Tier 2: 10% (up to 416 JOD)
                if rem > 0:
                    t2 = min(rem, Decimal("416.0"))
                    income_tax += t2 * Decimal("0.10")
                    rem -= t2
                # Tier 3: 15%
                if rem > 0:
                    income_tax += rem * Decimal("0.15")
        else:
            # Saudi Arabia has 0% personal income tax
            income_tax = Decimal("0.0")

        net_pay = base - employee_ss - income_tax

        return {
            "gross": base,
            "employee_social_security": round(employee_ss, 2),
            "employer_social_security": round(employer_ss, 2),
            "income_tax": round(income_tax, 2),
            "net": round(net_pay, 2),
        }

    @staticmethod
    def calculate_eos_gratuity(base_salary: Decimal, years_of_service: Decimal, country_code: str) -> Decimal:
        """Computes legally-compliant End of Service (EOS) / Gratuity accruals."""
        gratuity = Decimal("0.0")
        if country_code == "SA":
            # Saudi Labor Law: 15 days (0.5 month) for first 5 years, 30 days (1 month) thereafter
            if years_of_service <= 5:
                gratuity = years_of_service * (base_salary / 2)
            else:
                gratuity = (5 * (base_salary / 2)) + ((years_of_service - 5) * base_salary)
        elif country_code == "JO":
            # Jordan Labor Law: 1 month salary for each year of service
            gratuity = years_of_service * base_salary
        else:
            # Fallback: 15 days per year
            gratuity = years_of_service * (base_salary / 2)
        return round(gratuity, 2)

    @staticmethod
    def post_payroll_to_ledger(db: Session, employee: Employee, payroll_details: dict, tenant_id: int, company_id: int) -> JournalEntry:
        """Converts payslip calculation outputs into a dual-entry ledger transaction."""
        # Retrieve or create base accounts for payroll operations
        salary_exp_acct = db.query(Account).filter(Account.code == "500200_salary_expense").first()
        if not salary_exp_acct:
            salary_exp_acct = Account(code="500200_salary_expense", name="Salaries & Wages Expense", type="expense", tenant_id=tenant_id, company_id=company_id)
            db.add(salary_exp_acct)

        employer_ss_exp_acct = db.query(Account).filter(Account.code == "500300_employer_ss_expense").first()
        if not employer_ss_exp_acct:
            employer_ss_exp_acct = Account(code="500300_employer_ss_expense", name="Employer Social Security Expense", type="expense", tenant_id=tenant_id, company_id=company_id)
            db.add(employer_ss_exp_acct)

        salary_payable_acct = db.query(Account).filter(Account.code == "200200_salaries_payable").first()
        if not salary_payable_acct:
            salary_payable_acct = Account(code="200200_salaries_payable", name="Accrued Salaries Payable", type="liability", tenant_id=tenant_id, company_id=company_id)
            db.add(salary_payable_acct)

        ss_payable_acct = db.query(Account).filter(Account.code == "200300_ss_payable").first()
        if not ss_payable_acct:
            ss_payable_acct = Account(code="200300_ss_payable", name="Social Security Liability Payable", type="liability", tenant_id=tenant_id, company_id=company_id)
            db.add(ss_payable_acct)

        tax_payable_acct = db.query(Account).filter(Account.code == "200400_tax_payable").first()
        if not tax_payable_acct:
            tax_payable_acct = Account(code="200400_tax_payable", name="Income Tax Withholdings Payable", type="liability", tenant_id=tenant_id, company_id=company_id)
            db.add(tax_payable_acct)

        db.commit()

        # Create Journal Entry
        entry = JournalEntry(
            number=f"PAY/{employee.employee_no}/{Decimal(str(payroll_details['net']))}",
            narration=f"Automated payroll provision for {employee.first_name} {employee.last_name}",
            status="draft",
            tenant_id=tenant_id,
            company_id=company_id
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        # DEBITS:
        # 1. Debit Salary Expense (Gross salary)
        db.add(JournalLine(
            entry_id=entry.id, account_id=salary_exp_acct.id,
            debit=payroll_details["gross"], credit=Decimal("0.0"),
            tenant_id=tenant_id, company_id=company_id
        ))
        # 2. Debit Employer Social Security Expense
        db.add(JournalLine(
            entry_id=entry.id, account_id=employer_ss_exp_acct.id,
            debit=payroll_details["employer_social_security"], credit=Decimal("0.0"),
            tenant_id=tenant_id, company_id=company_id
        ))

        # CREDITS:
        # 3. Credit Salaries Payable (Net pay)
        db.add(JournalLine(
            entry_id=entry.id, account_id=salary_payable_acct.id,
            debit=Decimal("0.0"), credit=payroll_details["net"],
            tenant_id=tenant_id, company_id=company_id
        ))
        # 4. Credit SS Liability Payable (Employee + Employer share)
        total_ss_payable = payroll_details["employee_social_security"] + payroll_details["employer_social_security"]
        db.add(JournalLine(
            entry_id=entry.id, account_id=ss_payable_acct.id,
            debit=Decimal("0.0"), credit=total_ss_payable,
            tenant_id=tenant_id, company_id=company_id
        ))
        # 5. Credit Income Tax Withholdings Payable
        db.add(JournalLine(
            entry_id=entry.id, account_id=tax_payable_acct.id,
            debit=Decimal("0.0"), credit=payroll_details["income_tax"],
            tenant_id=tenant_id, company_id=company_id
        ))

        db.commit()
        logger.info(f"Payroll Journal Entry {entry.number} posted successfully.")
        return entry
