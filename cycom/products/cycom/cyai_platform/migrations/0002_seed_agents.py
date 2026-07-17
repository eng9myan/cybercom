from django.db import migrations

AGENTS = [
    {
        "agent_key": "ask_cycom",
        "customer_facing_name": "Ask CyCom",
        "purpose": "Search, answer, navigate, and assist users inside the live ERP using authorized, governed data.",
        "capabilities": [
            "retrieve_live_data",
            "calculate_governed_totals",
            "display_records",
            "open_record_deep_link",
            "apply_filters",
            "explain_workflow_status",
            "draft_action_for_confirmation",
        ],
        "requires_elevated_approval": False,
        "suggested_pricing_note": "$4 per enabled user/month, or organization-wide package based on query volume.",
    },
    {
        "agent_key": "report_studio",
        "customer_facing_name": "CyCom Report Studio AI",
        "purpose": "Create permanent, reusable, parameterized reports and dashboards in Advanced Reports. Saves report definitions, not static data snapshots.",
        "capabilities": [
            "discover_governed_measures_dimensions",
            "build_report_definition",
            "validate_against_source_records",
            "generate_list_pivot_chart_dashboard_export",
            "save_to_advanced_reports",
            "assign_report_permissions",
            "version_reports",
        ],
        "requires_elevated_approval": False,
        "suggested_pricing_note": "$49 per company/month, includes a defined report-build allowance. Running/refreshing saved reports is not billed as new creation.",
    },
    {
        "agent_key": "builder_ai",
        "customer_facing_name": "CyCom Builder AI",
        "purpose": "ERP business analyst, implementation consultant, developer, tester, and controlled deployment assistant. Never modifies production directly from an unrestricted chat instruction.",
        "capabilities": [
            "requirement_analysis",
            "capability_inspection",
            "impact_analysis",
            "isolated_development",
            "automated_testing",
            "staging_deployment",
            "controlled_production_deployment",
            "rollback",
        ],
        "requires_elevated_approval": True,
        "suggested_pricing_note": "$199-$499 monthly platform access; development work consumes scoped implementation credits; large modules require an approved quotation.",
    },
]


def seed_agents(apps, schema_editor):
    AgentDefinition = apps.get_model("cycom_cyai_platform", "AgentDefinition")
    for spec in AGENTS:
        AgentDefinition.objects.update_or_create(agent_key=spec["agent_key"], defaults=spec)


def unseed_agents(apps, schema_editor):
    AgentDefinition = apps.get_model("cycom_cyai_platform", "AgentDefinition")
    AgentDefinition.objects.filter(agent_key__in=[a["agent_key"] for a in AGENTS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("cycom_cyai_platform", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_agents, unseed_agents),
    ]
