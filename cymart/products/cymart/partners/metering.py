"""Usage metering must never take a safety answer down with it.

A failed write to the usage log (a locked or briefly unavailable database, for example) is recorded in the server log and the
customer still gets the verdict. The cost is one missing usage row, which the log line lets an operator reconcile; the
alternative was a 500 on a safety check."""
import logging

from .models import PartnerCallLog

log = logging.getLogger(__name__)


def record_usage(partner, item_count) -> None:
    try:
        PartnerCallLog.objects.create(partner=partner, item_count=min(max(int(item_count), 0), 32000))
    except Exception as exc:  # noqa: BLE001 - deliberately broad: metering is not allowed to fail a request
        log.error("usage metering failed for partner %s: %s", getattr(partner, "id", "?"), type(exc).__name__)
