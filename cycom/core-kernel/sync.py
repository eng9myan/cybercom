# -*- coding: utf-8 -*-
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal

import sys
import os
sys.path.append(os.path.dirname(__file__))

from db import SyncLog
from rpc import MODEL_MAP, serialize_generic

logger = logging.getLogger("cycom-sync")


def make_naive(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


class EdgeSyncManager:
    """Manages transactional state synchronization between local edge nodes and the central cloud."""

    @staticmethod
    def process_upward_sync(db: Session, edge_id: str, batch: List[Dict[str, Any]], tenant_id: int, company_id: int) -> dict:
        """Processes a batch of database mutations uploaded by an edge node."""
        success_count = 0
        skipped_count = 0
        error_logs = []

        for item in batch:
            model_name = item.get("model")
            action = item.get("action")
            data = item.get("data", {})

            if model_name not in MODEL_MAP:
                error_logs.append(f"Model '{model_name}' not supported.")
                continue

            model_class = MODEL_MAP[model_name]
            record_id = data.get("id")

            if not record_id:
                error_logs.append(f"Missing ID in sync payload for model {model_name}")
                continue

            try:
                # Query existing cloud record
                cloud_record = db.query(model_class).filter(
                    model_class.id == record_id,
                    model_class.tenant_id == tenant_id
                ).first()

                # Parse modification times
                edge_mod_str = data.get("last_modified")
                edge_mod_time = datetime.fromisoformat(edge_mod_str.replace("Z", "+00:00")) if edge_mod_str else datetime.utcnow()

                if cloud_record:
                    # Last-Write-Wins conflict resolution
                    cloud_mod_time = cloud_record.last_modified
                    if cloud_mod_time and make_naive(edge_mod_time) <= make_naive(cloud_mod_time):
                        # Cloud record is newer or same age, skip upward update (Cloud wins)
                        skipped_count += 1
                        continue

                    # Apply updates to existing record
                    for k, v in data.items():
                        if k not in ("id", "tenant_id", "last_modified") and hasattr(cloud_record, k):
                            if isinstance(getattr(model_class, k).type, Numeric) and v is not None:
                                setattr(cloud_record, k, Decimal(str(v)))
                            else:
                                setattr(cloud_record, k, v)
                    cloud_record.last_modified = edge_mod_time
                else:
                    # Insert new record with edge-assigned ID
                    insert_vals = {
                        "id": record_id,
                        "tenant_id": tenant_id,
                        "company_id": company_id,
                        "last_modified": edge_mod_time
                    }
                    for k, v in data.items():
                        if k not in ("id", "tenant_id", "last_modified") and hasattr(model_class, k):
                            insert_vals[k] = Decimal(str(v)) if hasattr(model_class, k) and isinstance(getattr(model_class, k).type, Numeric) and v is not None else v
                    
                    new_obj = model_class(**insert_vals)
                    db.add(new_obj)

                db.commit()
                success_count += 1
            except Exception as e:
                db.rollback()
                error_logs.append(f"Error syncing {model_name} #{record_id}: {str(e)}")

        # Log this sync session
        log_status = "success" if not error_logs else "error"
        sync_log = SyncLog(
            edge_id=edge_id,
            last_sync_timestamp=datetime.utcnow(),
            status=log_status,
            details="; ".join(error_logs) if error_logs else f"Successfully synced {success_count} records.",
            tenant_id=tenant_id,
            company_id=company_id
        )
        db.add(sync_log)
        db.commit()

        return {
            "status": log_status,
            "synced": success_count,
            "skipped": skipped_count,
            "errors": error_logs
        }

    @staticmethod
    def generate_downward_delta(db: Session, last_timestamp: datetime, tenant_id: int) -> List[Dict[str, Any]]:
        """Queries the cloud database for all records modified since the last sync time."""
        delta_payload = []

        for model_name, model_class in MODEL_MAP.items():
            if not hasattr(model_class, "last_modified"):
                continue

            # Query delta records
            records = db.query(model_class).filter(
                model_class.last_modified > last_timestamp,
                model_class.tenant_id == tenant_id
            ).all()

            for r in records:
                delta_payload.append({
                    "model": model_name,
                    "action": "write",
                    "data": serialize_generic(r, db)
                })

        return delta_payload
from sqlalchemy import Numeric
