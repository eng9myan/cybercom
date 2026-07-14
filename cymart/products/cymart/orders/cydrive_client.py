"""
CyMart -> CyDrive integration (master spec section 6: CyMart orchestrates
delivery, it doesn't own delivery-company data). Cross-service HTTP call —
cymart and cydrive are separate Django projects/databases (separate
deployables), so this is a real network boundary, not a Python import.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger("cymart.cydrive_integration")


class CyDriveIntegrationError(Exception):
    pass


class CyDriveClient:
    def create_delivery_job(
        self,
        access_token: str,
        delivery_company_id: str,
        source_order_id: str,
        pickup_address: dict,
        dropoff_address: dict,
        requires_temperature_control: bool = False,
        cash_collection_amount: "float | None" = None,
    ) -> dict:
        """Creates a CyDrive DeliveryJob for this order. Raises
        CyDriveIntegrationError on any non-2xx response or network failure
        — callers decide whether that should roll back the order
        transition or retry, this doesn't swallow the error."""
        url = f"{settings.CYDRIVE_BASE_URL}/fleet/jobs/"
        payload = {
            "company": delivery_company_id,
            "source_order_id": source_order_id,
            "pickup_address": pickup_address,
            "dropoff_address": dropoff_address,
            "requires_temperature_control": requires_temperature_control,
        }
        if cash_collection_amount is not None:
            payload["cash_collection_amount"] = cash_collection_amount

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=settings.CYDRIVE_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            logger.error("CyDrive job creation failed for order %s: %s", source_order_id, exc)
            raise CyDriveIntegrationError(f"Could not reach CyDrive: {exc}") from exc

        if not response.ok:
            logger.error(
                "CyDrive job creation rejected for order %s: %s %s",
                source_order_id,
                response.status_code,
                response.text,
            )
            raise CyDriveIntegrationError(
                f"CyDrive rejected job creation ({response.status_code}): {response.text}"
            )

        return response.json()
