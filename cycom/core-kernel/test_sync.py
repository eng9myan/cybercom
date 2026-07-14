# -*- coding: utf-8 -*-
import sys
import os

# Override database URLs BEFORE importing the database module to isolate tests
os.environ["DATABASE_URL"] = "sqlite:///test_sync_cycom.db"
os.environ["EU_DATABASE_URL"] = "sqlite:///test_sync_cycom_eu.db"

import unittest
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from db import Base, get_engine_for_tenant, get_tenant_session, SyncLog
from apps.inventory.models import Product
from sync import EdgeSyncManager


class CycomSyncTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Remove any existing test database files to force fresh schema creation
        for db_file in ("test_sync_cycom.db", "test_sync_cycom_eu.db"):
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass

        engine = get_engine_for_tenant(1)
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        # Clean up test database files
        for db_file in ("test_sync_cycom.db", "test_sync_cycom_eu.db"):
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass

    def setUp(self):
        """Reset database tables before each test case."""
        db = get_tenant_session(1)
        try:
            db.execute(Base.metadata.tables["core_sync_logs"].delete())
            db.execute(Base.metadata.tables["inv_products"].delete())
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    def test_edge_to_cloud_upload(self):
        """Verify that edge uploaded records are correctly instantiated or updated on the cloud."""
        db = get_tenant_session(1)
        try:
            # 1. Prepare edge sync batch (Product creation)
            edge_time = datetime.utcnow()
            batch = [
                {
                    "model": "inventory.product",
                    "action": "create",
                    "data": {
                        "id": 999,
                        "name": "Sync Test product",
                        "code": "SYNC_PROD_1",
                        "cost": 50.00,
                        "price": 75.00,
                        "last_modified": edge_time.isoformat() + "Z"
                    }
                }
            ]

            res = EdgeSyncManager.process_upward_sync(db, "edge_register_01", batch, tenant_id=1, company_id=1)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["synced"], 1)

            # Query database and verify product exists with correct details
            prod = db.query(Product).filter(Product.id == 999, Product.tenant_id == 1).first()
            self.assertIsNotNone(prod)
            self.assertEqual(prod.name, "Sync Test product")
            self.assertEqual(prod.code, "SYNC_PROD_1")
            self.assertEqual(float(prod.cost), 50.00)

            # Check that SyncLog was created
            log = db.query(SyncLog).filter(SyncLog.edge_id == "edge_register_01").first()
            self.assertIsNotNone(log)
            self.assertEqual(log.status, "success")
        finally:
            db.close()

    def test_conflict_resolution_lww(self):
        """Verify Last-Write-Wins (LWW) conflict resolution logic is strictly enforced."""
        db = get_tenant_session(1)
        try:
            cloud_time = datetime.utcnow()
            
            # 1. Set initial product state on cloud
            prod = Product(
                id=999,
                name="Cloud Product Old",
                code="SYNC_PROD_1",
                cost=Decimal("100.00"),
                price=Decimal("150.00"),
                last_modified=cloud_time,
                tenant_id=1,
                company_id=1
            )
            db.add(prod)
            db.commit()

            # 2. Upload batch with an OLDER timestamp (should be skipped)
            older_time = cloud_time - timedelta(minutes=10)
            batch_old = [
                {
                    "model": "inventory.product",
                    "action": "write",
                    "data": {
                        "id": 999,
                        "name": "Should Not Update",
                        "cost": 10.00,
                        "last_modified": older_time.isoformat() + "Z"
                    }
                }
            ]

            res1 = EdgeSyncManager.process_upward_sync(db, "edge_register_01", batch_old, tenant_id=1, company_id=1)
            self.assertEqual(res1["skipped"], 1)

            # Verify no changes in cloud database
            db.refresh(prod)
            self.assertEqual(prod.name, "Cloud Product Old")
            self.assertEqual(float(prod.cost), 100.00)

            # 3. Upload batch with a NEWER timestamp (should overwrite)
            newer_time = cloud_time + timedelta(minutes=10)
            batch_new = [
                {
                    "model": "inventory.product",
                    "action": "write",
                    "data": {
                        "id": 999,
                        "name": "Cloud Product Updated",
                        "cost": 200.00,
                        "last_modified": newer_time.isoformat() + "Z"
                    }
                }
            ]

            res2 = EdgeSyncManager.process_upward_sync(db, "edge_register_01", batch_new, tenant_id=1, company_id=1)
            self.assertEqual(res2["synced"], 1)

            # Verify changes are applied in cloud database
            db.refresh(prod)
            self.assertEqual(prod.name, "Cloud Product Updated")
            self.assertEqual(float(prod.cost), 200.00)
        finally:
            db.close()

    def test_downward_delta_download(self):
        """Verify downward delta generator bundles modified records since last sync time."""
        db = get_tenant_session(1)
        try:
            # 1. Create a product modified in the past
            past_time = datetime.utcnow() - timedelta(hours=1)
            prod_past = Product(
                id=801,
                name="Past Product",
                code="PROD_PAST",
                last_modified=past_time,
                tenant_id=1,
                company_id=1
            )
            db.add(prod_past)

            # 2. Create a product modified recently (fresh update)
            recent_time = datetime.utcnow()
            prod_recent = Product(
                id=802,
                name="Recent Product",
                code="PROD_RECENT",
                last_modified=recent_time,
                tenant_id=1,
                company_id=1
            )
            db.add(prod_recent)
            db.commit()

            # 3. Generate delta since 10 minutes ago
            sync_time = datetime.utcnow() - timedelta(minutes=10)
            delta = EdgeSyncManager.generate_downward_delta(db, sync_time, tenant_id=1)

            # Assert only prod_recent (id=802) is fetched, not prod_past
            self.assertEqual(len(delta), 1)
            self.assertEqual(delta[0]["data"]["id"], 802)
            self.assertEqual(delta[0]["data"]["name"], "Recent Product")
        finally:
            db.close()

    def test_sync_endpoints_via_live_server(self):
        """Verify the sync HTTP endpoints (upload and download) on the live running micro-kernel."""
        import urllib.request
        import json
        
        # 1. Login to get token
        login_url = "http://127.0.0.1:8888/api/auth/login"
        payload = json.dumps({"email": "admin@cycom.com", "password": "admin123"}).encode()
        req = urllib.request.Request(login_url, data=payload, headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req) as res:
                body = json.loads(res.read().decode())
                token = body["access_token"]
        except Exception as e:
            # If live server is not running, skip test gracefully instead of failing
            self.skipTest(f"Live server not available: {e}")
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": "1",
            "Content-Type": "application/json"
        }

        # 2. Test Upload Endpoint
        edge_time = datetime.utcnow()
        upload_payload = json.dumps({
            "edge_id": "pos_register_e2e",
            "batch": [
                {
                    "model": "inventory.product",
                    "action": "create",
                    "data": {
                        "id": 888,
                        "name": "Live HTTP Sync Product",
                        "code": "HTTP_SYNC_PROD",
                        "cost": 12.50,
                        "price": 20.00,
                        "last_modified": edge_time.isoformat() + "Z"
                    }
                }
            ]
        }).encode()

        upload_url = "http://127.0.0.1:8888/api/sync/upload"
        req_upload = urllib.request.Request(upload_url, data=upload_payload, headers=headers)
        with urllib.request.urlopen(req_upload) as res:
            res_body = json.loads(res.read().decode())
            self.assertEqual(res_body["status"], "success")

        # 3. Test Download Endpoint
        sync_time = edge_time - timedelta(minutes=1)
        download_url = f"http://127.0.0.1:8888/api/sync/download?edge_id=pos_register_e2e&last_sync_time={sync_time.isoformat() + 'Z'}"
        req_download = urllib.request.Request(download_url, headers=headers)
        with urllib.request.urlopen(req_download) as res:
            res_body = json.loads(res.read().decode())
            self.assertEqual(res_body["edge_id"], "pos_register_e2e")
            self.assertTrue(len(res_body["delta"]) >= 1)


if __name__ == "__main__":
    unittest.main()
