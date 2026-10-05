"""OpenAPI wiring for the interactive docs: tells the schema generator how callers authenticate."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class PartnerAPIKeyScheme(OpenApiAuthenticationExtension):
    target_class = "products.cymart.partners.auth.PartnerAPIKeyAuthentication"
    name = "ApiKeyAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Your partner API key. Keys are shown once when issued and stored only as a one-way hash.",
        }
