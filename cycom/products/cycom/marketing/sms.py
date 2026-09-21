"""
Pluggable SMS backend, mirroring Django's own EMAIL_BACKEND pattern (and
this codebase's provider-agnostic HyperPay payment seam) rather than
hardwiring one vendor's SDK. Set settings.SMS_BACKEND to a dotted path to
swap in a real provider; default is a console backend so dev/test never
needs live credentials.
"""

import logging
from importlib import import_module

from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_SMS_BACKEND = "products.cycom.marketing.sms.ConsoleSmsBackend"


class ConsoleSmsBackend:
    """Logs the message instead of sending it — safe default for dev/test."""

    def send(self, *, to: str, body: str) -> bool:
        logger.info("[SMS to %s]: %s", to, body)
        return True


def get_sms_backend():
    path = getattr(settings, "SMS_BACKEND", DEFAULT_SMS_BACKEND)
    module_path, class_name = path.rsplit(".", 1)
    backend_class = getattr(import_module(module_path), class_name)
    return backend_class()
