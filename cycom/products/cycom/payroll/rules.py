"""
Statutory payroll rules (Jordan).

Social security: employee 7.5%, employer 14.25% of subject wage.

Income tax (Jordan personal income tax) — computed on the BASIC salary
(not gross), against an annual personal exemption:
  * married / legal cohabitant with a NON-employed spouse -> 18,000/yr
  * everyone else                                         ->  9,000/yr
Only annual basic above the exemption is taxed, in 5,000 bands at
5% / 10% / 15% / 20%, then 25% on the remainder. Monthly tax = annual / 12,
prorated by (current-period basic / full monthly basic) for part-periods.
"""

from decimal import Decimal

Z = Decimal("0.00")

JO_SOCIAL_SECURITY = {"employee_rate": Decimal("7.5"), "employer_rate": Decimal("14.25")}

EXEMPTION_MARRIED_SOLE_EARNER = Decimal("18000")
EXEMPTION_DEFAULT = Decimal("9000")

# (band_size, rate). Remainder past the last band is taxed at TOP_RATE.
JO_TAX_BANDS = [
    (Decimal("5000"), Decimal("0.05")),
    (Decimal("5000"), Decimal("0.10")),
    (Decimal("5000"), Decimal("0.15")),
    (Decimal("5000"), Decimal("0.20")),
]
JO_TOP_RATE = Decimal("0.25")


def _q(x) -> Decimal:
    return (x or Z).quantize(Decimal("0.01"))


def social_security(gross: Decimal, cfg: dict | None = None) -> tuple[Decimal, Decimal]:
    cfg = cfg or JO_SOCIAL_SECURITY
    emp = gross * cfg["employee_rate"] / 100
    empr = gross * cfg["employer_rate"] / 100
    return _q(emp), _q(empr)


def personal_exemption(marital: str, spouse_employed: bool) -> Decimal:
    if (marital or "") in ("married", "cohabitant") and not spouse_employed:
        return EXEMPTION_MARRIED_SOLE_EARNER
    return EXEMPTION_DEFAULT


def annual_income_tax(annual_basic: Decimal, marital: str = "single", spouse_employed: bool = False) -> Decimal:
    """Jordan annual income tax on basic salary, after the personal exemption."""
    start = personal_exemption(marital, spouse_employed)
    tax = Z
    if annual_basic > start:
        remaining = annual_basic - start
        for band_size, rate in JO_TAX_BANDS:
            if remaining <= 0:
                break
            portion = min(remaining, band_size)
            tax += portion * rate
            remaining -= portion
        if remaining > 0:
            tax += remaining * JO_TOP_RATE
    return _q(tax)


def monthly_income_tax(
    monthly_basic: Decimal,
    marital: str = "single",
    spouse_employed: bool = False,
    current_basic: Decimal | None = None,
) -> Decimal:
    """
    Monthly income tax = annual tax / 12, on annual basic (monthly_basic * 12).
    If current_basic is given (an actually-earned partial basic for the period),
    the monthly tax is prorated by current_basic / monthly_basic.
    """
    if monthly_basic <= 0:
        return Z
    annual_basic = monthly_basic * 12
    monthly = annual_income_tax(annual_basic, marital, spouse_employed) / 12
    if current_basic is not None and current_basic > 0:
        monthly = monthly * (current_basic / monthly_basic)
    return _q(monthly)


# ===========================================================================
# Saudi Arabia (GOSI) + United Arab Emirates (GPSSA / end-of-service gratuity)
# Neither KSA nor UAE levies personal income tax on salaries.
#
# SOURCES (retrieved 2026-08; CONFIRM before production payroll runs — two
# figures below are marked (confirm) where sources disagree):
#   - Saudi GOSI 2026 rates + SAR 45,000 cap: Mercans, ZenHR, Saudi Compliance
#     Institute (see PROJECT docs / chat citations).
#   - UAE gratuity (21/30-day rule, 24-month cap) + GPSSA: GPSSA.gov.ae, Zoho,
#     teamed.
# ===========================================================================

