"""
AI-guided industry proposal tests.

Two things matter here: (1) every industry pack that ships is actually
reachable through the free-text matcher -- a pack nobody's description can
ever surface is dead weight, not a feature -- and (2) a description naming
a specific business type resolves to the precise pack for it rather than
falling into a generic bucket that happens to share a keyword.
"""

import pytest
from django.core.management import call_command

from platform.provisioning.proposal import INDUSTRY_SIGNALS, propose

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_packs(db):
    """propose() resolves a matched key against real IndustryTemplate rows,
    which only exist once the catalog JSON is loaded -- same pattern
    test_provisioning.py already uses."""
    call_command("seed_packs")


@pytest.mark.parametrize("description,expected_key", [
    ("We're a law firm handling litigation and corporate matters.", "law_firm"),
    ("Accounting firm doing audit and tax advisory for local businesses.", "accounting_firm"),
    ("We run a marketing agency doing media buying and ad campaigns.", "marketing_agency"),
    ("Managed service provider offering IT support and helpdesk services.", "it_services"),
    ("A hair salon and barbershop with stylists.", "salon_spa"),
    ("Veterinary clinic treating animal patients, vaccinations and microchipping.", "veterinary"),
    ("Dental clinic doing orthodontic and general dentist work.", "dental_clinic"),
    ("Coworking space with hot desks and meeting rooms.", "coworking"),
    ("Event management company organising weddings and exhibitions.", "event_management"),
    ("A bakery producing bread and pastries daily.", "bakery"),
    ("Florist shop selling bouquets and floral arrangements.", "florist"),
    ("Electronics store selling mobile phones and handling RMA warranty claims.", "electronics_retail"),
    ("Hardware store and builders merchant with a trade counter.", "hardware_store"),
    ("Optician selling eyewear and doing sight tests.", "optical"),
    ("Driving school giving driving lessons to learner drivers.", "driving_school"),
    ("Commercial cleaning company doing office cleaning contracts.", "cleaning_services"),
    ("HVAC contractor doing air conditioning and PPM visits.", "hvac_services"),
    ("Solar installer doing PV system and photovoltaic panel installs.", "solar_energy"),
    ("Equipment rental company doing tool hire and plant hire.", "equipment_rental"),
    ("Print shop doing large format printing and signage.", "printing"),
    ("Metal fabrication shop doing steel fabrication and welding.", "metal_fabrication"),
    ("Food distribution company running a cold chain frozen food depot.", "food_distribution"),
    ("Letting agency managing a rental portfolio of tenancy agreements.", "property_management"),
    ("Car workshop doing vehicle service and MOT repair orders.", "auto_service"),
    ("Travel agency booking flights and hotels for clients.", "travel_agency"),
    ("Architecture firm doing RIBA stage design and planning submissions.", "architecture_firm"),
    ("Electrical contractor issuing EICR electrical certificates.", "electrician_services"),
    ("Land surveyor doing topographic and measured building surveys.", "surveying_mapping"),
    ("Contract manufacturer doing PCB assembly and box build.", "electronics_assembly"),
    ("Plastic manufacturer doing injection moulding and mould tooling.", "packaging_manufacturing"),
    ("Carpentry and joinery workshop making bespoke fitted wardrobes.", "woodworking_carpentry"),
    ("Garment factory doing cut and sew textile manufacturing.", "textile_manufacturing"),
    ("Third-party logistics provider doing contract warehousing and pick pack ship.", "logistics_3pl"),
    ("A bookstore selling books by ISBN.", "bookstore"),
    ("Beverage distributor doing wholesale drinks and returnable bottles.", "beverage_distributor"),
    ("Bicycle shop with a bike mechanic doing repairs.", "bike_shop"),
])
def test_new_industries_are_reachable_by_description(description, expected_key):
    result = propose(description)
    assert result["matched"] is True, f"no match for: {description!r}"
    assert result["industry_key"] == expected_key, (
        f"{description!r} matched {result['industry_key']!r}, expected {expected_key!r} "
        f"(evidence: {result['evidence']})"
    )


def test_law_firm_no_longer_falls_into_generic_services():
    """Before adding the dedicated pack, 'law firm' was a signal for the
    generic services bucket -- that collision would make the precise pack
    unreachable even after it existed."""
    result = propose("We are a law firm.")
    assert result["industry_key"] == "law_firm"


def test_accounting_firm_no_longer_falls_into_generic_services():
    result = propose("We run an accounting firm.")
    assert result["industry_key"] == "accounting_firm"


def test_generic_consulting_description_still_matches_services():
    """The disambiguation fix must not break the generic bucket for
    descriptions that really are generic."""
    result = propose("We are a consulting agency working on retainer, billing by timesheet.")
    assert result["industry_key"] == "services"


def test_every_industry_signal_key_has_a_real_active_pack():
    """A signal block pointing at a key with no matching IndustryTemplate
    row would let propose() claim a match and then 404 downstream."""
    from platform.provisioning.models import IndustryTemplate

    active_keys = set(IndustryTemplate.objects.filter(is_active=True).values_list("key", flat=True))
    missing = set(INDUSTRY_SIGNALS) - active_keys
    assert not missing, f"signals reference industries with no active pack: {missing}"


def test_ambiguous_short_description_does_not_crash():
    result = propose("We do business.")
    assert result["matched"] is False
    assert result["candidates"] == []


def test_veterinary_beats_generic_healthcare_bucket():
    """Both healthcare and veterinary would score on 'clinic' -- the
    distinctive veterinary terms must win for an actual vet description."""
    result = propose("Veterinary clinic for animal patients, pet vaccinations.")
    assert result["industry_key"] == "veterinary"
