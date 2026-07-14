import { setRequestLocale } from "next-intl/server";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { buildMetadata } from "@/lib/metadata";
import { type Locale } from "@/lib/i18n";
import { ArrowRight, Check, ExternalLink, Play, BookOpen, ChevronRight, Brain, Layers, Phone } from "lucide-react";
import { ModuleExplorer, type ProductModule } from "@/components/products/ModuleExplorer";
import { RoleWorkflowExplorer, type RoleWorkflow } from "@/components/products/RoleWorkflowExplorer";
import { PermissionsMatrix, type PermissionRole } from "@/components/products/PermissionsMatrix";
import { PRODUCT_MODULES_DATA } from "@/lib/product-modules-data";

interface ProductPageProps {
  params: Promise<{ locale: string; slug: string }>;
}

const PRODUCT_DATA: Record<string, {
  name: string;
  tagline: string;
  category: string;
  description: string;
  features: string[];
  compliance: string[];
  editions: { name: string; desc: string; features: string[] }[];
  deployment: string[];
  color: string;
  accentClass: string;
  categoryLabel: string;
  subProducts?: { name: string; slug: string; desc: string }[];
  aiFeatures?: { title: string; desc: string }[];
  workflows?: { step: string; title: string; desc: string }[];
  erpModules?: { module: string; desc: string }[];
  modules?: ProductModule[];
  roleWorkflows?: RoleWorkflow[];
  permissionRoles?: PermissionRole[];
}> = {
  "cymed": {
    name: "CyMed",
    tagline: "Intelligent Healthcare Platform — Complete Clinical Suite",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "CyMed is a comprehensive FHIR-native clinical platform covering every care setting — from outpatient clinics to large hospitals, laboratories, pharmacies, imaging centers, and patient engagement. Built on ICD-11, SNOMED CT, and LOINC, CyMed connects the complete healthcare continuum through a unified clinical data model.",
    features: [
      "FHIR R4/R5 native across all modules",
      "ICD-11 & SNOMED CT clinical coding",
      "Single patient record across facilities",
      "Drug interaction engine (5 types)",
      "CyAI advisory-only clinical decision support",
      "Break Glass emergency access",
      "Hash-chained audit trail",
      "Arabic & English clinical interface (RTL/LTR)",
      "HL7 v2/v3 & DICOM integration",
      "Population health analytics",
    ],
    compliance: ["ICD-11", "FHIR R4", "SNOMED CT", "LOINC", "DICOM", "HL7 v2/v3"],
    editions: [
      { name: "CyMed Clinic", desc: "Outpatient EMR, scheduling, billing", features: ["Clinic module", "Patient portal", "Revenue cycle"] },
      { name: "CyMed Hospital", desc: "Inpatient, OR, ICU, ward management", features: ["All Clinic features", "ADT", "CPOE", "OR & ICU"] },
      { name: "CyMed Full Suite", desc: "All 9 CyMed products", features: ["All Hospital features", "Lab, Imaging, Pharmacy", "Population health", "Full RCM"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise", "Hybrid"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    subProducts: [
      { name: "CyMed Hospital", slug: "cymed-hospital", desc: "Complete hospital information system — ADT, OR, ICU, CPOE" },
      { name: "CyMed Clinic", slug: "cymed-clinic", desc: "Outpatient EMR, scheduling, billing, telemedicine" },
      { name: "CyMed Laboratory", slug: "cymed-laboratory", desc: "LIS with auto-verification, LOINC coding, analyzer interfacing" },
      { name: "CyMed Imaging", slug: "cymed-imaging", desc: "RIS/PACS, DICOM, structured reporting, AI image analysis" },
      { name: "CyMed Pharmacy", slug: "cymed-pharmacy", desc: "Clinical pharmacy, drug interactions, inventory management" },
      { name: "Patient Portal", slug: "cymed-patient-portal", desc: "Patient self-service, appointments, records, telemedicine" },
      { name: "Provider Portal", slug: "cymed-provider-portal", desc: "Provider scheduling, documentation, performance analytics" },
      { name: "Revenue Cycle", slug: "cymed-revenue-cycle", desc: "Insurance eligibility, coding, claims, denial management" },
      { name: "Population Health", slug: "cymed-population-health", desc: "Risk stratification, care programs, quality measures" },
    ],
  },
  "cymed-clinic": {
    name: "CyMed Clinic",
    tagline: "Intelligent Outpatient Clinical Management",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "A comprehensive outpatient management platform built for modern clinics. FHIR-native, ICD-11 coded, with integrated scheduling, EMR, billing, and patient engagement.",
    features: [
      "FHIR R4/R5 native EMR",
      "ICD-11 & SNOMED CT clinical coding",
      "Intelligent appointment scheduling",
      "Clinical decision support (CDS Hooks)",
      "E-prescribing & medication management",
      "Patient portal integration",
      "Revenue cycle management",
      "Telemedicine support",
      "Multi-language (EN/AR) interface",
      "Mobile-first provider app",
    ],
    compliance: ["ICD-11", "FHIR R4", "SNOMED CT", "LOINC", "HL7 v2.x"],
    editions: [
      { name: "Clinic Starter", desc: "For small clinics up to 5 providers", features: ["Core EMR", "Scheduling", "Billing", "Patient records"] },
      { name: "Clinic Professional", desc: "For multi-specialty practices", features: ["All Starter features", "Multi-specialty", "Lab integration", "Pharmacy", "Analytics"] },
      { name: "Clinic Enterprise", desc: "For clinic chains and networks", features: ["All Professional features", "Multi-branch", "API access", "Custom workflows", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise", "Hybrid"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    aiFeatures: [
      { title: "No-Show Prediction", desc: "Predicts appointment no-shows 48 h in advance with 87% accuracy, enabling proactive rescheduling and waitlist fills." },
      { title: "Chronic Disease Risk Stratification", desc: "Flags high-risk patients for care gap closure and proactive outreach before clinical deterioration." },
      { title: "Clinical Documentation AI", desc: "Auto-generates SOAP notes from consultation templates — advisory only, physician reviews and confirms every entry." },
      { title: "Drug Interaction Alerts", desc: "Real-time 5-type interaction checking (drug-drug, allergy, food, disease, age) at point of e-prescribing." },
      { title: "ICD-11 Diagnosis Suggestions", desc: "CDS Hooks-powered ICD-11 suggestion engine surfaced to clinician — never autonomous, always advisory." },
    ],
    erpModules: [
      { module: "Finance & Billing", desc: "GL integration, copay collection, insurance claim routing, and revenue reconciliation." },
      { module: "HR & Staff Scheduling", desc: "Provider scheduling, attendance tracking, leave management, and shift planning." },
      { module: "Patient CRM", desc: "Care follow-up campaigns, patient retention tracking, and engagement analytics." },
      { module: "Clinical Supply Inventory", desc: "Consumable stock management, reorder automation, and expiry tracking." },
      { module: "Payroll Integration", desc: "Provider compensation processing, WPS-ready salary run, and overtime calculation." },
    ],
    modules: [
      { name: "Patient Registration & Demographics", category: "clinical", desc: "Register new patients, capture demographics, insurance details, emergency contacts, and digital consent forms.", roles: ["Receptionist", "Nurse"] },
      { name: "Appointment Scheduling", category: "clinical", desc: "Book, reschedule, cancel, and manage waitlists across providers, specialties, and branches.", roles: ["Receptionist", "Physician"] },
      { name: "Patient Check-In & ADT", category: "clinical", desc: "Patient arrival check-in, demographic updates, copay collection, and encounter open event.", roles: ["Receptionist"] },
      { name: "Insurance Verification", category: "clinical", desc: "Real-time eligibility check — coverage confirmed, copay displayed, pre-auth status visible.", roles: ["Receptionist", "Finance"] },
      { name: "Electronic Medical Record (EMR)", category: "clinical", desc: "Full patient history, problem list, allergies, medications, vitals, and SOAP documentation.", roles: ["Physician", "Nurse"] },
      { name: "E-Prescribing", category: "clinical", desc: "Electronic prescriptions with real-time drug-drug, allergy, food, and disease interaction checking.", roles: ["Physician"] },
      { name: "Clinical Decision Support", category: "clinical", desc: "ICD-11 diagnosis suggestions and care gap alerts powered by CDS Hooks — advisory only.", roles: ["Physician"] },
      { name: "Lab Orders & Results Viewer", category: "clinical", desc: "CPOE lab orders, FHIR-delivered results, and critical value alerts inside the patient EMR.", roles: ["Physician", "Nurse"] },
      { name: "Referral Management", category: "clinical", desc: "Generate and track specialist referrals, view referral status, and receive back-referral notes.", roles: ["Physician", "Receptionist"] },
      { name: "Telemedicine", category: "clinical", desc: "Video consultations, remote prescribing, and secure patient messaging for virtual care.", roles: ["Physician", "Patient"] },
      { name: "Finance & Revenue Cycle", category: "erp", desc: "Copay collection, GL integration, insurance claim submission, and full revenue reconciliation.", roles: ["Finance", "Clinic Manager"] },
      { name: "HR & Staff Management", category: "erp", desc: "Employee records, contracts, org hierarchy, job roles, and staff onboarding/offboarding.", roles: ["Clinic Manager", "HR"] },
      { name: "Payroll (WPS-Ready)", category: "erp", desc: "Salary processing, WPS file generation, deductions, overtime, and payslip distribution.", roles: ["Finance", "HR"] },
      { name: "Attendance & Leave", category: "erp", desc: "Shift-based attendance tracking, leave requests, approvals, overtime calculation, and time reports.", roles: ["Clinic Manager", "HR", "All Staff"] },
      { name: "Clinical Supply Inventory", category: "erp", desc: "Consumable stock levels, FIFO dispensing, reorder automation, and expiry tracking.", roles: ["Clinic Manager", "Nurse"] },
      { name: "Patient CRM & Engagement", category: "erp", desc: "Recall campaigns, satisfaction surveys, patient retention tracking, and engagement analytics.", roles: ["Clinic Manager", "Receptionist"] },
      { name: "No-Show Prediction", category: "ai", desc: "Predicts appointment no-shows 48 h in advance with 87% accuracy — enables proactive waitlist fill.", roles: ["Receptionist", "Clinic Manager"] },
      { name: "Chronic Risk Stratification", category: "ai", desc: "Flags high-risk patients for proactive outreach and care gap closure before clinical deterioration.", roles: ["Physician", "Clinic Manager"] },
      { name: "Documentation AI", category: "ai", desc: "Auto-generates SOAP notes from consultation templates — physician reviews and confirms every entry.", roles: ["Physician"] },
      { name: "Drug Interaction Alerts", category: "ai", desc: "Real-time 5-type interaction checking at point of e-prescribing — never autonomous.", roles: ["Physician"] },
      { name: "ICD-11 Code Suggestions", category: "ai", desc: "CDS Hooks-powered diagnosis suggestion engine surfaced to clinician — advisory only, clinician confirms.", roles: ["Physician"] },
    ],
    roleWorkflows: [
      {
        role: "Receptionist",
        description: "Front desk operations: patient registration, appointment scheduling, check-in, insurance verification, and copay collection.",
        steps: [
          { action: "Search or Register Patient", detail: "Search by name, MRN, or phone. New patient: capture demographics, insurance card, emergency contacts, and digital consent." },
          { action: "Verify Insurance", detail: "Real-time eligibility check — coverage confirmed, copay amount shown, pre-authorization status visible instantly." },
          { action: "Schedule Appointment", detail: "Select provider, specialty, appointment type, and available slot. Patient receives automatic SMS/email confirmation." },
          { action: "Patient Check-In", detail: "Mark arrived, confirm demographics, collect and post copay, open encounter, and print visit summary if needed." },
          { action: "Manage Waitlist & Flow", detail: "Auto-fill cancellations from waitlist, reschedule walk-ins, and track daily patient flow across all providers." },
        ],
      },
      {
        role: "Physician",
        description: "Full clinical workflow: schedule review, EMR access, encounter documentation, orders, prescribing, and encounter closure.",
        steps: [
          { action: "Review Today's Schedule", detail: "See all booked patients, acuity flags, wait times, and notes from reception before entering the room." },
          { action: "Open Patient EMR", detail: "Full history at a glance: past visits, problem list, allergies, current medications, lab results, and vital trends." },
          { action: "Document Encounter", detail: "SOAP note via structured template or AI draft. ICD-11 diagnosis picker. Vitals auto-pulled from nurse entry." },
          { action: "Order Labs or Imaging", detail: "CPOE orders route directly to CyMed Laboratory or Imaging. Results appear in patient EMR when available." },
          { action: "E-Prescribe & Close", detail: "Medication search with drug interaction check → sign electronically → encounter closed → billing triggered automatically." },
        ],
      },
      {
        role: "Nurse",
        description: "Triage, vitals recording, medication administration, and care coordination support.",
        steps: [
          { action: "Patient Triage & Vitals", detail: "Record blood pressure, weight, temperature, SpO2, and pain score directly into the EMR vitals panel." },
          { action: "Medication Administration", detail: "Verify order, administer dose, scan barcode, and record Medication Administration Record (MAR) entry." },
          { action: "Clinical Notes", detail: "Nursing assessment notes, wound care documentation, and patient education records in the EMR." },
          { action: "Care Coordination", detail: "Lab specimen collection, referral follow-up, patient escort, and discharge instruction delivery." },
        ],
      },
      {
        role: "Clinic Manager",
        description: "Operational oversight: staff scheduling, inventory, performance metrics, and daily reporting.",
        steps: [
          { action: "Staff Scheduling", detail: "Build provider and nurse schedules, manage shifts, approve leave requests, and view attendance compliance." },
          { action: "Inventory Review", detail: "Check clinical supply stock levels, approve reorder requests, and reconcile supplier deliveries." },
          { action: "Financial Dashboard", detail: "Daily revenue summary, collection rates, outstanding insurance claims, and top provider performance KPIs." },
          { action: "Patient Experience", detail: "Satisfaction survey results, complaint tracking, waitlist analysis, and no-show rate trend review." },
        ],
      },
      {
        role: "Finance / Billing",
        description: "Revenue cycle: claim preparation, submission, denial management, reconciliation, and payroll.",
        steps: [
          { action: "Claim Preparation", detail: "Auto-generated claims from closed encounters with ICD-11 and CPT codes. Pre-submission scrubbing to catch errors." },
          { action: "Insurance Submission", detail: "Submit to payers electronically. Track claim status, ERA receipts, adjustment codes, and denial reasons." },
          { action: "Denial Management", detail: "Appeal denied claims, correct coding errors, and re-submit with supporting clinical documentation." },
          { action: "Payroll Processing", detail: "Run WPS-compliant payroll, approve payslips, and post salary journal entries to the general ledger." },
        ],
      },
    ],
  },
  "cymed-hospital": {
    name: "CyMed Hospital",
    tagline: "Complete Hospital Information System",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "End-to-end hospital management platform covering inpatient care, OR management, ICU, nursing station, ward management, and clinical operations — all FHIR-native and ICD-11 coded.",
    features: [
      "FHIR R4/R5 inpatient EMR",
      "ADT (Admission, Discharge, Transfer)",
      "OR scheduling & surgical management",
      "ICU monitoring integration",
      "Nursing station workflows",
      "Clinical order management (CPOE)",
      "Blood bank management",
      "Bed management & census",
      "Revenue cycle & claims",
      "Population health analytics",
    ],
    compliance: ["ICD-11", "FHIR R4", "SNOMED CT", "LOINC", "DICOM", "HL7 v2.x", "HL7 v3"],
    editions: [
      { name: "Hospital Core", desc: "For hospitals up to 200 beds", features: ["ADT", "EMR", "Nursing", "Billing", "Laboratory integration"] },
      { name: "Hospital Advanced", desc: "For hospitals 200-500 beds", features: ["All Core features", "OR Management", "ICU", "Blood Bank", "PACS integration"] },
      { name: "Hospital Enterprise", desc: "For large hospitals and health systems", features: ["All Advanced features", "Multi-facility", "Population health", "AI clinical decision support", "24/7 SLA"] },
    ],
    deployment: ["Private Cloud", "On-Premise", "Hybrid"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    aiFeatures: [
      { title: "Sepsis Early Warning", desc: "SOFA/NEWS2 scoring with 6-hour sepsis prediction — alerts nursing station and attending physician immediately." },
      { title: "ICU Deterioration Prediction", desc: "Continuous vital sign trend analysis predicts deterioration events 2–4 hours before clinical signs appear." },
      { title: "Bed Demand Forecasting", desc: "Predicts 24–72 h bed demand by ward type enabling proactive capacity planning and transfer coordination." },
      { title: "Surgical Risk Scoring", desc: "Pre-operative AI risk scoring (ASA + custom model) surfaced in OR scheduling — advisory only, surgeon confirms." },
      { title: "30-Day Readmission Risk", desc: "Discharge-time readmission risk flag with care plan recommendations for high-risk patients." },
      { title: "Clinical Documentation AI", desc: "CPOE auto-suggestion, discharge summary drafting, and nursing handover notes — physician confirms all." },
    ],
    erpModules: [
      { module: "Finance & Revenue Cycle", desc: "Insurance billing, claims submission, denial management, and collections integrated with hospital billing." },
      { module: "HR & Workforce", desc: "Nursing rosters, clinical staff scheduling, shift planning, on-call management, and payroll." },
      { module: "Medical Supply Inventory", desc: "Surgical supplies, ward medications, and consumables tracked in real time across all floors and stores." },
      { module: "Procurement", desc: "Medical equipment RFQs, supplier management, purchase order workflow, and GRN processing." },
      { module: "Fixed Asset Registry", desc: "Medical equipment lifecycle tracking, preventive maintenance schedules, and depreciation management." },
      { module: "Payroll", desc: "Clinical and administrative staff compensation with on-call differentials and WPS compliance." },
    ],
    modules: [
      { name: "Patient Admission (ADT)", category: "clinical", desc: "Full Admission, Discharge, Transfer management with bed assignment, pre-admission planning, and insurance verification.", roles: ["Admissions", "Receptionist"] },
      { name: "Bed Management & Census", category: "clinical", desc: "Real-time bed availability across all wards, housekeeping status, and discharge lounge management.", roles: ["Ward Manager", "Admissions"] },
      { name: "Inpatient EMR & CPOE", category: "clinical", desc: "Complete inpatient record with physician orders, clinical notes, problem list, allergies, and medication orders.", roles: ["Physician", "Nurse"] },
      { name: "Nursing Station", category: "clinical", desc: "Nursing assessment, medication administration record (MAR), vital signs, care plans, and handover notes.", roles: ["Nurse", "Head Nurse"] },
      { name: "OR Scheduling & Management", category: "clinical", desc: "Surgical scheduling, pre-op checklist, anesthesia consent, intraoperative notes, and post-op recovery.", roles: ["OR Coordinator", "Surgeon", "Anesthesiologist"] },
      { name: "ICU Monitoring Integration", category: "clinical", desc: "Vital sign device integration, SOFA/NEWS2 scoring, ventilator parameters, and critical care flowsheets.", roles: ["ICU Physician", "ICU Nurse"] },
      { name: "Blood Bank Management", category: "clinical", desc: "Blood product inventory, crossmatch requests, transfusion records, and wastage tracking.", roles: ["Lab Technician", "Physician"] },
      { name: "Pharmacy Dispensing", category: "clinical", desc: "Ward medication dispensing, narcotic tracking, unit-dose packaging, and drug interaction checking.", roles: ["Pharmacist", "Nurse"] },
      { name: "Discharge Planning", category: "clinical", desc: "Discharge summary generation, follow-up scheduling, patient education, and readmission risk flagging.", roles: ["Physician", "Social Worker", "Nurse"] },
      { name: "Finance & Revenue Cycle", category: "erp", desc: "DRG-based billing, insurance claim management, denial tracking, collections, and revenue reconciliation.", roles: ["Finance", "Billing"] },
      { name: "HR & Workforce Management", category: "erp", desc: "Nursing rosters, clinical staff scheduling, shift rotation, on-call management, and workforce analytics.", roles: ["HR Manager", "Ward Manager"] },
      { name: "Medical Supply Inventory", category: "erp", desc: "Surgical supplies, ward medications, and consumables tracked in real time across all floors and central stores.", roles: ["Storekeeper", "Ward Manager"] },
      { name: "Procurement", category: "erp", desc: "Medical equipment RFQs, supplier management, purchase order workflow, goods receiving, and GRN processing.", roles: ["Procurement Manager"] },
      { name: "Fixed Asset Registry", category: "erp", desc: "Medical equipment lifecycle, scheduled maintenance, warranty tracking, and depreciation management.", roles: ["Maintenance Manager", "Finance"] },
      { name: "Payroll (WPS)", category: "erp", desc: "Clinical and admin staff compensation with on-call differentials, overtime, and WPS compliance.", roles: ["HR Manager", "Finance"] },
      { name: "Attendance & Leave", category: "erp", desc: "Shift-based attendance for all clinical and support staff. Leave requests, approvals, and overtime tracking.", roles: ["HR Manager", "Ward Manager", "All Staff"] },
      { name: "Sepsis Early Warning", category: "ai", desc: "SOFA/NEWS2 scoring with 6-hour sepsis prediction — alerts nursing station and attending physician immediately.", roles: ["Physician", "ICU Nurse"] },
      { name: "ICU Deterioration Prediction", category: "ai", desc: "Continuous vital trend analysis predicts deterioration events 2–4 hours before clinical signs appear.", roles: ["ICU Physician", "ICU Nurse"] },
      { name: "Bed Demand Forecasting", category: "ai", desc: "Predicts 24–72 h bed demand by ward type for proactive capacity planning and transfer coordination.", roles: ["Ward Manager", "Admissions"] },
      { name: "Surgical Risk Scoring", category: "ai", desc: "Pre-operative AI risk scoring (ASA + custom model) surfaced in OR scheduling — surgeon confirms.", roles: ["Surgeon", "OR Coordinator"] },
      { name: "30-Day Readmission Risk", category: "ai", desc: "Discharge-time readmission risk flag with care plan recommendations for high-risk patients.", roles: ["Physician", "Social Worker"] },
      { name: "Documentation AI", category: "ai", desc: "CPOE auto-suggestion, discharge summary drafting, and nursing handover notes — clinician confirms all.", roles: ["Physician", "Nurse"] },
    ],
    roleWorkflows: [
      {
        role: "Admissions / Reception",
        description: "Patient admission: registration, bed assignment, insurance verification, and ADT event management.",
        steps: [
          { action: "Pre-Admission Planning", detail: "Review pre-admission forms, confirm insurance pre-authorization, and prepare patient demographic record." },
          { action: "Admit Patient (ADT)", detail: "Complete ADT admission — assign bed, ward, and attending physician. Insurance eligibility verified in real time." },
          { action: "Bed Assignment", detail: "View real-time bed availability across all wards. Assign appropriate bed based on case type and isolation requirements." },
          { action: "Wristband & Documentation", detail: "Print patient wristband with MRN barcode, distribute welcome pack, and collect consent forms." },
          { action: "Track Transfers & Discharge", detail: "Manage bed transfers between wards, update ADT events, and prepare discharge paperwork when physician orders." },
        ],
      },
      {
        role: "Physician",
        description: "Inpatient clinical workflow: rounding, CPOE orders, clinical documentation, and discharge.",
        steps: [
          { action: "Patient Rounding List", detail: "Review assigned inpatients with overnight notes, pending results, and AI-flagged deterioration alerts." },
          { action: "CPOE Orders", detail: "Enter medication, lab, imaging, and consult orders. Drug interaction checks run automatically at order entry." },
          { action: "Clinical Documentation", detail: "Progress notes, operative reports, and consult notes structured by template — AI drafts available for review." },
          { action: "Results Review", detail: "Lab and imaging results appear in patient EMR. Critical values auto-flagged. Radiology reports with AI pre-reads." },
          { action: "Discharge & Summary", detail: "Order discharge, select follow-up plan, AI drafts discharge summary — physician edits and signs electronically." },
        ],
      },
      {
        role: "Nurse",
        description: "Nursing station: medication administration, vitals monitoring, care plans, and shift handover.",
        steps: [
          { action: "Shift Handover", detail: "Review handover notes from prior shift. Acknowledge pending orders, critical values, and patient alerts." },
          { action: "Vital Signs & Monitoring", detail: "Record vitals from bedside devices or manual entry. SOFA/NEWS2 scores calculated automatically." },
          { action: "Medication Administration", detail: "Verify CPOE order, scan patient wristband and medication barcode, administer, and record MAR electronically." },
          { action: "Care Plan Execution", detail: "Document wound care, mobility assessments, nutrition records, fall risk, and pressure ulcer prevention." },
          { action: "Escalation & Handover", detail: "Escalate deteriorating patients using AI early warning. Complete electronic handover notes for next shift." },
        ],
      },
      {
        role: "OR Coordinator",
        description: "Surgical suite management: scheduling, pre-op checklist, equipment, and post-op recovery.",
        steps: [
          { action: "Surgical Scheduling", detail: "Book OR time based on surgeon availability, case duration, equipment needs, and room requirements." },
          { action: "Pre-Op Checklist", detail: "Verify pre-op labs, imaging, consent forms, anesthesia review, and NPO status before case starts." },
          { action: "Intraoperative Management", detail: "Track case start/end, anesthesia events, implant lot numbers, and intraoperative complications." },
          { action: "Post-Op Recovery", detail: "Transfer patient to PACU, record recovery vitals, and manage discharge criteria from recovery room." },
        ],
      },
      {
        role: "Finance / Billing",
        description: "Hospital billing: DRG coding, insurance claims, denial management, and revenue reconciliation.",
        steps: [
          { action: "Charge Capture", detail: "All clinical orders and procedures auto-generate charges. Review and approve before claim generation." },
          { action: "DRG & Coding", detail: "ICD-11 principal diagnosis and procedure codes auto-suggested from clinical documentation — coder reviews." },
          { action: "Insurance Submission", detail: "Submit clean claims electronically. Track status, ERA posting, and adjustment codes from payers." },
          { action: "Denial & Appeals", detail: "Work denied claims, correct errors, attach clinical documentation, and re-submit with full audit trail." },
          { action: "Revenue Reconciliation", detail: "Daily cash posting, GL journal entries, outstanding AR aging report, and financial close reporting." },
        ],
      },
    ],
  },
  "cymed-laboratory": {
    name: "CyMed Laboratory",
    tagline: "Laboratory Information System with Auto-Verification",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "Full-featured LIS with LOINC coding, auto-verification rules, QC management, interfacing with analyzers, and FHIR-based result delivery.",
    features: [
      "LOINC-coded test catalog",
      "Auto-verification engine",
      "QC management (Westgard rules)",
      "Analyzer interfacing (bidirectional)",
      "Specimen collection & tracking",
      "Result delivery via FHIR",
      "Critical value alerting",
      "Microbiology & blood bank modules",
      "Reference lab management",
      "Mobile phlebotomist app",
    ],
    compliance: ["LOINC", "FHIR R4", "ICD-11", "HL7 v2.x"],
    editions: [
      { name: "Lab Core", desc: "Clinical chemistry & hematology", features: ["Core test catalog", "Basic QC", "Analyzer interface", "FHIR results"] },
      { name: "Lab Full", desc: "Full-service laboratory", features: ["All Core features", "Microbiology", "Blood bank", "Auto-verification", "Advanced QC"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    aiFeatures: [
      { title: "Auto-Verification Rules Engine", desc: "Configurable multi-rule auto-verification releases normal results instantly; exceptions flagged for tech review." },
      { title: "Critical Value Intelligence", desc: "Context-aware critical value alerting with priority routing based on patient acuity and care setting." },
      { title: "TAT Prediction", desc: "Predicts test turnaround time per analyzer load, enabling proactive patient and clinician communication." },
      { title: "QC Anomaly Detection", desc: "Westgard rule monitoring with ML drift detection catches equipment calibration issues before patient results are affected." },
      { title: "Reflex Testing AI", desc: "Auto-triggers reflex tests based on primary result patterns, configured per clinical protocol." },
    ],
    erpModules: [
      { module: "Reagent & Consumables Inventory", desc: "Real-time stock levels, expiry tracking, FIFO dispensing, and automated reorder for all lab consumables." },
      { module: "Lab Procurement", desc: "Reagent RFQs, supplier catalog management, and purchase cycle automation with lead-time tracking." },
      { module: "Finance & Test Billing", desc: "Test tariff management, insurance billing, patient invoicing, and collection reconciliation." },
      { module: "Analyzer Asset Registry", desc: "Equipment lifecycle tracking, preventive maintenance scheduling, warranty management, and depreciation." },
      { module: "Staff & Shift Management", desc: "Phlebotomist and lab technician scheduling, shift rotation, overtime, and attendance." },
    ],
  },
  "cymed-imaging": {
    name: "CyMed Imaging",
    tagline: "Radiology Information System & PACS Integration",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "Integrated RIS with DICOM-native PACS connectivity, radiologist worklists, structured reporting, and AI-powered image analysis.",
    features: [
      "DICOM-native image management",
      "Radiologist worklist management",
      "Structured reporting (RSNA templates)",
      "AI-assisted image analysis",
      "PACS/VNA connectivity",
      "3D visualization support",
      "Critical finding alerts",
      "Peer review workflows",
      "Teleradiology support",
      "FHIR ImagingStudy integration",
    ],
    compliance: ["DICOM", "FHIR R4", "IHE Profiles", "LOINC"],
    editions: [
      { name: "Imaging Core", desc: "Basic RIS with PACS connectivity", features: ["RIS workflow", "DICOM viewer", "Basic reporting"] },
      { name: "Imaging Advanced", desc: "Full RIS with AI capabilities", features: ["All Core features", "AI image analysis", "3D visualization", "Teleradiology", "Advanced structured reporting"] },
    ],
    deployment: ["On-Premise", "Private Cloud", "Hybrid"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    aiFeatures: [
      { title: "AI-Assisted Image Analysis", desc: "Advisory-only findings suggestions for chest X-ray, brain CT, and mammography — radiologist reviews and signs all reports." },
      { title: "Study Urgency Scoring", desc: "Prioritizes radiologist worklist by clinical urgency, reducing critical finding turnaround time significantly." },
      { title: "Structured Report AI", desc: "Pre-populates structured radiology report templates based on study type and modality findings pattern." },
      { title: "Scheduling Optimization", desc: "Optimizes modality booking to minimize patient wait time and maximize expensive equipment utilization." },
      { title: "DICOM Anomaly Flagging", desc: "Detects incomplete or corrupted DICOM datasets before radiologist reading, preventing missed or incomplete studies." },
    ],
    erpModules: [
      { module: "Medical Equipment Asset Registry", desc: "MRI, CT, X-ray, and ultrasound equipment lifecycle tracking, scheduled maintenance, and depreciation." },
      { module: "Contrast & Consumables Inventory", desc: "Contrast media, films, and radiology consumable stock management with expiry control." },
      { module: "Procurement", desc: "Radiology supply RFQs, supplier management, and purchase order processing." },
      { module: "Finance & Imaging Billing", desc: "Procedure-based billing, RVS/RUVS coding, and insurance claim routing for all imaging modalities." },
      { module: "Staff Management", desc: "Radiologist and radiographer scheduling, performance tracking, and on-call management." },
    ],
  },
  "cymed-pharmacy": {
    name: "CyMed Pharmacy",
    tagline: "Clinical Pharmacy Management System",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "End-to-end pharmacy management covering dispensing, clinical pharmacy review, drug interaction checking, inventory, and FHIR-based medication reconciliation.",
    features: [
      "E-prescription reception (FHIR)",
      "Clinical pharmacist review",
      "Drug-drug interaction checking",
      "Allergy alert system",
      "Inventory management (FIFO/FEFO)",
      "Narcotic & controlled substance tracking",
      "Automated dispensing cabinet integration",
      "IV admixture & chemotherapy preparation",
      "Pharmacy analytics & reporting",
      "Mobile pharmacist tools",
    ],
    compliance: ["FHIR R4", "ICD-11", "LOINC", "GS1 Barcoding"],
    editions: [
      { name: "Pharmacy Core", desc: "Retail & hospital pharmacy dispensing", features: ["Dispensing", "Inventory", "Drug interactions", "Basic reporting"] },
      { name: "Pharmacy Clinical", desc: "Full clinical pharmacy operations", features: ["All Core features", "Clinical review", "IV admixture", "Narcotic tracking", "Analytics"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    aiFeatures: [
      { title: "5-Type Drug Interaction Detection", desc: "Drug-drug, drug-allergy, drug-food, drug-disease, and drug-age interaction checking at point of dispensing." },
      { title: "Adherence Prediction", desc: "Identifies patients at risk of non-adherence based on refill patterns and flags them for pharmacist counseling." },
      { title: "Inventory Demand Forecasting", desc: "Predicts drug demand by consumption patterns, reducing stockouts and overstock simultaneously." },
      { title: "Expiry & Wastage AI", desc: "Predicts near-expiry risk per SKU and suggests inter-location transfers to minimize wastage cost." },
      { title: "Therapeutic Substitution AI", desc: "Recommends therapeutic equivalents during drug shortages, surfaced to clinical pharmacist for approval." },
    ],
    erpModules: [
      { module: "Drug Inventory (FIFO/FEFO)", desc: "Real-time stock control, expiry management, batch tracking, and automated reorder for all medications." },
      { module: "Pharmaceutical Procurement", desc: "Supplier catalog, purchase orders, goods receiving notes, and contract pricing management." },
      { module: "Finance & Dispensing Revenue", desc: "Dispensing revenue tracking, insurance claims, patient billing, and reconciliation." },
      { module: "Supplier Management", desc: "Vendor scorecards, lead-time tracking, preferred supplier lists, and tender management." },
      { module: "Controlled Substance Tracking", desc: "Narcotic logs, regulatory reporting, and chain-of-custody audit trail for controlled medications." },
    ],
  },
  "cymed-patient-portal": {
    name: "CyMed Patient Portal",
    tagline: "Patient Engagement & Self-Service Platform",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "FHIR R4-native patient portal giving patients 24/7 access to their health records, lab results, appointments, telemedicine, and bill payment — on web or mobile. Built-in family account management lets caregivers manage dependents securely.",
    features: [
      "Online appointment booking & real-time slot availability",
      "FHIR-native health records — full medical history",
      "Lab results with reference ranges & trend graphs",
      "Secure encrypted messaging with care team",
      "Video telemedicine (HD, end-to-end encrypted)",
      "Prescription refill requests",
      "Medication tracking & adherence reminders",
      "Vaccination & immunization records",
      "Bill payment & insurance explanation of benefits",
      "Family account — manage dependents & minors",
      "Arabic & English interface (RTL/LTR)",
      "Offline-capable PWA — no app store install required",
    ],
    compliance: ["FHIR R4", "HIPAA Ready", "GDPR Ready", "OAuth 2.1"],
    editions: [
      { name: "Portal Starter", desc: "Core patient engagement", features: ["Appointments", "Health records", "Lab results", "Provider messaging", "Bill payment"] },
      { name: "Portal Full", desc: "Complete patient experience", features: ["All Starter", "Telemedicine", "Prescription refills", "Family management", "Adherence reminders", "Analytics"] },
    ],
    deployment: ["SaaS Cloud"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    aiFeatures: [
      { title: "Symptom Pre-screening", desc: "Patients complete an AI-guided symptom questionnaire before their appointment. Summary reaches the provider before the visit starts." },
      { title: "Appointment Recommendation", desc: "AI suggests appointment type, urgency, and specialty based on stated concern — reducing unnecessary ED visits." },
      { title: "Lab Trend Interpretation", desc: "Plain-language interpretation of out-of-range results with trend visualization across visits, reviewed by provider." },
      { title: "Medication Adherence AI", desc: "Detects refill gaps and sends contextual reminders — proven to improve chronic disease medication adherence." },
      { title: "Care Gap Alerts", desc: "Proactively flags overdue screenings, vaccines, and follow-ups based on patient's age, diagnosis, and care protocols." },
    ],
    workflows: [
      { step: "01", title: "Register / Sign In", desc: "Patient creates account with national ID or MRN. MFA via OTP or biometric. Linked to hospital record automatically." },
      { step: "02", title: "Book Appointment", desc: "Select specialty, provider, and time. Real-time slot availability from CyMed Hospital/Clinic calendar." },
      { step: "03", title: "Pre-visit Check-in", desc: "Complete AI symptom questionnaire, upload referrals, confirm insurance. Zero paperwork on arrival." },
      { step: "04", title: "Visit & Telehealth", desc: "In-person or video consultation. Provider notes sync to patient record within minutes of visit end." },
      { step: "05", title: "Post-visit Care", desc: "Lab results, prescriptions, and follow-up instructions appear automatically. Pay bill online. Manage family." },
    ],
    erpModules: [
      { module: "Patient Billing & Payments", desc: "Online payment gateway, insurance EOB, installment plans, and refund processing." },
      { module: "CRM & Patient Engagement", desc: "Campaign management for preventive care outreach, satisfaction surveys, and recall scheduling." },
    ],
  },
  "cymed-provider-portal": {
    name: "CyMed Provider Portal",
    tagline: "Clinical Workforce Management Portal",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "Provider-facing portal for credential management, schedule management, clinical documentation, and performance analytics.",
    features: [
      "Provider credentialing & licensing",
      "Schedule & availability management",
      "Clinical documentation access",
      "Performance dashboards",
      "CME & training tracking",
      "Peer review participation",
      "Referral management",
      "Patient panel management",
      "Mobile provider app",
      "MFA & device registration",
    ],
    compliance: ["FHIR R4", "OAuth 2.1", "HIPAA Ready"],
    editions: [
      { name: "Provider Core", desc: "Schedule & documentation", features: ["Scheduling", "Records", "Dashboards"] },
      { name: "Provider Full", desc: "Complete provider experience", features: ["All Core", "CME tracking", "Analytics", "Referrals"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
  },
  "cymed-revenue-cycle": {
    name: "CyMed Revenue Cycle",
    tagline: "Healthcare Revenue Cycle Management",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "Comprehensive RCM platform covering patient registration, insurance eligibility verification, medical coding, claims submission, denial management, and collections.",
    features: [
      "Patient financial counseling",
      "Insurance eligibility verification",
      "ICD-11 & CPT medical coding",
      "Claims submission & tracking",
      "Denial management & appeals",
      "Payment posting & reconciliation",
      "Collections management",
      "Payor contract management",
      "AR analytics & dashboards",
      "Integration with major insurers",
    ],
    compliance: ["ICD-11", "CPT", "FHIR R4", "X12 EDI"],
    editions: [
      { name: "RCM Core", desc: "Basic billing operations", features: ["Registration", "Coding", "Billing", "Claims"] },
      { name: "RCM Full", desc: "Complete revenue cycle", features: ["All Core", "Denial management", "Collections", "Analytics"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
  },
  "cymed-population-health": {
    name: "CyMed Population Health",
    tagline: "Population Health Analytics & Care Programs",
    category: "healthcare",
    categoryLabel: "CyMed Healthcare",
    description:
      "AI-powered population health management platform for risk stratification, chronic disease management, care gap identification, and population analytics.",
    features: [
      "Population risk stratification",
      "Chronic disease program management",
      "Care gap identification",
      "Social determinants of health (SDOH)",
      "Predictive analytics",
      "Care coordination workflows",
      "Patient outreach campaigns",
      "Quality measure reporting",
      "Public health reporting",
      "Geographic health mapping",
    ],
    compliance: ["FHIR R4", "HL7 QRDA", "ICD-11"],
    editions: [
      { name: "PopHealth Core", desc: "Analytics & reporting", features: ["Risk stratification", "Analytics", "Reporting"] },
      { name: "PopHealth Full", desc: "Complete population management", features: ["All Core", "Care programs", "Outreach", "SDOH", "AI"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud"],
    color: "emerald",
    accentClass: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
  },
  "cycom": {
    name: "CyCom ERP",
    tagline: "Unified Enterprise Resource Planning Platform",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description:
      "A comprehensive ERP platform unifying Finance, HR, Procurement, Inventory, Assets, Manufacturing, CRM, Retail, and Payroll in a single integrated system.",
    features: [
      "Financial management & accounting",
      "Human resources & payroll",
      "Procurement & vendor management",
      "Inventory & warehouse management",
      "Fixed asset management",
      "Manufacturing & production",
      "CRM & sales management",
      "Retail operations",
      "Business intelligence & analytics",
      "Multi-currency & multi-language",
    ],
    compliance: ["IFRS", "GAAP", "VAT/TAX compliant"],
    editions: [
      { name: "Business", desc: "SME operations", features: ["Finance", "HR", "Inventory", "CRM"] },
      { name: "Enterprise", desc: "Large organization operations", features: ["All Business", "Manufacturing", "Advanced analytics", "API access"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
    aiFeatures: [
      { title: "Financial Forecasting", desc: "AI-driven cash flow, revenue, and expense forecasting with scenario modeling across all legal entities." },
      { title: "Procurement Intelligence", desc: "Identifies cost-saving opportunities in procurement patterns and surfaces preferred supplier recommendations." },
      { title: "HR Analytics", desc: "Workforce productivity analytics, attrition prediction, and headcount optimization across departments." },
      { title: "Inventory Optimization", desc: "Demand-driven reorder point calculation that minimizes carrying cost while preventing stockouts." },
      { title: "Financial Anomaly Detection", desc: "Real-time transaction anomaly detection flagging fraud, data-entry errors, and policy violations instantly." },
      { title: "NL Query (BI)", desc: "Natural language interface to BI dashboards — ask questions in Arabic or English and get charts and tables." },
    ],
    erpModules: [
      { module: "Finance & Accounting", desc: "GL, AP, AR, bank reconciliation, multi-currency, budgeting, and financial reporting." },
      { module: "Procurement", desc: "Purchase requisitions, RFQs, POs, supplier portal, contract management, and GRN workflow." },
      { module: "Inventory & Warehouse", desc: "Multi-warehouse stock control, serial/batch tracking, transfers, and cycle counting." },
      { module: "HR & Payroll", desc: "Employee records, performance, recruitment, attendance, and WPS-compliant payroll." },
      { module: "Manufacturing", desc: "Bill of materials, MRP, work orders, production scheduling, and quality inspection." },
      { module: "CRM & Sales", desc: "Lead pipeline, customer management, quotations, contracts, and helpdesk ticketing." },
      { module: "Fixed Assets", desc: "Asset registry, depreciation runs (multiple methods), maintenance schedules, and disposal." },
      { module: "BI & Analytics", desc: "Drag-and-drop dashboards, KPI widgets, drill-down reports, and natural language queries." },
      { module: "Multi-Entity & Multi-Currency", desc: "Consolidated financial reporting across legal entities, branches, and currencies in real time." },
      { module: "eSign & Documents", desc: "Digital document workflow with e-signature, version control, and approval routing." },
      { module: "Point of Sale", desc: "Retail checkout, shift management, cash-up reconciliation, and loyalty integration." },
      { module: "Fleet Management", desc: "Vehicle registry, maintenance scheduling, driver assignment, and fuel cost tracking." },
    ],
    subProducts: [
      { name: "CyCom Finance", slug: "cycom-finance", desc: "General ledger, budgeting, cash flow management" },
      { name: "CyCom Accounting", slug: "cycom-accounting", desc: "Accounts payable, accounts receivable, tax compliance" },
      { name: "CyCom Procurement", slug: "cycom-procurement", desc: "Supplier management, purchase requisitions, purchasing cycles" },
      { name: "CyCom Inventory", slug: "cycom-inventory", desc: "Multi-warehouse tracking, stock movements, serial/batch control" },
      { name: "CyCom HR", slug: "cycom-hr", desc: "Employee records, performance tracking, recruitment" },
      { name: "CyCom Payroll", slug: "cycom-payroll", desc: "Bilingual salary processing, local labor compliance" },
      { name: "CyCom CRM", slug: "cycom-crm", desc: "Lead pipeline, client relationships, support portals" },
      { name: "CyCom Assets", slug: "cycom-assets", desc: "Fixed assets register, automated depreciation schedules" },
      { name: "CyCom Manufacturing", slug: "cycom-manufacturing", desc: "Bill of materials (BOM), production scheduling" },
      { name: "CyCom Retail", slug: "cycom-retail", desc: "Point of Sale (POS), checkout, loyalty rewards" },
      { name: "CyCom BI", slug: "cycom-bi", desc: "Drag-and-drop analytics dashboards, business reporting" },
    ],
  },
  "cygov": {
    name: "CyGov",
    tagline: "Government Digital Transformation Platform",
    category: "government",
    categoryLabel: "CyGov Government",
    description:
      "Comprehensive digital government platform enabling citizen services, national registries, licensing, permits, digital identity, and government workflow automation.",
    features: [
      "Citizen services portal",
      "Online licensing & permitting",
      "National registries management",
      "Government workflow automation",
      "Digital document management",
      "Inter-agency integration",
      "E-payment & fee collection",
      "Audit trail & compliance",
      "Multilingual (EN/AR)",
      "WCAG 2.1 AA accessibility",
    ],
    compliance: ["GDPR", "ISO 27001 Ready", "eIDAS compliant"],
    editions: [
      { name: "Gov Starter", desc: "Core citizen services", features: ["Services portal", "Licensing", "Payments"] },
      { name: "Gov Enterprise", desc: "Full digital government", features: ["All Starter", "Registries", "Workflows", "Integration", "Analytics"] },
    ],
    deployment: ["Government Cloud", "On-Premise", "Air-Gapped"],
    color: "amber",
    accentClass: "text-amber-400 border-amber-500/20 bg-amber-500/5",
  },
  "cyidentity": {
    name: "CyIdentity",
    tagline: "Identity & Access Management Platform",
    category: "identity",
    categoryLabel: "CyIdentity Platform",
    description:
      "Enterprise-grade IAM platform implementing OAuth 2.1, OpenID Connect, passkeys, SSO, RBAC, ABAC, and Zero Trust architecture across all CyberCom platforms.",
    features: [
      "OAuth 2.1 + PKCE authorization",
      "OpenID Connect (OIDC)",
      "Passkeys & FIDO2 support",
      "Single Sign-On (SSO)",
      "Role-Based Access Control (RBAC)",
      "Attribute-Based Access Control (ABAC)",
      "Zero Trust architecture",
      "MFA (TOTP, SMS, passkey)",
      "Device registration & management",
      "Audit logging & compliance",
    ],
    compliance: ["OAuth 2.1", "OIDC", "FIDO2", "WebAuthn"],
    editions: [
      { name: "Identity Core", desc: "OAuth 2.1 & SSO", features: ["OAuth 2.1", "OIDC", "SSO", "MFA"] },
      { name: "Identity Enterprise", desc: "Full Zero Trust IAM", features: ["All Core", "Passkeys", "RBAC/ABAC", "Zero Trust", "Audit"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise"],
    color: "violet",
    accentClass: "text-violet-400 border-violet-500/20 bg-violet-500/5",
  },
  "cyintegrationhub": {
    name: "CyIntegrationHub",
    tagline: "Healthcare & Enterprise Integration Middleware",
    category: "integration",
    categoryLabel: "CyIntegrationHub Platform",
    description:
      "Comprehensive integration middleware supporting FHIR, HL7 v2/v3, DICOM, REST, Kafka, EDI, SOAP, LDAP, and SFTP — the connective tissue of the CyberCom ecosystem.",
    features: [
      "FHIR R4/R5 integration engine",
      "HL7 v2.x & v3 processing",
      "DICOM worklist & result integration",
      "REST API orchestration",
      "Apache Kafka event streaming",
      "EDI X12 processing",
      "SOAP/web service bridging",
      "LDAP directory integration",
      "SFTP file exchange",
      "Real-time monitoring dashboard",
    ],
    compliance: ["FHIR R4", "IHE Profiles", "HL7", "DICOM"],
    editions: [
      { name: "Hub Core", desc: "REST & FHIR integration", features: ["REST", "FHIR", "Basic transforms"] },
      { name: "Hub Full", desc: "Full protocol support", features: ["All Core", "HL7", "Kafka", "EDI", "DICOM", "Monitoring"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "cyan",
    accentClass: "text-cyan-400 border-cyan-500/20 bg-cyan-500/5",
  },
  "cyai": {
    name: "CyAI",
    tagline: "Artificial Intelligence & Intelligent Automation Platform",
    category: "ai",
    categoryLabel: "CyAI Platform",
    description:
      "AI platform delivering clinical AI, government AI, enterprise automation, predictive analytics, and NLP across the CyberCom ecosystem. Advisory-only by design — no autonomous clinical decisions.",
    features: [
      "Clinical AI (diagnosis assistance, triage)",
      "Government AI (fraud detection, compliance)",
      "Enterprise AI (process automation)",
      "Predictive analytics engine",
      "Natural language processing (NLP/NER)",
      "Computer vision (radiology, pathology)",
      "AI model management & governance",
      "Explainable AI (XAI) reports",
      "Federated learning support",
      "Real-time inference API",
    ],
    compliance: ["ISO 42001 AI Ready", "GDPR", "Explainability standards"],
    editions: [
      { name: "AI Core", desc: "Predictive analytics & NLP", features: ["Analytics", "NLP", "APIs"] },
      { name: "AI Platform", desc: "Full AI & automation", features: ["All Core", "Clinical AI", "Computer vision", "Model governance"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise"],
    color: "pink",
    accentClass: "text-pink-400 border-pink-500/20 bg-pink-500/5",
  },
  "cydata": {
    name: "CyData",
    tagline: "Data Lakehouse & Analytics Platform",
    category: "data",
    categoryLabel: "CyData Platform",
    description:
      "Enterprise data platform providing lakehouse architecture, BI analytics, data governance, and population health analytics across all CyberCom data sources.",
    features: [
      "Data lakehouse architecture",
      "ETL/ELT pipelines",
      "Business intelligence dashboards",
      "Self-service analytics",
      "Data governance & cataloging",
      "Data quality management",
      "Population health analytics",
      "Real-time streaming analytics",
      "Predictive modeling",
      "Multi-tenant data isolation",
    ],
    compliance: ["GDPR", "ISO 27001 Ready"],
    editions: [
      { name: "Data Core", desc: "BI & analytics", features: ["BI dashboards", "ETL", "Basic governance"] },
      { name: "Data Enterprise", desc: "Full lakehouse platform", features: ["All Core", "Lakehouse", "Streaming", "ML integration"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud"],
    color: "teal",
    accentClass: "text-teal-400 border-teal-500/20 bg-teal-500/5",
  },
  "cyconnect": {
    name: "CyConnect",
    tagline: "Unified Communications & Collaboration Platform",
    category: "communications",
    categoryLabel: "CyConnect Platform",
    description:
      "Secure messaging, notifications, video, and collaboration platform integrated across the CyberCom ecosystem for healthcare, government, and enterprise contexts.",
    features: [
      "Secure clinical messaging (HIPAA-ready)",
      "Push & in-app notifications",
      "Video conferencing",
      "Team collaboration workspaces",
      "Document sharing",
      "Critical alert routing",
      "SMS & email gateway",
      "API-first architecture",
      "Audit logging",
      "Multi-tenant isolation",
    ],
    compliance: ["HIPAA Ready", "GDPR", "TLS 1.3 encryption"],
    editions: [
      { name: "Connect Core", desc: "Messaging & notifications", features: ["Messaging", "Notifications", "Alerts"] },
      { name: "Connect Full", desc: "Complete communications suite", features: ["All Core", "Video", "Collaboration", "SMS gateway"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise"],
    color: "orange",
    accentClass: "text-orange-400 border-orange-500/20 bg-orange-500/5",
  },
  "cyshop": {
    name: "CyShop",
    tagline: "Intelligent Retail & Commerce Platform for Every Business",
    category: "retail",
    categoryLabel: "CyShop Retail",
    description:
      "CyShop is a complete cloud-native retail and commerce platform built for restaurants, cafés, bakeries, grocery stores, supermarkets, and convenience stores. With KDS, online ordering, delivery management, AI-powered analytics, and CyberCom Platform integration, CyShop unifies every point of sale under one intelligent system.",
    features: [
      "Kitchen Display System (KDS) — real-time order routing to kitchen stations",
      "Online ordering — QR menu, web store, app ordering, aggregator integration",
      "Delivery management — driver dispatch, live tracking, zone pricing, ETA",
      "Omnichannel POS (cloud + offline resilience mode)",
      "Self-service kiosk & customer-facing display",
      "Table management & reservation system",
      "AI sales forecasting & demand prediction",
      "Real-time inventory management with auto-replenishment",
      "Multi-location & franchise management",
      "Customer loyalty, rewards & digital wallet",
      "Recipe management, ingredient costing & central kitchen",
      "MADA, Visa, Apple Pay, STC Pay, cash payment processing",
      "Staff management, shift scheduling & time attendance",
      "Business intelligence dashboards & daily reports",
      "Arabic & English bilingual interface (RTL/LTR)",
    ],
    compliance: ["PCI-DSS Ready", "VAT / ZATCA Compliant", "GS1 Barcoding", "GDPR Ready"],
    editions: [
      { name: "CyShop Starter", desc: "Single location, up to 3 terminals", features: ["Core POS", "Basic KDS", "Online ordering", "Inventory", "Sales reports"] },
      { name: "CyShop Business", desc: "Multi-location, delivery & analytics", features: ["All Starter", "Delivery management", "Multi-branch", "Loyalty program", "Staff management", "AI forecasting"] },
      { name: "CyShop Enterprise", desc: "Franchise & chain operations", features: ["All Business", "Central kitchen", "Franchise management", "Custom KDS routing", "API access", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "orange",
    accentClass: "text-cy-orange border-cy-orange/20 bg-cy-orange/5",
    workflows: [
      { step: "01", title: "Order Placed", desc: "Customer orders via POS, kiosk, QR menu, or delivery app. Single order stream regardless of channel." },
      { step: "02", title: "KDS Routing", desc: "Order auto-routes to the right kitchen station in real time. Prep timers start. No paper tickets." },
      { step: "03", title: "Kitchen Prep", desc: "Each station works its items independently. Bump bar confirms completion per station." },
      { step: "04", title: "Dispatch / Serve", desc: "Dine-in: runner notified. Delivery: driver assigned automatically. Estimated arrival shown to customer." },
      { step: "05", title: "Payment & Close", desc: "Split payments, wallets, loyalty redemption. VAT receipt auto-generated. Revenue syncs to CyCom ERP." },
    ],
    subProducts: [
      { name: "Retail", slug: "cyshop-retail", desc: "General retail, fashion, electronics, household" },
      { name: "Restaurant", slug: "cyshop-restaurant", desc: "Full-service restaurant & dine-in management" },
      { name: "Bakery & Café", slug: "cyshop-bakery", desc: "Recipe management, fresh production scheduling" },
      { name: "Coffee Shop", slug: "cyshop-coffee", desc: "Menu customization, loyalty cards, barista workflow" },
      { name: "Fast Food", slug: "cyshop-fastfood", desc: "KDS, queue management, drive-through, kiosk" },
      { name: "Grocery", slug: "cyshop-grocery", desc: "Weighted items, bulk pricing, supplier orders" },
      { name: "Supermarket", slug: "cyshop-supermarket", desc: "Self-checkout, multi-department, loyalty program" },
      { name: "Convenience Store", slug: "cyshop-convenience", desc: "Quick checkout, fuel management, kiosk mode" },
    ],
    aiFeatures: [
      { title: "Demand Forecasting", desc: "Predicts daily and weekly demand per SKU with 91% accuracy, reducing overstock and stockouts across all locations." },
      { title: "Waste Prevention", desc: "For F&B businesses: AI forecasts food prep quantities to minimize end-of-day waste and ingredient spoilage." },
      { title: "KDS Smart Routing", desc: "Learns prep times per item and station, automatically rebalancing load during rush hours to hit your SLA target." },
      { title: "Delivery ETA Prediction", desc: "Predicts accurate delivery times using driver location, traffic, and historical route data to reduce late deliveries." },
      { title: "Menu Engineering AI", desc: "Identifies high-margin, high-velocity items and surfaces menu optimization opportunities to managers." },
      { title: "Customer Insights", desc: "Segments customers by spend, frequency, and preferences for targeted loyalty campaigns and promotions." },
    ],
    erpModules: [
      { module: "Finance & Accounting", desc: "POS revenue recognition, GL integration, ZATCA e-Invoice, VAT posting, and daily cash-up reconciliation." },
      { module: "Real-Time Inventory", desc: "Live stock levels across all locations, auto-replenishment alerts, and inter-branch transfer orders." },
      { module: "Procurement & Purchasing", desc: "Supplier purchase orders, goods receiving, cost of goods tracking, and supplier portal." },
      { module: "HR & Payroll", desc: "Staff scheduling, shift management, attendance, and WPS-compliant payroll for all outlets." },
      { module: "Customer CRM & Loyalty", desc: "Customer profiles, loyalty point engine, spend analytics, and segmented campaign management." },
      { module: "Delivery Operations", desc: "Driver management, zone configuration, delivery cost tracking, and third-party courier reconciliation." },
    ],
    modules: [
      { name: "Point of Sale (POS)", category: "operations", desc: "Cloud-based POS with offline resilience — process sales, split payments, print receipts, and manage returns.", roles: ["Cashier", "Supervisor"] },
      { name: "Kitchen Display System (KDS)", category: "operations", desc: "Real-time order routing to kitchen stations with prep timers, bump bar, and station-level completion tracking.", roles: ["Kitchen Staff", "Chef"] },
      { name: "Table Management & Reservations", category: "operations", desc: "Interactive floor plan, table status, cover count, waitlist management, and reservation confirmation.", roles: ["Host", "Waiter", "Manager"] },
      { name: "Self-Service Kiosk", category: "operations", desc: "Customer-facing order and payment kiosk with product images, customizations, and upsell prompts.", roles: ["Customer"] },
      { name: "Online Ordering", category: "operations", desc: "QR menu, web store, and mobile app ordering with aggregator integration (Talabat, Careem, Jahez).", roles: ["Customer", "Manager"] },
      { name: "Delivery Management", category: "operations", desc: "Driver dispatch, live GPS tracking, zone pricing, estimated delivery time, and delivery proof of completion.", roles: ["Driver", "Delivery Manager"] },
      { name: "Customer Loyalty & Rewards", category: "operations", desc: "Points engine, digital wallet, reward redemption, tier management, and targeted promotions.", roles: ["Customer", "Manager"] },
      { name: "Finance & Accounting", category: "erp", desc: "POS revenue recognition, GL posting, ZATCA e-Invoice, VAT calculation, and daily cash-up reconciliation.", roles: ["Finance Manager", "Store Manager"] },
      { name: "Real-Time Inventory", category: "erp", desc: "Live stock levels across all locations, auto-replenishment alerts, wastage tracking, and inter-branch transfers.", roles: ["Inventory Manager", "Store Manager"] },
      { name: "Procurement & Purchasing", category: "erp", desc: "Supplier POs, goods receiving, cost of goods tracking, three-way matching, and supplier portal.", roles: ["Procurement Manager", "Store Manager"] },
      { name: "HR & Staff Management", category: "erp", desc: "Employee records, contracts, org hierarchy, onboarding workflows, and performance tracking.", roles: ["HR Manager", "Store Manager"] },
      { name: "Payroll (WPS)", category: "erp", desc: "Shift-based payroll, tip distribution, WPS file generation, overtime, and payslip distribution.", roles: ["Finance Manager", "HR Manager"] },
      { name: "Attendance & Shift Scheduling", category: "erp", desc: "Clock-in/out tracking, shift scheduling, leave requests, and overtime calculation for all outlet staff.", roles: ["Store Manager", "HR Manager", "All Staff"] },
      { name: "Customer CRM & Engagement", category: "erp", desc: "Customer profiles, spend analytics, loyalty segmentation, and campaign management.", roles: ["Marketing Manager", "Store Manager"] },
      { name: "Demand Forecasting", category: "ai", desc: "Predicts daily and weekly demand per SKU with 91% accuracy — reduces overstock and stockouts.", roles: ["Inventory Manager", "Store Manager"] },
      { name: "Waste Prevention AI", category: "ai", desc: "Forecasts F&B prep quantities to minimize end-of-day waste and ingredient spoilage.", roles: ["Chef", "Kitchen Manager"] },
      { name: "KDS Smart Routing", category: "ai", desc: "Learns prep times per item and station, rebalancing kitchen load during rush hours to hit SLA targets.", roles: ["Kitchen Manager", "Chef"] },
      { name: "Delivery ETA Prediction", category: "ai", desc: "Predicts accurate delivery times using driver location, traffic, and historical route data.", roles: ["Delivery Manager", "Customer"] },
      { name: "Menu Engineering AI", category: "ai", desc: "Identifies high-margin, high-velocity items and surfaces menu optimization opportunities to management.", roles: ["Store Manager", "Operations Manager"] },
      { name: "Customer Insights", category: "ai", desc: "Segments customers by spend, frequency, and preferences for targeted loyalty campaigns.", roles: ["Marketing Manager", "Store Manager"] },
    ],
    roleWorkflows: [
      {
        role: "Cashier",
        description: "Front-line POS operations: order entry, payment processing, receipt, and loyalty redemption.",
        steps: [
          { action: "Open or Recall Order", detail: "Start a new transaction or recall a table/kiosk order. Products scanned by barcode or selected from menu grid." },
          { action: "Customize & Add Items", detail: "Add modifiers, size options, special instructions, and combo items. KDS order auto-sent to kitchen on confirm." },
          { action: "Apply Discount or Loyalty", detail: "Apply manager discount, scan loyalty card, or redeem points. System validates reward eligibility automatically." },
          { action: "Process Payment", detail: "Accept MADA, Visa, Apple Pay, STC Pay, cash, or split payment across methods. Change calculated automatically." },
          { action: "Receipt & Close", detail: "Print or send digital receipt. VAT breakdown shown. Transaction synced to Finance GL in real time." },
        ],
      },
      {
        role: "Kitchen Staff",
        description: "KDS workflow: receiving orders, managing prep, bumping completion, and alerting delays.",
        steps: [
          { action: "View Incoming Orders", detail: "Orders appear on KDS screen in real time as Cashier confirms. Color coding shows channel (dine-in/delivery/pickup)." },
          { action: "Accept & Start Prep", detail: "Tap order to start prep timer. Each station sees only its items — station-level routing prevents confusion." },
          { action: "Coordinate Across Stations", detail: "Grill, fryer, assembly stations work in parallel. KDS synchronizes completion for simultaneous plating." },
          { action: "Bump & Complete", detail: "Bump bar confirms item complete. Order status updates on dine-in runner screen and delivery app automatically." },
          { action: "Delay Alert", detail: "If prep time exceeds SLA, KDS flashes alert to kitchen supervisor for immediate intervention." },
        ],
      },
      {
        role: "Delivery Driver",
        description: "Order pickup, navigation, delivery confirmation, and cash/card reconciliation.",
        steps: [
          { action: "Accept Delivery Assignment", detail: "Driver app shows new order with pickup location, customer address, and estimated delivery time." },
          { action: "Pickup from Kitchen", detail: "Scan order barcode at pickup. System confirms items packaged, driver assigned, and ETA communicated to customer." },
          { action: "Navigate to Customer", detail: "Built-in navigation with live traffic. Delivery zone restrictions enforced. Customer notified when driver is near." },
          { action: "Confirm Delivery", detail: "Capture customer signature or OTP, take photo proof. Mark delivered in app. Cash collected and logged if applicable." },
        ],
      },
      {
        role: "Store Manager",
        description: "Daily operations: inventory, staff, performance dashboards, and end-of-day close.",
        steps: [
          { action: "Morning Briefing Dashboard", detail: "Yesterday's revenue, top-selling items, low-stock alerts, pending supplier orders, and staff schedule overview." },
          { action: "Inventory Management", detail: "Confirm opening stock counts, approve reorder requests, receive supplier deliveries, and update wastage logs." },
          { action: "Staff & Shift Management", detail: "View today's roster, approve shift swaps, record attendance, and manage break schedules for all staff." },
          { action: "Live Sales Monitoring", detail: "Real-time POS sales, payment method breakdown, table occupancy, KDS performance, and delivery status." },
          { action: "End-of-Day Close", detail: "Cash drawer reconciliation, Z-report generation, ZATCA e-invoice summary, and daily revenue sync to Finance." },
        ],
      },
      {
        role: "Franchise / Chain Manager",
        description: "Multi-branch oversight: cross-location performance, menu management, and consolidated reporting.",
        steps: [
          { action: "Multi-Branch Dashboard", detail: "Consolidated revenue, top-performing locations, underperformers, and inventory health across all outlets." },
          { action: "Central Menu Management", detail: "Push menu updates, price changes, new items, and promotions to all branches simultaneously." },
          { action: "Inventory & Procurement", detail: "Approve inter-branch transfers, manage central kitchen supply, and review supplier costs across the chain." },
          { action: "HR & Payroll Overview", detail: "Review staffing levels per branch, approve bulk payroll runs, and compare labor cost ratios across locations." },
        ],
      },
    ],
  },
  "cycitizen": {
    name: "CyCitizen",
    tagline: "Citizen Digital Experience Platform",
    category: "citizen",
    categoryLabel: "CyCitizen Platform",
    description:
      "Complete citizen digital experience platform providing a citizen portal, digital wallet, national identity services, and government service delivery.",
    features: [
      "Citizen self-service portal",
      "Digital wallet & documents",
      "National identity verification",
      "Government service catalog",
      "Online payments",
      "Document authentication",
      "Appointment booking for gov services",
      "Mobile-first (iOS & Android)",
      "Biometric authentication",
      "Offline-capable PWA",
    ],
    compliance: ["eIDAS", "GDPR", "FIDO2", "ISO 27001 Ready"],
    editions: [
      { name: "Citizen Core", desc: "Portal & payments", features: ["Portal", "Payments", "Services"] },
      { name: "Citizen Full", desc: "Complete citizen platform", features: ["All Core", "Digital wallet", "National ID", "Biometrics"] },
    ],
    deployment: ["Government Cloud", "On-Premise"],
    color: "indigo",
    accentClass: "text-indigo-400 border-indigo-500/20 bg-indigo-500/5",
  },
  "cycom-finance": {
    name: "CyCom Finance",
    tagline: "Unified Financial Management & Budgeting",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "CyCom Finance provides unified general ledger control, cash flow monitoring, multi-currency processing, and budgeting capabilities across enterprise divisions, fully compliant with IFRS standards.",
    features: [
      "Bilingual general ledger control",
      "Real-time cash flow monitoring",
      "Multi-currency conversion engine",
      "Dynamic budgeting & forecasting",
      "Auditable journals & ledger entries",
      "IFRS/GAAP financial statements",
    ],
    compliance: ["IFRS", "GAAP", "SOC 1 & SOC 2 Ready"],
    editions: [
      { name: "Finance Starter", desc: "Core ledger & budgeting", features: ["General ledger", "Basic budgeting", "Standard reporting"] },
      { name: "Finance Enterprise", desc: "Advanced cash flow & multi-currency", features: ["All Starter features", "Multi-currency processing", "Automated reconciliation", "Consolidated statements"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-accounting": {
    name: "CyCom Accounting",
    tagline: "Accounts Payable, Receivable & Tax Compliance",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Manage accounts payable, receivable, and automatic tax calculations. Complete support for local VAT/tax reporting requirements and billing reconciliation.",
    features: [
      "Accounts Payable (AP) matching",
      "Accounts Receivable (AR) invoicing",
      "Automatic VAT & sales tax calculation",
      "Local tax compliance export utilities",
      "Bank statement auto-reconciliation",
      "Aging schedules and collections control",
    ],
    compliance: ["VAT compliant", "Tax authority integration guidelines"],
    editions: [
      { name: "Accounting Core", desc: "AP, AR, and basic tax filing", features: ["AP ledger", "AR invoicing", "Standard tax calculation"] },
      { name: "Accounting Advanced", desc: "Enterprise invoicing and local integration", features: ["All Core features", "E-invoicing integration", "Auto-reconciliation", "Multi-tax-entity support"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-procurement": {
    name: "CyCom Procurement",
    tagline: "Sourcing & Supplier Relationship Management",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Streamline procurement from purchase requisitions to purchase orders (PO), vendor bidding, and three-way invoice matching.",
    features: [
      "Purchase requisition workflows",
      "Supplier bidding & quotation management",
      "Automated Purchase Order (PO) creation",
      "Three-way invoice matching checks",
      "Supplier scorecards & performance",
      "Contract term monitoring",
    ],
    compliance: ["ISO 9001 quality guidelines", "Anti-bribery audit tracing"],
    editions: [
      { name: "Procurement Starter", desc: "Purchase requests & orders", features: ["Requisition workflow", "PO creation", "Basic vendor listing"] },
      { name: "Procurement Enterprise", desc: "Full bidding & contract management", features: ["All Starter features", "Vendor portal access", "Bidding engine", "SLA tracking", "Contract renewals"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-inventory": {
    name: "CyCom Inventory",
    tagline: "Multi-Warehouse Tracking & Inventory Control",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Manage stock across multiple warehouses. Features batch/serial number tracking, FIFO/FEFO costing methods, and auto-replenishment notifications.",
    features: [
      "Multi-warehouse inventory tracking",
      "Batch & serial number verification",
      "FIFO & FEFO costing calculations",
      "Barcode scanning integration",
      "Auto-replenishment threshold alerts",
      "Stock transfer tracking",
    ],
    compliance: ["GS1 Barcoding standards", "FDA CFR Title 21 compliant tracking"],
    editions: [
      { name: "Inventory Standard", desc: "Single warehouse, batch tracking", features: ["Core stock tracking", "Batch tracking", "Barcode scanning"] },
      { name: "Inventory Enterprise", desc: "Multi-warehouse, cost valuation", features: ["All Standard features", "Multi-warehouse mapping", "FEFO auto-allocation", "Reorder algorithms"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-hr": {
    name: "CyCom HR",
    tagline: "Strategic Human Resource & Talent Management",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Core HR operations including employee records management, performance tracking, dynamic organizational hierarchy mapping, and onboarding workflows.",
    features: [
      "Secure employee records database",
      "Org chart & hierarchy mapping",
      "Performance evaluation templates",
      "Onboarding & offboarding workflows",
      "Time and attendance tracking",
      "Employee self-service (ESS) portal",
    ],
    compliance: ["GDPR data privacy standards", "Local labor law record keeping"],
    editions: [
      { name: "HR Core", desc: "Employee database & records", features: ["Employee database", "ESS portal", "Attendance tracking"] },
      { name: "HR Strategic", desc: "Recruiting & performance management", features: ["All Core features", "Performance management", "Onboarding checklists", "Custom org charts"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-payroll": {
    name: "CyCom Payroll",
    tagline: "Bilingual Salary Processing & Compliance",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Bilingual payroll processing system supporting salary calculations, local labor compliance checks (such as WPS in the GCC), benefit tracking, and tax withholding.",
    features: [
      "Bilingual payroll generation (AR/EN)",
      "Wage Protection System (WPS) export",
      "Social security & pension calculations",
      "Overtime & allowance formulas",
      "End of Service (EOS) calculation",
      "Pay slip delivery via ESS portal",
    ],
    compliance: ["WPS compliant (GCC)", "Social security tax withholding codes"],
    editions: [
      { name: "Payroll Core", desc: "Monthly run & standard allowances", features: ["Payroll generation", "Pay slip delivery", "Standard tax withholding"] },
      { name: "Payroll Enterprise", desc: "Multi-country & local compliance integrations", features: ["All Core features", "WPS integration", "Social security automation", "Custom allowances formulas"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-crm": {
    name: "CyCom CRM",
    tagline: "Lead Pipeline & Customer Relationship Management",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Track leads, manage sales pipelines, customer interactions, service support tickets, and client portals.",
    features: [
      "Interactive sales pipeline dashboard",
      "Contact & lead profile management",
      "Customer interaction history log",
      "Support ticket queue management",
      "Contract renewal reminder engine",
      "Customer portal integration",
    ],
    compliance: ["GDPR consent management", "SOC 2 security parameters"],
    editions: [
      { name: "CRM Starter", desc: "Lead and contact management", features: ["Contact directory", "Pipeline dashboard", "Task reminders"] },
      { name: "CRM Enterprise", desc: "Customer ticketing and portal mapping", features: ["All Starter features", "Ticketing system", "Customer portal integration", "Automated marketing rules"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-assets": {
    name: "CyCom Assets",
    tagline: "Fixed Asset Registry & Depreciation Scheduling",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Fixed assets register. Automatic depreciation calculations (straight-line, double-declining), maintenance scheduling, and location tracking.",
    features: [
      "Fixed asset registry database",
      "Straight-line & declining depreciation",
      "Asset maintenance scheduling alerts",
      "Barcoded asset location mapping",
      "Asset disposal & retirement records",
      "Automated financial journal postings",
    ],
    compliance: ["IFRS 16 lease standards", "IAS 16 property, plant, and equipment"],
    editions: [
      { name: "Assets Core", desc: "Asset registry & depreciation", features: ["Registry database", "Standard depreciation", "Journal posting"] },
      { name: "Assets Advanced", desc: "Maintenance management & location audits", features: ["All Core features", "Maintenance alerts", "GPS/Barcode tracking", "IFRS 16 compliant leases"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud", "On-Premise"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-manufacturing": {
    name: "CyCom Manufacturing",
    tagline: "Production Scheduling & Bill of Materials",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Optimize production lines. Features Bill of Materials (BOM) management, material requirements planning (MRP), and factory scheduling tools.",
    features: [
      "Multi-level Bill of Materials (BOM)",
      "Material Requirements Planning (MRP)",
      "Production order status tracking",
      "Shop floor scheduling dashboards",
      "Quality assurance inspection checksheets",
      "Machine capacity planning logs",
    ],
    compliance: ["ISO 9001 quality audits", "GMP compliance readiness"],
    editions: [
      { name: "Manufacturing Standard", desc: "BOM management & production tracking", features: ["BOM database", "Production orders", "Quality checklists"] },
      { name: "Manufacturing Advanced", desc: "Full MRP and capacity scheduling", features: ["All Standard features", "MRP calculator", "Capacity planning", "Factory IoT interfaces"] },
    ],
    deployment: ["Private Cloud", "On-Premise", "Hybrid"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-retail": {
    name: "CyCom Retail",
    tagline: "Point of Sale (POS) & Checkout Operations",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Manage retail checkouts. Secure POS interfaces, offline transactional capabilities, loyalty programs, and inventory synchronization.",
    features: [
      "Secure POS checkout screen",
      "Offline transactional resilience",
      "Real-time inventory synchronization",
      "Loyalty rewards & customer history",
      "Multi-payment terminal interfaces",
      "Shift reconciliation reporting",
    ],
    compliance: ["PCI DSS payment standards", "VAT e-invoicing compliance"],
    editions: [
      { name: "Retail Core", desc: "Single terminal POS operations", features: ["POS screen", "Shift reconciliation", "VAT invoicing"] },
      { name: "Retail Enterprise", desc: "Multi-store and loyalty management", features: ["All Core features", "Multi-store dashboard", "Loyalty engine", "Offline sync server"] },
    ],
    deployment: ["SaaS Cloud", "Hybrid Local POS Server"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },
  "cycom-bi": {
    name: "CyCom BI",
    tagline: "Business Intelligence & Drag-and-Drop Dashboards",
    category: "erp",
    categoryLabel: "CyCom Enterprise",
    description: "Create visual reports using drag-and-drop dashboard tools. Access cross-module business intelligence and share metrics.",
    features: [
      "Drag-and-drop dashboard editor",
      "Cross-module ERP data access",
      "Prebuilt financial KPI widgets",
      "Scheduled report delivery engine",
      "Role-based visualization control",
      "Excel/CSV data export engines",
    ],
    compliance: ["ISO 27001 info security guidelines", "GDPR privacy scopes"],
    editions: [
      { name: "BI Standard", desc: "View dashboards & export reports", features: ["Prebuilt dashboards", "Export tools", "Scheduled delivery"] },
      { name: "BI Creator", desc: "Custom dashboards & data sources", features: ["All Standard features", "Drag-and-drop editor", "Custom SQL/CyData connections", "Embeddable analytics"] },
    ],
    deployment: ["SaaS Cloud", "Private Cloud"],
    color: "blue",
    accentClass: "text-blue-400 border-blue-500/20 bg-blue-500/5",
  },

  // ── CyShop Business Types ──────────────────────────────────────
  "cyshop-retail": {
    name: "CyShop Retail",
    tagline: "Smart POS for General Retail — Fashion, Electronics & More",
    category: "retail",
    categoryLabel: "CyShop Retail",
    description: "CyShop Retail is a cloud-native POS and inventory management system purpose-built for general retail: fashion, electronics, household goods, and accessories. Supports barcode scanning, multi-size/color variants, customer loyalty, and real-time inventory across branches.",
    features: [
      "Multi-variant product catalog (size, color, SKU)",
      "Barcode / QR scan checkout",
      "Customer loyalty & reward points",
      "Real-time inventory across branches",
      "Staff sales performance tracking",
      "Discount & promotion engine",
      "End-of-day cashier reconciliation",
      "Supplier order management",
      "Customer purchase history & CRM",
      "Arabic & English bilingual interface (RTL/LTR)",
    ],
    compliance: ["PCI-DSS Ready", "VAT Compliant", "GS1 Barcoding", "GDPR Ready"],
    editions: [
      { name: "Starter", desc: "Single store, up to 3 terminals", features: ["Core POS", "Inventory", "Barcode scan", "Sales reports"] },
      { name: "Business", desc: "Multi-branch retail operations", features: ["All Starter", "Multi-branch", "Loyalty program", "Staff management"] },
      { name: "Enterprise", desc: "Retail chain & franchise", features: ["All Business", "Franchise management", "AI forecasting", "API access", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "orange",
    accentClass: "text-cy-orange border-cy-orange/20 bg-cy-orange/5",
  },
  "cyshop-restaurant": {
    name: "CyShop Restaurant",
    tagline: "Complete Restaurant Management — Dine-in, Takeaway & Delivery",
    category: "retail",
    categoryLabel: "CyShop Retail",
    description: "CyShop Restaurant handles every aspect of restaurant operations: table management, waiter ordering app, kitchen display system (KDS), delivery integration, and end-of-shift reporting. Built for full-service restaurants, bistros, and casual dining.",
    features: [
      "Table & reservation management",
      "Waiter mobile ordering app",
      "Kitchen display system (KDS)",
      "Dine-in, takeaway & delivery modes",
      "Recipe costing & portion control",
      "Modifier & add-on item support",
      "Real-time menu updates",
      "Split bill & multi-payment types",
      "Delivery integration (Talabat, Careem)",
      "Arabic & English bilingual interface (RTL/LTR)",
    ],
    compliance: ["PCI-DSS Ready", "VAT Compliant", "HACCP Ready", "GDPR Ready"],
    editions: [
      { name: "Starter", desc: "Single restaurant location", features: ["Table POS", "Kitchen display", "Daily reports"] },
      { name: "Business", desc: "Multi-outlet dining group", features: ["All Starter", "Multi-outlet", "Delivery integration", "Recipe costing"] },
      { name: "Enterprise", desc: "Restaurant chain operations", features: ["All Business", "Central menu control", "AI demand forecast", "API access", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "orange",
    accentClass: "text-cy-orange border-cy-orange/20 bg-cy-orange/5",
  },
  "cyshop-bakery": {
    name: "CyShop Bakery",
    tagline: "Bakery & Patisserie Management — Recipe, Production & Sales",
    category: "retail",
    categoryLabel: "CyShop Retail",
    description: "CyShop Bakery is built for artisan bakeries, patisseries, and confectioneries. Manage recipes, ingredient batches, fresh production schedules, and retail counters — all in one system with real-time ingredient costing.",
    features: [
      "Recipe & ingredient costing engine",
      "Fresh production scheduling",
      "Batch tracking & expiry management",
      "Daily/weekly production forecast",
      "Retail counter POS with item photos",
      "Supplier ingredient ordering",
      "Waste & yield reporting",
      "Custom cake & order management",
      "Staff shift scheduling",
      "Arabic & English bilingual interface (RTL/LTR)",
    ],
    compliance: ["PCI-DSS Ready", "VAT Compliant", "HACCP Ready", "GDPR Ready"],
    editions: [
      { name: "Starter", desc: "Single bakery shop", features: ["Recipe management", "Counter POS", "Daily production log"] },
      { name: "Business", desc: "Multi-branch bakery", features: ["All Starter", "Central production", "Branch stock transfer", "Supplier orders"] },
      { name: "Enterprise", desc: "Bakery chain & commissary", features: ["All Business", "Central kitchen", "AI production forecast", "API access", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "orange",
    accentClass: "text-cy-orange border-cy-orange/20 bg-cy-orange/5",
  },
  "cyshop-coffee": {
    name: "CyShop Coffee",
    tagline: "Coffee Shop POS — Menu, Loyalty & Barista Workflow",
    category: "retail",
    categoryLabel: "CyShop Retail",
    description: "CyShop Coffee is designed for specialty coffee shops, café chains, and beverage outlets. Streamline barista workflows with a dedicated KDS, manage loyalty cards, customize drink modifiers, and track cup-by-cup ingredient usage.",
    features: [
      "Barista-focused KDS display",
      "Drink modifier & customization engine",
      "Loyalty card & stamp programs",
      "Customer name on orders",
      "Ingredient usage per cup tracking",
      "Mobile ordering QR code",
      "Split payment (cash + card + wallet)",
      "Shift reporting & cash management",
      "Menu board digital integration",
      "Arabic & English bilingual interface (RTL/LTR)",
    ],
    compliance: ["PCI-DSS Ready", "VAT Compliant", "GDPR Ready"],
    editions: [
      { name: "Starter", desc: "Single coffee shop", features: ["Barista POS", "Modifier system", "Shift reports"] },
      { name: "Business", desc: "Multi-branch café chain", features: ["All Starter", "Loyalty program", "Menu board control", "Branch analytics"] },
      { name: "Enterprise", desc: "Large chain & franchise", features: ["All Business", "Franchise control", "AI demand forecast", "API access", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "orange",
    accentClass: "text-cy-orange border-cy-orange/20 bg-cy-orange/5",
  },
  "cyshop-fastfood": {
    name: "CyShop Fast Food",
    tagline: "Fast Food POS — Queue, Kitchen Display & Drive-Through",
    category: "retail",
    categoryLabel: "CyShop Retail",
    description: "CyShop Fast Food powers quick-service restaurants (QSR) with high-speed checkout, queue management, kitchen display systems, and drive-through integration. Designed for volume and speed — handle hundreds of orders per hour.",
    features: [
      "High-speed checkout (under 3 seconds)",
      "Kitchen display system (KDS)",
      "Drive-through order management",
      "Self-service kiosk integration",
      "Combo meal & upsell engine",
      "Queue number display system",
      "Peak hour performance analytics",
      "Delivery aggregator integration",
      "Shift & cash management",
      "Arabic & English bilingual interface (RTL/LTR)",
    ],
    compliance: ["PCI-DSS Ready", "VAT Compliant", "HACCP Ready", "GDPR Ready"],
    editions: [
      { name: "Starter", desc: "Single QSR location", features: ["Fast POS", "KDS", "Basic reports"] },
      { name: "Business", desc: "Multi-location QSR chain", features: ["All Starter", "Drive-through", "Self-service kiosk", "Central menu"] },
      { name: "Enterprise", desc: "Franchise & large chain", features: ["All Business", "Franchise control", "AI demand forecast", "API access", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "orange",
    accentClass: "text-cy-orange border-cy-orange/20 bg-cy-orange/5",
  },
  "cyshop-grocery": {
    name: "CyShop Grocery",
    tagline: "Grocery Store Management — Weighted Items, Bulk & Supplier Orders",
    category: "retail",
    categoryLabel: "CyShop Retail",
    description: "CyShop Grocery handles the unique requirements of grocery stores: weighted items, scale integration, bulk pricing, perishable expiry management, and supplier order automation. Ideal for independent grocers and neighborhood markets.",
    features: [
      "Weight scale POS integration",
      "Perishable & expiry management",
      "Bulk pricing & quantity discounts",
      "Supplier order automation",
      "Category & aisle management",
      "Customer account & credit",
      "Barcode label printing",
      "Real-time stock alerts",
      "Daily fresh receiving log",
      "Arabic & English bilingual interface (RTL/LTR)",
    ],
    compliance: ["PCI-DSS Ready", "VAT Compliant", "GS1 Barcoding", "GDPR Ready"],
    editions: [
      { name: "Starter", desc: "Small grocery store", features: ["Core POS", "Scale integration", "Stock alerts"] },
      { name: "Business", desc: "Growing grocery market", features: ["All Starter", "Supplier orders", "Customer credit", "Expiry tracking"] },
      { name: "Enterprise", desc: "Grocery chain & market group", features: ["All Business", "Multi-branch", "AI reorder forecast", "API access", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "orange",
    accentClass: "text-cy-orange border-cy-orange/20 bg-cy-orange/5",
  },
  "cyshop-supermarket": {
    name: "CyShop Supermarket",
    tagline: "Supermarket Platform — Self-Checkout, Multi-Department & Loyalty",
    category: "retail",
    categoryLabel: "CyShop Retail",
    description: "CyShop Supermarket is a full-featured platform for mid-to-large supermarkets: multi-department management, self-checkout terminals, loyalty program, promotions engine, and department-level P&L reporting. Handles thousands of SKUs across multiple cashier lanes simultaneously.",
    features: [
      "Multi-cashier lane management",
      "Self-checkout terminal support",
      "Department-level inventory & P&L",
      "Promotions & price rollback engine",
      "Loyalty card & points program",
      "Wholesale & retail dual pricing",
      "Age verification for restricted items",
      "Central buying & supplier management",
      "End-of-day & shift reconciliation",
      "Arabic & English bilingual interface (RTL/LTR)",
    ],
    compliance: ["PCI-DSS Ready", "VAT Compliant", "GS1 Barcoding", "GDPR Ready"],
    editions: [
      { name: "Business", desc: "Single supermarket", features: ["Multi-lane POS", "Department inventory", "Loyalty program", "Promotion engine"] },
      { name: "Enterprise", desc: "Supermarket chain", features: ["All Business", "Self-checkout", "Central buying", "Multi-branch BI"] },
      { name: "Hypermarket", desc: "Large format & hypermarket", features: ["All Enterprise", "AI demand planning", "Vendor portals", "API access", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "orange",
    accentClass: "text-cy-orange border-cy-orange/20 bg-cy-orange/5",
  },
  "cyshop-convenience": {
    name: "CyShop Convenience",
    tagline: "Convenience Store POS — Fast Checkout, Kiosk & Fuel Management",
    category: "retail",
    categoryLabel: "CyShop Retail",
    description: "CyShop Convenience is built for petrol station shops, 24/7 convenience stores, and kiosk operations. Features rapid checkout, fuel pump integration, overnight mode, and compact touchscreen POS that works even in offline mode.",
    features: [
      "High-speed compact POS terminal",
      "Fuel pump integration",
      "Kiosk & self-service mode",
      "24/7 overnight shift support",
      "Offline mode (sync on reconnect)",
      "Age verification for restricted items",
      "Lottery & prepaid card sales",
      "Quick item barcode lookup",
      "Daily safe count & cash management",
      "Arabic & English bilingual interface (RTL/LTR)",
    ],
    compliance: ["PCI-DSS Ready", "VAT Compliant", "GDPR Ready"],
    editions: [
      { name: "Starter", desc: "Single convenience location", features: ["Compact POS", "Offline mode", "Daily reports"] },
      { name: "Business", desc: "Petrol station with shop", features: ["All Starter", "Fuel pump integration", "Shift management", "Supplier orders"] },
      { name: "Enterprise", desc: "Convenience chain & franchise", features: ["All Business", "Multi-location BI", "AI restock alerts", "API access", "24/7 SLA"] },
    ],
    deployment: ["SaaS Cloud", "On-Premise", "Hybrid"],
    color: "orange",
    accentClass: "text-cy-orange border-cy-orange/20 bg-cy-orange/5",
  },
  "cydeveloper": {
    name: "CyDeveloper",
    tagline: "Developer Platform — APIs, SDKs & Integration Tools for the CyberCom Ecosystem",
    category: "developer",
    categoryLabel: "CyDeveloper Platform",
    description:
      "CyDeveloper is CyberCom's unified developer platform — giving engineering teams full programmatic access to every CyberCom product through REST APIs, FHIR R4/R5 endpoints, webhooks, and typed SDKs. Build custom integrations, extend clinical workflows, automate ERP operations, or embed CyberCom data into your own applications.",
    features: [
      "FHIR R4/R5 REST API across all CyMed modules",
      "OpenAPI 3.1 specs with interactive sandbox",
      "OAuth 2.1 / OIDC client app registration",
      "Webhook subscriptions with HMAC-SHA256 signing",
      "Typed SDKs: Python, TypeScript/JS, Java",
      "CyIntegrationHub — low-code connector builder",
      "Developer console with live request logs",
      "Rate limit & quota dashboard per API key",
      "CyAI API — advisory model endpoints",
      "Staging sandbox with synthetic patient data",
    ],
    compliance: ["FHIR R4", "FHIR R5", "OAuth 2.1", "OpenID Connect", "SMART on FHIR", "OpenAPI 3.1"],
    editions: [
      { name: "Free Tier",   desc: "For individual developers & prototyping", features: ["Sandbox environment", "5,000 API calls/month", "Community support", "Public documentation"] },
      { name: "Build",       desc: "For startups & ISVs building integrations", features: ["All Free features", "100K API calls/month", "Webhook subscriptions", "SDK access", "Email support"] },
      { name: "Enterprise",  desc: "For enterprise integrators & OEMs",        features: ["All Build features", "Unlimited API calls", "Dedicated staging tenant", "SLA 99.9%", "Dedicated engineer"] },
    ],
    deployment: ["SaaS API", "Private API Gateway", "On-Premise"],
    color: "violet",
    accentClass: "text-violet-400 border-violet-500/20 bg-violet-500/5",
  },
};

const WORKFLOW_DATA: Record<string, { step: number; title: string; desc: string }[]> = {
  "cymed": [
    { step: 1, title: "Choose & Configure Module", desc: "Select CyMed products (Clinic, Hospital, Lab, Pharmacy, etc.) and configure for your facility type and specialty." },
    { step: 2, title: "Provision Tenant & Users", desc: "CyIdentity provisions your organization's tenant with role-based access for providers, nurses, staff, and administrators." },
    { step: 3, title: "Migrate & Integrate", desc: "Import existing patient records via FHIR or CSV migration tools. Connect lab analyzers, PACS, and external systems via CyIntegrationHub." },
    { step: 4, title: "Clinical Validation & Training", desc: "Complete UAT for all clinical workflows. Train staff using the CyberCom Academy curriculum." },
    { step: 5, title: "Go Live & Expand", desc: "Launch with hypercare support. Add additional modules as your facility grows — no data migration needed." },
  ],
  "cymed-clinic": [
    { step: 1, title: "Patient Registration", desc: "Staff registers patient with demographic data, insurance, and national ID. MRN auto-generated, FHIR Patient resource created." },
    { step: 2, title: "Appointment Booking", desc: "Patient or staff books appointment via portal or front desk. Intelligent scheduling assigns provider and room." },
    { step: 3, title: "Clinical Consultation", desc: "Provider conducts consultation with ICD-11 coded chief complaint, vitals, SOAP notes, and clinical decision support." },
    { step: 4, title: "Orders & Prescriptions", desc: "Provider issues lab orders (FHIR ServiceRequest), imaging orders, and e-prescriptions via FHIR MedicationRequest." },
    { step: 5, title: "Billing & Collection", desc: "Revenue cycle module generates claim, verifies insurance, submits to payor, and posts payment with ICD-11/CPT coding." },
  ],
  "cymed-hospital": [
    { step: 1, title: "Admission (ADT)", desc: "Patient admitted via ED or pre-admission. ADT event fires HL7 notification to all subscribed systems. Bed assigned." },
    { step: 2, title: "Inpatient Assessment", desc: "Nursing admission assessment completed. ICD-11 coded diagnoses documented. Treatment team assigned." },
    { step: 3, title: "Clinical Orders (CPOE)", desc: "Physician enters medication, lab, imaging, and procedure orders. Drug interaction check fires for all medication orders." },
    { step: 4, title: "Treatment & Nursing", desc: "Nursing station executes medication administration (MAR), documents vitals and care activities, manages IV and procedures." },
    { step: 5, title: "Discharge & Billing", desc: "Discharge summary generated, instructions printed in EN/AR. Insurance claim auto-generated from clinical documentation." },
  ],
  "cymed-laboratory": [
    { step: 1, title: "Receive Lab Order", desc: "FHIR ServiceRequest received from EMR. Order queued in LIS with LOINC test codes. Phlebotomist notified." },
    { step: 2, title: "Specimen Collection", desc: "Phlebotomist collects specimen with mobile app barcode scanning. Specimen labeled and tracked through processing." },
    { step: 3, title: "Analyzer Processing", desc: "Specimen processed by bidirectional analyzer interface. Results transmitted electronically to LIS in real time." },
    { step: 4, title: "Auto-Verification", desc: "Auto-verification rules (delta checks, Westgard QC) applied. Normal results auto-released; abnormals flagged for review." },
    { step: 5, title: "Result Delivery", desc: "FHIR Observation results delivered to ordering provider. Critical values trigger immediate alert via CyConnect." },
  ],
  "cymed-imaging": [
    { step: 1, title: "Order Imaging Study", desc: "FHIR ImagingStudy request received from EMR. RIS schedules study and assigns modality." },
    { step: 2, title: "Schedule & Acquire", desc: "DICOM worklist sends study parameters to modality. Images acquired and sent to PACS." },
    { step: 3, title: "PACS Processing", desc: "DICOM images received, archived, and available in radiologist worklist viewer with 3D visualization tools." },
    { step: 4, title: "Radiologist Reporting", desc: "Radiologist reads images, creates structured report using RSNA templates. AI-assisted analysis highlights findings." },
    { step: 5, title: "Result Delivery", desc: "Signed report delivered via FHIR DiagnosticReport to ordering provider. Critical findings trigger urgent alert." },
  ],
  "cymed-pharmacy": [
    { step: 1, title: "Receive E-Prescription", desc: "FHIR MedicationRequest received from prescribing provider. Order auto-queued in pharmacy dispensing workflow." },
    { step: 2, title: "Clinical Review", desc: "Clinical pharmacist reviews prescription for drug interactions (5 types), allergy conflicts, and dose appropriateness." },
    { step: 3, title: "Dispense & Label", desc: "Drug dispensed from inventory (FIFO/FEFO). Label printed in EN/AR with barcode for verification scanning." },
    { step: 4, title: "Patient Counseling", desc: "Pharmacist provides medication counseling. Digital consent recorded. Instructions delivered in patient's language." },
    { step: 5, title: "Record & Audit", desc: "Dispensing recorded in FHIR MedicationDispense. Inventory updated. Controlled substances logged for regulatory audit." },
  ],
  "cymed-patient-portal": [
    { step: 1, title: "Register & Verify", desc: "Patient registers with national ID or mobile number. Identity verified via CyIdentity. FHIR Patient record linked." },
    { step: 2, title: "Book Appointment", desc: "Patient selects specialty, provider, and time slot. Confirmation sent via SMS and email. Reminder automated." },
    { step: 3, title: "View Health Records", desc: "Patient accesses complete medical history, lab results, medications, and visit summaries — all FHIR-native." },
    { step: 4, title: "Communicate with Provider", desc: "Secure encrypted messaging with care team. Telehealth consultation launched for remote visits." },
    { step: 5, title: "Pay & Manage", desc: "Patient pays bills online, views insurance claims, manages family accounts, and downloads vaccination records." },
  ],
  "cymed-provider-portal": [
    { step: 1, title: "Login & Verify Credentials", desc: "Provider authenticates via CyIdentity MFA. Credential and license status verified. Device registered for secure access." },
    { step: 2, title: "Manage Schedule", desc: "Provider sets availability, manages appointment slots, and configures templates for different appointment types." },
    { step: 3, title: "Access Patient Records", desc: "Provider views assigned patient panel, pending orders, and clinical documentation through FHIR-secured APIs." },
    { step: 4, title: "Document & Sign", desc: "Provider completes clinical notes, signs orders, and approves results. Electronic signature validated and audit-trailed." },
    { step: 5, title: "Track Performance", desc: "Provider views personal dashboards — productivity, patient satisfaction, quality metrics, and CME hours." },
  ],
  "cymed-revenue-cycle": [
    { step: 1, title: "Registration & Financial Counseling", desc: "Financial counselor verifies patient identity, captures insurance details, and provides cost estimate before service." },
    { step: 2, title: "Eligibility Verification", desc: "Real-time insurance eligibility check via EDI 270/271. Coverage details, deductibles, and copay amounts verified." },
    { step: 3, title: "Coding & Charge Capture", desc: "ICD-11 diagnoses and CPT procedures automatically suggested from clinical documentation. Coding specialist reviews." },
    { step: 4, title: "Claims Submission", desc: "Clean claims submitted electronically to payors via EDI 837. Status tracked in real time. Rejections flagged immediately." },
    { step: 5, title: "Payment & Reconciliation", desc: "Remittances (EDI 835) auto-posted. Denials managed with appeal workflow. AR aged and collections prioritized." },
  ],
  "cymed-population-health": [
    { step: 1, title: "Data Ingestion", desc: "Clinical data from EMR, lab, imaging, and pharmacy aggregated. FHIR-based population registry created and refreshed." },
    { step: 2, title: "Risk Stratification", desc: "AI risk models score patients by chronic disease risk, readmission risk, and preventive care gaps. Cohorts identified." },
    { step: 3, title: "Care Gap Identification", desc: "Preventive screenings, medication adherence, and chronic disease management gaps identified per patient." },
    { step: 4, title: "Care Program Enrollment", desc: "High-risk patients enrolled in disease management programs. Care coordinators assigned and outreach scheduled." },
    { step: 5, title: "Outcome Reporting", desc: "Quality measures (HEDIS, JAWDA) tracked and reported. Public health dashboards available for health ministry reporting." },
  ],
  "cycom": [
    { step: 1, title: "Chart of Accounts Setup", desc: "Configure chart of accounts per IFRS/GAAP, cost centers, departments, and fiscal year. Multi-currency enabled." },
    { step: 2, title: "Transactional Operations", desc: "AP, AR, GL, inventory, procurement, and payroll transactions processed with automatic journal entries and tax calculations." },
    { step: 3, title: "HR & Payroll Processing", desc: "Employee onboarding, leave management, payroll calculation with local compliance, and benefits administration." },
    { step: 4, title: "Procurement & Inventory", desc: "Purchase orders issued, received, and matched to invoices (3-way match). Inventory tracked across warehouses." },
    { step: 5, title: "Reporting & BI", desc: "Financial statements, dashboards, and custom BI reports generated. Data exported to CyData for advanced analytics." },
  ],
  "cygov": [
    { step: 1, title: "Citizen Service Request", desc: "Citizen submits request via CyCitizen portal or in-person kiosk. Digital identity verified via CyIdentity." },
    { step: 2, title: "Document Verification", desc: "Supporting documents uploaded and verified against national registry. Anti-fraud checks performed automatically." },
    { step: 3, title: "Government Workflow", desc: "Request routed through government workflow engine. Internal departments review, approve, or request additional info." },
    { step: 4, title: "Payment & Fee Collection", desc: "Citizen notified of fees. Online payment processed via integrated payment gateway. Receipt auto-generated." },
    { step: 5, title: "Issue & Archive", desc: "Approved license, permit, or certificate issued digitally. Archived in national registry. Citizen notified via SMS/email." },
  ],
  "cyidentity": [
    { step: 1, title: "Register Application", desc: "Application registered in CyIdentity admin portal. OAuth 2.1 client credentials issued. Redirect URIs configured." },
    { step: 2, title: "Configure Realm & Policies", desc: "Authentication policies, MFA requirements, session limits, and RBAC/ABAC rules configured per tenant." },
    { step: 3, title: "User Provisioning", desc: "Users provisioned via SCIM or manual admin console. Roles assigned. Groups configured for attribute-based control." },
    { step: 4, title: "SSO & MFA Authentication", desc: "User authenticates via PKCE flow. MFA challenge issued (TOTP, passkey, or SMS). Session token issued and validated." },
    { step: 5, title: "Audit & Compliance", desc: "All authentication events hash-chain audited. Compliance reports generated. Break Glass access logged and alerted." },
  ],
  "cyintegrationhub": [
    { step: 1, title: "Connect Source System", desc: "Source system connected via REST, HL7, FHIR, DICOM, SOAP, SFTP, or Kafka. Credentials and endpoint configured." },
    { step: 2, title: "Map & Transform Data", desc: "Source message mapped to target schema using visual transformation editor. Terminology mapped (ICD-9→ICD-11)." },
    { step: 3, title: "Route to Target", desc: "Transformed message routed to target system(s). Content-based routing rules applied. Duplicate detection enabled." },
    { step: 4, title: "Monitor & Alert", desc: "All message flows monitored in real-time dashboard. Failures trigger alerts via CyConnect. SLA compliance tracked." },
    { step: 5, title: "Audit Trail", desc: "Every message transaction logged with content, timing, and status. Replays enabled for failed messages." },
  ],
  "cyai": [
    { step: 1, title: "Connect Data Sources", desc: "CyData and clinical data sources connected. Training datasets prepared with governance and privacy controls applied." },
    { step: 2, title: "Configure AI Models", desc: "Clinical or enterprise AI models selected or custom models uploaded. Explainability (XAI) requirements configured." },
    { step: 3, title: "Generate Advisory Output", desc: "AI generates advisory recommendations. Never autonomous — all outputs are advisory for human review." },
    { step: 4, title: "Clinician Review & Act", desc: "All AI recommendations reviewed and accepted/rejected by qualified clinicians or operators. Human approval required." },
    { step: 5, title: "Track & Improve", desc: "Acceptance rates, accuracy, and drift monitored. Model performance dashboards track quality over time." },
  ],
  "cydata": [
    { step: 1, title: "Connect Data Sources", desc: "CyMed, CyCom, CyGov, and external data sources connected via native connectors and CyIntegrationHub adapters." },
    { step: 2, title: "ETL Pipeline Execution", desc: "Data extracted, transformed, and loaded into the lakehouse. Schema registry validates structure. Data quality rules applied." },
    { step: 3, title: "Build BI Dashboards", desc: "Analysts build dashboards using drag-and-drop BI tools. Charts, KPIs, and population health maps configured." },
    { step: 4, title: "Self-Service Analytics", desc: "Business users query data in plain language or SQL. AI-assisted query generation available via CyAI integration." },
    { step: 5, title: "Export & Share", desc: "Reports scheduled and auto-delivered by email or API. Raw data exports in CSV, Parquet, or FHIR Bundle format." },
  ],
  "cyconnect": [
    { step: 1, title: "Configure Channels", desc: "Notification channels configured: push, email, SMS, in-app. Clinical alert routing rules set by severity and recipient role." },
    { step: 2, title: "Send Clinical Notifications", desc: "Critical lab values, medication alerts, and care reminders sent automatically. Priority queuing ensures critical alerts arrive first." },
    { step: 3, title: "Secure Clinical Messaging", desc: "HIPAA-ready encrypted messaging between care team members. Message read receipts, attachments, and group chat supported." },
    { step: 4, title: "Video Conferencing", desc: "Telehealth consultation or team meeting launched from the clinical workflow. Recording optional with consent." },
    { step: 5, title: "Monitor Delivery", desc: "Delivery rates, read rates, and alert response times tracked on operations dashboard. Failed deliveries auto-retried." },
  ],
  "cycitizen": [
    { step: 1, title: "Citizen Registration", desc: "Citizen registers with national ID, mobile number, or biometric. CyIdentity provisions citizen account with MFA." },
    { step: 2, title: "Identity Verification", desc: "National ID verified against government registry. Biometric face match optional. Digital identity certificate issued." },
    { step: 3, title: "Browse Service Catalog", desc: "Citizen browses available government services. AI chatbot guides citizen to correct service and requirements." },
    { step: 4, title: "Submit & Track Request", desc: "Request submitted with supporting documents. Citizen receives reference number and real-time status updates." },
    { step: 5, title: "Receive Digital Documents", desc: "Approved documents delivered to citizen's digital wallet. QR code verification available for physical presentation." },
  ],
  "cycom-finance": [
    { step: 1, title: "Chart of Accounts Setup", desc: "Define fiscal entities, cost centers, general ledger accounts, and reporting currency per standard IFRS." },
    { step: 2, title: "Budget Planning", desc: "Create annual budgets and expense thresholds for each corporate department or project registry." },
    { step: 3, title: "Transaction Posting", desc: "Post financial journal entries. Verify and adjust cash flow, accounts payable, and accounts receivable ledgers." },
    { step: 4, title: "Reconciliation", desc: "Run automatic bank statement matching to verify treasury holdings and highlight discrepancies." },
    { step: 5, title: "Reporting & Auditing", desc: "Generate audited financial balance sheets, income statements, and IFRS-compliant annual filings." },
  ],
  "cycom-accounting": [
    { step: 1, title: "Verify Accounts Payable", desc: "Review and approve incoming vendor invoices, matching purchase orders and receiving slips." },
    { step: 2, title: "Process Billing", desc: "Generate outgoing customer invoices, configure payment terms, and deliver billing statements electronically." },
    { step: 3, title: "Tax Computation", desc: "Automatically compute local VAT, withholding taxes, and sales tax adjustments per national rules." },
    { step: 4, title: "Cash Allocation", desc: "Map incoming bank deposits to outstanding accounts receivable invoices to reconcile cash accounts." },
    { step: 5, title: "Tax Filing", desc: "Compile and export VAT declarations and local tax filing reports for submission to national authorities." },
  ],
  "cycom-procurement": [
    { step: 1, title: "Purchase Requisition", desc: "Department requests items. Requisition automatically routed through organizational approval levels." },
    { step: 2, title: "RFQ & Bidding", desc: "Invite vendor quotes and track bids on the supplier portal. Compare pricing and terms." },
    { step: 3, title: "PO Issuance", desc: "Generate Purchase Order (PO) with final pricing, terms, and shipping addresses. Auto-deliver to vendor." },
    { step: 4, title: "Three-Way Match", desc: "Match invoice, receiving voucher, and PO. Flag price mismatches or quantity variances." },
    { step: 5, title: "Supplier Evaluation", desc: "Log vendor delivery times, quality scores, and pricing accuracy to guide future sourcing cycles." },
  ],
  "cycom-inventory": [
    { step: 1, title: "Warehouse Mapping", desc: "Configure warehouses, virtual zones, shelves, and bin addresses for optimized physical picking." },
    { step: 2, title: "Barcode Ingestion", desc: "Scan barcode labels during stock arrival. Record batch numbers, lot codes, and expiration parameters." },
    { step: 3, title: "Stock Allocation", desc: "Track serialized inventory and allocate items based on FIFO/FEFO costing rules." },
    { step: 4, title: "Internal Movement", desc: "Manage stock transfers, cycle counts, and adjustments with digital verification." },
    { step: 5, title: "Replenishment", desc: "Generate auto-reorder suggestions when stock falls below defined thresholds." },
  ],
  "cycom-hr": [
    { step: 1, title: "Onboarding Flow", desc: "Employee profile setup: personal details, contracts, org hierarchy mapping, and IT provisioning." },
    { step: 2, title: "Record Management", desc: "Maintain central repository of employee credentials, emergency contacts, and job change history." },
    { step: 3, title: "Time Tracking", desc: "Capture work hours via biometric integration, mobile check-ins, or web-based timesheets." },
    { step: 4, title: "Performance Evaluation", desc: "Initiate evaluation cycles, configure peer reviews, and track goals." },
    { step: 5, title: "Self-Service Requests", desc: "Employees submit leave requests, expense reimbursements, and document inquiries via the ESS portal." },
  ],
  "cycom-payroll": [
    { step: 1, title: "Formula Setup", desc: "Configure base salaries, overtime multipliers, and recurring allowances in the calculations engine." },
    { step: 2, title: "Timesheet Integration", desc: "Sync approved employee timecards, shifts, leaves, and unpaid absences into the payroll run." },
    { step: 3, title: "Deductions & Benefits", desc: "Calculate social security, healthcare contributions, pension withholdings, and end-of-service accruals." },
    { step: 4, title: "WPS Export", desc: "Generate Wage Protection System (WPS) bank transfer files compliant with local regulatory formats." },
    { step: 5, title: "Slip Delivery", desc: "Deliver secure, detailed pay slips to employee portals and post journal entries to general ledger accounts." },
  ],
  "cycom-crm": [
    { step: 1, title: "Lead Ingestion", desc: "Capture prospective leads from website forms, partner portals, and marketing events." },
    { step: 2, title: "Pipeline Tracking", desc: "Manage deals through visual pipeline stages. Track email history and schedule calls." },
    { step: 3, title: "Quotation Drafting", desc: "Generate commercial proposals and pricing quotes, pulling items directly from the catalog." },
    { step: 4, title: "Contract Management", desc: "Track active customer contracts, SLA agreements, and set automatic renewal notifications." },
    { step: 5, title: "Customer Ticketing", desc: "Route helpdesk inquiries. Track response times, support statuses, and resolve service issues." },
  ],
  "cycom-assets": [
    { step: 1, title: "Asset Registry", desc: "Register property, plant, equipment, and IT hardware. Assign barcodes and locations." },
    { step: 2, title: "Depreciation Run", desc: "Run straight-line, declining-balance, or custom depreciation cycles. Automatically update asset book value." },
    { step: 3, title: "Maintenance Alerts", desc: "Schedule preventive maintenance tasks, assign technicians, and track maintenance histories." },
    { step: 4, title: "Asset Audit", desc: "Perform physical asset audits using mobile barcode and RFID scans." },
    { step: 5, title: "Disposal & Postings", desc: "Log asset write-offs, retirements, or sales, and automatically post financial adjustments." },
  ],
  "cycom-manufacturing": [
    { step: 1, title: "Bill of Materials (BOM)", desc: "Build multi-level product recipes, compiling raw materials, intermediate assemblies, and labor costs." },
    { step: 2, title: "MRP Calculation", desc: "Run Material Requirements Planning (MRP) to calculate purchasing needs based on demand forecast." },
    { step: 3, title: "Work Order Release", desc: "Release production work orders to the shop floor. Assign work centers and schedule operations." },
    { step: 4, title: "Assembly Tracking", desc: "Monitor raw material consumption, machine running times, and assembly milestones." },
    { step: 5, title: "QA Inspection", desc: "Conduct quality checksheets at production stages, logging compliance before inventory storage." },
  ],
  "cycom-retail": [
    { step: 1, title: "Register Boot", desc: "Cashier logs into terminal, validates cash register contents, and opens checkout shift." },
    { step: 2, title: "Item Checkout", desc: "Scan product barcodes, retrieve real-time prices, apply loyalty discounts, and calculate VAT." },
    { step: 3, title: "Payment Settlement", desc: "Accept cards, digital wallets, cash, or credit. Secure integration with payment terminals." },
    { step: 4, title: "Offline Sync", desc: "If offline, POS stores transactions locally, syncs to cloud database once connection is restored." },
    { step: 5, title: "Shift Closing", desc: "Perform cash reconciliation audits, print closing reports, and post POS totals to general ledger accounts." },
  ],
  "cyshop": [
    { step: 1, title: "Setup & Configure", desc: "Configure your business type (retail, restaurant, grocery), add locations, set up the menu or product catalog, and configure payment terminals." },
    { step: 2, title: "Staff & Permissions", desc: "Add staff accounts via CyIdentity SSO. Assign roles (cashier, manager, admin). Set shift schedules and access permissions per role." },
    { step: 3, title: "Go Live with POS", desc: "Launch POS on tablet, touchscreen, or desktop. Scan barcodes, take orders, and accept all payment methods including card, cash, and digital wallets." },
    { step: 4, title: "Manage Inventory", desc: "Track stock in real time. Auto-replenishment alerts when items run low. Receive supplier deliveries and update inventory via barcode scanning." },
    { step: 5, title: "Analyze & Grow", desc: "View AI-powered sales forecasts, bestseller reports, and peak-hour analytics. Use CyShop BI dashboards to make data-driven decisions." },
  ],
  "cyshop-retail": [
    { step: 1, title: "Catalog & Barcodes", desc: "Import product catalog with barcodes, multi-variant SKUs (size, color), and pricing tiers. Print barcode labels from the system." },
    { step: 2, title: "Configure Terminals", desc: "Set up POS terminals with touchscreen or barcode scanner. Configure receipt printer and cash drawer per station." },
    { step: 3, title: "Checkout & Payments", desc: "Cashier scans items, applies discounts, and accepts card, cash, or loyalty points. Receipt printed or emailed." },
    { step: 4, title: "Loyalty & CRM", desc: "Customers earn points on each purchase. Reward redemption applied automatically at checkout. CRM tracks purchase history." },
    { step: 5, title: "Stock & Reporting", desc: "Daily stock reconciliation, bestseller reports, and low-stock alerts. Supplier reorder auto-generated when thresholds hit." },
  ],
  "cyshop-restaurant": [
    { step: 1, title: "Menu & Tables Setup", desc: "Configure menu categories, items, modifiers, and price variants. Set up table layout with zone mapping." },
    { step: 2, title: "Take Order", desc: "Waiter selects table, takes order on mobile app or tableside tablet. Order fires to kitchen display instantly." },
    { step: 3, title: "Kitchen Prepares", desc: "KDS shows order queue with priority. Kitchen marks items ready — waiter notified to serve." },
    { step: 4, title: "Payment & Split Bill", desc: "Waiter closes table bill. Customer pays by card, cash, or split. VAT-compliant receipt printed or sent to email." },
    { step: 5, title: "End-of-Day Reports", desc: "Manager reviews daily sales, covers, average spend, and cancellation reports. Delivery revenue reconciled separately." },
  ],
  "cyshop-bakery": [
    { step: 1, title: "Recipes & Ingredients", desc: "Enter recipes with ingredients and quantities. System calculates cost per item and batch automatically." },
    { step: 2, title: "Daily Production Plan", desc: "Set production targets per item based on historical sales. Ingredient quantities auto-calculated for the batch." },
    { step: 3, title: "Production & Quality", desc: "Baker records batch completion. Yield and waste logged. Freshness timers set per item category." },
    { step: 4, title: "Counter Sales", desc: "Cashier uses counter POS with item photos. Customer selects by weight or unit. VAT-compliant receipt issued." },
    { step: 5, title: "Review & Order Supplies", desc: "End of day: waste report, ingredient usage, and remaining stock. Supplier reorder generated for next day production." },
  ],
  "cyshop-coffee": [
    { step: 1, title: "Menu & Modifiers", desc: "Configure drink menu with sizes, milk types, syrups, and extras. Price rules set per modifier combination." },
    { step: 2, title: "Order & Customer Name", desc: "Cashier takes order, enters customer name. Order appears on barista KDS with full customization details." },
    { step: 3, title: "Barista Prepares", desc: "Barista prepares drink per KDS instructions. Taps 'Ready' when done — customer display shows name." },
    { step: 4, title: "Loyalty & Payment", desc: "Customer pays and earns stamp/points on loyalty card. Rewards redeemed for free drinks. Receipt emailed or printed." },
    { step: 5, title: "Inventory & Waste", desc: "Ingredient consumption tracked per cup. Low-stock alerts for milk, beans, syrups. Waste logged and analyzed weekly." },
  ],
  "cyshop-fastfood": [
    { step: 1, title: "Menu & Combos", desc: "Configure menu with combo meals, upsell items, and limited-time offers. Prices updated centrally across all lanes." },
    { step: 2, title: "Fast Checkout", desc: "Cashier or self-service kiosk takes order in under 3 seconds. Combo auto-suggests upsell items." },
    { step: 3, title: "KDS & Kitchen", desc: "Order fires to kitchen display with priority queue. Kitchen marks items ready per station (fry, grill, assembly)." },
    { step: 4, title: "Drive-Through Lane", desc: "Drive-through orders taken at intercom, displayed in kitchen, and completed at payment window. Timer tracked." },
    { step: 5, title: "Shift & Peak Analytics", desc: "Manager reviews peak-hour throughput, average ticket time, and items sold per shift. Staffing adjusted accordingly." },
  ],
  "cyshop-grocery": [
    { step: 1, title: "Receive & Price", desc: "Receive supplier delivery, scan items, enter quantities and expiry dates. Prices updated automatically from supplier invoice." },
    { step: 2, title: "Shelf & Barcode", desc: "Print barcode labels with price. Fresh items labeled with production and expiry date. Shelf placement logged." },
    { step: 3, title: "Customer Checkout", desc: "Cashier scans items or enters PLU codes for loose items. Weighted items connected to scale. VAT receipt issued." },
    { step: 4, title: "Credit Accounts", desc: "Regular customers maintain credit accounts. Monthly statements printed. Credit limits enforced at checkout." },
    { step: 5, title: "Stock & Expiry", desc: "Daily expiry check report. Low-stock alerts trigger reorder. Supplier orders auto-generated from minimum stock levels." },
  ],
  "cyshop-supermarket": [
    { step: 1, title: "Department Setup", desc: "Configure departments (fresh, frozen, bakery, deli, household). Each has independent inventory, pricing, and P&L tracking." },
    { step: 2, title: "Central Buying", desc: "Buying team creates purchase orders per department. Goods received centrally and distributed to shelves by department." },
    { step: 3, title: "Multi-Lane Checkout", desc: "Multiple cashier lanes operate simultaneously. Self-checkout kiosks handle simple baskets independently." },
    { step: 4, title: "Promotions & Loyalty", desc: "Promotional prices active by time slot or member card scan. Loyalty points awarded per basket. Offers targeted by purchase history." },
    { step: 5, title: "Department BI Reports", desc: "Department managers review shrinkage, margin, turnover, and waste daily. GM views supermarket-wide P&L dashboard." },
  ],
  "cyshop-convenience": [
    { step: 1, title: "Quick Setup", desc: "Add product catalog with barcodes. Configure compact touchscreen POS and receipt printer. Enable offline mode for 24/7 operation." },
    { step: 2, title: "Fast Checkout", desc: "Cashier scans items rapidly. Cash or card payment accepted. Age verification prompt appears for restricted items." },
    { step: 3, title: "Fuel Pump Integration", desc: "Fuel amount entered or pump linked automatically. Combined fuel + shop receipt generated for customer." },
    { step: 4, title: "Shift & Safe Management", desc: "Cashier opens and closes shift with cash count. Safe deposit recorded. Discrepancy alerts sent to manager." },
    { step: 5, title: "Stock & Reorder", desc: "Low-stock alerts generated automatically. Supplier reorder created with one tap. Delivery confirmed by barcode scan." },
  ],
  "cycom-bi": [
    { step: 1, title: "Data Source Mapping", desc: "Map analytical data views from EMR, ERP, and IAM modules via secure lakehouse endpoints." },
    { step: 2, title: "Dashboard Building", desc: "Select visual widgets — bar charts, line graphs, KPI tiles, and geographical maps." },
    { step: 3, title: "Dynamic Querying", desc: "Query data tables in natural language or SQL. Filter and slice dashboards in real time." },
    { step: 4, title: "Delivery Scheduling", desc: "Schedule automated PDF dashboard deliveries to emails of key stakeholders." },
    { step: 5, title: "Data Exporting", desc: "Export dataset tables to Excel, CSV, or Parquet formats for external financial or clinical research." },
  ],
};

const LAUNCH_URLS: Record<string, string | undefined> = {
  "cymed":                    process.env.NEXT_PUBLIC_CYMED_URL ?? "https://cymed.cy-com.com",
  "cymed-hospital":           process.env.NEXT_PUBLIC_CYMED_HOSPITAL_URL ?? "https://cymed.cy-com.com/hospital",
  "cymed-clinic":             process.env.NEXT_PUBLIC_CYMED_CLINIC_URL ?? "https://cymed.cy-com.com/clinic",
  "cymed-laboratory":         process.env.NEXT_PUBLIC_CYMED_LAB_URL ?? "https://cymed.cy-com.com/laboratory",
  "cymed-imaging":            process.env.NEXT_PUBLIC_CYMED_IMAGING_URL ?? "https://cymed.cy-com.com/imaging",
  "cymed-pharmacy":           process.env.NEXT_PUBLIC_CYMED_PHARMACY_URL ?? "https://cymed.cy-com.com/pharmacy",
  "cymed-patient-portal":     process.env.NEXT_PUBLIC_CYMED_PATIENT_PORTAL_URL ?? "https://cymed.cy-com.com/patient-portal",
  "cymed-provider-portal":    process.env.NEXT_PUBLIC_CYMED_PROVIDER_PORTAL_URL ?? "https://cymed.cy-com.com/provider-portal",
  "cymed-revenue-cycle":      process.env.NEXT_PUBLIC_CYMED_RCM_URL ?? "https://cymed.cy-com.com/rcm",
  "cymed-population-health":  process.env.NEXT_PUBLIC_CYMED_POPULATION_HEALTH_URL ?? "https://cymed.cy-com.com/population-health",
  "cycom":                    process.env.NEXT_PUBLIC_CYCOM_URL ?? "https://www.cy-com.com/erp",
  "cygov":                    process.env.NEXT_PUBLIC_CYGOV_URL,
  "cyidentity":               process.env.NEXT_PUBLIC_CYIDENTITY_URL,
  "cyintegrationhub":         process.env.NEXT_PUBLIC_CYINTEGRATIONHUB_URL,
  "cyai":                     process.env.NEXT_PUBLIC_CYAI_URL,
  "cydata":                   process.env.NEXT_PUBLIC_CYDATA_URL,
  "cyconnect":                process.env.NEXT_PUBLIC_CYCONNECT_URL,
  "cycitizen":                process.env.NEXT_PUBLIC_CYCITIZEN_URL,
  "cycom-finance":            process.env.NEXT_PUBLIC_CYCOM_FINANCE_URL,
  "cycom-accounting":         process.env.NEXT_PUBLIC_CYCOM_ACCOUNTING_URL,
  "cycom-procurement":        process.env.NEXT_PUBLIC_CYCOM_PROCUREMENT_URL,
  "cycom-inventory":          process.env.NEXT_PUBLIC_CYCOM_INVENTORY_URL,
  "cycom-hr":                 process.env.NEXT_PUBLIC_CYCOM_HR_URL,
  "cycom-payroll":            process.env.NEXT_PUBLIC_CYCOM_PAYROLL_URL,
  "cycom-crm":                process.env.NEXT_PUBLIC_CYCOM_CRM_URL,
  "cycom-assets":             process.env.NEXT_PUBLIC_CYCOM_ASSETS_URL,
  "cycom-manufacturing":      process.env.NEXT_PUBLIC_CYCOM_MANUFACTURING_URL,
  "cycom-retail":             process.env.NEXT_PUBLIC_CYCOM_RETAIL_URL,
  "cycom-bi":                 process.env.NEXT_PUBLIC_CYCOM_BI_URL,
  "cyshop":                   process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com",
  "cyshop-retail":            process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com/retail",
  "cyshop-restaurant":        process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com/restaurant",
  "cyshop-bakery":            process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com/bakery",
  "cyshop-coffee":            process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com/coffee",
  "cyshop-fastfood":          process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com/fastfood",
  "cyshop-grocery":           process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com/grocery",
  "cyshop-supermarket":       process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com/supermarket",
  "cyshop-convenience":       process.env.NEXT_PUBLIC_CYSHOP_URL ?? "https://cyshop.cy-com.com/convenience",
  "cydeveloper":              process.env.NEXT_PUBLIC_CYDEVELOPER_URL ?? "https://developer.cy-com.com",
};

export async function generateStaticParams() {
  return Object.keys(PRODUCT_DATA).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: ProductPageProps): Promise<Metadata> {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const product = PRODUCT_DATA[slug];
  if (!product) return {};

  return buildMetadata({
    title: `${product.name} — ${product.tagline}`,
    description: product.description,
    path: `/products/${slug}`,
    locale,
  });
}

const COLOR_MAP: Record<string, { badge: string; btn: string; icon: string; gradient: string }> = {
  emerald: {
    badge: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    btn: "bg-emerald-500 hover:bg-emerald-400 text-white",
    icon: "bg-emerald-500/10 border-emerald-500/20",
    gradient: "from-emerald-900/20 to-transparent",
  },
  blue: {
    badge: "text-blue-400 border-blue-500/20 bg-blue-500/5",
    btn: "bg-blue-500 hover:bg-blue-400 text-white",
    icon: "bg-blue-500/10 border-blue-500/20",
    gradient: "from-blue-900/20 to-transparent",
  },
  amber: {
    badge: "text-amber-400 border-amber-500/20 bg-amber-500/5",
    btn: "bg-amber-500 hover:bg-amber-400 text-white",
    icon: "bg-amber-500/10 border-amber-500/20",
    gradient: "from-amber-900/20 to-transparent",
  },
  violet: {
    badge: "text-violet-400 border-violet-500/20 bg-violet-500/5",
    btn: "bg-violet-500 hover:bg-violet-400 text-white",
    icon: "bg-violet-500/10 border-violet-500/20",
    gradient: "from-violet-900/20 to-transparent",
  },
  cyan: {
    badge: "text-cyan-400 border-cyan-500/20 bg-cyan-500/5",
    btn: "bg-cyan-500 hover:bg-cyan-400 text-cy-black",
    icon: "bg-cyan-500/10 border-cyan-500/20",
    gradient: "from-cyan-900/20 to-transparent",
  },
  pink: {
    badge: "text-pink-400 border-pink-500/20 bg-pink-500/5",
    btn: "bg-pink-500 hover:bg-pink-400 text-white",
    icon: "bg-pink-500/10 border-pink-500/20",
    gradient: "from-pink-900/20 to-transparent",
  },
  teal: {
    badge: "text-teal-400 border-teal-500/20 bg-teal-500/5",
    btn: "bg-teal-500 hover:bg-teal-400 text-white",
    icon: "bg-teal-500/10 border-teal-500/20",
    gradient: "from-teal-900/20 to-transparent",
  },
  orange: {
    badge: "text-orange-400 border-orange-500/20 bg-orange-500/5",
    btn: "bg-cy-orange hover:bg-cy-orange-light text-white",
    icon: "bg-cy-orange/10 border-cy-orange/20",
    gradient: "from-orange-900/20 to-transparent",
  },
  indigo: {
    badge: "text-indigo-400 border-indigo-500/20 bg-indigo-500/5",
    btn: "bg-indigo-500 hover:bg-indigo-400 text-white",
    icon: "bg-indigo-500/10 border-indigo-500/20",
    gradient: "from-indigo-900/20 to-transparent",
  },
};

export default async function ProductPage({ params }: ProductPageProps) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const product = PRODUCT_DATA[slug];

  if (!product) notFound();

  const colors = (COLOR_MAP[product.color] ?? COLOR_MAP.emerald) as { badge: string; btn: string; icon: string; gradient: string };
  const l = locale as Locale;
  const workflows = WORKFLOW_DATA[slug] ?? [];
  const launchUrl = LAUNCH_URLS[slug] ?? `https://www.cy-com.com/${locale}/demo?product=${slug}`;
  const docsUrl = process.env.NEXT_PUBLIC_DOCS_URL ?? "https://docs.cy-com.com";

  // Merge comprehensive module data from lib file (overrides inline data)
  const richData = PRODUCT_MODULES_DATA[slug];
  const modules = richData?.modules ?? product.modules;
  const roleWorkflows = richData?.roleWorkflows ?? product.roleWorkflows;
  const permissionRoles = richData?.permissionRoles ?? product.permissionRoles;

  return (
    <div className="min-h-dvh pt-16">
      {/* Hero */}
      <div className={`relative py-24 overflow-hidden bg-gradient-to-br ${colors.gradient}`}>
        <div className="section-container relative z-10">
          <nav className="flex items-center gap-2 text-xs text-cy-gray-400 mb-8" aria-label="Breadcrumb">
            <Link href={`/${l}`} className="hover:text-white transition-colors">Home</Link>
            <ChevronRight className="w-3 h-3" aria-hidden="true" />
            <Link href={`/${l}/products`} className="hover:text-white transition-colors">Products</Link>
            <ChevronRight className="w-3 h-3" aria-hidden="true" />
            <span className="text-white">{product.name}</span>
          </nav>

          <div className="max-w-3xl">
            <span className={`product-badge mb-4 ${colors.badge}`}>
              {product.categoryLabel}
            </span>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-semibold text-white mb-4 leading-tight">
              {product.name}
            </h1>
            <p className="text-xl text-cy-gray-400 mb-6">{product.tagline}</p>
            <p className="text-base text-cy-gray-400 leading-relaxed mb-8 max-w-2xl">{product.description}</p>

            <div className="flex flex-wrap gap-2 mb-8" aria-label="Compliance standards">
              {product.compliance.map((c) => (
                <span key={c} className={`product-badge ${colors.badge}`}>
                  <Check className="w-3 h-3" aria-hidden="true" />
                  {c}
                </span>
              ))}
            </div>

            <div className="flex flex-wrap gap-3">
              <Link
                href={`/${l}/demo?product=${slug}`}
                className={`inline-flex items-center gap-2 px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 cursor-pointer ${colors.btn}`}
              >
                Request a Demo
                <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
              </Link>
              <a
                href={launchUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 btn-secondary px-6 py-3 text-sm"
              >
                <Play className="w-4 h-4" aria-hidden="true" />
                Launch Product
                <ExternalLink className="w-3.5 h-3.5 opacity-60" aria-hidden="true" />
              </a>
              <a
                href={`${docsUrl}/products/${slug}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 btn-ghost px-5 py-3 text-sm"
              >
                <BookOpen className="w-4 h-4" aria-hidden="true" />
                Documentation
                <ExternalLink className="w-3.5 h-3.5 opacity-60" aria-hidden="true" />
              </a>
              <Link
                href={`/${l}/contact?interest=enterprise-sales&product=${slug}`}
                className="inline-flex items-center gap-2 btn-ghost px-5 py-3 text-sm"
              >
                <Phone className="w-4 h-4" aria-hidden="true" />
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Sub-products (CyMed platform overview) */}
      {product.subProducts && (
        <section className="py-20 bg-cy-dark/30" aria-labelledby="subproducts-heading">
          <div className="section-container">
            <h2 id="subproducts-heading" className="text-2xl font-heading font-semibold text-white mb-4">
              CyMed Product Suite
            </h2>
            <p className="text-cy-gray-400 mb-8">
              Nine integrated clinical products covering every care setting — all FHIR-native, all on one platform.
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {product.subProducts.map((sp) => (
                <Link
                  key={sp.slug}
                  href={`/${l}/products/${sp.slug}`}
                  className="glass-card p-5 rounded-xl hover:border-cy-glass-bg-hover transition-all duration-150 cursor-pointer group"
                >
                  <div className="text-sm font-heading font-semibold text-white group-hover:text-gradient-orange mb-1 transition-colors">
                    {sp.name}
                  </div>
                  <div className="text-xs text-cy-gray-400 leading-relaxed mb-3">{sp.desc}</div>
                  <span className="text-xs text-emerald-400 flex items-center gap-1">
                    Learn more
                    <ArrowRight className="w-3 h-3 rtl:rotate-180" aria-hidden="true" />
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Features */}
      <section className="py-20" aria-labelledby="features-heading">
        <div className="section-container">
          <h2 id="features-heading" className="text-2xl font-heading font-semibold text-white mb-8">
            Key Features
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {product.features.map((feature) => (
              <div key={feature} className="flex items-start gap-3 glass-card p-4 rounded-xl">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${colors.icon} border`}>
                  <Check className="w-3 h-3 text-white" aria-hidden="true" />
                </div>
                <span className="text-sm text-cy-gray-200">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* All Modules — prominent, filterable */}
      {modules && modules.length > 0 && (
        <section className="py-20 bg-cy-dark/30" aria-labelledby="modules-heading">
          <div className="section-container">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center border ${colors.icon}`}>
                <Layers className={`w-5 h-5 ${colors.badge.split(" ")[0]}`} aria-hidden="true" />
              </div>
              <div>
                <h2 id="modules-heading" className="text-2xl font-heading font-semibold text-white">All Modules</h2>
                <p className="text-sm text-cy-gray-400">Complete module directory — clinical, ERP, and AI. Filter by category or user role below.</p>
              </div>
            </div>
            <ModuleExplorer modules={modules} />
          </div>
        </section>
      )}

      {/* Role-Based Workflows */}
      {roleWorkflows && roleWorkflows.length > 0 && (
        <section className="py-20" aria-labelledby="roles-heading">
          <div className="section-container">
            <div className="mb-8">
              <p className="text-sm font-medium text-cy-orange mb-2 uppercase tracking-wider">By User Role</p>
              <h2 id="roles-heading" className="text-2xl font-heading font-semibold text-white mb-2">
                How Each Role Uses {product.name}
              </h2>
              <p className="text-sm text-cy-gray-400">
                Select a user role to see their exact step-by-step workflow inside the platform.
              </p>
            </div>
            <RoleWorkflowExplorer roleWorkflows={roleWorkflows} />
          </div>
        </section>
      )}

      {/* User Permissions — Odoo-style RBAC */}
      {permissionRoles && permissionRoles.length > 0 && (
        <section className="py-20 bg-cy-dark/30" aria-labelledby="permissions-heading">
          <div className="section-container">
            <div className="mb-8">
              <p className="text-sm font-medium text-cy-orange mb-2 uppercase tracking-wider">Access Control</p>
              <h2 id="permissions-heading" className="text-2xl font-heading font-semibold text-white mb-2">
                User Permissions & Role-Based Access
              </h2>
              <p className="text-sm text-cy-gray-400 max-w-2xl">
                When you purchase {product.name}, your System Admin can assign each user a role that controls exactly which modules and actions they can see and perform — similar to Odoo. Click a role below to explore its module access.
              </p>
            </div>
            <PermissionsMatrix roles={permissionRoles} />
          </div>
        </section>
      )}

      {/* AI Features */}
      {product.aiFeatures && product.aiFeatures.length > 0 && (
        <section className="py-20 bg-cy-dark/30" aria-labelledby="ai-heading">
          <div className="section-container">
            <div className="flex items-center gap-3 mb-8">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center border ${colors.icon}`}>
                <Brain className={`w-5 h-5 ${colors.badge.split(" ")[0]}`} aria-hidden="true" />
              </div>
              <div>
                <h2 id="ai-heading" className="text-2xl font-heading font-semibold text-white">AI-Powered Intelligence</h2>
                <p className="text-sm text-cy-gray-400">Advisory-only — every AI output reviewed and confirmed by a qualified human</p>
              </div>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {product.aiFeatures.map((ai) => (
                <div key={ai.title} className="glass-card p-5 rounded-xl">
                  <div className={`text-sm font-heading font-semibold mb-2 ${colors.badge.split(" ")[0]}`}>{ai.title}</div>
                  <p className="text-xs text-cy-gray-400 leading-relaxed">{ai.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Workflows */}
      {workflows.length > 0 && (
        <section className="py-20 bg-cy-dark/30" aria-labelledby="workflows-heading">
          <div className="section-container">
            <h2 id="workflows-heading" className="text-2xl font-heading font-semibold text-white mb-4">
              How It Works
            </h2>
            <p className="text-cy-gray-400 mb-10">
              End-to-end workflow in {product.name}.
            </p>
            <div className="relative">
              <div className="hidden lg:block absolute top-8 left-8 right-8 h-px bg-gradient-to-r from-transparent via-cy-glass-border to-transparent" aria-hidden="true" />
              <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {workflows.map((w) => (
                  <div key={w.step} className="glass-card p-5 rounded-2xl">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-sm font-heading font-bold mb-4 border ${colors.icon} ${colors.badge.split(" ")[0]}`}>
                      {w.step}
                    </div>
                    <h3 className="text-sm font-heading font-semibold text-white mb-2">{w.title}</h3>
                    <p className="text-xs text-cy-gray-400 leading-relaxed">{w.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Platform Preview — live iframe */}
      <section className="py-20" aria-labelledby="preview-heading">
        <div className="section-container">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
            <div>
              <h2 id="preview-heading" className="text-2xl font-heading font-semibold text-white mb-2">
                Platform Preview
              </h2>
              <p className="text-cy-gray-400 text-sm">
                Live interface — interact directly or open in a new tab.
              </p>
            </div>
            <a
              href={launchUrl}
              target="_blank"
              rel="noreferrer"
              className="btn-secondary text-sm py-2 px-4 flex-shrink-0 inline-flex items-center gap-2"
            >
              <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
              Open Full Screen
            </a>
          </div>

          {/* Browser chrome wrapper */}
          <div className="rounded-2xl border border-cy-glass-border bg-cy-dark/40 overflow-hidden shadow-2xl">
            {/* Title bar */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-cy-glass-border bg-cy-dark/70">
              <div className="flex gap-1.5" aria-hidden="true">
                <div className="w-3 h-3 rounded-full bg-red-500/60" />
                <div className="w-3 h-3 rounded-full bg-amber-500/60" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/60" />
              </div>
              <div className="flex-1 mx-2">
                <div
                  className="h-6 rounded-lg bg-cy-glass-bg border border-cy-glass-border flex items-center px-3 gap-2 max-w-sm mx-auto"
                >
                  <span className="text-xs text-cy-gray-500 truncate">{launchUrl.replace("https://", "")}</span>
                </div>
              </div>
              <div className={`text-xs px-2.5 py-1 rounded-lg font-medium flex-shrink-0 ${colors.badge}`}>
                Live
              </div>
            </div>

            {/* iframe */}
            <div className="relative" style={{ height: "580px" }}>
              <iframe
                src={launchUrl}
                title={`${product.name} — Live Platform Preview`}
                className="w-full h-full border-0"
                loading="lazy"
                allow="fullscreen"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
              />
              {/* Overlay gradient at bottom to fade into section */}
              <div
                className="absolute inset-x-0 bottom-0 h-16 pointer-events-none"
                style={{ background: "linear-gradient(to top, rgba(15,15,26,0.6), transparent)" }}
                aria-hidden="true"
              />
            </div>
          </div>

          <p className="text-xs text-cy-gray-500 mt-3 text-center">
            Live demo environment · Read-only mode · Data is illustrative
          </p>
        </div>
      </section>

      {/* Integrated ERP — shown only for products WITHOUT the full modules explorer */}
      {product.erpModules && product.erpModules.length > 0 && !modules && (
        <section className="py-20 bg-cy-dark/30" aria-labelledby="erp-heading">
          <div className="section-container">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center border bg-blue-500/10 border-blue-500/20">
                <Layers className="w-5 h-5 text-blue-400" aria-hidden="true" />
              </div>
              <div>
                <h2 id="erp-heading" className="text-2xl font-heading font-semibold text-white">Integrated ERP Backbone</h2>
                <p className="text-sm text-cy-gray-400">Every {product.name} deployment connects natively to CyCom ERP — no middleware, no data silos</p>
              </div>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {product.erpModules.map((m) => (
                <div key={m.module} className="glass-card p-5 rounded-xl border border-blue-500/10">
                  <div className="flex items-center gap-2 mb-2">
                    <Check className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" aria-hidden="true" />
                    <span className="text-sm font-heading font-semibold text-white">{m.module}</span>
                  </div>
                  <p className="text-xs text-cy-gray-400 leading-relaxed">{m.desc}</p>
                </div>
              ))}
            </div>
            <p className="text-xs text-cy-gray-500 mt-6">
              Powered by{" "}
              <Link href={`/${l}/erp`} className="text-blue-400 hover:text-blue-300 transition-colors">CyCom ERP</Link>
              {" "}— unified finance, HR, procurement, and operations across the CyberCom ecosystem.
            </p>
          </div>
        </section>
      )}

      {/* Editions */}
      <section className="py-20 bg-cy-dark/30" aria-labelledby="editions-heading">
        <div className="section-container">
          <h2 id="editions-heading" className="text-2xl font-heading font-semibold text-white mb-8">
            Editions
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {product.editions.map((edition, i) => (
              <div key={edition.name} className={`glass-card p-6 rounded-2xl border ${i === product.editions.length - 1 ? `border-${product.color}-500/30` : "border-cy-glass-border"}`}>
                <h3 className="font-heading font-semibold text-white mb-1">{edition.name}</h3>
                <p className="text-sm text-cy-gray-400 mb-4">{edition.desc}</p>
                <ul className="space-y-2">
                  {edition.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-cy-gray-200">
                      <Check className="w-3.5 h-3.5 text-cy-orange flex-shrink-0" aria-hidden="true" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href={`/${l}/demo?product=${slug}&edition=${encodeURIComponent(edition.name)}`}
                  className="mt-6 btn-secondary w-full justify-center text-sm"
                >
                  Get Started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Deployment */}
      <section className="py-20" aria-labelledby="deployment-heading">
        <div className="section-container">
          <h2 id="deployment-heading" className="text-2xl font-heading font-semibold text-white mb-6">
            Deployment Models
          </h2>
          <div className="flex flex-wrap gap-3">
            {product.deployment.map((d) => (
              <div key={d} className="flex items-center gap-2 glass-card px-5 py-3 rounded-xl">
                <div className="w-2 h-2 rounded-full bg-cy-orange" aria-hidden="true" />
                <span className="text-sm font-medium text-white">{d}</span>
              </div>
            ))}
          </div>

          <div className="mt-12 glass-card p-8 rounded-2xl">
            <div className="grid sm:grid-cols-2 gap-6 items-center">
              <div>
                <h3 className="text-lg font-heading font-semibold text-white mb-1">
                  Ready to see {product.name} in action?
                </h3>
                <p className="text-sm text-cy-gray-400">
                  Schedule a personalized demo or launch the product to explore it live.
                </p>
              </div>
              <div className="flex flex-wrap gap-3 sm:justify-end">
                <Link
                  href={`/${l}/demo?product=${slug}`}
                  className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 cursor-pointer ${colors.btn}`}
                >
                  Request Demo
                  <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
                </Link>
                <a
                  href={launchUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 btn-secondary px-5 py-2.5 text-sm"
                >
                  <Play className="w-4 h-4" aria-hidden="true" />
                  Launch Product
                  <ExternalLink className="w-3.5 h-3.5 opacity-60" aria-hidden="true" />
                </a>
                <a
                  href={`${docsUrl}/products/${slug}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 btn-ghost px-5 py-2.5 text-sm"
                >
                  <BookOpen className="w-4 h-4" aria-hidden="true" />
                  Docs
                </a>
                <Link
                  href={`/${l}/contact?interest=enterprise-sales&product=${slug}`}
                  className="inline-flex items-center gap-2 btn-ghost px-5 py-2.5 text-sm"
                >
                  <Phone className="w-4 h-4" aria-hidden="true" />
                  Contact Sales
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
