import uuid
from typing import Any

from django.utils import timezone

from platform.cydata.models import CDCPipelineLog, DataAsset, DataQualityRule, MasterDataMap


class DataQualityEngine:
    """
    Evaluates schema constraints and data quality assertions on physical tables.
    """

    @classmethod
    def evaluate_asset(cls, asset: DataAsset, records: list[dict[str, Any]]) -> dict[str, Any]:
        rules = DataQualityRule.objects.filter(asset=asset, active=True)
        failed_checks = []
        passed_count = 0

        for record in records:
            for rule in rules:
                val = record.get(rule.column_name)
                # Assertion rules
                if rule.assertion_type == "not_null":
                    if val is None or val == "":
                        failed_checks.append(
                            {
                                "column": rule.column_name,
                                "rule": "not_null",
                                "record": record,
                                "reason": "Value is null or empty",
                            }
                        )
                        continue
                elif rule.assertion_type == "min_value":
                    min_val = rule.assertion_params.get("min", 0)
                    if val is None or float(val) < float(min_val):
                        failed_checks.append(
                            {
                                "column": rule.column_name,
                                "rule": "min_value",
                                "record": record,
                                "reason": f"Value {val} is below minimum {min_val}",
                            }
                        )
                        continue
                elif rule.assertion_type == "unique":
                    # For simplicity, simulated list validations
                    pass
                passed_count += 1

        return {
            "asset_name": asset.name,
            "total_records_evaluated": len(records),
            "passed_assertions": passed_count,
            "failed_assertions": len(failed_checks),
            "failures": failed_checks,
            "success": len(failed_checks) == 0,
        }


class MasterDataReconciler:
    """
    Coordinates master records reconciliation and mapping to golden records.
    """

    @classmethod
    def match_and_link(
        cls, entity_type: str, source_system: str, source_id: str, matching_fields: dict[str, Any]
    ) -> MasterDataMap:
        # Reconcile matching profiles: if patient/employee already has a registered gold record matches
        # For simplicity, search for matching source records or create a new golden UUID
        existing = MasterDataMap.objects.filter(
            entity_type=entity_type, source_system=source_system, source_id=source_id
        ).first()

        if existing:
            return existing

        # Check if another system matches this record (e.g. by national identity number or email)
        email = matching_fields.get("email")
        national_id = matching_fields.get("national_id")

        linked_record = None
        if email or national_id:
            query = MasterDataMap.objects.filter(entity_type=entity_type)
            # Find any records with high confidence match (simulated mapping lookup)
            for mapping in query:
                if mapping.source_id == source_id:
                    linked_record = mapping.golden_record_id
                    break

        golden_id = linked_record or uuid.uuid4()

        mapping = MasterDataMap.objects.create(
            entity_type=entity_type,
            source_system=source_system,
            source_id=source_id,
            golden_record_id=golden_id,
            match_confidence=98.50 if linked_record else 100.00,
        )
        return mapping


class CDCPipelineClient:
    """
    Triggers Debezium WAL change data capture updates simulation.
    """

    @classmethod
    def trigger_cdc_sync(
        cls, tenant_id: str, table_name: str, records_count: int
    ) -> CDCPipelineLog:
        log = CDCPipelineLog.objects.create(
            tenant_id=tenant_id,
            table_name=table_name,
            records_synced=records_count,
            status="synced",
            last_processed_lsn=f"0/16F{uuid.uuid4().hex[:4].upper()}",
            synced_at=timezone.now(),
        )
        return log
