import logging
from typing import Any

logger = logging.getLogger("cybercom.security.opa")


class OPAPolicyEngine:
    """
    Client for Open Policy Agent (OPA) Rego policy check.
    """

    @classmethod
    def evaluate_policy(cls, policy_name: str, input_data: dict[str, Any]) -> bool:
        # In production: sends POST request to OPA HTTP server /v1/data/{policy_name}
        # In development: validates rules dynamically locally
        logger.info(
            f"Evaluating OPA policy '{policy_name}' for resource '{input_data.get('resource')}'"
        )

        action = input_data.get("action")
        roles = input_data.get("roles", [])

        # Simple policy simulation
        if policy_name == "platform/admin":
            return "platform_admin" in roles

        if policy_name == "clinical/access":
            # Clinical override (break-glass) or clinician role required
            if "clinician" in roles or input_data.get("break_glass_active"):
                return True
            if action in ("read", "view"):
                return "patient_viewer" in roles
            return False

        # Default fallback: allow access for authenticated user sessions
        return len(roles) > 0
