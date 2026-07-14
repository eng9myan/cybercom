# -*- coding: utf-8 -*-
import logging
import re
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Strict regular expression validating the parameterized query structure.
# Prevents interpolation, inline values, nested queries, or comment characters.
STRICT_QUERY_REGEX = re.compile(
    r"^select \* from (hr_employees|hr_departments|proj_tasks|crm_leads) "
    r"where tenant_id = :tenant_id and company_id = :company_id and is_active = :is_active"
    r"(?: and [a-z0-9_]+ = :[a-z0-9_]+)*"
    r"(?: and [a-z0-9_]+ ilike :[a-z0-9_]+)*$",
    re.IGNORECASE
)


class InsightEngine:
    """Secure Semantic NLP-to-SQL compiler enforcing parameterized query boundaries."""

    @staticmethod
    def nlp_to_sql(user_text: str, tenant_id: int, company_id: int) -> tuple:
        """Translates natural language statements into strict, parameterized SQL and query parameters."""
        query = user_text.lower().strip()

        # Target table routing based on semantic tokens
        table_name = None
        if any(w in query for w in ["employee", "staff", "workforce"]):
            table_name = "hr_employees"
        elif "department" in query:
            table_name = "hr_departments"
        elif any(w in query for w in ["task", "todo", "kanban"]):
            table_name = "proj_tasks"
        elif any(w in query for w in ["lead", "pipeline", "deal"]):
            table_name = "crm_leads"
        else:
            raise ValueError("Query domain not recognized or out of scope.")

        # Baseline multi-tenant parameterized query template
        sql = f"SELECT * FROM {table_name} WHERE tenant_id = :tenant_id AND company_id = :company_id AND is_active = :is_active"
        params = {
            "tenant_id": tenant_id,
            "company_id": company_id,
            "is_active": True
        }

        # Apply simple criteria matching to bound variables instead of concatenating strings
        email_match = re.search(r"email\s+(?:is|equals|=)\s+['\"]?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)['\"]?", query)
        if email_match:
            sql += " AND email = :email"
            params["email"] = email_match.group(1)

        location_match = re.search(r"in\s+([a-zA-Z]+)", query)
        if location_match:
            loc = location_match.group(1)
            # Filter out noise keywords
            if loc not in ["employee", "staff", "department", "task", "lead", "pipeline", "amman"]:
                sql += " AND location ILIKE :location"
                params["location"] = f"%{loc}%"
            elif loc == "amman":
                sql += " AND location ILIKE :location"
                params["location"] = "%amman%"

        return sql, params

    @staticmethod
    def execute_query(db: Session, sql_query: str, params: dict) -> list:
        """Runs the generated SQL query with parameter bindings after verifying safety regex."""
        # Normalise whitespace for regex matching
        normalised_sql = " ".join(sql_query.split())

        # Enforce AST-like structural safety regex
        if not STRICT_QUERY_REGEX.match(normalised_sql):
            logger.critical(f"SECURITY ALERT: InsightEngine blocked query: {normalised_sql}")
            raise PermissionError("Execution blocked: SQL failed structural integrity safety checks.")

        try:
            res = db.execute(text(sql_query), params)
            return [dict(row._mapping) for row in res.all()]
        except Exception as e:
            logger.error(f"SQL execution error in InsightEngine: {str(e)}")
            raise e
