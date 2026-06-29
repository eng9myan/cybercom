"""
Tests: CyMed Laboratory — Microbiology, Culture, Sensitivity, Resistance
"""

import uuid
from decimal import Decimal

import pytest

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()


def make_order_item(tenant_id):
    from products.cymed.laboratory.orders.models import LabOrder, LabOrderItem, LabTest

    test = LabTest.objects.create(
        tenant_id=tenant_id,
        code=f"MICRO-{uuid.uuid4().hex[:4]}",
        name="Culture Test",
        category="microbiology",
    )
    order = LabOrder.objects.create(
        tenant_id=tenant_id,
        patient_id=PATIENT,
        ordered_by=PROVIDER,
        order_number=f"ORD-{uuid.uuid4().hex[:8]}",
    )
    return LabOrderItem.objects.create(tenant_id=tenant_id, order=order, test=test)


def make_specimen(tenant_id):
    from products.cymed.laboratory.specimens.models import Specimen

    return Specimen.objects.create(
        tenant_id=tenant_id,
        patient_id=PATIENT,
        specimen_number=f"SP-{uuid.uuid4().hex[:6]}",
        barcode=f"BC-{uuid.uuid4().hex[:6]}",
        specimen_type="blood",
    )


@pytest.mark.django_db
class TestCulture:
    def test_create_culture(self):
        from products.cymed.laboratory.microbiology.models import Culture, CultureStatus

        item = make_order_item(TENANT)
        sp = make_specimen(TENANT)
        culture = Culture.objects.create(
            tenant_id=TENANT,
            order_item=item,
            specimen=sp,
            culture_number=f"CUL-{uuid.uuid4().hex[:8]}",
            culture_type="aerobic",
            medium="Blood Agar",
            incubation_temperature_celsius=Decimal("37.0"),
            incubation_hours=48,
        )
        assert culture.status == CultureStatus.PENDING

    def test_organism_identification(self):
        from products.cymed.laboratory.microbiology.models import Culture, Organism

        item = make_order_item(TENANT)
        sp = make_specimen(TENANT)
        culture = Culture.objects.create(
            tenant_id=TENANT,
            order_item=item,
            specimen=sp,
            culture_number=f"CUL-{uuid.uuid4().hex[:8]}",
            culture_type="aerobic",
        )
        organism = Organism.objects.create(
            tenant_id=TENANT,
            culture=culture,
            organism_name="Staphylococcus aureus",
            snomed_code="3092008",
            gram_stain="gram_positive",
            morphology="cocci",
            growth_level="heavy",
        )
        assert organism.gram_stain == "gram_positive"
        assert culture.organisms.count() == 1

    def test_antibiotic_sensitivity(self):
        from products.cymed.laboratory.microbiology.models import (
            Culture,
            Organism,
            Sensitivity,
            SensitivityResult,
        )

        item = make_order_item(TENANT)
        sp = make_specimen(TENANT)
        culture = Culture.objects.create(
            tenant_id=TENANT,
            order_item=item,
            specimen=sp,
            culture_number=f"CUL-{uuid.uuid4().hex[:8]}",
            culture_type="aerobic",
        )
        organism = Organism.objects.create(
            tenant_id=TENANT,
            culture=culture,
            organism_name="E. coli",
            gram_stain="gram_negative",
        )
        sens = Sensitivity.objects.create(
            tenant_id=TENANT,
            organism=organism,
            antibiotic_code="AMX",
            antibiotic_name="Amoxicillin",
            method="disk_diffusion",
            result=SensitivityResult.RESISTANT,
            mic_value=">32",
        )
        assert sens.result == "R"

    def test_mrsa_resistance_profile(self):
        from products.cymed.laboratory.microbiology.models import (
            Culture,
            Organism,
            ResistanceProfile,
        )

        item = make_order_item(TENANT)
        sp = make_specimen(TENANT)
        culture = Culture.objects.create(
            tenant_id=TENANT,
            order_item=item,
            specimen=sp,
            culture_number=f"CUL-{uuid.uuid4().hex[:8]}",
            culture_type="aerobic",
        )
        organism = Organism.objects.create(
            tenant_id=TENANT,
            culture=culture,
            organism_name="Staphylococcus aureus",
            gram_stain="gram_positive",
        )
        profile = ResistanceProfile.objects.create(
            tenant_id=TENANT,
            organism=organism,
            resistance_mechanism="mrsa",
            confirmed=True,
        )
        assert profile.confirmed is True

    def test_microbiology_result(self):
        from products.cymed.laboratory.microbiology.models import MicrobiologyResult

        item = make_order_item(TENANT)
        result = MicrobiologyResult.objects.create(
            tenant_id=TENANT,
            order_item=item,
            final_interpretation="No growth after 5 days",
            reported_by=PROVIDER,
        )
        assert "No growth" in result.final_interpretation
