import uuid
import pytest
from rest_framework.test import APIClient
import jwt

from platform.cydata.models import DataAsset, DataLineage, DataQualityRule, MasterDataMap, CDCPipelineLog
from platform.cydata.services import DataQualityEngine, MasterDataReconciler, CDCPipelineClient

@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()

@pytest.fixture
def auth_client(test_tenant_id):
    client = APIClient()
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "admin@cybercom.io",
        "tenant_id": str(test_tenant_id),
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = jwt.encode(payload, "dummy-secret", algorithm="HS256")
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_TENANT_ID=str(test_tenant_id),
    )
    return client

@pytest.mark.django_db
class TestDataModels:
    def test_data_asset(self):
        asset = DataAsset.objects.create(
            name="patient_records",
            asset_type="table",
            physical_path="s3://cybercom-data/patients",
            schema_definition={"columns": ["id", "email", "age"]},
            pii_columns=["email"],
            phi_columns=["id"],
            data_residency_region="me-central-1"
        )
        assert asset.name == "patient_records"
        assert asset.data_residency_region == "me-central-1"

    def test_data_lineage(self, test_tenant_id):
        asset_src = DataAsset.objects.create(
            name="patients_raw",
            asset_type="table",
            physical_path="s3://patients_raw"
        )
        asset_dst = DataAsset.objects.create(
            name="patients_clean",
            asset_type="table",
            physical_path="s3://patients_clean"
        )
        lineage = DataLineage.objects.create(
            tenant_id=test_tenant_id,
            source_asset=asset_src,
            target_asset=asset_dst,
            transformation_job="spark_etl_patients"
        )
        assert lineage.source_asset == asset_src
        assert lineage.target_asset == asset_dst

    def test_data_quality_rule(self):
        asset = DataAsset.objects.create(
            name="patients",
            asset_type="table",
            physical_path="s3://patients"
        )
        rule = DataQualityRule.objects.create(
            asset=asset,
            column_name="email",
            assertion_type="not_null",
            assertion_params={},
            active=True
        )
        assert rule.column_name == "email"

    def test_master_data_map(self):
        mapping = MasterDataMap.objects.create(
            entity_type="Patient",
            source_system="Epic",
            source_id="EPIC-1",
            golden_record_id=uuid.uuid4(),
            match_confidence=100.00
        )
        assert mapping.entity_type == "Patient"


@pytest.mark.django_db
class TestDataQualityEngine:
    def test_quality_assertions(self):
        asset = DataAsset.objects.create(
            name="test_asset",
            asset_type="table",
            physical_path="s3://test"
        )
        # Add Rules
        DataQualityRule.objects.create(
            asset=asset,
            column_name="email",
            assertion_type="not_null",
            active=True
        )
        DataQualityRule.objects.create(
            asset=asset,
            column_name="age",
            assertion_type="min_value",
            assertion_params={"min": 18},
            active=True
        )

        records = [
            {"email": "test@cybercom.io", "age": 25},
            {"email": "", "age": 20},  # Fails not_null
            {"email": "valid@cybercom.io", "age": 15},  # Fails min_value
        ]

        report = DataQualityEngine.evaluate_asset(asset, records)
        assert report["total_records_evaluated"] == 3
        assert report["failed_assertions"] == 2
        assert report["success"] is False
        assert len(report["failures"]) == 2


@pytest.mark.django_db
class TestMasterDataReconciler:
    def test_reconciliation(self):
        # 1. First record reconciliation (creates a new golden record)
        map1 = MasterDataReconciler.match_and_link(
            entity_type="Patient",
            source_system="Epic",
            source_id="EPIC-101",
            matching_fields={"email": "p1@cybercom.io"}
        )
        assert map1.match_confidence == 100.00
        gold_id = map1.golden_record_id

        # 2. Subsequent match (should return the same map)
        map2 = MasterDataReconciler.match_and_link(
            entity_type="Patient",
            source_system="Epic",
            source_id="EPIC-101",
            matching_fields={"email": "p1@cybercom.io"}
        )
        assert map2.id == map1.id
        assert map2.golden_record_id == gold_id


@pytest.mark.django_db
class TestCDCPipelineClient:
    def test_sync(self, test_tenant_id):
        log = CDCPipelineClient.trigger_cdc_sync(str(test_tenant_id), "patient_table", 45)
        assert log.table_name == "patient_table"
        assert log.records_synced == 45
        assert log.status == "synced"


@pytest.mark.django_db
class TestDataAPIs:
    def test_list_assets(self, auth_client):
        DataAsset.objects.create(name="asset_1", asset_type="table", physical_path="s3://1")
        resp = auth_client.get("/api/v1/data/assets/")
        assert resp.status_code == 200
        assert len(resp.data) >= 1

    def test_evaluate_quality_api(self, auth_client):
        asset = DataAsset.objects.create(name="asset_2", asset_type="table", physical_path="s3://2")
        DataQualityRule.objects.create(asset=asset, column_name="age", assertion_type="not_null", active=True)
        resp = auth_client.post(
            f"/api/v1/data/assets/{asset.id}/evaluate/",
            {"records": [{"age": 30}]},
            format="json"
        )
        assert resp.status_code == 200
        assert resp.data["success"] is True

    def test_match_mdm_api(self, auth_client):
        resp = auth_client.post(
            "/api/v1/data/master-data/match/",
            {
                "entity_type": "Patient",
                "source_system": "Epic",
                "source_id": "EPIC-202",
                "matching_fields": {"email": "p2@cybercom.io"}
            },
            format="json"
        )
        assert resp.status_code == 200
        assert resp.data["entity_type"] == "Patient"

    def test_sync_cdc_api(self, auth_client, test_tenant_id):
        resp = auth_client.post(
            "/api/v1/data/cdc-logs/sync/",
            {
                "tenant_id": str(test_tenant_id),
                "table_name": "clinical_encounter",
                "records_count": 15
            },
            format="json"
        )
        assert resp.status_code == 201
        assert resp.data["table_name"] == "clinical_encounter"
        assert resp.data["records_synced"] == 15
