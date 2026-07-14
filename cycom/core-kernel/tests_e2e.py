# -*- coding: utf-8 -*-
import hashlib
import sys
import os

# Override database URLs BEFORE importing the database module to isolate tests
os.environ["DATABASE_URL"] = "sqlite:///test_e2e_cycom.db"
os.environ["EU_DATABASE_URL"] = "sqlite:///test_e2e_cycom_eu.db"

import unittest
from decimal import Decimal

# Include root apps path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from db import Base, AuditLog, get_engine_for_tenant, get_tenant_session
from insight_engine import InsightEngine
from auth import JWTManager

# HR & Payroll
from apps.hr.payroll_calc import PayrollEngine
from apps.hr.models import Contract, Employee

# CRM
from apps.crm.models import Lead, Partner, SaleOrder, CRMWorkflowService

# Inventory
from apps.inventory.models import Product, StockLocation, StockQuant, StockMove, InventoryService

# MRP
from apps.mrp.models import BillOfMaterials, BillOfMaterialsLine, ManufacturingOrder, MRPProductionService


class CycomE2ETests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Remove any existing test database files to force fresh schema creation
        for db_file in ("test_e2e_cycom.db", "test_e2e_cycom_eu.db"):
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass

        """Initialise database tables for both main and EU shards prior to executing tests."""
        engine_us = get_engine_for_tenant(1)
        engine_eu = get_engine_for_tenant(1050)
        Base.metadata.create_all(bind=engine_us)
        Base.metadata.create_all(bind=engine_eu)

    @classmethod
    def tearDownClass(cls):
        # Clean up test database files
        for db_file in ("test_e2e_cycom.db", "test_e2e_cycom_eu.db"):
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass

    def setUp(self):
        """Clean database tables before each test to ensure complete isolation."""
        db = get_tenant_session(1)
        try:
            # Clear test tables in reverse order of foreign key dependency
            db.execute(Base.metadata.tables["mrp_manufacturing_orders"].delete())
            db.execute(Base.metadata.tables["mrp_bom_lines"].delete())
            db.execute(Base.metadata.tables["mrp_boms"].delete())
            db.execute(Base.metadata.tables["inv_stock_moves"].delete())
            db.execute(Base.metadata.tables["inv_quants"].delete())
            db.execute(Base.metadata.tables["inv_locations"].delete())
            db.execute(Base.metadata.tables["inv_products"].delete())
            db.execute(Base.metadata.tables["crm_sale_orders"].delete())
            db.execute(Base.metadata.tables["crm_partners"].delete())
            db.execute(Base.metadata.tables["crm_leads"].delete())
            db.execute(Base.metadata.tables["hr_employees"].delete())
            db.execute(Base.metadata.tables["fin_journal_lines"].delete())
            db.execute(Base.metadata.tables["fin_journal_entries"].delete())
            db.execute(Base.metadata.tables["fin_accounts"].delete())
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"setUp database cleanup encountered error: {e}")
        finally:
            db.close()

    def test_shard_routing(self):
        """Verify dynamic GDPR sharding based on tenant ID routing boundaries."""
        engine_us = get_engine_for_tenant(1)
        engine_eu = get_engine_for_tenant(1050)

        self.assertNotEqual(engine_us.url.database, engine_eu.url.database)
        self.assertTrue("eu" in engine_eu.url.database.lower())

    def test_audit_hash_chain(self):
        """Verify cryptographic SHA-256 blockchain-style chaining on audit entries."""
        db = get_tenant_session(1)
        try:
            # Clear previous test data to run isolation tests
            db.query(AuditLog).delete()
            db.commit()

            # Insert First Block
            prev_hash = "0"
            user = "tester@cycom.com"
            action = "POST /api/setup/bootstrap"
            details = "HTTP Response: 200"

            raw_payload1 = f"{prev_hash}|{user}|{action}|{details}"
            hash1 = hashlib.sha256(raw_payload1.encode("utf-8")).hexdigest()

            block1 = AuditLog(
                user_email=user,
                action=action,
                details=details,
                tenant_id=1,
                company_id=1,
                prev_hash=prev_hash,
                current_hash=hash1
            )
            db.add(block1)
            db.commit()

            # Insert Second Block chained to First
            raw_payload2 = f"{hash1}|{user}|{action}|{details}"
            hash2 = hashlib.sha256(raw_payload2.encode("utf-8")).hexdigest()

            block2 = AuditLog(
                user_email=user,
                action=action,
                details=details,
                tenant_id=1,
                company_id=1,
                prev_hash=hash1,
                current_hash=hash2
            )
            db.add(block2)
            db.commit()

            # Fetch blocks and assert link validation
            records = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].prev_hash, "0")
            self.assertEqual(records[1].prev_hash, records[0].current_hash)
            self.assertEqual(records[1].current_hash, hash2)

        finally:
            db.close()

    def test_safe_insight_engine(self):
        """Verify InsightEngine compiles parameterized queries and blocks structural exploits."""
        sql, params = InsightEngine.nlp_to_sql("show active employees in Amman", tenant_id=1, company_id=1)

        self.assertIn("tenant_id = :tenant_id", sql)
        self.assertEqual(params["tenant_id"], 1)
        self.assertEqual(params["location"], "%amman%")

        # Test blocking SQL Injection structural alteration attempts
        with self.assertRaises(PermissionError):
            InsightEngine.execute_query(None, "SELECT * FROM hr_employees; DROP TABLE users;", {})

    def test_payroll_tax_brackets(self):
        """Verify Jordanian income tax brackets and net wage calculations."""
        contract = Contract(base_salary=Decimal("1500.00"))
        res = PayrollEngine.calculate_payslip(contract, country_code="JO")

        self.assertEqual(res["employee_social_security"], Decimal("112.50"))
        self.assertEqual(res["income_tax"], Decimal("42.95"))
        self.assertEqual(res["net"], Decimal("1344.55"))

    def test_multi_line_payroll_posting(self):
        """Verify dynamic balanced 5-line ledger payroll entry postings."""
        db = get_tenant_session(1)
        try:
            employee = Employee(
                employee_no="EMP_E2E_01",
                first_name="John",
                last_name="Doe",
                tenant_id=1,
                company_id=1
            )
            db.add(employee)
            db.commit()

            payroll_details = {
                "gross": Decimal("2000.00"),
                "employee_social_security": Decimal("150.00"),
                "employer_social_security": Decimal("285.00"),
                "income_tax": Decimal("180.00"),
                "net": Decimal("1670.00")
            }

            entry = PayrollEngine.post_payroll_to_ledger(
                db=db,
                employee=employee,
                payroll_details=payroll_details,
                tenant_id=1,
                company_id=1
            )

            from apps.finance.models import JournalLine
            lines = db.query(JournalLine).filter(JournalLine.entry_id == entry.id).all()
            self.assertEqual(len(lines), 5)

            # Sum Debits and Credits and assert balance
            total_debits = sum(Decimal(str(line.debit)) for line in lines)
            total_credits = sum(Decimal(str(line.credit)) for line in lines)

            self.assertEqual(total_debits, Decimal("2285.00"))
            self.assertEqual(total_credits, Decimal("2285.00"))
        finally:
            db.close()

    def test_crm_lead_to_sale_order_workflow(self):
        """Verify B2B CRM lead-to-order pipeline transitions and customer provisioning."""
        db = get_tenant_session(1)
        try:
            lead = Lead(
                name="E2E Corp Supply Deal",
                contact_name="Alice Smith",
                contact_email="alice@e2ecorp.com",
                contact_phone="+962790000000",
                expected_revenue=Decimal("10000.00"),
                stage="proposal",
                tenant_id=1,
                company_id=1
            )
            db.add(lead)
            db.commit()

            order = CRMWorkflowService.convert_lead_to_order(
                db=db,
                lead=lead,
                order_number="SO-E2E-001",
                tenant_id=1,
                company_id=1
            )

            self.assertEqual(lead.stage, "won")
            self.assertEqual(order.number, "SO-E2E-001")
            self.assertEqual(order.amount_untaxed, Decimal("10000.00"))

            partner = db.query(Partner).filter(Partner.id == order.partner_id).first()
            self.assertIsNotNone(partner)
            self.assertEqual(partner.name, "Alice Smith")
        finally:
            db.close()

    def test_inventory_avco_costing_and_mrp_consumption(self):
        """Verify double-entry stock moves, AVCO updates, and production loop consumptions."""
        db = get_tenant_session(1)
        try:
            # 1. Create Raw Material (steel) and Finished Product (frame)
            steel = Product(name="Raw Steel", code="MAT_STEEL", cost=Decimal("10.00"), price=Decimal("12.00"), tenant_id=1, company_id=1)
            frame = Product(name="Bicycle Frame", code="PROD_FRAME", cost=Decimal("0.00"), price=Decimal("150.00"), tenant_id=1, company_id=1)
            db.add(steel)
            db.add(frame)
            db.commit()

            # 2. Add Stock Locations
            loc_src = StockLocation(warehouse_id=1, name="Raw Stores", tenant_id=1, company_id=1)
            loc_dest = StockLocation(warehouse_id=1, name="Finished Stores", tenant_id=1, company_id=1)
            db.add(loc_src)
            db.add(loc_dest)
            db.commit()

            # 3. Simulate Purchase Order receipt of Raw Materials (sets AVCO cost)
            InventoryService.execute_stock_move(
                db=db,
                product_id=steel.id,
                from_loc_id=None,  # Incoming purchase
                to_loc_id=loc_src.id,
                qty=Decimal("100.00"),
                price_unit=Decimal("12.00"),  # New purchase price changes cost from $10 to $12
                reference="PO-E2E-01",
                tenant_id=1,
                company_id=1
            )

            # Recalculate steel cost
            db.refresh(steel)
            self.assertEqual(steel.cost, Decimal("12.00"))

            # 4. Create BOM: 1 Frame requires 5 steel components
            bom = BillOfMaterials(product_id=frame.id, name="Frame BOM", version="1.0", tenant_id=1, company_id=1)
            db.add(bom)
            db.commit()

            bom_line = BillOfMaterialsLine(bom_id=bom.id, component_product_id=steel.id, qty=Decimal("5.00"), tenant_id=1, company_id=1)
            db.add(bom_line)
            db.commit()

            # 5. Create and Execute Manufacturing Order
            mo = ManufacturingOrder(
                number="MO-E2E-001",
                product_id=frame.id,
                bom_id=bom.id,
                qty_planned=Decimal("2.00"),
                tenant_id=1,
                company_id=1
            )
            db.add(mo)
            db.commit()

            # Execute MO completion
            MRPProductionService.complete_manufacturing_order(
                db=db,
                mo_id=mo.id,
                component_loc_id=loc_src.id,
                finished_loc_id=loc_dest.id,
                tenant_id=1,
                company_id=1
            )

            # Assert raw steel was consumed: 100 - (5 components * 2 planned) = 90
            quant_steel = db.query(StockQuant).filter(StockQuant.location_id == loc_src.id, StockQuant.product_id == steel.id).first()
            self.assertEqual(quant_steel.qty, Decimal("90.00"))

            # Assert finished frame was produced: 2
            quant_frame = db.query(StockQuant).filter(StockQuant.location_id == loc_dest.id, StockQuant.product_id == frame.id).first()
            self.assertEqual(quant_frame.qty, Decimal("2.00"))
        finally:
            db.close()

    def test_jwt_authentication_mechanisms(self):
        """Verify cryptographically signed JWT token creation and payload validations."""
        claims = {"email": "manager@cycom.com", "role": "manager"}
        token = JWTManager.encode(claims, expires_in=10)
        self.assertIsNotNone(token)

        decoded = JWTManager.decode(token)
        self.assertEqual(decoded["email"], "manager@cycom.com")
        self.assertEqual(decoded["role"], "manager")


if __name__ == "__main__":
    unittest.main()
