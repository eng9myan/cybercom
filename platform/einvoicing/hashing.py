"""Invoice hash chain — the tamper-evidence primitive behind e-invoicing.

Every cleared invoice carries the SHA-256 of its own canonical XML plus the
hash of the previous invoice in the same sequence (PIH — Previous Invoice
Hash), so a regulator (or an auditor) can verify the ledger has no gaps or
substitutions. See docs/blueprint/H_nfr_checklist.md C4.
"""
from __future__ import annotations

import base64
import hashlib

# Seed value for the first invoice in a sequence — 64 hex zeros, as ZATCA
# specifies; JoFotara has no formal seed so we reuse the same convention.
GENESIS_PIH = "0" * 64


def invoice_hash(canonical_xml: str) -> str:
    """Base64(SHA-256) of the canonicalised invoice XML."""
    digest = hashlib.sha256(canonical_xml.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


def chain_ok(items: list[tuple[str, str]]) -> bool:
    """Verify a chain.

    `items` is an ordered list of (pih, hash) pairs. Returns True iff the
    first item's pih is the genesis value and every subsequent pih equals
    the prior item's hash.
    """
    if not items:
        return True
    prev = GENESIS_PIH
    for pih, h in items:
        if pih != prev:
            return False
        prev = h
    return True
