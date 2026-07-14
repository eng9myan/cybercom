"""API versioning support. ADR-0003: URL-path versioning."""

from rest_framework.versioning import URLPathVersioning


class CyberComAPIVersioning(URLPathVersioning):
    allowed_versions = ["v1", "v2"]
    default_version = "v1"
    version_param = "version"
