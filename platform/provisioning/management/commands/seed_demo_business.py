"""
Seed a realistic, runnable demo business into an already-provisioned tenant,
so every role has real data to test against (not empty pages).

Prereq: the tenant must already be provisioned (its CoA exists) — run the
Ready-ERP wizard or ProvisioningService first. This command then adds
customers, vendors, materials, employees + contracts, sales orders, purchase
orders, helpdesk tickets, applicants, expenses, and attendance.

Idempotent: keyed on natural keys, safe to re-run.

    python manage.py seed_demo_business --industry construction
"""

import uuid
from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.hr.models import Contract, Employee
from products.cycom.helpdesk.models import Ticket
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.payroll.models import AttendanceRecord
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine
from products.cycom.expenses.models import Expense
from products.cycom.leave.models import LeaveRequest, LeaveType
from products.cycom.recruitment.models import Applicant
from products.cycom.sales.models import SalesOrder

DEV_TENANT = uuid.UUID("11111111-1111-1111-1111-111111111111")


class Command(BaseCommand):
    help = "Seed a runnable demo business into a provisioned tenant."

    def add_arguments(self, parser):
        parser.add_argument("--industry", default="construction")
        parser.add_argument("--tenant", default=str(DEV_TENANT))

    def handle(self, *args, **opts):
        tid = uuid.UUID(opts["tenant"])

        def acct(code):
            a = Account.objects.filter(tenant_id=tid, code=code).first()
            if not a:
                raise CommandError(
                    f"Account {code} not found for tenant {tid}. Provision the company first."
                )
            return a

        inv_acct = acct("1140")
        ap_acct = acct("2110")
        ga_acct = acct("5900")

        n = {"customers": 0, "vendors": 0, "products": 0, "employees": 0,
             "sales": 0, "pos": 0, "tickets": 0, "applicants": 0,
             "expenses": 0, "attendance": 0, "leave_types": 0, "leave": 0}

        # Warehouses
        wh_main, _ = Warehouse.objects.get_or_create(
            tenant_id=tid, code="WH-MAIN", defaults={"name": "Central Warehouse"}
        )
        Warehouse.objects.get_or_create(
            tenant_id=tid, code="WH-SITE1", defaults={"name": "Tower B Site Store"}
        )

        # Customers (clients)
        clients = ["Ministry of Public Works", "Zara Real Estate", "Al-Manara Developments",
                   "Jordan Hypermarkets", "Aqaba Ports Authority"]
        for c in clients:
            _, created = Partner.objects.get_or_create(
                tenant_id=tid, name=c, partner_type="customer",
                defaults={"credit_limit": Decimal("50000"), "payment_terms_days": 45,
                          "approval_status": "approved", "city": "Amman"},
            )
            n["customers"] += created

        # Vendors (subcontractors / suppliers), approved
        vendors = ["Amman Steel Trading", "Gulf Cement Co.", "MEP Subcontractors LLC",
                   "Sabateen Aggregates", "Royal Electrical Supplies", "Petra Rebar Works"]
        vendor_objs = []
        for v in vendors:
            obj, created = Partner.objects.get_or_create(
                tenant_id=tid, name=v, partner_type="vendor",
                defaults={"category": "goods", "payment_terms_days": 30,
                          "approval_status": "approved", "cr_number": f"CR-{1000+len(v)}",
                          "iban": "JO85ARAB000000000000000000", "city": "Amman"},
            )
            vendor_objs.append(obj)
            n["vendors"] += created

        # Materials
        materials = [("RB-12", "Rebar 12mm"), ("RB-16", "Rebar 16mm"), ("CM-42", "Cement 42.5N"),
                     ("AG-20", "Aggregate 20mm"), ("BL-STD", "Concrete Block"),
                     ("WR-25", "Electrical Wire 2.5mm"), ("PP-110", "PVC Pipe 110mm"),
                     ("TL-CER", "Ceramic Tile")]
        prod_objs = []
        for sku, name in materials:
            obj, created = Product.objects.get_or_create(
                tenant_id=tid, sku=sku,
                defaults={"name": name, "uom": "each", "inventory_account": inv_acct},
            )
            prod_objs.append(obj)
            n["products"] += created

        # Employees + contracts
        people = [("EMP-001", "Omar", "Haddad", "Site Engineer"), ("EMP-002", "Rania", "Odeh", "Quantity Surveyor"),
                  ("EMP-003", "Khaled", "Nassar", "Project Manager"), ("EMP-004", "Lina", "Shawabkeh", "Accountant"),
                  ("EMP-005", "Sami", "Barakat", "Procurement Officer"), ("EMP-006", "Nour", "Halaby", "HR Officer"),
                  ("EMP-007", "Tariq", "Mansour", "Foreman"), ("EMP-008", "Dina", "Qasem", "Safety Officer"),
                  ("EMP-009", "Yousef", "Ali", "Storekeeper"), ("EMP-010", "Maha", "Zaid", "Site Engineer"),
                  ("EMP-011", "Faris", "Hijazi", "Electrician"), ("EMP-012", "Hana", "Darwish", "Draftsperson")]
        emp_objs = []
        for num, fn, ln, title in people:
            emp, created = Employee.objects.get_or_create(
                tenant_id=tid, employee_number=num,
                defaults={"first_name": fn, "last_name": ln, "job_title": title,
                          "department": "Operations", "hire_date": date(2025, 1, 15),
                          "email": f"{fn.lower()}@ammanbuilders.jo"},
            )
            emp_objs.append(emp)
            n["employees"] += created
            Contract.objects.get_or_create(
                tenant_id=tid, employee=emp, start_date=date(2025, 1, 15),
                defaults={"contract_type": "full_time", "base_salary": Decimal("650"),
                          "housing_allowance": Decimal("100"), "transport_allowance": Decimal("50")},
            )

        # Sales orders (contracts)
        so = [("SO-1001", "Ministry of Public Works", "confirmed", "185000"),
              ("SO-1002", "Zara Real Estate", "draft", "92000"),
              ("SO-1003", "Al-Manara Developments", "confirmed", "47500"),
              ("SO-1004", "Aqaba Ports Authority", "invoiced", "310000")]
        for num, cust, st, amt in so:
            _, created = SalesOrder.objects.get_or_create(
                tenant_id=tid, number=num,
                defaults={"customer_name": cust, "order_date": date.today() - timedelta(days=10),
                          "amount_total": Decimal(amt), "status": st, "salesperson": "Khaled Nassar"},
            )
            n["sales"] += created

        # Purchase orders (approved, with lines)
        for i, (vendor, prod) in enumerate(zip(vendor_objs[:3], prod_objs[:3]), start=1):
            po, created = PurchaseOrder.objects.get_or_create(
                tenant_id=tid, vendor=vendor, warehouse=wh_main, status="approved",
                defaults={},
            )
            if created:
                PurchaseOrderLine.objects.get_or_create(
                    tenant_id=tid, order=po, product=prod,
                    defaults={"quantity": Decimal("100"), "unit_cost": Decimal("5"),
                              "offset_account": ap_acct},
                )
                n["pos"] += 1

        # Helpdesk tickets
        tk = [("HD-001", "Site power outage — Tower B", "high", "in_progress"),
              ("HD-002", "Crane inspection overdue", "urgent", "new"),
              ("HD-003", "Access badge for new hire", "normal", "solved")]
        for num, subj, pr, stg in tk:
            _, created = Ticket.objects.get_or_create(
                tenant_id=tid, number=num,
                defaults={"subject": subj, "priority": pr, "stage": stg,
                          "team": "Site Support", "assignee": "Tariq Mansour"},
            )
            n["tickets"] += created

        # Applicants
        ap = [("Ahmad Sweiss", "Civil Engineer", "interview"), ("Rasha Kilani", "Accountant", "screening"),
              ("Bilal Awad", "Heavy Equipment Operator", "new"), ("Sara Nimri", "HSE Officer", "offer")]
        for name, job, stg in ap:
            _, created = Applicant.objects.get_or_create(
                tenant_id=tid, name=name, job_title=job,
                defaults={"stage": stg, "source": "LinkedIn", "email": "n/a"},
            )
            n["applicants"] += created

        # Expenses
        ex = [("Site fuel — week 28", "Fuel", "120", "submitted"),
              ("Safety equipment", "Supplies", "340", "approved"),
              ("Client lunch meeting", "Entertainment", "85", "draft"),
              ("Permit renewal fee", "Government", "500", "approved"),
              ("Tool replacement", "Supplies", "210", "submitted")]
        for i, (desc, cat, amt, st) in enumerate(ex):
            _, created = Expense.objects.get_or_create(
                tenant_id=tid, description=desc,
                defaults={"employee_name": emp_objs[i % len(emp_objs)].first_name,
                          "category": cat, "amount": Decimal(amt), "expense_date": date.today(),
                          "status": st, "expense_account": ga_acct, "payable_account": ap_acct},
            )
            n["expenses"] += created

        # Attendance (last 3 days for first 6 employees)
        for emp in emp_objs[:6]:
            for d in range(1, 4):
                _, created = AttendanceRecord.objects.get_or_create(
                    tenant_id=tid, employee=emp, date=date.today() - timedelta(days=d),
                    defaults={"check_in": time(8, 0), "check_out": time(17, 0), "source": "manual"},
                )
                n["attendance"] += created

        # Leave types + a few requests
        leave_types = {}
        for name, code, paid, days in [("Annual Leave", "ANN", True, 14),
                                       ("Sick Leave", "SICK", True, 14),
                                       ("Unpaid Leave", "UNPAID", False, 0)]:
            lt, created = LeaveType.objects.get_or_create(
                tenant_id=tid, code=code,
                defaults={"name": name, "is_paid": paid, "days_per_year": days},
            )
            leave_types[code] = lt
            n["leave_types"] += created
        lv = [(emp_objs[0], "ANN", date(2026, 8, 3), date(2026, 8, 7), "approved"),
              (emp_objs[1], "SICK", date(2026, 7, 20), date(2026, 7, 21), "approved"),
              (emp_objs[2], "ANN", date(2026, 9, 1), date(2026, 9, 5), "submitted")]
        for emp, code, s, e, st in lv:
            obj, created = LeaveRequest.objects.get_or_create(
                tenant_id=tid, employee=emp, leave_type=leave_types[code], start_date=s,
                defaults={"end_date": e, "status": st, "reason": "Demo"},
            )
            if created:
                obj.days = obj.compute_days()
                obj.save(update_fields=["days"])
                n["leave"] += 1

        self.stdout.write(self.style.SUCCESS(
            "Demo business seeded: " + ", ".join(f"{k}={v}" for k, v in n.items())
        ))
