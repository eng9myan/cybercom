"""
CyMed WHO ICD-11 integration package.

Real client for the WHO ICD-11 REST API (https://icd.who.int/icdapi):
  * OAuth2 client_credentials token exchange
  * Linearization search, entity/foundation lookup, code info

The public surface is :class:`WHOICDClient` — a library-only integration,
not wired into URL routers here.
"""
from __future__ import annotations

from .client import WHOICDClient

__all__ = ["WHOICDClient"]

default_app_config = "products.cymed.integrations.whoicd.apps.WHOICDConfig"
