"""
CyberCom Demo Seeder — populate_demo management command.

Seeds a complete, interconnected healthcare demonstration network with realistic
patient journeys, clinical workflows, RCM billing, and ERP integration.

All model field names are validated against the actual Django model definitions.
"""
import uuid
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

# Tenant
from platform.tenant.models import Tenant

# Core Cymed Models
from products.cymed.core.organizations.models import Organization
from products.cymed.core.facilities.models import Facility, Department as CymedDepartment, Ward, Room, Bed
from products.cymed.core.patients.models import Patient, PatientAddress, PatientContact
from products.cymed.core.providers.models import Provider, ProviderSpecialty, ProviderCredential
from products.cymed.core.encounters.models import Encounter, EpisodeOfCare, EncounterParticipant, EncounterDiagnosis, EncounterReason

# Lab
from products.cymed.laboratory.orders.models import LabTest, LabOrder, LabOrderItem, LabPriority
from products.cymed.laboratory.specimens.models import Specimen, SpecimenStatus
from products.cymed.laboratory.results.models import LabResult, ResultStatus, ResultValue, ReferenceRange
from products.cymed.laboratory.worklists.models import LabWorklist, WorklistItem

# Imaging
from products.cymed.imaging.orders.models import ImagingProtocol, ImagingProcedure, ImagingOrder, ImagingOrderItem
from products.cymed.imaging.radiology_reporting.models import RadiologyReport, RadiologyFinding, RadiologyImpression

# Pharmacy
from products.cymed.pharmacy.prescriptions.models import Prescription, PrescriptionItem
from products.cymed.pharmacy.dispensing.models import DispenseOrder, DispenseItem, DispenseStatus
from products.cymed.pharmacy.formulary.models import Formulary, FormularyDrug

# RCM
from products.cymed.rcm.billing.models import PatientAccount, EncounterBilling, Invoice as RcmInvoice, InvoiceLine as RcmInvoiceLine
from products.cymed.rcm.claims.models import Claim, ClaimLine, ClaimSubmission, ClaimResponse
from products.cymed.rcm.denials.models import Denial, DenialReason
from products.cymed.rcm.insurance.models import InsuranceCompany, InsurancePlan, InsuranceMember

# HWM (Workforce)
from products.cymed.workforce_management.workforce_profiles.models import WorkforceProfile
from products.cymed.workforce_management.scheduling.models import ShiftTemplate, RosterCycle, RosterSlot

# CyCom ERP Models
from products.cycom.hr.models import Employee, Department as CycomDepartment
from products.cycom.payroll.models import PayrollRun, Payslip
from products.cycom.inventory.models import Warehouse, StockItem, StockMovement
from products.cycom.assets.models import Asset, AssetDepreciation
from products.cycom.bi.models import BIReport, DashboardMetric
from products.cycom.finance.gl.models import Account, JournalEntry, JournalLine
from products.cycom.finance.ap.models import Vendor, Bill, BillLine, VendorPayment
from products.cycom.finance.ar.models import Customer, Invoice as ArInvoice, InvoiceLine as ArInvoiceLine, Payment as ArPayment
from products.cycom.procurement.purchase_orders.models import PurchaseOrder, POLine, GoodsReceipt, GoodsReceiptLine


