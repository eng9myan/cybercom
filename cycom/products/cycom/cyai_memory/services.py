from products.cycom.cyai_memory.matching import match_question
from products.cycom.cyai_memory.models import MemoryQueryLog
from products.cycom.cyai_memory.plans import PLAN_REGISTRY


def _format_answer(plan_code: str, result: dict) -> str:
    if plan_code == "sales_summary":
        return (
            f"Sales for {result['warehouse']} ({result['period'].replace('_', ' ')}): "
            f"{result['order_count']} orders totaling {result['total_sales']} {result['currency']}."
        )
    if plan_code == "overdue_invoices":
        if result["count"] == 0:
            return "No overdue invoices."
        return (
            f"{result['count']} overdue invoice(s) totaling {result['total_amount_due']}: "
            f"{', '.join(result['invoice_numbers'])}"
        )
    if plan_code == "product_stock":
        if not result["found"]:
            return f"No product matching '{result['product_name']}' found."
        lines = [f"{r['warehouse']}: {r['quantity_on_hand']}" for r in result["by_warehouse"]]
        return f"Total stock: {result['total_quantity']} ({'; '.join(lines)})."
    if plan_code == "late_employees":
        if result["count"] == 0:
            return f"No employees were late on {result['date']}."
        names = ", ".join(f"{e['name']} ({e['late_minutes']}m)" for e in result["employees"])
        return f"{result['count']} employee(s) late on {result['date']}: {names}."
    return "No formatter for this plan."


class LocalMemoryAgent:
    """
    Entry point for ordinary business Q&A. Every question is matched against
    a fixed set of validated query plans first; only questions that don't
    match any plan fall through — and even then, this deliberately does NOT
    hand off to a paid LLM to guess an answer about real business data (that
    would mean an ungrounded model hallucinating numbers, which is worse
    than an honest "I don't know how to answer that yet"). LLM use is
    reserved for the separate Advanced Report Builder flow, which the user
    explicitly confirms before anything is saved.
    """

    @classmethod
    def answer(cls, *, tenant_id, question: str, asked_by: str = "") -> dict:
        match = match_question(tenant_id, question)

        if not match:
            log = MemoryQueryLog.objects.create(
                tenant_id=tenant_id,
                question=question,
                matched_plan_code="",
                answer_text="No matching query plan for this question.",
                used_llm_fallback=False,
                asked_by=asked_by,
            )
            return {
                "answer": (
                    "I don't have a validated query plan for that question yet. "
                    "Try asking about sales, overdue invoices, stock levels, or "
                    "today's late employees — or use the Advanced Report Builder "
                    "for a custom report."
                ),
                "plan_used": None,
                "log_id": str(log.id),
            }

        plan_code, params = match
        plan_fn = PLAN_REGISTRY[plan_code]
        result = plan_fn(tenant_id, **params)
        answer_text = _format_answer(plan_code, result)

        log = MemoryQueryLog.objects.create(
            tenant_id=tenant_id,
            question=question,
            matched_plan_code=plan_code,
            params=params,
            answer_text=answer_text,
            used_llm_fallback=False,
            asked_by=asked_by,
        )

        return {
            "answer": answer_text,
            "plan_used": plan_code,
            "data": result,
            "log_id": str(log.id),
        }
