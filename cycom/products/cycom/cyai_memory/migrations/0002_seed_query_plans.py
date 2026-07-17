from django.db import migrations

PLANS = [
    {
        "code": "sales_summary",
        "name": "Sales Summary",
        "description": "Total sales (paid POS orders) for a period, optionally filtered by branch/warehouse.",
        "example_questions": [
            "What are sales for Amman branch this month?",
            "What are total sales today?",
        ],
    },
    {
        "code": "overdue_invoices",
        "name": "Overdue Invoices",
        "description": "Count and total of posted invoices past their due date with a remaining balance.",
        "example_questions": ["How many overdue invoices exist?"],
    },
    {
        "code": "product_stock",
        "name": "Product Stock Level",
        "description": "Current on-hand quantity for a product, broken down by warehouse.",
        "example_questions": ["What is the current stock of Product A?"],
    },
    {
        "code": "late_employees",
        "name": "Late Employees",
        "description": "Employees with a positive late_minutes on a given attendance date (defaults to today).",
        "example_questions": ["Which employees were late today?"],
    },
]


def seed_plans(apps, schema_editor):
    QueryPlan = apps.get_model("cycom_cyai_memory", "QueryPlan")
    for plan in PLANS:
        QueryPlan.objects.update_or_create(code=plan["code"], defaults=plan)


def remove_plans(apps, schema_editor):
    QueryPlan = apps.get_model("cycom_cyai_memory", "QueryPlan")
    QueryPlan.objects.filter(code__in=[p["code"] for p in PLANS]).delete()


class Migration(migrations.Migration):
    dependencies = [("cycom_cyai_memory", "0001_initial")]
    operations = [migrations.RunPython(seed_plans, remove_plans)]
