from django.db import migrations

# Real starting catalog: Jordan, Saudi Arabia, UAE, USA — the four
# markets named explicitly in the CyID ecosystem brief. AE has no
# dedicated plugin in compliance-gateway/main.py yet (only JO/SA/US-EU-GB
# are handled there) — seeded honestly anyway so the jurisdiction lookup
# itself works; the gateway's own "unsupported region" fallback applies
# until a real UAE e-invoicing plugin is built, not silently faked here.
SEED = [
    {"country_code": "JO", "name": "Jordan", "currency_code": "JOD", "currency_name": "Jordanian Dinar", "decimal_places": 3, "tax_rate": "16.00", "region": "JO"},
    {"country_code": "SA", "name": "Saudi Arabia", "currency_code": "SAR", "currency_name": "Saudi Riyal", "decimal_places": 2, "tax_rate": "15.00", "region": "SA"},
    {"country_code": "AE", "name": "United Arab Emirates", "currency_code": "AED", "currency_name": "UAE Dirham", "decimal_places": 2, "tax_rate": "5.00", "region": "AE"},
    {"country_code": "US", "name": "United States", "currency_code": "USD", "currency_name": "US Dollar", "decimal_places": 2, "tax_rate": "0.00", "region": "US"},
]


def seed(apps, schema_editor):
    Currency = apps.get_model("cycom_localization", "Currency")
    Jurisdiction = apps.get_model("cycom_localization", "Jurisdiction")
    for entry in SEED:
        currency, _ = Currency.objects.get_or_create(
            code=entry["currency_code"],
            defaults={"name": entry["currency_name"], "decimal_places": entry["decimal_places"]},
        )
        Jurisdiction.objects.get_or_create(
            country_code=entry["country_code"],
            defaults={
                "name": entry["name"],
                "default_currency": currency,
                "default_tax_rate": entry["tax_rate"],
                "compliance_region": entry["region"],
            },
        )


def unseed(apps, schema_editor):
    Jurisdiction = apps.get_model("cycom_localization", "Jurisdiction")
    Currency = apps.get_model("cycom_localization", "Currency")
    Jurisdiction.objects.filter(country_code__in=["JO", "SA", "AE", "US"]).delete()
    Currency.objects.filter(code__in=["JOD", "SAR", "AED", "USD"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("cycom_localization", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