class Command(BaseCommand):
    help = "Seed the CyberCom Platform with a complete, interconnected healthcare demonstration network and datasets."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Clean existing demo data before seeding.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting CyberCom Demo data seeding..."))

        try:
            with transaction.atomic():
                # Get or create primary tenant
                tenant, _ = Tenant.objects.get_or_create(
                    slug="cybercom-care",
                    defaults={
                        "name": "CyberCom Care Network",
                        "display_name": "CyberCom Care Network",
                        "tenant_type": "saas",
                        "status": "active",
                    }
                )
                t_id = tenant.id

                # ---------------------------------------------------------------------------
                # Phase 1: Healthcare Network Setup
                # ---------------------------------------------------------------------------
                self.stdout.write("Phase 1: Setting up Healthcare Network...")

                org, _ = Organization.objects.get_or_create(
                    tenant_id=t_id,
                    slug="cybercom-network",
                    defaults={
                        "name": "CyberCom Healthcare Network",
                        "organization_type": "hospital",
                    }
                )

                # Facilities mapping
                facilities_data = [
                    ("Al-Amal General Hospital", "HOSP-AMAL"),
                    ("Primary Care Clinic", "CLIN-PRIMARY"),
                    ("Specialty Pediatrics Clinic", "CLIN-PEDS"),
                    ("Dental & Orthodontics Clinic", "CLIN-DENTAL"),
                    ("Central Diagnostic Laboratory", "LAB-CENTRAL"),
                    ("Advanced Imaging & Radiology Center", "IMG-ADVANCED"),
                    ("Al-Amal Hospital Pharmacy", "PHARM-AMAL"),
                    ("Community Care Pharmacy", "PHARM-COMM"),
                ]

                facilities = {}
                for name, code in facilities_data:
                    fac, _ = Facility.objects.get_or_create(
                        tenant_id=t_id,
                        code=code,
                        defaults={
                            "organization": org,
                            "name": name,
                            "is_active": True,
                        }
                    )
                    facilities[code] = fac

                # Create building, floor, department, ward, room, and bed for the hospital
                hosp = facilities["HOSP-AMAL"]
                dept_er, _ = CymedDepartment.objects.get_or_create(
                    tenant_id=t_id,
                    facility=hosp,
                    code="DEPT-ER",
                    defaults={"name": "Emergency Room"}
                )
                ward_er, _ = Ward.objects.get_or_create(
                    tenant_id=t_id,
                    department=dept_er,
                    code="WARD-ER",
                    defaults={"name": "Emergency Ward"}
                )
                room_er, _ = Room.objects.get_or_create(
                    tenant_id=t_id,
                    ward=ward_er,
                    room_number="ER-101",
                    defaults={"room_type": "exam"}
                )
                bed_er, _ = Bed.objects.get_or_create(
                    tenant_id=t_id,
                    room=room_er,
                    bed_number="ER-BED-1",
                    defaults={"status": "available"}
                )

                # Create department and ward for inpatient
                dept_inpatient, _ = CymedDepartment.objects.get_or_create(
                    tenant_id=t_id,
                    facility=hosp,
                    code="DEPT-INPATIENT",
                    defaults={"name": "Inpatient Medicine"}
                )
                ward_med, _ = Ward.objects.get_or_create(
                    tenant_id=t_id,
                    department=dept_inpatient,
                    code="WARD-MED",
                    defaults={"name": "Medical Ward"}
                )
                room_med, _ = Room.objects.get_or_create(
                    tenant_id=t_id,
                    ward=ward_med,
                    room_number="MED-202",
                    defaults={"room_type": "standard"}
                )
                bed_med, _ = Bed.objects.get_or_create(
                    tenant_id=t_id,
                    room=room_med,
                    bed_number="MED-BED-2",
                    defaults={"status": "available"}
                )

                # ---------------------------------------------------------------------------
                # Phase 2: Seeding Providers, Staff, and HR Profiles
                # ---------------------------------------------------------------------------
                self.stdout.write("Phase 2: Seeding Providers, Staff, and HR Profiles...")

                # CyCom Departments for HR
                cycom_depts = {}
                for code, name in [("HR", "Human Resources"), ("FIN", "Finance & AP/AR"), ("CLIN", "Clinical Operations")]:
                    dept, _ = CycomDepartment.objects.get_or_create(
                        tenant_id=t_id,
                        code=code,
                        defaults={"name": name}
                    )
                    cycom_depts[code] = dept

                # Helper to create Provider & Employee
                def create_staff(first_name, last_name, role_type, npi, facility, specialty=None, credential_title=None):
                    user_uuid = uuid.uuid4()

                    # 1. CyMed Clinical Provider
                    prov, _ = Provider.objects.get_or_create(
                        npi=npi,
                        defaults={
                            "tenant_id": t_id,
                            "user_id": user_uuid,
                            "first_name": first_name,
                            "last_name": last_name,
                            "provider_type": role_type,
                            "is_active": True,
                        }
                    )

                    if specialty:
                        ProviderSpecialty.objects.get_or_create(
                            tenant_id=t_id,
                            provider=prov,
                            specialty_code=specialty.upper().replace(" ", "_"),
                            defaults={"specialty_display": specialty}
                        )
                    if credential_title:
                        ProviderCredential.objects.get_or_create(
                            tenant_id=t_id,
                            provider=prov,
                            title=credential_title,
                            defaults={
                                "issuer": "Saudi Commission for Health Specialties",
                                "date_issued": datetime.date(2022, 1, 1),
                            }
                        )

                    # 2. CyCom ERP Employee
                    emp, _ = Employee.objects.get_or_create(
                        email=f"{first_name.lower()}.{last_name.lower()}@cy-com.com",
                        defaults={
                            "tenant_id": t_id,
                            "first_name": first_name,
                            "last_name": last_name,
                            "phone": "+966 50 XXX XXXX",
                            "department": cycom_depts["CLIN"],
                            "job_title": role_type.title(),
                            "hire_date": datetime.date(2023, 1, 15),
                            "status": "active",
                        }
                    )

                    # 3. CyMed Workforce Profile (HWM)
                    WorkforceProfile.objects.get_or_create(
                        tenant_id=t_id,
                        employee_id=emp.id,
                        defaults={
                            "facility_id": facility.id,
                            "display_name": f"{first_name} {last_name}",
                            "role_type": role_type,
                            "clinical_category": "nursing" if role_type == "nurse" else "physician",
                            "specialty": specialty or "General Practice",
                        }
                    )

                    return prov, emp

                # Create key roles across facilities
                phys_er, emp_phys_er = create_staff("Khalid", "Mansour", "physician", "NPI-PHYS-001", hosp, "Emergency Medicine", "MD")
                nurse_er, emp_nurse_er = create_staff("Sarah", "Jordan", "nurse", "NPI-NURSE-001", hosp, "Critical Care", "RN")
                phys_clinic, _ = create_staff("Ahmad", "Hameed", "physician", "NPI-PHYS-002", facilities["CLIN-PRIMARY"], "Primary Care", "MD")
                rad, _ = create_staff("Tareq", "Saleh", "radiologist", "NPI-RAD-001", facilities["IMG-ADVANCED"], "Diagnostic Radiology", "MD")
                pharmacist, _ = create_staff("Rania", "Badawi", "pharmacist", "NPI-PHARM-001", facilities["PHARM-AMAL"], "Clinical Pharmacy", "PharmD")
                lab_tech, _ = create_staff("Yousef", "Naser", "lab_technician", "NPI-LAB-001", facilities["LAB-CENTRAL"], "Medical Lab Science", "BSc")

                # ---------------------------------------------------------------------------
                # Phase 3: Seeding Patients and Interconnected Workflows
                # ---------------------------------------------------------------------------
                self.stdout.write("Phase 3: Seeding Patients and Workflows...")

                # Aisha (Outpatient to Lab/Img/Pharm workflow)
                pat_aisha, _ = Patient.objects.get_or_create(
                    mrn="MRN-PAT-001",
                    defaults={
                        "tenant_id": t_id,
                        "first_name": "Aisha",
                        "last_name": "Al-Otaibi",
                        "dob": datetime.date(1988, 4, 12),
                        "gender": "female",
                        "national_id": "1098765432",
                    }
                )
                PatientAddress.objects.get_or_create(
                    tenant_id=t_id,
                    patient=pat_aisha,
                    use="home",
                    defaults={
                        "line1": "King Fahd Road",
                        "city": "Riyadh",
                        "country": "Saudi Arabia",
                    }
                )
                PatientContact.objects.get_or_create(
                    tenant_id=t_id,
                    patient=pat_aisha,
                    telecom_system="phone",
                    defaults={"telecom_value": "+966 50 123 4567"}
                )

                # Faisal (Emergency Inpatient workflow)
                pat_faisal, _ = Patient.objects.get_or_create(
                    mrn="MRN-PAT-002",
                    defaults={
                        "tenant_id": t_id,
                        "first_name": "Faisal",
                        "last_name": "Al-Shammari",
                        "dob": datetime.date(1975, 11, 22),
                        "gender": "male",
                        "national_id": "1087654321",
                    }
                )

                # --- Setup Insurance Coverage ---
                ins_co, _ = InsuranceCompany.objects.get_or_create(
                    payer_id="PAYER-BUPA",
                    defaults={
                        "tenant_id": t_id,
                        "name": "Bupa Arabia",
                        "short_name": "Bupa",
                        "company_type": "private",
                    }
                )
                plan, _ = InsurancePlan.objects.get_or_create(
                    plan_code="BUPA-PREM",
                    defaults={
                        "tenant_id": t_id,
                        "company": ins_co,
                        "plan_name": "Premium Corporate Network",
                        "plan_type": "corporate",
                        "network_type": "in_network",
                        "coverage_category": "premium",
                    }
                )
                ins_member, _ = InsuranceMember.objects.get_or_create(
                    member_id="MEM-84729",
                    defaults={
                        "tenant_id": t_id,
                        "patient_id": pat_aisha.id,
                        "insurance_plan": plan,
                        "member_relationship": "self",
                        "effective_date": timezone.now().date(),
                    }
                )

                # Patient account linking
                pat_account, _ = PatientAccount.objects.get_or_create(
                    account_number=f"ACC-{pat_aisha.mrn}",
                    defaults={
                        "tenant_id": t_id,
                        "patient_id": pat_aisha.id,
                        "primary_insurance_member_id": ins_member.id,
                        "account_status": "active",
                    }
                )

                # --- Workflow 1 execution ---
                # 1. Outpatient Clinic Consultation
                ep_care = EpisodeOfCare.objects.create(
                    tenant_id=t_id,
                    patient=pat_aisha,
                    status="active",
                    managing_organization=org
                )
                enc_clinic = Encounter.objects.create(
                    tenant_id=t_id,
                    patient=pat_aisha,
                    episode_of_care=ep_care,
                    encounter_type="outpatient",
                    status="finished",
                    organization=org,
                    facility=facilities["CLIN-PRIMARY"],
                    start_time=timezone.now() - datetime.timedelta(hours=4),
                    end_time=timezone.now() - datetime.timedelta(hours=3),
                )
                EncounterParticipant.objects.create(
                    tenant_id=t_id,
                    encounter=enc_clinic,
                    provider=phys_clinic,
                    role="lead"
                )
                EncounterReason.objects.create(
                    tenant_id=t_id,
                    encounter=enc_clinic,
                    reason_code="R53",
                    reason_text="Chronic fatigue and abdominal discomfort"
                )
                EncounterDiagnosis.objects.create(
                    tenant_id=t_id,
                    encounter=enc_clinic,
                    condition_code="E55.9",
                    display="Vitamin D deficiency, unspecified",
                    use="chief_complaint"
                )

                # 2. Lab order, specimen collection, analysis, and results
                # LabTest has no reference_range field — that lives in ReferenceRange model
                lab_test, _ = LabTest.objects.get_or_create(
                    code="VIT-D",
                    defaults={
                        "tenant_id": t_id,
                        "name": "25-Hydroxy Vitamin D Test",
                        "category": "chemistry",      # LabTestCategory.CHEMISTRY
                        "loinc_code": "62292-8",
                        "unit": "ng/mL",
                    }
                )
                # Create the reference range as a separate ReferenceRange record
                ReferenceRange.objects.get_or_create(
                    tenant_id=t_id,
                    test=lab_test,
                    sex="all",
                    defaults={
                        "analyte_code": "VIT-D",
                        "value_low": 30.0,
                        "value_high": 100.0,
                        "critical_low": 10.0,
                        "unit": "ng/mL",
                        "text_range": "30.0 - 100.0 ng/mL",
                        "is_active": True,
                    }
                )

                # LabOrder — uses patient_id (UUID), encounter_id (UUID), ordered_by (UUID)
                lab_order = LabOrder.objects.create(
                    tenant_id=t_id,
                    patient_id=pat_aisha.id,
                    encounter_id=enc_clinic.id,
                    order_number=f"LAB-{uuid.uuid4().hex[:8].upper()}",
                    ordered_by=phys_clinic.id,
                    priority=LabPriority.ROUTINE,
                    status="completed",
                )
                # LabOrderItem — links order to the test
                lab_order_item = LabOrderItem.objects.create(
                    tenant_id=t_id,
                    order=lab_order,
                    test=lab_test,
                    status="resulted",
                    priority=LabPriority.ROUTINE,
                    specimen_type="serum",
                )

                # Specimen — uses patient_id (UUID), order_item (FK to LabOrderItem)
                specimen = Specimen.objects.create(
                    tenant_id=t_id,
                    patient_id=pat_aisha.id,
                    order_item=lab_order_item,
                    specimen_number=f"SPC-{uuid.uuid4().hex[:8].upper()}",
                    barcode=f"BAR-{uuid.uuid4().hex[:6].upper()}",
                    specimen_type="serum",
                    status=SpecimenStatus.RECEIVED,
                    collected_at=timezone.now() - datetime.timedelta(hours=3),
                    received_at=timezone.now() - datetime.timedelta(hours=2, minutes=30),
                )

                # LabResult — uses order_item (FK), specimen (FK), ResultStatus choices
                lab_result = LabResult.objects.create(
                    tenant_id=t_id,
                    order_item=lab_order_item,
                    specimen=specimen,
                    status=ResultStatus.APPROVED,
                    resulted_by=lab_tech.id,
                    resulted_at=timezone.now() - datetime.timedelta(hours=2),
                    verified_by=lab_tech.id,
                    verified_at=timezone.now() - datetime.timedelta(hours=1, minutes=30),
                    approved_by=lab_tech.id,
                    approved_at=timezone.now() - datetime.timedelta(hours=1),
                )
                # ResultValue — individual analyte measurement
                ResultValue.objects.create(
                    tenant_id=t_id,
                    result=lab_result,
                    analyte_code="VIT-D",
                    analyte_name="25-Hydroxy Vitamin D",
                    loinc_code="62292-8",
                    value_type="numeric",
                    value_numeric=12.5,     # Deficient level
                    unit="ng/mL",
                    interpretation="L",    # Low
                    is_abnormal=True,
                    sequence=1,
                )

                # 3. Imaging order, modality scheduling, reporting, findings
                img_proc, _ = ImagingProcedure.objects.get_or_create(
                    code="US-ABD",
                    defaults={
                        "tenant_id": t_id,
                        "name": "Ultrasound Abdomen",
                        "modality": "us",
                        "body_part": "abdomen",
                        "loinc_code": "3070-9",
                    }
                )
                # ImagingOrder — uses patient_id (UUID), encounter_id (UUID), ordered_by (UUID)
                img_order = ImagingOrder.objects.create(
                    tenant_id=t_id,
                    patient_id=pat_aisha.id,
                    encounter_id=enc_clinic.id,
                    ordered_by=phys_clinic.id,
                    order_number=f"IMG-{uuid.uuid4().hex[:8].upper()}",
                    status="completed",
                )
                img_item = ImagingOrderItem.objects.create(
                    tenant_id=t_id,
                    order=img_order,
                    procedure=img_proc,
                    status="completed",
                )
                rad_report = RadiologyReport.objects.create(
                    tenant_id=t_id,
                    order_item=img_item,
                    patient_id=pat_aisha.id,
                    radiologist_id=rad.id,
                    findings="Mild fatty liver changes, gallbladder and kidneys are unremarkable.",
                    impression="Grade 1 Hepatic Steatosis. Otherwise normal abdominal study.",
                    ai_summary="AI: Suggestive of mild fatty liver changes. Consistent with metabolic evaluation.",
                    ai_assistance_used=True,
                    status="final",
                )

                # 4. Prescription & Medication Dispensing
                formulary, _ = Formulary.objects.get_or_create(
                    name="National Formulary - Saudi Arabia",
                    defaults={"tenant_id": t_id, "is_active": True}
                )
                form_drug, _ = FormularyDrug.objects.get_or_create(
                    formulary=formulary,
                    drug_code="RXCUI-197399",   # Alfacalcidol RxNorm
                    defaults={
                        "tenant_id": t_id,
                        "drug_name": "One-Alpha Vitamin D3",
                        "generic_name": "Alfacalcidol",
                        "atc_code": "A11CC03",
                        "status": "preferred",
                        "tier": 1,
                    }
                )

                # Prescription — uses patient_id (UUID), encounter_id (UUID), prescriber_id (UUID)
                presc = Prescription.objects.create(
                    tenant_id=t_id,
                    patient_id=pat_aisha.id,
                    encounter_id=enc_clinic.id,
                    prescriber_id=phys_clinic.id,
                    prescription_number=f"RX-{uuid.uuid4().hex[:6].upper()}",
                    prescription_type="outpatient",
                    status="dispensed",
                    priority="routine",
                )
                # PrescriptionItem — individual medication line
                PrescriptionItem.objects.create(
                    tenant_id=t_id,
                    prescription=presc,
                    drug_code="RXCUI-197399",
                    drug_name="One-Alpha (Alfacalcidol) 1mcg Capsule",
                    dose="1",
                    dose_unit="mcg",
                    route="oral",
                    frequency="once_daily",
                    quantity=30,
                    quantity_unit="capsule",
                    days_supply=30,
                    sig="Take one capsule by mouth once daily with food.",
                )

                # DispenseOrder — uses prescription_id (UUID), patient_id (UUID)
                disp_order = DispenseOrder.objects.create(
                    tenant_id=t_id,
                    prescription_id=presc.id,
                    patient_id=pat_aisha.id,
                    dispense_number=f"DISP-{uuid.uuid4().hex[:6].upper()}",
                    dispense_type="retail",
                    status=DispenseStatus.DISPENSED,
                    pickup_method="counter",
                    pharmacist_id=pharmacist.id,
                    dispensed_by=pharmacist.id,
                    dispensed_at=timezone.now() - datetime.timedelta(hours=1),
                )
                # DispenseItem — individual medication dispensed
                DispenseItem.objects.create(
                    tenant_id=t_id,
                    dispense_order=disp_order,
                    drug_code="RXCUI-197399",
                    drug_name="One-Alpha (Alfacalcidol) 1mcg Capsule",
                    quantity_prescribed=30,
                    quantity_dispensed=30,
                    quantity_unit="capsule",
                    days_supply=30,
                    barcode_verified=True,
                    barcode_verified_by=pharmacist.id,
                    barcode_verified_at=timezone.now() - datetime.timedelta(hours=1),
                    status="dispensed",
                )

                # 5. Billing, Claim Submission, Co-pay Payment
                today = timezone.now().date()
                billing_enc = EncounterBilling.objects.create(
                    tenant_id=t_id,
                    patient_account=pat_account,
                    encounter_id=enc_clinic.id,
                    encounter_type="outpatient",
                    encounter_date=today,
                    facility_id=facilities["CLIN-PRIMARY"].id,
                    attending_provider_id=phys_clinic.id,
                    total_charges=450.00,
                    insurance_expected=360.00,
                    patient_responsibility=90.00,
                    amount_paid=450.00,
                    balance_due=0.00,
                    billing_status="paid",
                    icd11_primary_diagnosis="E55.9",
                )

                # Invoice — patient invoice
                rcm_inv = RcmInvoice.objects.create(
                    tenant_id=t_id,
                    patient_account=pat_account,
                    encounter_billing=billing_enc,
                    invoice_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
                    invoice_type="patient",
                    invoice_date=today,
                    due_date=today + datetime.timedelta(days=30),
                    billing_party_type="self_pay",
                    status="paid",
                    amount_subtotal=450.00,
                    amount_total=450.00,
                    amount_paid=450.00,
                    amount_outstanding=0.00,
                    currency="SAR",
                )
                # Invoice lines
                for line_num, (desc, amount) in enumerate([
                    ("General Practice Consultation", 150.00),
                    ("25-Hydroxy Vitamin D Test", 100.00),
                    ("Ultrasound Abdomen", 200.00),
                ], start=1):
                    RcmInvoiceLine.objects.create(
                        tenant_id=t_id,
                        invoice=rcm_inv,
                        line_number=line_num,
                        service_date=today,
                        service_code=f"SVC-{line_num:03d}",
                        service_description=desc,
                        quantity=1,
                        unit_price=amount,
                        line_total=amount,
                    )

                # Insurance Claim — field names from Claim model
                claim = Claim.objects.create(
                    tenant_id=t_id,
                    claim_number=f"CLM-{uuid.uuid4().hex[:6].upper()}",
                    patient_id=pat_aisha.id,
                    insurance_member_id=ins_member.id,
                    insurance_plan_id=plan.id,
                    encounter_billing_id=billing_enc.id,
                    claim_type="professional",
                    claim_date=today,
                    service_from_date=today,
                    service_to_date=today,
                    facility_id=facilities["CLIN-PRIMARY"].id,
                    rendering_provider_id=phys_clinic.id,
                    status="paid",
                    total_billed_amount=450.00,
                    total_approved_amount=360.00,
                    total_paid_amount=360.00,
                    patient_responsibility=90.00,
                    icd11_primary_diagnosis="E55.9",
                )
                # Claim line
                ClaimLine.objects.create(
                    tenant_id=t_id,
                    claim=claim,
                    line_number=1,
                    service_date=today,
                    service_code="SVC-001",
                    service_description="General Practice Consultation",
                    quantity=1,
                    unit_charge=150.00,
                    line_charge=150.00,
                    approved_amount=120.00,
                    paid_amount=120.00,
                    line_status="included",
                    icd11_diagnosis_code="E55.9",
                    rendering_provider_id=phys_clinic.id,
                )

                # --- Workflow 2: Emergency Department Triage & Inpatient Admission ---
                enc_er = Encounter.objects.create(
                    tenant_id=t_id,
                    patient=pat_faisal,
                    encounter_type="emergency",
                    status="finished",
                    organization=org,
                    facility=hosp,
                    start_time=timezone.now() - datetime.timedelta(days=1),
                    end_time=timezone.now() - datetime.timedelta(days=1, hours=-2),
                )
                EncounterParticipant.objects.create(
                    tenant_id=t_id,
                    encounter=enc_er,
                    provider=phys_er,
                    role="lead"
                )
                EncounterReason.objects.create(
                    tenant_id=t_id,
                    encounter=enc_er,
                    reason_code="I20.9",
                    reason_text="Acute substernal chest pain, radiating to left arm"
                )

                # Inpatient Stay Admission
                enc_inpatient = Encounter.objects.create(
                    tenant_id=t_id,
                    patient=pat_faisal,
                    encounter_type="inpatient",
                    status="in_progress",
                    organization=org,
                    facility=hosp,
                    start_time=timezone.now() - datetime.timedelta(hours=22),
                )
                EncounterParticipant.objects.create(
                    tenant_id=t_id,
                    encounter=enc_inpatient,
                    provider=phys_er,
                    role="lead"
                )

                # ---------------------------------------------------------------------------
                # Phase 6: Validate CyCom ERP Integration (HR/GL/Inventory/Assets/BI)
                # ---------------------------------------------------------------------------
                self.stdout.write("Phase 6: Seeding CyCom ERP Financial Ledger & Sub-Modules...")

                # GL Chart of Accounts Setup
                gl_accounts = {}
                accounts_meta = [
                    ("101000", "Cash", "asset"),
                    ("102000", "Accounts Receivable", "asset"),
                    ("105000", "Inventory - Medical Supplies", "asset"),
                    ("151000", "Fixed Assets - Medical Devices", "asset"),
                    ("151099", "Accumulated Depreciation - Medical Devices", "asset"),
                    ("201000", "Accounts Payable", "liability"),
                    ("401000", "Healthcare Service Revenue", "revenue"),
                    ("501000", "Clinical Payroll Expense", "expense"),
                    ("502000", "Depreciation Expense", "expense"),
                ]

                for code, name, acc_type in accounts_meta:
                    acc, _ = Account.objects.get_or_create(
                        code=code,
                        defaults={
                            "tenant_id": t_id,
                            "name": name,
                            "account_type": acc_type,
                            "is_active": True,
                            "currency": "SAR",
                        }
                    )
                    gl_accounts[code] = acc

                # Journal Entry: Outpatient Clinical revenue recognition
                je_rev = JournalEntry.objects.create(
                    tenant_id=t_id,
                    entry_date=timezone.now().date(),
                    description=f"Recognize revenue & patient co-pay for Invoice {rcm_inv.invoice_number}",
                    reference=rcm_inv.invoice_number,
                    status="posted",
                    total_debit=450.00,
                    total_credit=450.00,
                )
                # Debit AR (Insurance portion)
                JournalLine.objects.create(
                    tenant_id=t_id,
                    journal=je_rev,
                    account=gl_accounts["102000"],
                    debit=360.00,
                    description="Bupa insurance receivable",
                )
                # Debit Cash (Patient portion)
                JournalLine.objects.create(
                    tenant_id=t_id,
                    journal=je_rev,
                    account=gl_accounts["101000"],
                    debit=90.00,
                    description="Patient co-pay received",
                )
                # Credit Revenue
                JournalLine.objects.create(
                    tenant_id=t_id,
                    journal=je_rev,
                    account=gl_accounts["401000"],
                    credit=450.00,
                    description="Clinical diagnostic & consultation services revenue",
                )

                # Update Account balances
                gl_accounts["102000"].balance += 360.00
                gl_accounts["102000"].save()
                gl_accounts["101000"].balance += 90.00
                gl_accounts["101000"].save()
                gl_accounts["401000"].balance += 450.00
                gl_accounts["401000"].save()

                # HR & Payroll Run
                payroll_run = PayrollRun.objects.create(
                    tenant_id=t_id,
                    run_date=timezone.now().date(),
                    status="paid",
                    total_gross=25000.00,
                    total_deductions=2200.00,
                    total_net=22800.00,
                )
                # Sarah RN Payslip
                Payslip.objects.create(
                    tenant_id=t_id,
                    payroll_run=payroll_run,
                    employee_id=emp_nurse_er.id,
                    basic_salary=12000.00,
                    allowances=1500.00,
                    deductions=1200.00,
                )
                # Khalid MD Payslip
                Payslip.objects.create(
                    tenant_id=t_id,
                    payroll_run=payroll_run,
                    employee_id=emp_phys_er.id,
                    basic_salary=20000.00,
                    allowances=3000.00,
                    deductions=2000.00,
                )

                # Inventory Stock management
                wh, _ = Warehouse.objects.get_or_create(
                    code="WH-MAIN",
                    defaults={
                        "tenant_id": t_id,
                        "name": "Central Pharmacy Warehouse",
                        "location": "Al-Amal Hospital Basement",
                    }
                )
                stock_item, _ = StockItem.objects.get_or_create(
                    sku="DRUG-VITD-001",
                    defaults={
                        "tenant_id": t_id,
                        "name": "Vitamin D3 50k IU Capsules",
                        "warehouse": wh,
                        "quantity": 1000.00,
                        "unit": "capsule",
                        "unit_cost": 2.50,
                    }
                )
                # Stock Movement (receipt of 500 capsules)
                StockMovement.objects.create(
                    tenant_id=t_id,
                    stock_item=stock_item,
                    movement_type="receipt",
                    quantity=500.00,
                    notes="Direct purchase order replenishment",
                )

                # Assets Management (Medical Device CT Scanner)
                scanner, _ = Asset.objects.get_or_create(
                    code="AST-CT-001",
                    defaults={
                        "tenant_id": t_id,
                        "name": "Siemens Somatom CT Scanner",
                        "asset_type": "medical_device",
                        "purchase_date": datetime.date(2024, 1, 1),
                        "purchase_cost": 750000.00,
                        "salvage_value": 50000.00,
                        "useful_life_years": 7,
                        "status": "active",
                    }
                )
                # Depreciate
                AssetDepreciation.objects.create(
                    tenant_id=t_id,
                    asset=scanner,
                    depreciation_date=timezone.now().date(),
                    amount=8333.33,
                    accumulated_depreciation=8333.33,
                    book_value=741666.67,
                )

                # BI & Metrics
                BIReport.objects.get_or_create(
                    name="Monthly Clinical Operations Summary",
                    defaults={
                        "tenant_id": t_id,
                        "report_type": "operations",
                        "query_definition": "SELECT COUNT(*) FROM cymed_encounters",
                        "active": True,
                    }
                )
                DashboardMetric.objects.get_or_create(
                    name="average_er_wait_time_minutes",
                    defaults={
                        "tenant_id": t_id,
                        "metric_value": 24.50,
                        "period": "daily",
                        "dimensions": {"facility": "HOSP-AMAL"},
                    }
                )
                DashboardMetric.objects.get_or_create(
                    name="monthly_gross_revenue_sar",
                    defaults={
                        "tenant_id": t_id,
                        "metric_value": 450.00,
                        "period": "monthly",
                        "dimensions": {"department": "CLIN"},
                    }
                )

            self.stdout.write(self.style.SUCCESS("Demo database successfully seeded!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding demo database: {e}"))
            raise e
