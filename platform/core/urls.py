"""Root URLconf for the standalone platform test project.

Mounts every platform app that ships a urls module at the same prefix the
product projects use, so endpoint tests have a real route to hit. A missing
module is skipped rather than fatal.
"""
import importlib

from django.urls import include, path

urlpatterns = []

_APP_ROUTES = [
    ("", "platform.observability.urls"),
    ("api/v1/public/", "platform.tenant.urls_public"),
    ("api/v1/tenants/", "platform.tenant.urls"),
    ("api/v1/identity/", "platform.cyidentity.urls"),
    ("api/v1/wallet/", "platform.wallet.urls"),
    ("api/v1/events/", "platform.events.urls"),
    ("api/v1/integration/", "platform.cyintegrationhub.urls"),
    ("api/v1/data/", "platform.cydata.urls"),
    ("api/v1/ai/", "platform.cyai.urls"),
    ("api/v1/common/", "platform.common.urls"),
    ("api/v1/terminology/", "platform.terminology.urls"),
    ("api/v1/notifications/", "platform.notifications.urls"),
    ("api/v1/audit/", "platform.audit.urls"),
    ("api/v1/canonical/", "platform.canonical.urls"),
    ("api/v1/provisioning/", "platform.provisioning.urls"),
    ("api/v1/einvoicing/", "platform.einvoicing.urls"),
    ("api/v1/", "platform.api.urls"),
]

for prefix, module in _APP_ROUTES:
    try:
        importlib.import_module(module)
    except ModuleNotFoundError:
        continue
    urlpatterns.append(path(prefix, include(module)))