# GOSI contributable wage = basic + housing, capped monthly.
SA_GOSI_WAGE_CAP = Decimal("45000")

# Saudi nationals — TOTAL contribution (pension branch rises yearly under the
# post-2024 reform; SANED + occupational hazards flat). 2026 figures.
SA_GOSI_SAUDI = {"employee_rate": Decimal("10.75"), "employer_rate": Decimal("12.75")}
# Legacy scheme (Saudis subscribed before 2024-07-03) — kept for existing staff.
SA_GOSI_SAUDI_LEGACY = {"employee_rate": Decimal("9.75"), "employer_rate": Decimal("11.75")}
# Expats/non-Saudis — occupational hazards only, employer-side.
SA_GOSI_EXPAT = {"employee_rate": Decimal("0"), "employer_rate": Decimal("2")}

# UAE nationals via GPSSA (federal). (confirm) — the 2023 pension law / Abu Dhabi
# ADPF cite higher rates (up to 11%/15%); this is the widely-used federal figure.
AE_GPSSA_NATIONAL = {"employee_rate": Decimal("5"), "employer_rate": Decimal("12.5")}
AE_GRATUITY_SALARY_CAP_MONTHS = Decimal("24")  # gratuity capped at 24 months' basic


def gosi(basic: Decimal, housing: Decimal = Z, *, saudi: bool = True, legacy: bool = False):
    """Saudi GOSI. Contributable wage = (basic + housing) capped at SAR 45,000.
    Returns (employee, employer). Expats: only the 2% employer occupational hazard."""
    if saudi:
        cfg = SA_GOSI_SAUDI_LEGACY if legacy else SA_GOSI_SAUDI
    else:
        cfg = SA_GOSI_EXPAT
    wage = min((basic or Z) + (housing or Z), SA_GOSI_WAGE_CAP)
    return social_security(wage, cfg)


def uae_gratuity(monthly_basic: Decimal, years_of_service: Decimal) -> Decimal:
    """UAE end-of-service gratuity for an expat employee (the common case).
    21 days of basic per year for the first 5 years, 30 days/year thereafter,
    on a 30-day-month daily wage, capped at 24 months' basic. Fractional years
    accrue pro-rata."""
    monthly_basic = monthly_basic or Z
    years = years_of_service or Z
    if monthly_basic <= 0 or years <= 0:
        return Z
    daily = monthly_basic / Decimal("30")
    first5_years = min(years, Decimal("5"))
    after_years = max(years - Decimal("5"), Z)
    total = first5_years * Decimal("21") * daily + after_years * Decimal("30") * daily
    cap = AE_GRATUITY_SALARY_CAP_MONTHS * monthly_basic
    return _q(min(total, cap))


def statutory_social_security(country: str, basic: Decimal, housing: Decimal = Z, **kw):
    """Country dispatcher for monthly social-security-style deductions.
    (UAE expats have no monthly deduction — their entitlement is gratuity at
    separation, via uae_gratuity.)"""
    c = (country or "JO").upper()
    if c == "JO":
        return social_security((basic or Z) + (housing or Z))
    if c == "SA":
        return gosi(basic, housing, saudi=kw.get("saudi", True), legacy=kw.get("legacy", False))
    if c == "AE":
        if kw.get("national"):
            return social_security((basic or Z) + (housing or Z), AE_GPSSA_NATIONAL)
        return (Z, Z)  # expat: no monthly contribution
    raise ValueError(f"Unsupported payroll country: {country}")


def statutory_income_tax(country: str, annual_basic: Decimal, **kw) -> Decimal:
    """Personal income tax by country. KSA and UAE: none (returns 0)."""
    c = (country or "JO").upper()
    if c == "JO":
        return annual_income_tax(annual_basic, kw.get("marital", "single"), kw.get("spouse_employed", False))
    if c in ("SA", "AE"):
        return Z
    raise ValueError(f"Unsupported payroll country: {country}")
