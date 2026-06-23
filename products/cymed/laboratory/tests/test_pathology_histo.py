"""
Tests: CyMed Laboratory — Pathology and Histopathology
"""
import uuid
import pytest
import datetime

TENANT = uuid.uuid4()
PATIENT = uuid.uuid4()
PROVIDER = uuid.uuid4()
PATHOLOGIST = uuid.uuid4()


def make_order_item(tenant_id):
    from products.cymed.laboratory.orders.models import LabOrder, LabOrderItem, LabTest
    test = LabTest.objects.create(tenant_id=tenant_id, code=f"PATH-{uuid.uuid4().hex[:4]}", name="Path Test", category="pathology")
    order = LabOrder.objects.create(
        tenant_id=tenant_id, patient_id=PATIENT, ordered_by=PROVIDER,
        order_number=f"ORD-{uuid.uuid4().hex[:8]}",
    )
    return LabOrderItem.objects.create(tenant_id=tenant_id, order=order, test=test)


@pytest.mark.django_db
class TestPathology:
    def test_create_pathology_case(self):
        from products.cymed.laboratory.pathology.models import PathologyCase, PathologyCaseStatus
        item = make_order_item(TENANT)
        case = PathologyCase.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT,
            case_number=f"PATH-{uuid.uuid4().hex[:8]}",
            clinical_history="Mass in left breast",
            assigned_pathologist=PATHOLOGIST,
        )
        assert case.status == PathologyCaseStatus.RECEIVED

    def test_pathology_specimen(self):
        from products.cymed.laboratory.pathology.models import PathologyCase, PathologySpecimen
        item = make_order_item(TENANT)
        case = PathologyCase.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT,
            case_number=f"PATH-{uuid.uuid4().hex[:8]}",
            clinical_history="Biopsy",
        )
        specimen = PathologySpecimen.objects.create(
            tenant_id=TENANT, case=case, part_label="A",
            description="Breast biopsy, left upper outer quadrant",
            cassettes_submitted=3,
        )
        assert specimen.part_label == "A"

    def test_gross_examination(self):
        from products.cymed.laboratory.pathology.models import PathologyCase, PathologySpecimen, GrossExamination
        item = make_order_item(TENANT)
        case = PathologyCase.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT,
            case_number=f"PATH-{uuid.uuid4().hex[:8]}", clinical_history="Specimen",
        )
        specimen = PathologySpecimen.objects.create(
            tenant_id=TENANT, case=case, part_label="A",
            description="Specimen A", cassettes_submitted=2,
        )
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        gross = GrossExamination.objects.create(
            tenant_id=TENANT, case=case, pathology_specimen=specimen,
            gross_description="Firm grey mass 2.5 x 2.0 x 1.5 cm",
            examined_by=PATHOLOGIST, examined_at=now,
        )
        assert "2.5" in gross.gross_description

    def test_pathology_diagnosis(self):
        from products.cymed.laboratory.pathology.models import PathologyCase, PathologyDiagnosis
        item = make_order_item(TENANT)
        case = PathologyCase.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT,
            case_number=f"PATH-{uuid.uuid4().hex[:8]}", clinical_history="Biopsy",
        )
        diag = PathologyDiagnosis.objects.create(
            tenant_id=TENANT, case=case,
            snomed_code="254838004", icd11_code="2C61",
            diagnosis_text="Invasive ductal carcinoma, Grade 2",
            diagnosis_category="malignant",
            signed_by=PATHOLOGIST,
        )
        assert diag.diagnosis_category == "malignant"


@pytest.mark.django_db
class TestHistopathology:
    def make_path_case(self):
        from products.cymed.laboratory.pathology.models import PathologyCase
        item = make_order_item(TENANT)
        return PathologyCase.objects.create(
            tenant_id=TENANT, order_item=item, patient_id=PATIENT,
            case_number=f"PATH-{uuid.uuid4().hex[:8]}", clinical_history="Test",
        )

    def test_histology_case(self):
        from products.cymed.laboratory.histopathology.models import HistologyCase, HistologyCaseStatus
        path_case = self.make_path_case()
        case = HistologyCase.objects.create(
            tenant_id=TENANT, pathology_case=path_case,
            case_number=f"HISTO-{uuid.uuid4().hex[:6]}",
        )
        assert case.status == HistologyCaseStatus.RECEIVED

    def test_tissue_block(self):
        from products.cymed.laboratory.histopathology.models import HistologyCase, TissueBlock
        path_case = self.make_path_case()
        case = HistologyCase.objects.create(
            tenant_id=TENANT, pathology_case=path_case,
            case_number=f"HISTO-{uuid.uuid4().hex[:6]}",
        )
        block = TissueBlock.objects.create(
            tenant_id=TENANT, case=case,
            block_number="A1", cassette_number="1",
            tissue_type="breast tissue",
        )
        assert block.embedding_status == "pending"

    def test_slide_creation(self):
        from products.cymed.laboratory.histopathology.models import HistologyCase, TissueBlock, Slide
        path_case = self.make_path_case()
        case = HistologyCase.objects.create(
            tenant_id=TENANT, pathology_case=path_case,
            case_number=f"HISTO-{uuid.uuid4().hex[:6]}",
        )
        block = TissueBlock.objects.create(
            tenant_id=TENANT, case=case,
            block_number="A1", cassette_number="1",
        )
        slide = Slide.objects.create(
            tenant_id=TENANT, block=block,
            slide_number="1", stain_type="he",
            barcode=f"SLD-{uuid.uuid4().hex[:8]}",
        )
        assert slide.stain_type == "he"

    def test_slide_review(self):
        from products.cymed.laboratory.histopathology.models import HistologyCase, TissueBlock, Slide, SlideReview
        path_case = self.make_path_case()
        case = HistologyCase.objects.create(
            tenant_id=TENANT, pathology_case=path_case,
            case_number=f"HISTO-{uuid.uuid4().hex[:6]}",
        )
        block = TissueBlock.objects.create(
            tenant_id=TENANT, case=case, block_number="B1", cassette_number="2",
        )
        slide = Slide.objects.create(
            tenant_id=TENANT, block=block, slide_number="1",
            stain_type="pas", barcode=f"SLD-{uuid.uuid4().hex[:8]}",
        )
        review = SlideReview.objects.create(
            tenant_id=TENANT, slide=slide, reviewed_by=PATHOLOGIST,
            findings="PAS positive deposits in tubular epithelium",
        )
        assert "PAS" in review.findings
