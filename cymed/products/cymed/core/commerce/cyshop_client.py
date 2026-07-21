"""
CyID ecosystem, Phase 8 — cymed -> cyshop integration for cross-network
checkout. cymed and cyshop are separate Django projects/databases — real
network boundary, same pattern as platform/tenant/services.py's cyshop
demo-provisioning adapter and cymart's cydrive_client.py.

Two real calls chained: exchange the person's CyID token for a cyshop
session (Phase 3's bridge), then place a real SalesOrder in that session
under the target merchant tenant's default Company/Branch.
"""

import os

import httpx


class CyshopIntegrationError(Exception):
    pass


def _base_url() -> str:
    return os.environ.get("CYSHOP_BACKEND_URL", "http://localhost:8020")


def exchange_and_place_order(
    cyid_token: str,
    cyshop_tenant_id: str,
    *,
    company_id: str,
    branch_id: str,
    customer_name: str,
    line_items: list[dict],
    timeout: float = 15,
) -> dict:
    """line_items: [{"item_name": ..., "qty": ..., "unit_price": ...}, ...].
    company_id/branch_id identify which cyshop merchant storefront the
    cart item came from — the same thing a real shopping cart already
    knows about any item in it, supplied by the caller rather than
    guessed here (cyshop has no "default storefront for a tenant"
    concept — a tenant can have several branches)."""
    base = _base_url()

    try:
        exchange_resp = httpx.post(
            f"{base}/api/v1/identity/cyid-exchange/",
            json={"cyid_token": cyid_token, "tenant_id": cyshop_tenant_id},
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise CyshopIntegrationError(f"Could not reach cyshop for CyID exchange: {exc}") from exc
    if exchange_resp.status_code != 200:
        raise CyshopIntegrationError(
            f"cyshop CyID exchange failed ({exchange_resp.status_code}): {exchange_resp.text}"
        )
    session = exchange_resp.json()
    access_token = session["access_token"]

    total = sum(float(li["qty"]) * float(li["unit_price"]) for li in line_items)
    order_payload = {
        "order_number": f"CYID-{session['user_id']}-{os.urandom(4).hex()}",
        "tenant_id": cyshop_tenant_id,
        "company": company_id,
        "branch": branch_id,
        "customer_name": customer_name,
        "total_amount": total,
        "lines": line_items,
    }
    try:
        order_resp = httpx.post(
            f"{base}/api/v1/sales/orders/",
            json=order_payload,
            headers={"Authorization": f"Bearer {access_token}", "X-Tenant-ID": cyshop_tenant_id},
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise CyshopIntegrationError(f"Could not reach cyshop for order creation: {exc}") from exc
    if order_resp.status_code not in (200, 201):
        raise CyshopIntegrationError(
            f"cyshop order creation failed ({order_resp.status_code}): {order_resp.text}"
        )
    return order_resp.json()
