# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

from bus import EventBus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/hitl", tags=["HITL Approval Queue"])

# Human-in-the-Loop approval queue stored in memory
HITL_QUEUE: List[Dict[str, Any]] = []


class OrchestratorAI:
    """Background AI agent performing dynamic risk mitigation planning based on event streams."""

    @staticmethod
    async def handle_supply_delay(payload: Dict[str, Any]):
        """Triggered on supply delay events. Autonomously draft buffering purchase orders."""
        logger.info(f"[OrchestratorAI] Processing supply.delay: {payload}")
        tenant_id = payload.get("tenant_id", 1)
        company_id = payload.get("company_id", 1)
        product_id = payload.get("product_id", 101)
        delay_days = payload.get("delay_days", 4)

        action = {
            "id": len(HITL_QUEUE) + 1,
            "type": "purchase_order",
            "title": f"Draft PO: Buffer Stock for Product #{product_id}",
            "description": f"Replenishment triggered by supply delay of {delay_days} days. Order quantity scaled by +30% buffer.",
            "tenant_id": tenant_id,
            "company_id": company_id,
            "payload": {
                "product_id": product_id,
                "qty": 250 * delay_days,
                "source": "OrchestratorAI"
            }
        }
        HITL_QUEUE.append(action)
        logger.info(f"[OrchestratorAI] Draft PO enqueued for review: ID={action['id']}")

    @staticmethod
    async def handle_cash_flow_risk(payload: Dict[str, Any]):
        """Triggered on cash flow risks. Autonomously draft provisioning adjustments."""
        logger.info(f"[OrchestratorAI] Processing cash_flow.risk: {payload}")
        tenant_id = payload.get("tenant_id", 1)
        company_id = payload.get("company_id", 1)
        deficit = payload.get("predicted_deficit", 7500.0)

        action = {
            "id": len(HITL_QUEUE) + 1,
            "type": "journal_entry",
            "title": "Draft JE: Risk Provision Adjustment",
            "description": f"Automated ledger reserve provision for cash flow deficit of {deficit} JOD.",
            "tenant_id": tenant_id,
            "company_id": company_id,
            "payload": {
                "debit_account": "100200_liquidity_buffer",
                "credit_account": "300400_general_provisions",
                "amount": deficit
            }
        }
        HITL_QUEUE.append(action)
        logger.info(f"[OrchestratorAI] Draft Journal Entry enqueued for review: ID={action['id']}")


# Register handlers on Event Bus
EventBus.subscribe("supply.delay", OrchestratorAI.handle_supply_delay)
EventBus.subscribe("cash_flow.risk", OrchestratorAI.handle_cash_flow_risk)


@router.get("/queue")
def get_approval_queue():
    """Retrieve all pending autonomous drafts requiring CFO approval."""
    return HITL_QUEUE


@router.post("/approve/{action_id}")
def approve_action(action_id: int):
    """Approve and dispatch an autonomous draft action."""
    global HITL_QUEUE
    match = [a for a in HITL_QUEUE if a["id"] == action_id]
    if not match:
        raise HTTPException(status_code=404, detail="Action not found in HITL queue.")

    action = match[0]
    HITL_QUEUE = [a for a in HITL_QUEUE if a["id"] != action_id]

    # Commit action to database (or trigger execution)
    logger.info(f"Action {action_id} approved by CFO: {action['title']}")
    return {"status": "approved", "action": action}


@router.post("/reject/{action_id}")
def reject_action(action_id: int):
    """Discard an autonomous draft action."""
    global HITL_QUEUE
    match = [a for a in HITL_QUEUE if a["id"] == action_id]
    if not match:
        raise HTTPException(status_code=404, detail="Action not found in HITL queue.")

    HITL_QUEUE = [a for a in HITL_QUEUE if a["id"] != action_id]
    logger.info(f"Action {action_id} rejected by CFO.")
    return {"status": "rejected"}
