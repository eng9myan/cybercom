import type { ProductModule } from "@/components/products/ModuleExplorer";
import type { RoleWorkflow } from "@/components/products/RoleWorkflowExplorer";
import type { PermissionRole } from "@/components/products/PermissionsMatrix";
export type { ProductModule, RoleWorkflow, PermissionRole };

export interface ProductModulesData {
  modules: ProductModule[];
  roleWorkflows: RoleWorkflow[];
  permissionRoles: PermissionRole[];
}

const M = (
  name: string,
  category: ProductModule["category"],
  desc: string,
  roles: string[],
  workflow: string,
  permission: string,
  demoRoute?: string
): ProductModule => ({ name, category, desc, roles, workflow, permission, demoRoute });

// ─────────────────────────────────────────────────────────────────────────────
// CyMed Hospital
// ─────────────────────────────────────────────────────────────────────────────
const hospitalModules: ProductModule[] = [
  // Clinical
  M("Reception & Registration", "clinical", "Patient registration, insurance capture, MRN assignment, and ID verification at the front desk.", ["Receptionist", "Registration Clerk"], "Arrive → Identify → Verify Insurance → Create MRN → Print Wristband", "receptionist", "/reception"),
  M("Patient Management", "clinical", "Unified patient record: demographics, visit history, allergies, chronic conditions, care team assignments.", ["Receptionist", "Nurse", "Physician"], "Search Patient → Review History → Update Record → Assign Physician", "receptionist", "/patients"),
  M("Admission (ADT)", "clinical", "Inpatient admission, transfer, and discharge workflow with bed assignment, ADT events, and payer authorization.", ["Admissions Officer", "Bed Manager"], "Receive Order → Select Bed → Authorize → Admit → Generate ADT", "admissions", "/adt"),
  M("Emergency Module", "clinical", "ED triage, ESI scoring, trauma bay management, waiting room board, and real-time escalation alerts.", ["ED Triage Nurse", "Emergency Physician"], "Arrive → ESI Triage → Board Assignment → Evaluate → Disposition", "emergency", "/emergency"),
  M("Bed Board", "clinical", "Real-time visual bed map with occupancy status, cleaning queue, isolation flags, and census forecasting.", ["Bed Manager", "Charge Nurse"], "View Map → Filter Unit → Request Clean → Assign Bed → Confirm", "bed-manager", "/bed-board"),
  M("Nurse Station", "clinical", "Nursing workflow hub: shift assignments, task lists, vital signs entry, medication admin record (MAR), and care notes.", ["Nurse", "Charge Nurse"], "Receive Handover → Review Tasks → Enter Vitals → Administer Meds → Document", "nurse", "/nurse-station"),
  M("Doctor Workspace", "clinical", "Physician dashboard with patient list, CPOE, clinical notes (SOAP/APSO), results review, and order management.", ["Physician", "Resident", "Consultant"], "Open Patient → Review Results → Place Orders → Write Notes → Sign", "physician", "/doctor"),
  M("Inpatient EMR & CPOE", "clinical", "Structured electronic medical records with computerized physician order entry — labs, meds, radiology, consults.", ["Physician", "Resident"], "Select Patient → Write Orders → Pharmacist Verify → Nurse Execute → Document", "physician", "/emr"),
  M("OR Scheduling & Management", "clinical", "Surgical scheduling, pre-op checklist, equipment booking, sterile instrument tracking, and post-op handover.", ["OR Coordinator", "Surgeon", "Anesthetist"], "Schedule → Pre-op Check → Equipment Reserve → Operate → Post-op Handover", "or-coordinator", "/or"),
  M("ICU / Virtual ICU", "clinical", "Intensive care flowsheet, ventilator parameters, drip management, hourly vitals, and telemedicine ICU consults.", ["ICU Nurse", "Intensivist"], "Admit ICU → Setup Monitor → Flowsheet → Drips → Remote Consult → Transfer Out", "icu", "/icu"),
  M("Blood Bank", "clinical", "Type & screen, crossmatch, blood product inventory, transfusion workflow, and adverse reaction reporting.", ["Blood Bank Tech", "Transfusion Nurse"], "Order → Type & Screen → Crossmatch → Issue → Transfuse → Document", "blood-bank", "/blood-bank"),
  M("Pharmacy Dispensing", "clinical", "Ward pharmacy: unit-dose dispensing, narcotic log, IV admixture, barcode scan verification, and return management.", ["Pharmacist", "Pharmacy Tech"], "Receive Order → Verify → Prepare → Barcode Scan → Dispense → MAR Update", "pharmacist", "/pharmacy"),
  M("Laboratory / LIS", "clinical", "Full lab order-to-result workflow: specimen collection, LIS routing, auto-verification, and CPOE result alerts.", ["Lab Technician", "Phlebotomist"], "Order → Collect → Label → Analyze → Auto-Verify → Result Alert", "lab-tech", "/lab"),
  M("Radiology / RIS", "clinical", "Radiology information system with DICOM/PACS, structured reporting, AI-assisted reads, and worklist management.", ["Radiologist", "Radiographer"], "Order → Schedule → Acquire Image → Read → Report → Sign → Distribute", "radiologist", "/radiology"),
  M("Consent Management", "clinical", "Digital informed consent: procedure-specific templates, patient signature, witness capture, and consent log.", ["Nurse", "Physician"], "Select Procedure → Generate Form → Explain → Patient Signs → Witness → Archive", "nurse", "/consent"),
  M("Discharge & Planning", "clinical", "Discharge planning: criteria tracking, post-acute referral, patient education, follow-up scheduling, and summary generation.", ["Physician", "Case Manager"], "Flag Ready → Complete Criteria → Schedule Follow-up → Generate Summary → Discharge", "physician", "/discharge"),
  M("Scheduling", "clinical", "Appointment booking for outpatient clinics, procedures, and follow-ups integrated with inpatient visit planning.", ["Receptionist", "Scheduler"], "Request → Check Availability → Book → Confirm → SMS Reminder", "receptionist", "/scheduling"),
  M("Order Sets", "clinical", "Pre-built clinical order sets for common diagnoses — sepsis, chest pain, stroke — reducing physician entry time.", ["Physician", "Clinical Pharmacist"], "Diagnose → Select Order Set → Modify → Approve → Execute", "physician", "/order-sets"),
  M("Telehealth", "clinical", "Video consultation module for remote specialist review, post-discharge follow-up, and virtual ICU coverage.", ["Physician", "Nurse"], "Schedule → Send Link → Join Video → Consult → Document → Close Encounter", "physician", "/telehealth"),
  M("Social Work", "clinical", "Social work assessments, community resource referrals, discharge barrier tracking, and care coordination notes.", ["Social Worker", "Case Manager"], "Screen → Assess → Refer → Track → Document → Close Case", "social-worker", "/social-work"),
  M("Wound Care", "clinical", "Wound assessment charting with photo documentation, dressing orders, healing progress tracking, and consult workflow.", ["Wound Nurse", "Physician"], "Assess Wound → Photo → Document → Order Dressing → Track Healing", "nurse", "/wound-care"),
  M("Nutrition & Dietetics", "clinical", "Nutritional screening, diet order management, enteral/parenteral feeding protocols, and dietitian consult notes.", ["Dietitian", "Nurse"], "Screen → Assess → Calculate Needs → Order Diet → Monitor → Adjust", "dietitian", "/nutrition"),
  M("Maternity & Obstetrics", "clinical", "Labor & delivery workflows: partograph, fetal monitoring, delivery notes, newborn registration, and postpartum care.", ["Obstetrician", "Midwife", "L&D Nurse"], "Admit → Partograph → Fetal Monitor → Deliver → Newborn Register → Postpartum", "physician", "/maternity"),
  M("Allied Health", "clinical", "Physiotherapy, occupational therapy, speech therapy scheduling, session notes, and progress tracking.", ["Physical Therapist", "OT", "Speech Therapist"], "Refer → Assess → Schedule → Treat → Document → Discharge", "allied-health", "/allied-health"),
  M("Clinical Research", "clinical", "Protocol management, patient enrollment, IRB tracking, data collection, and adverse event reporting.", ["Research Coordinator", "Principal Investigator"], "Protocol Load → Screen → Enroll → Collect Data → AE Report → Submit", "researcher", "/research"),
  M("Home Health", "clinical", "Home visit scheduling, remote vital sign collection, medication compliance tracking, and care team communication.", ["Home Health Nurse", "Care Coordinator"], "Discharge Plan → Schedule Visit → Collect Vitals → Document → Alert MD", "home-health", "/home-health"),
  M("MoH Integration", "clinical", "Ministry of Health reporting, national disease registry submission, DRG coding, and NPHIES claim integration.", ["HIM Coder", "IT Admin"], "Generate Report → Validate → Map Codes → Submit → Receive ACK", "admin", "/moh"),
  M("National Registry", "clinical", "National patient registry submissions for cancer, chronic disease, newborn screening, and immunization.", ["HIM Staff", "Physician"], "Identify Case → Complete Registry Form → Validate → Submit → Confirm", "him", "/registry"),
  M("Command Center", "clinical", "Real-time hospital operations dashboard: capacity, throughput, staffing, alerts, and escalation command.", ["Hospital Director", "Charge Nurse"], "Monitor Board → Identify Bottleneck → Escalate → Assign Resource → Resolve", "operations", "/command-center"),
  // AI
  M("AI Scribe", "ai", "Ambient voice documentation: AI converts physician-patient conversations into structured clinical notes in real time.", ["Physician", "Resident"], "Start Encounter → Speak → AI Transcribe → Review Draft → Edit → Sign", "physician", "/ai-scribe"),
  M("Sepsis Alert", "ai", "Early sepsis detection using qSOFA, SIRS, and NEWS2 scoring with automated nursing escalation triggers.", ["Nurse", "Rapid Response Team"], "Monitor Vitals → Score Alert → Notify MD → Sepsis Protocol → Document", "nurse", "/sepsis-alert"),
  M("IOMT / Wearables", "ai", "Real-time patient vitals streaming from bedside monitors, wearables, and RTLS location badges.", ["ICU Nurse", "Physician"], "Connect Device → Stream → Threshold Alert → View Trend → Intervene", "icu", "/iomt"),
  M("RTLS", "ai", "Real-time location system for patients, staff, and high-value equipment using RFID/BLE asset tracking.", ["Security", "Asset Manager"], "Tag Asset → Monitor Location → Trigger Alert → Locate → Confirm", "operations", "/rtls"),
  M("Genomics", "ai", "Pharmacogenomics alerts, variant interpretation, hereditary risk flags, and genetic counseling referral workflows.", ["Geneticist", "Physician"], "Order Test → Sequence → Interpret → Alert Variant → Counsel → Document", "physician", "/genomics"),
  M("30-Day Readmission AI", "ai", "ML model predicting readmission risk at discharge, triggering post-discharge calls and follow-up scheduling.", ["Case Manager", "Physician"], "Flag at Discharge → Score Risk → Alert Care Manager → Schedule Follow-up", "case-manager", "/ai-readmission"),
  M("Bed Demand Forecasting", "ai", "Predictive analytics for bed demand over 24–72h, enabling proactive capacity planning and elective scheduling.", ["Bed Manager", "Operations"], "Pull Census → Run Model → Forecast → Adjust Electives → Plan Staffing", "operations", "/ai-bed-forecast"),
  M("Surgical Risk Scoring", "ai", "Pre-operative risk stratification using ASA class, ACS NSQIP predictions, and comorbidity scoring.", ["Anesthesiologist", "Surgeon"], "Enter Comorbidities → Run Score → Review Risk → Modify Plan → Document", "physician", "/surgical-risk"),
  // Finance
  M("Finance & Revenue Cycle", "finance", "End-to-end revenue cycle: charge capture, insurance claims, remittance posting, denial management, and AR reporting.", ["Finance Manager", "Billing Specialist"], "Capture Charges → Submit Claim → Receive EOB → Post Payment → Manage Denials", "finance", "/finance"),
  M("Accounting (AP/AR)", "finance", "General ledger, accounts payable, accounts receivable, journal entries, trial balance, and financial statements.", ["Accountant"], "Post Entry → Approve Invoice → Pay → Reconcile → Generate Report", "finance", "/accounting"),
  M("Fixed Assets", "finance", "Medical equipment registry, depreciation schedules, disposal tracking, and asset audit reports.", ["Finance Manager", "Asset Manager"], "Register Asset → Set Depreciation → Run Monthly → Audit → Report", "finance", "/assets"),
  // HR
  M("HR & Employees", "hr", "Employee profiles, contract management, job grades, department structure, and organizational chart.", ["HR Officer", "HR Manager"], "Hire → Create Profile → Set Grade → Assign Department → Onboard", "hr", "/hr/employees"),
  M("Payroll (WPS)", "hr", "MOCI-compliant WPS payroll processing with allowances, deductions, overtime, end-of-service, and pay slips.", ["Payroll Officer"], "Lock Attendance → Calculate → Deductions → Generate Slip → WPS Submit", "hr", "/hr/payroll"),
  M("Attendance & Shifts", "hr", "Biometric integration, shift scheduling, leave requests, overtime tracking, and attendance exception handling.", ["HR Officer", "Department Head"], "Import Biometric → Review → Approve Leave → Adjust Shifts → Finalize", "hr", "/hr/attendance"),
  // Inventory
  M("Medical Supply Inventory", "inventory", "Real-time stock tracking for medications, consumables, and implants across departments and storerooms.", ["Inventory Officer", "Nurse"], "Check Stock → Request → Issue → Update Qty → Reorder Alert", "inventory", "/inventory"),
  M("Procurement", "inventory", "Purchase requisition, RFQ, supplier comparison, PO generation, goods receipt, and invoice matching.", ["Procurement Officer", "Finance"], "Requisition → Approve → RFQ → PO → Receive → 3-Way Match → Pay", "inventory", "/procurement"),
  // Reports
  M("Reports & Dashboards", "reports", "Executive dashboards, clinical KPIs, financial analytics, department performance, and regulatory report exports.", ["Hospital Director", "Manager", "All"], "Select Dashboard → Filter Period → Drill Down → Export → Share", "manager", "/reports"),
  M("Helpdesk", "admin", "Internal IT and facilities helpdesk with ticket tracking, SLA monitoring, escalation, and resolution reporting.", ["Staff", "IT Admin"], "Submit Ticket → Assign → Resolve → Close → Rate", "admin", "/helpdesk"),
];

const hospitalWorkflows: RoleWorkflow[] = [
  {
    role: "Receptionist / Admissions",
    description: "Handles patient registration, insurance verification, bed assignment, and visitor coordination at the front desk.",
    steps: [
      { action: "Register Patient", detail: "Search existing MRN or create new record with demographics, contact, and ID." },
      { action: "Insurance Verification", detail: "Submit eligibility check to payer via NPHIES or manual entry; document authorization number." },
      { action: "Assign Bed", detail: "Check bed board availability, select appropriate unit and room, flag isolation requirements." },
      { action: "Print Wristband", detail: "Generate patient wristband with MRN, name, DOB, and allergy flags; scan to confirm." },
      { action: "ADT Notification", detail: "System triggers ADT event — notifies nursing unit, housekeeping, and billing of admission." },
    ],
  },
  {
    role: "Physician (Inpatient)",
    description: "Manages the full clinical encounter: orders, notes, results review, and discharge planning for admitted patients.",
    steps: [
      { action: "Patient List Review", detail: "Open morning list with flagged critical results, pending orders, and overnight events." },
      { action: "CPOE — Place Orders", detail: "Enter lab, medication, radiology, and consult orders using order sets or manual entry." },
      { action: "Clinical Note", detail: "Dictate or type SOAP note; AI Scribe captures ambient voice and drafts the note automatically." },
      { action: "Results Review", detail: "Review lab and imaging results; acknowledge critical values; update clinical plan." },
      { action: "Discharge Summary", detail: "Complete discharge criteria, write summary, arrange follow-up appointments, and sign." },
    ],
  },
  {
    role: "Nurse",
    description: "Executes clinical care at the bedside: vital signs, medication administration, patient education, and care documentation.",
    steps: [
      { action: "Receive Handover", detail: "Review shift report, outstanding tasks, pending medications, and patient acuity from previous nurse." },
      { action: "Vital Signs Entry", detail: "Enter or auto-import vitals from bedside monitor; system flags abnormal values for escalation." },
      { action: "MAR — Medication Admin", detail: "Scan patient wristband and medication barcode; confirm 5 rights before administering." },
      { action: "Care Documentation", detail: "Document nursing assessments, interventions, patient response, and wound/fall risk scores." },
      { action: "Escalation", detail: "Trigger rapid response or sepsis protocol alert if patient deteriorates; notify attending physician." },
    ],
  },
  {
    role: "OR Coordinator",
    description: "Schedules surgical cases, coordinates pre-op preparation, equipment, and ensures sterile instrument readiness.",
    steps: [
      { action: "Schedule Case", detail: "Book OR slot, assign surgeon, anesthesiologist, and scrub team; send notification." },
      { action: "Pre-op Checklist", detail: "Confirm H&P complete, consent signed, NPO status, blood type verified, and implants available." },
      { action: "Equipment Booking", detail: "Reserve specialized equipment (C-arm, robot, endoscope) and sterile instrument sets." },
      { action: "Intraoperative Capture", detail: "Document procedure start/stop, anesthesia type, implants used, and sponge count." },
      { action: "Post-op Handover", detail: "Transfer patient to PACU with complete operative note; update bed board; debrief team." },
    ],
  },
  {
    role: "Finance / Billing",
    description: "Captures charges, processes insurance claims, manages denials, and posts payments to close the revenue cycle.",
    steps: [
      { action: "Charge Capture", detail: "Review clinical activity for billable services; verify CPT/ICD codes against documentation." },
      { action: "Claim Submission", detail: "Submit NPHIES or payer-specific claim with supporting authorization and diagnosis codes." },
      { action: "ERA / Remittance", detail: "Receive electronic remittance advice; auto-post payments; flag under-paid claims." },
      { action: "Denial Management", detail: "Review denied claims, attach corrected documentation, and resubmit within timely filing period." },
      { action: "AR Reporting", detail: "Generate aging AR report; escalate accounts over 60 days; update CFO dashboard." },
    ],
  },
  {
    role: "HR Officer",
    description: "Manages staff records, payroll processing, attendance, and compliance with labor regulations.",
    steps: [
      { action: "Employee Onboarding", detail: "Create staff profile, attach contracts, assign department, set job grade and salary." },
      { action: "Attendance Import", detail: "Sync biometric data, review exceptions, approve leave requests and overtime." },
      { action: "Payroll Calculation", detail: "Lock attendance, apply allowances/deductions, calculate end-of-service, generate payslips." },
      { action: "WPS Submission", detail: "Export WPS file in MOCI format, submit to bank, confirm employee payment confirmation." },
      { action: "HR Reporting", detail: "Generate headcount, turnover, leave liability, and payroll cost reports for management." },
    ],
  },
];

const hospitalPermissions: PermissionRole[] = [
  { role: "System Admin", level: "full", categories: ["clinical", "erp", "ai", "operations", "finance", "hr", "inventory", "reports", "admin"], description: "Full platform access — all modules, all settings, user management." },
  { role: "Hospital Director", level: "operations", categories: ["clinical", "operations", "finance", "hr", "reports"], description: "Operational and executive visibility across departments; no clinical data entry." },
  { role: "Physician", level: "clinical", categories: ["clinical", "ai", "reports"], description: "Full clinical module access — orders, notes, results; no financial or HR data." },
  { role: "Nurse", level: "clinical", categories: ["clinical", "ai"], description: "Clinical workflow access — vitals, MAR, care notes; no financial records." },
  { role: "Receptionist", level: "limited", categories: ["clinical"], description: "Patient registration, scheduling, and bed board only; no clinical or financial records." },
  { role: "Accountant", level: "finance", categories: ["finance", "reports"], description: "Revenue cycle, accounts, and financial reporting; no clinical data." },
  { role: "HR Officer", level: "hr", categories: ["hr", "reports"], description: "Employee management, payroll, and attendance; no clinical or financial records." },
  { role: "Inventory Officer", level: "inventory", categories: ["inventory", "reports"], description: "Stock management, procurement, and inventory reporting." },
  { role: "Radiologist", level: "clinical", categories: ["clinical", "ai", "reports"], description: "Radiology worklist, DICOM viewer, reporting; no ward access." },
];

// ─────────────────────────────────────────────────────────────────────────────
// CyMed Clinic
// ─────────────────────────────────────────────────────────────────────────────
const clinicModules: ProductModule[] = [
  // Clinical
  M("Patient Registration", "clinical", "New patient onboarding: demographics, photo ID, insurance capture, MRN assignment, and consent forms.", ["Receptionist", "Registration Clerk"], "Arrive → ID Check → Insurance → MRN → Consent → Card Print", "receptionist", "/reception"),
  M("Appointment Scheduling", "clinical", "Multi-resource booking: physician, room, and equipment with waitlist management and automated SMS/email reminders.", ["Receptionist", "Scheduler"], "Search Slot → Select Physician → Book → Confirm → Auto-Reminder", "receptionist", "/scheduling"),
  M("Patient Check-In & ADT", "clinical", "Self-service kiosk or staff-assisted check-in, room assignment, and waiting room queue display.", ["Receptionist", "Patient"], "Arrive → QR Scan → Confirm Details → Assign Room → Display Queue", "receptionist", "/check-in"),
  M("Insurance Verification", "clinical", "Real-time eligibility check, benefit breakdown, co-pay calculation, and pre-authorization submission.", ["Insurance Coordinator"], "Submit Eligibility → Receive Response → Document Benefits → Notify Patient", "insurance", "/insurance"),
  M("Electronic Medical Record (EMR)", "clinical", "Structured outpatient EMR: problem list, medication list, allergy registry, SOAP notes, and encounter summaries.", ["Physician", "Nurse"], "Open Encounter → Chief Complaint → Assessment → Plan → Sign Note", "physician", "/emr"),
  M("E-Prescribing", "clinical", "Electronic prescription with formulary checks, pharmacy routing, controlled substance log, and patient history.", ["Physician"], "Select Medication → Formulary Check → Add Dose → Send to Pharmacy → Log", "physician", "/prescriptions"),
  M("Clinical Decision Support", "clinical", "Evidence-based alerts at point-of-care: drug-drug interactions, allergy conflicts, guideline reminders, and preventive care gaps.", ["Physician", "Nurse"], "Trigger Alert → Review Recommendation → Accept or Override → Document Reason", "physician", "/cds"),
  M("Lab Orders & Results", "clinical", "Order lab tests, track specimen status, receive verified results, and view trends over time.", ["Physician", "Nurse"], "Order → Collect Specimen → Track → Results → Alert Critical → Acknowledge", "physician", "/lab"),
  M("Referral Management", "clinical", "Internal and external referrals with document attachment, referral tracking, feedback loop, and acceptance confirmation.", ["Physician", "Referral Coordinator"], "Write Referral → Attach Notes → Send → Track Status → Receive Feedback", "physician", "/referrals"),
  M("Telemedicine", "clinical", "Video consultation module with virtual waiting room, in-visit notes, e-prescription, and secure file sharing.", ["Physician", "Patient"], "Schedule → Send Link → Virtual Wait → Video Consult → Note → Close", "physician", "/telehealth"),
  // AI
  M("AI Scribe", "ai", "Ambient AI documentation: transcribes physician-patient conversations into structured SOAP notes in real time.", ["Physician"], "Enable Mic → Converse → AI Draft → Review → Edit → Sign", "physician", "/ai-scribe"),
  M("No-Show Prediction", "ai", "ML model scoring appointment no-show risk; triggers proactive reminder calls for high-risk patients.", ["Scheduler", "Front Desk"], "Score Appointments → Flag High-Risk → Send Extra Reminder → Track Outcome", "manager", "/ai-no-show"),
  M("Chronic Risk Stratification", "ai", "Identifies high-risk chronic disease patients due for preventive care, lab monitoring, or escalation.", ["Physician", "Care Manager"], "Analyze Patient List → Flag High-Risk → Generate Outreach List → Contact", "physician", "/ai-chronic"),
  M("Drug Interaction Alerts", "ai", "Real-time AI-powered drug-drug, drug-allergy, and drug-condition interaction checking at prescribing.", ["Physician"], "Prescribe → Check Interactions → Alert → Review → Override or Change", "physician", "/ai-interactions"),
  M("ICD-11 Code Suggestions", "ai", "Auto-suggests ICD-11 diagnosis codes based on clinical note content, reducing coding time and errors.", ["Physician", "Coder"], "Write Note → AI Suggests Codes → Review → Accept or Modify → Post", "physician", "/ai-coding"),
  // Finance
  M("Finance & Billing", "finance", "Outpatient revenue cycle: charge capture, co-pay collection, insurance claims, and ERA posting.", ["Finance Manager", "Billing Clerk"], "Capture Charge → Verify Insurance → Submit Claim → Receive ERA → Post → Report", "finance", "/finance"),
  M("Accounting (AP/AR)", "finance", "General ledger, vendor invoices, patient accounts receivable, and monthly financial close.", ["Accountant"], "Post Entry → Approve → Pay Vendor → Reconcile → Month-End Close", "finance", "/accounting"),
  // HR
  M("HR & Staff Management", "hr", "Staff profiles, credentials tracking, contract management, and organizational structure.", ["HR Officer"], "Hire → Create Profile → Credentials → Contract → Assign Department", "hr", "/hr/employees"),
  M("Payroll (WPS)", "hr", "WPS-compliant payroll with allowances, deductions, overtime, and automated payslip distribution.", ["Payroll Officer"], "Lock Attendance → Calculate Payroll → Generate Slips → Submit WPS", "hr", "/hr/payroll"),
  M("Attendance & Leave", "hr", "Biometric or app-based attendance, leave request workflow, and shift scheduling for clinic staff.", ["HR Officer", "Department Head"], "Import Attendance → Approve Leave → Schedule Shifts → Finalize Report", "hr", "/hr/attendance"),
  // Inventory
  M("Clinical Supply Inventory", "inventory", "Real-time stock tracking for medical consumables, vaccines, and clinic supplies.", ["Inventory Officer", "Nurse"], "Check Stock → Request → Issue → Update Qty → Trigger Reorder", "inventory", "/inventory"),
  M("Procurement", "inventory", "Purchase requests, supplier selection, PO generation, goods receipt, and invoice processing.", ["Procurement Officer"], "Requisition → Approve → PO → Receive Goods → Invoice Match → Pay", "inventory", "/procurement"),
  // Reports
  M("Reports & Dashboards", "reports", "Clinic KPIs, physician productivity, revenue analytics, patient satisfaction, and appointment utilization.", ["Clinic Manager", "Finance", "All"], "Open Dashboard → Select Period → Filter → Drill Down → Export", "manager", "/reports"),
];

const clinicWorkflows: RoleWorkflow[] = [
  {
    role: "Receptionist",
    description: "Manages patient arrival, registration, scheduling, and front-desk coordination throughout the clinic day.",
    steps: [
      { action: "Patient Registration", detail: "Search existing record or create new patient with demographics, insurance, and consent documentation." },
      { action: "Appointment Scheduling", detail: "Book appointment with physician and room; set duration, type (new/follow-up), and send SMS confirmation." },
      { action: "Check-In", detail: "Check in patient on arrival; confirm details; assign to waiting queue and display on board." },
      { action: "Co-pay Collection", detail: "Calculate co-pay from insurance response; collect payment by cash, card, or split; print receipt." },
      { action: "Follow-up Booking", detail: "After physician orders follow-up, book next appointment and send calendar invite to patient." },
    ],
  },
  {
    role: "Physician",
    description: "Conducts clinical encounters, documents assessments, places orders, and coordinates specialist referrals.",
    steps: [
      { action: "Open Encounter", detail: "Select patient from schedule; review problem list, medications, allergies, and prior visit notes." },
      { action: "Clinical Assessment", detail: "Document chief complaint, HPI, physical exam findings using structured SOAP or free-text format." },
      { action: "AI-Assisted Note", detail: "Enable AI Scribe to capture ambient dictation; review draft note; correct and finalize." },
      { action: "Orders & E-Prescribing", detail: "Place lab orders, imaging requests, and e-prescriptions with formulary check and drug interaction alert." },
      { action: "Referral & Plan", detail: "Send specialist referral with clinical summary; document care plan; set follow-up appointment." },
    ],
  },
  {
    role: "Nurse",
    description: "Prepares patients for the physician, documents vitals and chief complaint, assists with procedures.",
    steps: [
      { action: "Call Patient", detail: "Call from waiting queue, escort to room, confirm identity with two patient identifiers." },
      { action: "Vital Signs", detail: "Measure and enter BP, HR, Temp, SpO2, weight, and BMI; flag any abnormal values." },
      { action: "Chief Complaint", detail: "Document reason for visit, pain score, current medications, and recent symptom history." },
      { action: "Assist Physician", detail: "Prepare equipment, assist with minor procedures, collect specimens, and label for lab." },
      { action: "Patient Education", detail: "Provide pre-discharge education on medications, wound care, or lifestyle modifications; document." },
    ],
  },
  {
    role: "Clinic Manager",
    description: "Oversees clinic operations, staff scheduling, KPI monitoring, and patient experience management.",
    steps: [
      { action: "Daily Briefing", detail: "Review appointment load, staff availability, and equipment status on operations dashboard." },
      { action: "Capacity Management", detail: "Adjust booking slots based on no-show predictions and same-day walk-in demand." },
      { action: "Staff Coordination", detail: "Assign nurses to physicians, manage break schedules, and resolve escalations." },
      { action: "KPI Review", detail: "Monitor wait times, LWBS rate, patient satisfaction scores, and revenue per encounter." },
      { action: "Report & Improve", detail: "Export performance report; identify improvement areas; update protocols and staff training." },
    ],
  },
  {
    role: "Accountant",
    description: "Processes clinic billing, insurance claims, payment posting, and financial reporting.",
    steps: [
      { action: "Charge Review", detail: "Verify charges against documentation; confirm CPT codes match procedures performed." },
      { action: "Claim Submission", detail: "Submit claims to insurance payers with required authorization and diagnosis codes." },
      { action: "Payment Posting", detail: "Receive and post ERA payments; flag discrepancies and short-payments for follow-up." },
      { action: "Denial Resolution", detail: "Appeal denied claims with corrected documentation; resubmit within payer filing window." },
      { action: "Financial Report", detail: "Generate monthly P&L, AR aging, and collection rate report for clinic management." },
    ],
  },
];

const clinicPermissions: PermissionRole[] = [
  { role: "System Admin", level: "full", categories: ["clinical", "erp", "ai", "operations", "finance", "hr", "inventory", "reports", "admin"], description: "Full access to all modules and settings." },
  { role: "Clinic Manager", level: "operations", categories: ["clinical", "operations", "hr", "reports"], description: "Operational oversight: staff, schedules, and performance KPIs." },
  { role: "Receptionist", level: "limited", categories: ["clinical"], description: "Patient registration, scheduling, and check-in only." },
  { role: "Physician", level: "clinical", categories: ["clinical", "ai", "reports"], description: "Full clinical module access — EMR, orders, referrals." },
  { role: "Nurse", level: "clinical", categories: ["clinical", "ai"], description: "Vitals, nursing documentation, and care workflows." },
  { role: "Accountant", level: "finance", categories: ["finance", "reports"], description: "Billing, claims, accounts, and financial reporting." },
  { role: "HR Officer", level: "hr", categories: ["hr", "reports"], description: "Staff management, payroll, attendance, and HR reporting." },
  { role: "Inventory Officer", level: "inventory", categories: ["inventory", "reports"], description: "Supply management and procurement." },
];

// ─────────────────────────────────────────────────────────────────────────────
// CyMed Pharmacy
// ─────────────────────────────────────────────────────────────────────────────
const pharmacyModules: ProductModule[] = [
  M("POS & Dispensing", "operations", "Point-of-sale drug dispensing with barcode scan verification, OTC sales, and prescription fulfillment queue.", ["Pharmacist", "Pharmacy Tech"], "Receive Rx → Scan Drug → Verify → Dispense → POS → Receipt", "pharmacist", "/pos"),
  M("Prescription Verification", "clinical", "Multi-stage Rx verification: pharmacist clinical review, DUR, dosing check, and patient history cross-reference.", ["Pharmacist"], "Receive → Clinical Review → DUR → Dose Check → Approve → Label", "pharmacist", "/verification"),
  M("Drug Interaction Checking", "clinical", "Real-time drug-drug, drug-allergy, and drug-food interaction alerts at dispensing with severity classification.", ["Pharmacist"], "Queue Rx → Check Interactions → Alert → Override with Reason → Document", "pharmacist", "/interactions"),
  M("Narcotic & Controlled Drug Log", "clinical", "Controlled substance dispensing log with DEA/MOH compliance, witness signature, count reconciliation, and audit trail.", ["Pharmacist", "Pharmacy Manager"], "Dispense → Log Count → Witness Sign → Reconcile End-of-Day → Audit Report", "pharmacist", "/narcotic"),
  M("E-Prescription Integration", "clinical", "FHIR-based e-prescription receipt from hospital EMR, clinic systems, and MOH e-Prescription network.", ["Pharmacist"], "Receive e-Rx → Validate → Queue → Fill → Notify Patient", "pharmacist", "/e-prescription"),
  M("Retail Counter (OTC)", "operations", "Over-the-counter product sales with loyalty points, promotions, combo pricing, and multi-tender checkout.", ["Pharmacy Tech", "Cashier"], "Select Product → Check Loyalty → Apply Promo → POS → Print Receipt", "pharmacy-tech", "/pos-otc"),
  M("Clinical Pharmacy Review", "clinical", "Pharmacist-led medication therapy management: comprehensive review, deprescribing recommendations, adherence support.", ["Clinical Pharmacist"], "Pull Patient Meds → Review → Identify Issues → Recommend → Document → Follow-up", "pharmacist", "/clinical-review"),
  M("Patient Counseling", "clinical", "Structured medication counseling workflow with education points, side effect discussion, and follow-up scheduling.", ["Pharmacist"], "Review Rx → Counsel Patient → Verify Understanding → Schedule Follow-up", "pharmacist", "/counseling"),
  M("Compounding Management", "clinical", "Extemporaneous compound preparation records, ingredient tracking, beyond-use dating, and QC documentation.", ["Pharmacist", "Compounding Tech"], "Compound Order → Calculate Formula → Prepare → QC → Label → Dispense", "pharmacist", "/compounding"),
  M("Patient Records Viewer", "clinical", "Read-only access to linked patient medication history, allergy list, and clinical notes from integrated EMR.", ["Pharmacist"], "Search Patient → View History → Review Allergies → Cross-Reference Current Rx", "pharmacist", "/patient-records"),
  M("Drug Interaction AI", "ai", "AI model detecting subtle multi-drug interaction patterns beyond standard databases, including new ADR signals.", ["Pharmacist"], "Submit Med List → AI Analyze → Flag Interactions → Severity Rank → Alert", "pharmacist", "/ai-interactions"),
  M("Demand Forecasting", "ai", "ML-driven drug demand forecasting using historical dispensing trends, season, and patient population data.", ["Pharmacy Manager", "Inventory Officer"], "Pull History → Run Model → Forecast Demand → Adjust Par Levels → Order", "manager", "/ai-demand"),
  M("Expiry Alert AI", "ai", "Proactive expiry monitoring with AI-ranked prioritization for near-expiry stock rotation and disposal planning.", ["Pharmacist", "Inventory Officer"], "Scan Batch → AI Flag Near-Expiry → Prioritize → Rotate Stock → Document", "pharmacist", "/ai-expiry"),
  M("Pharmacy Billing & POS Revenue", "finance", "POS revenue posting, insurance claim generation, co-pay reconciliation, and pharmacy revenue reporting.", ["Finance Officer"], "End-of-Day POS → Match Claims → Post Revenue → Reconcile → Report", "finance", "/billing"),
  M("Accounting (AP/AR)", "finance", "Supplier payable, patient receivable, journal entries, and monthly pharmacy financial close.", ["Accountant"], "Post → Approve → Pay → Reconcile → Close", "finance", "/accounting"),
  M("Insurance Claims", "finance", "Electronic claim submission for prescription coverage, prior authorization tracking, and denial management.", ["Insurance Coordinator"], "Verify Coverage → Submit Claim → Track → ERA → Denial → Resubmit", "finance", "/insurance"),
  M("HR & Staff Management", "hr", "Pharmacist and technician profiles, license tracking, shift scheduling, and performance management.", ["HR Officer"], "Hire → License Verify → Schedule → Evaluate → Renew License", "hr", "/hr/employees"),
  M("Payroll (WPS)", "hr", "WPS payroll for pharmacy staff with allowance structures and automated payslip generation.", ["Payroll Officer"], "Lock Attendance → Calculate → Slips → WPS Submit", "hr", "/hr/payroll"),
  M("Attendance & Shifts", "hr", "Pharmacist and tech shift management, leave requests, and biometric attendance integration.", ["HR Officer"], "Import Biometric → Approve Leave → Generate Schedule → Finalize", "hr", "/hr/attendance"),
  M("Drug Inventory & Stock Control", "inventory", "Real-time drug stock by SKU, batch, and expiry with bin location and automatic reorder triggers.", ["Inventory Officer", "Pharmacist"], "Receive Stock → Scan Barcode → Update Qty → Set Par → Trigger Reorder", "inventory", "/inventory"),
  M("Supplier Management", "inventory", "Pharmaceutical supplier registry, pricing agreements, lead time tracking, and vendor performance scoring.", ["Procurement Officer"], "Register Supplier → Agree Terms → Track Delivery → Score Performance", "inventory", "/suppliers"),
  M("Procurement & Purchasing", "inventory", "Drug purchase requisition, approval workflow, PO generation, goods receipt, and invoice matching.", ["Procurement Officer"], "Requisition → Approve → PO → Receive → Invoice Match → Pay", "inventory", "/procurement"),
  M("Cold Chain & Expiry Tracking", "inventory", "Temperature monitoring for cold-chain items, expiry date tracking, recall management, and disposal documentation.", ["Pharmacist", "Inventory Officer"], "Receive Cold Drug → Log Temp → Monitor → Alert Breach → Document", "inventory", "/cold-chain"),
  M("Sales & Dispensing Reports", "reports", "Daily dispensing volume, top drugs, pharmacist productivity, and regulatory compliance reports.", ["Pharmacy Manager", "All"], "Select Period → Filter Drug Class → View Volume → Export → Submit", "manager", "/reports/sales"),
  M("Financial Reports", "reports", "Revenue by channel (prescription vs OTC), insurance vs cash breakdown, and cost of goods sold analytics.", ["Finance Officer", "Manager"], "Select Period → Revenue Breakdown → Cost Analysis → Export", "finance", "/reports/finance"),
  M("Inventory Reports", "reports", "Stock on hand, slow-movers, near-expiry, procurement spend, and supplier performance reports.", ["Inventory Officer", "Manager"], "Select Period → Stock Report → Near-Expiry → Procurement Cost → Export", "inventory", "/reports/inventory"),
];

const pharmacyWorkflows: RoleWorkflow[] = [
  {
    role: "Pharmacist",
    description: "Receives, verifies, and dispenses prescriptions while ensuring clinical safety and patient counseling.",
    steps: [
      { action: "Receive Prescription", detail: "Accept paper, e-Rx, or hospital EMR prescription; verify prescriber credentials and signature." },
      { action: "Drug Utilization Review", detail: "Perform DUR — check drug-drug interactions, allergy conflicts, and dose appropriateness." },
      { action: "Prepare & Label", detail: "Count or compound medication; print label with patient name, dose, route, frequency, and expiry." },
      { action: "Barcode Verification", detail: "Scan final product barcode against prescription to confirm correct drug, dose, and patient." },
      { action: "Counsel & Dispense", detail: "Counsel patient on use, side effects, and storage; dispense; document in patient record." },
    ],
  },
  {
    role: "Pharmacy Technician",
    description: "Assists pharmacists with drug preparation, stock management, and POS operations under pharmacist supervision.",
    steps: [
      { action: "Queue Management", detail: "Receive prescriptions from counter; enter into queue; prioritize urgent or waiting patients." },
      { action: "Drug Retrieval", detail: "Pull medication from bin by barcode scan; confirm strength and form against prescription." },
      { action: "OTC Sales", detail: "Process over-the-counter sales on POS; apply loyalty points; collect payment." },
      { action: "Stock Replenishment", detail: "Check dispensing shelves against par levels; retrieve from stockroom; update bin qty." },
      { action: "End-of-Day Count", detail: "Perform end-of-day narcotic count; reconcile against log; get pharmacist sign-off." },
    ],
  },
  {
    role: "Pharmacy Manager",
    description: "Oversees pharmacy operations, staff performance, inventory KPIs, and regulatory compliance.",
    steps: [
      { action: "Daily Operations Review", detail: "Check dispensing volume, queue times, and staff productivity on operations dashboard." },
      { action: "Inventory Audit", detail: "Review stock levels, near-expiry items, and slow movers; approve disposal or return orders." },
      { action: "Staff Scheduling", detail: "Set pharmacist and technician shift schedule based on demand forecast and leave requests." },
      { action: "Compliance Check", detail: "Verify narcotic log reconciliation, temperature logs, and regulatory documentation completeness." },
      { action: "Performance Reporting", detail: "Generate weekly revenue, dispensing accuracy, and patient satisfaction reports for ownership." },
    ],
  },
  {
    role: "Finance Officer",
    description: "Manages pharmacy revenue cycle, insurance claim processing, and financial reporting.",
    steps: [
      { action: "POS Reconciliation", detail: "Match end-of-day POS totals against shift register; identify and resolve discrepancies." },
      { action: "Insurance Claim Batch", detail: "Compile daily insurance claims; verify authorization numbers; submit electronic batch." },
      { action: "ERA Posting", detail: "Receive remittance advice; post payments; flag denied or short-paid claims for follow-up." },
      { action: "AP Invoice Processing", detail: "Receive supplier invoices; match against POs; approve for payment; update cash flow." },
      { action: "Monthly Financial Close", detail: "Prepare monthly P&L, revenue by channel, and cost of goods sold report for management." },
    ],
  },
  {
    role: "HR Officer",
    description: "Manages pharmacy staff records, payroll, attendance, and license renewal tracking.",
    steps: [
      { action: "New Hire Setup", detail: "Create staff profile; verify pharmacist or technician license; set shift schedule and salary." },
      { action: "Attendance Review", detail: "Import biometric data; approve leave requests; flag absences for follow-up." },
      { action: "License Tracking", detail: "Monitor expiry dates for pharmacist licenses; send renewal reminders 90 days before expiry." },
      { action: "Payroll Processing", detail: "Lock attendance; apply allowances and overtime; generate payslips; submit WPS." },
      { action: "HR Reporting", detail: "Generate headcount, turnover, and payroll cost reports for pharmacy management." },
    ],
  },
];

const pharmacyPermissions: PermissionRole[] = [
  { role: "System Admin", level: "full", categories: ["clinical", "operations", "ai", "finance", "hr", "inventory", "reports", "admin"], description: "Full platform access — all modules and settings." },
  { role: "Pharmacy Manager", level: "operations", categories: ["clinical", "operations", "finance", "hr", "inventory", "reports"], description: "Full operational and management visibility." },
  { role: "Pharmacist", level: "clinical", categories: ["clinical", "ai", "operations"], description: "Dispensing, verification, counseling, and clinical review modules." },
  { role: "Pharmacy Technician", level: "limited", categories: ["operations", "inventory"], description: "POS, dispensing queue, and stock replenishment only." },
  { role: "Finance Officer", level: "finance", categories: ["finance", "reports"], description: "Billing, claims, reconciliation, and financial reporting." },
  { role: "HR Officer", level: "hr", categories: ["hr", "reports"], description: "Staff management, payroll, and attendance." },
];

// ─────────────────────────────────────────────────────────────────────────────
// CyMed Laboratory
// ─────────────────────────────────────────────────────────────────────────────
const laboratoryModules: ProductModule[] = [
  M("Test Order Management", "clinical", "Receive physician lab orders via CPOE integration or manual entry; validate, prioritize, and assign to worklist.", ["Lab Technician", "Lab Manager"], "Receive Order → Validate → Assign Section → Priority Flag → Worklist", "lab-tech", "/orders"),
  M("Sample Collection & Tracking", "clinical", "Phlebotomy scheduling, specimen collection documentation, tube labeling, and chain-of-custody barcode tracking.", ["Phlebotomist", "Lab Tech"], "Schedule Draw → Collect → Label Barcode → Log Chain → Transport", "phlebotomist", "/collection"),
  M("LIS Core", "clinical", "Laboratory information system core: specimen accession, workflow routing, result entry, and report generation.", ["Lab Technician", "Lab Manager"], "Accession → Route → Analyze → Enter Result → Verify → Report", "lab-tech", "/lis"),
  M("Worklist Management", "clinical", "Section-specific worklists (chemistry, hematology, microbiology) with status tracking and TAT monitoring.", ["Lab Technician"], "Open Worklist → Process Specimen → Enter Result → Flag → Complete", "lab-tech", "/worklist"),
  M("Results Entry & Verification", "clinical", "Manual and auto-imported result entry with two-stage verification: tech review and pathologist/supervisor sign-off.", ["Lab Technician", "Lab Supervisor"], "Enter Result → Tech Review → Auto Rules → Supervisor Verify → Release", "lab-tech", "/verification"),
  M("Auto-Verification Engine", "clinical", "Rule-based auto-verification applying Westgard QC, delta checks, and reference range logic to release results automatically.", ["Lab Supervisor", "Lab Manager"], "Set Rules → Run QC → Delta Check → Auto-Release → Audit Log", "lab-supervisor", "/auto-verification"),
  M("QC Management (Westgard)", "clinical", "Westgard multi-rule QC tracking, Levey-Jennings charts, control lot management, and corrective action documentation.", ["Lab Technician", "QC Officer"], "Run Controls → Plot Charts → Check Rules → Flag Violations → Action", "lab-tech", "/qc"),
  M("Microbiology Module", "clinical", "Culture, sensitivity, and organism identification workflows with EUCAST/CLSI breakpoints and antibiogram reporting.", ["Microbiologist", "Lab Tech"], "Receive Culture → Incubate → ID Organism → Sensitivity → Report → Antibiogram", "microbiologist", "/microbiology"),
  M("Blood Bank / Crossmatch", "clinical", "ABO/Rh typing, irregular antibody screen, crossmatch, unit selection, and transfusion compatibility reporting.", ["Blood Bank Tech"], "Request → Type & Screen → Crossmatch → Select Unit → Issue → Document", "blood-bank", "/blood-bank"),
  M("Analyzer Interfacing", "clinical", "Bidirectional analyzer connectivity via ASTM/HL7 for auto-download of results from chemistry, hematology, and coag analyzers.", ["Lab Manager", "IT Admin"], "Configure Interface → Verify Connection → Auto-Download → Validate → Release", "lab-manager", "/analyzers"),
  M("Critical Value Alerting", "clinical", "Automated critical value detection with escalating notification to ordering physician via SMS, in-app alert, and log.", ["Lab Technician", "Lab Manager"], "Detect Critical → Auto-Alert Physician → Acknowledge → Document Call → Log", "lab-tech", "/critical-values"),
  M("Reference Lab Management", "clinical", "Send-out test management: reference lab order, specimen shipping, result receipt, and turnaround tracking.", ["Lab Manager"], "Order Send-Out → Ship → Track → Receive Result → Import → Release", "lab-manager", "/reference-lab"),
  M("Mobile Phlebotomist App", "clinical", "Field phlebotomy app for patient-side collection with offline capability, barcode scan, and GPS timestamp.", ["Phlebotomist"], "Receive Assignment → Navigate → Scan Patient → Collect → Sync Result", "phlebotomist", "/mobile-phlebotomy"),
  M("FHIR Result Delivery", "clinical", "FHIR R4-compliant result delivery to physician EMRs, patient portals, and HIE networks.", ["IT Admin", "Lab Manager"], "Generate FHIR Bundle → Validate → Push → Confirm Delivery → Log", "admin", "/fhir"),
  M("Auto-Verification Rules AI", "ai", "AI refines auto-verification rules based on historical validation patterns, reducing manual review by up to 70%.", ["Lab Supervisor"], "Train Model → Apply Rules → Monitor Performance → Tune → Report", "lab-supervisor", "/ai-auto-verify"),
  M("TAT Prediction", "ai", "Machine learning predicts turnaround time per test and flags samples at risk of breaching TAT SLA.", ["Lab Manager"], "Load Worklist → Predict TAT → Flag At-Risk → Prioritize → Monitor", "lab-manager", "/ai-tat"),
  M("QC Anomaly Detection", "ai", "AI detects analyzer drift and reagent lot shift patterns before Westgard rules trigger, reducing false results.", ["Lab Manager", "QC Officer"], "Monitor QC Data → AI Flag Drift → Investigate → Corrective Action → Log", "lab-manager", "/ai-qc"),
  M("Critical Value Intelligence", "ai", "AI correlates critical values with patient diagnosis and medication context to reduce non-actionable critical alerts.", ["Lab Supervisor", "Physician"], "Detect Critical → AI Context → Smart Alert → Escalation Level → Notify", "lab-supervisor", "/ai-critical"),
  M("Test Billing & Invoicing", "finance", "Per-test charge capture, patient invoicing, insurance claims, and revenue by test category reporting.", ["Finance Officer"], "Capture Charges → Invoice → Submit Claim → Post ERA → Report", "finance", "/billing"),
  M("Insurance Claims", "finance", "Electronic claim submission with CPT mapping, pre-authorization tracking, and denial management.", ["Finance Officer"], "Map CPT → Verify Auth → Submit → Track → Appeal Denials", "finance", "/insurance"),
  M("Accounting (AP/AR)", "finance", "Accounts payable to reagent suppliers, patient AR, journal entries, and monthly financial close.", ["Accountant"], "Post → Approve → Pay → Reconcile → Close", "finance", "/accounting"),
  M("HR & Staff Management", "hr", "Lab staff profiles, CLIA certification tracking, shift management, and competency assessments.", ["HR Officer"], "Hire → Certify → Schedule → Assess Competency → Renew Cert", "hr", "/hr/employees"),
  M("Payroll", "hr", "WPS payroll for lab staff with on-call differential, night shift premium, and automated payslip delivery.", ["Payroll Officer"], "Lock Attendance → Calculate → Differentials → Slips → WPS Submit", "hr", "/hr/payroll"),
  M("Attendance & Shifts", "hr", "Shift scheduling for 24/7 lab operations, leave management, and overtime tracking.", ["HR Officer"], "Set Shift Template → Assign Staff → Approve Leave → Finalize → Report", "hr", "/hr/attendance"),
  M("Reagent & Consumables Inventory", "inventory", "Real-time reagent stock by lot number with expiry tracking, auto-reorder at par, and cold chain monitoring.", ["Inventory Officer", "Lab Tech"], "Receive Lot → Scan → Update Stock → Monitor Expiry → Reorder", "inventory", "/inventory"),
  M("Analyzer Asset Registry", "inventory", "Equipment registry with PM schedules, calibration logs, downtime tracking, and service contract management.", ["Lab Manager", "Biomedical"], "Register Analyzer → PM Schedule → Log Cal → Track Downtime → Contract", "inventory", "/assets"),
  M("Procurement & Purchasing", "inventory", "Reagent purchase requisition, RFQ, PO, goods receipt, and invoice matching for lab consumables.", ["Procurement Officer"], "Requisition → Approve → PO → Receive → Match → Pay", "inventory", "/procurement"),
  M("Lab Reports & Dashboards", "reports", "Test volume, TAT compliance, QC performance, critical value rate, and financial KPIs on one dashboard.", ["Lab Manager", "All"], "Open Dashboard → Filter Period → TAT Report → QC Summary → Export", "manager", "/reports"),
  M("QC Reports", "reports", "Westgard violation frequency, control lot stability, and instrument comparison reports for regulatory submission.", ["QC Officer", "Lab Manager"], "Select Period → Control Chart → Violations → Lot Comparison → Export", "lab-supervisor", "/reports/qc"),
  M("Financial Reports", "reports", "Revenue by test category, insurance vs self-pay, cost per test, and profitability analysis.", ["Finance Officer", "Manager"], "Select Period → Revenue Breakdown → Cost per Test → Profitability → Export", "finance", "/reports/finance"),
];

const laboratoryWorkflows: RoleWorkflow[] = [
  {
    role: "Lab Technician",
    description: "Processes specimens end-to-end: accession, analysis, result entry, and verification for routine lab testing.",
    steps: [
      { action: "Specimen Accession", detail: "Receive specimen; scan barcode; verify patient ID, tube type, and test orders; accession into LIS." },
      { action: "Analyzer Loading", detail: "Load specimens onto analyzer; confirm analyzer QC passed today; download results via interface." },
      { action: "Result Review", detail: "Review auto-downloaded results; check delta flags; confirm reference range compliance." },
      { action: "Auto-Verification", detail: "Westgard rules run automatically; specimens meeting criteria release; failing route to supervisor." },
      { action: "Critical Value Notification", detail: "For critical results: call ordering physician, document acknowledgment, and log call in LIS." },
    ],
  },
  {
    role: "Phlebotomist",
    description: "Performs patient-side blood collection with proper identification, technique, and specimen handling.",
    steps: [
      { action: "Assignment Review", detail: "Open daily collection list; sort by location and priority; note special collection requirements." },
      { action: "Patient Identification", detail: "Verify patient using two identifiers (name + MRN/DOB); match against order in mobile app." },
      { action: "Specimen Collection", detail: "Select correct tubes per test; perform venipuncture; fill tubes in correct order of draw." },
      { action: "Label & Transport", detail: "Scan barcode label onto each tube immediately after collection; place in biohazard bag; transport." },
      { action: "Sync & Confirm", detail: "Sync mobile app to record collection timestamp, GPS location, and collector ID; confirm receipt at lab." },
    ],
  },
  {
    role: "Lab Manager",
    description: "Oversees lab operations, QC compliance, staff productivity, TAT performance, and budget management.",
    steps: [
      { action: "Daily QC Review", detail: "Review morning QC runs; confirm all analyzers passed Westgard rules before patient testing." },
      { action: "TAT Monitoring", detail: "Monitor real-time TAT dashboard; identify bottlenecks; reassign staff or escalate instrument issues." },
      { action: "Staff Scheduling", detail: "Manage shift assignments for 24/7 operations; approve leave; plan coverage for holidays." },
      { action: "Reagent Management", detail: "Review inventory levels; approve purchase orders for reagents; manage lot changeovers." },
      { action: "Regulatory Reporting", detail: "Prepare CAP/CLIA or MOH inspection documentation; compile QC reports; manage proficiency testing." },
    ],
  },
  {
    role: "Finance Officer",
    description: "Manages lab billing, insurance claims, and financial reporting for laboratory revenue.",
    steps: [
      { action: "Charge Review", detail: "Verify billable tests performed against orders; confirm CPT codes and modifiers are correct." },
      { action: "Claim Submission", detail: "Submit electronic claims with test CPT codes, diagnosis, and insurance authorization." },
      { action: "ERA Posting", detail: "Receive and post insurance payments; flag denied claims; initiate appeals process." },
      { action: "Reagent Invoice Processing", detail: "Match supplier invoices to POs; approve for payment; track cost per test trends." },
      { action: "Financial Reporting", detail: "Generate monthly revenue by test category, cost of goods, and profitability report." },
    ],
  },
  {
    role: "HR Officer",
    description: "Manages lab staff certifications, shift schedules, payroll, and regulatory competency tracking.",
    steps: [
      { action: "Certification Management", detail: "Track CLIA, ASCP, or MOH licensing for each staff member; set 90-day renewal reminders." },
      { action: "Competency Assessment", detail: "Schedule and document annual competency assessments per CLIA/CAP requirements." },
      { action: "Shift Scheduling", detail: "Build 24/7 shift schedule; account for on-call rotation, weekend coverage, and leave requests." },
      { action: "Payroll Processing", detail: "Apply shift differentials and on-call pay; generate payslips; submit WPS file." },
      { action: "HR Reporting", detail: "Compile headcount, certification status, and payroll cost reports for lab management." },
    ],
  },
];

const laboratoryPermissions: PermissionRole[] = [
  { role: "System Admin", level: "full", categories: ["clinical", "ai", "finance", "hr", "inventory", "reports", "admin"], description: "Full platform access." },
  { role: "Lab Manager", level: "operations", categories: ["clinical", "ai", "finance", "hr", "inventory", "reports"], description: "Full operational oversight across all lab sections." },
  { role: "Lab Technician", level: "clinical", categories: ["clinical", "ai"], description: "Specimen processing, result entry, and verification." },
  { role: "Phlebotomist", level: "limited", categories: ["clinical"], description: "Specimen collection and transport workflows only." },
  { role: "Finance Officer", level: "finance", categories: ["finance", "reports"], description: "Billing, claims, and financial reporting." },
  { role: "HR Officer", level: "hr", categories: ["hr", "reports"], description: "Staff certifications, scheduling, and payroll." },
];

// ─────────────────────────────────────────────────────────────────────────────
// CyMed Imaging
// ─────────────────────────────────────────────────────────────────────────────
const imagingModules: ProductModule[] = [
  M("RIS Worklist", "clinical", "Radiology worklist with modality-specific queues, priority flagging, contrast alerts, and technologist assignment.", ["Radiographer", "Radiologist"], "Order Arrives → Priority Check → Assign Modality → Technologist Queue → Perform", "radiographer", "/worklist"),
  M("Radiology Scheduling", "clinical", "Appointment scheduling for MRI, CT, X-Ray, US, and Mammo with equipment availability and contrast pre-screening.", ["Scheduler", "Receptionist"], "Request → Select Modality → Check Equipment → Book → Contrast Screen → Confirm", "receptionist", "/scheduling"),
  M("DICOM Image Management", "clinical", "Full DICOM store, retrieve, route, and archive with multi-study comparison, hanging protocols, and CD export.", ["Radiologist", "PACS Admin"], "Acquire → Store DICOM → Route to PACS → Archive → Retrieve → Compare", "radiologist", "/dicom"),
  M("PACS Connectivity", "clinical", "PACS server integration with bidirectional DICOM routing, modality worklist, and storage commitment.", ["IT Admin", "Radiologist"], "Configure PACS → Worklist Push → Acquire → Store → Verify → Backup", "admin", "/pacs"),
  M("Structured Reporting", "clinical", "Template-based radiology reports with anatomy diagram markup, finding checkboxes, and clinical impression fields.", ["Radiologist"], "Open Study → Review Images → Select Template → Fill Findings → Dictate Impression → Sign", "radiologist", "/reporting"),
  M("AI-Assisted Image Analysis", "ai", "AI CAD tools for chest X-ray pathology detection, CT pulmonary embolism flagging, and mammography lesion detection.", ["Radiologist"], "Acquire Study → AI Analyze → Flag Findings → Radiologist Review → Accept/Reject → Report", "radiologist", "/ai-cad"),
  M("Peer Review Workflow", "clinical", "Structured radiologist peer review: random case selection, discrepancy rating, and QA reporting.", ["Radiologist", "QA Manager"], "Select Case → Read → Rate Concordance → Document → QA Report", "radiologist", "/peer-review"),
  M("Teleradiology", "clinical", "Remote radiologist reading workflow: encrypted DICOM push, remote report, e-signature, and result distribution.", ["Radiologist", "Teleradiology Coordinator"], "Push Study → Remote Read → Dictate → Sign → Distribute → Archive", "radiologist", "/teleradiology"),
  M("Critical Finding Alerts", "clinical", "Radiologist-triggered critical finding alert with acknowledgment tracking and time-stamp audit for ordering physicians.", ["Radiologist"], "Flag Critical → Alert Physician → Physician Acknowledges → Document → Close", "radiologist", "/critical-alerts"),
  M("3D Visualization", "clinical", "MPR, MIP, VR, and 3D reconstruction tools for CT and MRI datasets directly in the browser-based viewer.", ["Radiologist"], "Open CT/MRI → Reconstruct 3D → MPR Planes → VR View → Capture → Include in Report", "radiologist", "/3d-viewer"),
  M("Multi-Modality Support", "clinical", "Unified worklist and DICOM viewer for MRI, CT, X-Ray, Ultrasound, Mammography, and PET-CT studies.", ["Radiologist", "Radiographer"], "Select Modality → Apply Hanging Protocol → Read → Report", "radiologist", "/modalities"),
  M("Study Urgency Scoring", "ai", "AI scores inbound studies by clinical urgency using ordering indication text and patient flags, optimizing read order.", ["Radiologist", "Radiology Manager"], "Parse Indication → AI Score → Reorder Worklist → Urgent Flag → Notify", "radiologist", "/ai-urgency"),
  M("Structured Report AI", "ai", "AI pre-fills structured report templates using prior reports and image findings as context for radiologist review.", ["Radiologist"], "Open Study → AI Pre-fill Template → Review → Edit → Sign Report", "radiologist", "/ai-report"),
  M("Scheduling Optimization", "ai", "AI optimizes equipment scheduling based on scan duration, prep time, staff availability, and urgent demand.", ["Scheduler", "Radiology Manager"], "Input Demand → AI Schedule → Optimize Slots → Confirm → Monitor", "manager", "/ai-scheduling"),
  M("DICOM Anomaly Flagging", "ai", "AI detects failed DICOM studies, positioning errors, motion artifacts, and contrast timing issues at time of acquisition.", ["Radiographer", "QA Officer"], "Acquire Study → AI Quality Check → Flag Issues → Repeat if Needed → Accept", "radiographer", "/ai-dicom-qa"),
  M("Imaging Billing & RVS Coding", "finance", "RVU-based procedure coding, insurance claims, co-pay collection, and radiology revenue reporting.", ["Finance Officer"], "Review Procedure → Assign CPT/RVU → Verify Auth → Submit Claim → Post ERA", "finance", "/billing"),
  M("Insurance Claims", "finance", "Electronic imaging claim submission with modality-specific CPT codes, authorization tracking, and denial management.", ["Finance Officer"], "Map CPT → Verify Prior Auth → Submit Batch → Track → Appeal", "finance", "/insurance"),
  M("Accounting (AP/AR)", "finance", "Contrast and equipment supply accounts payable, patient receivables, and monthly financial close.", ["Accountant"], "Post → Approve → Pay → Reconcile → Close", "finance", "/accounting"),
  M("HR & Staff Management", "hr", "Radiologist, radiographer, and technologist profiles with ACR/MOH credential tracking and shift assignment.", ["HR Officer"], "Hire → Credential Verify → Privilege → Schedule → Annual Review", "hr", "/hr/employees"),
  M("Payroll", "hr", "WPS payroll with on-call and after-hours differentials for 24/7 radiology coverage.", ["Payroll Officer"], "Lock Attendance → Calculate Differentials → Slips → WPS Submit", "hr", "/hr/payroll"),
  M("Attendance", "hr", "Shift scheduling for round-the-clock radiology, leave management, and emergency on-call tracking.", ["HR Officer"], "Set Schedule → Assign On-Call → Approve Leave → Report Absences", "hr", "/hr/attendance"),
  M("Equipment Asset Registry", "inventory", "MRI, CT, X-ray, and ultrasound equipment registry with PM schedules, calibration logs, and service contracts.", ["Radiology Manager", "Biomedical"], "Register Equipment → PM Schedule → Log Calibration → Service Contract → Downtime Report", "inventory", "/assets"),
  M("Contrast & Consumables", "inventory", "Contrast media inventory with expiry tracking, cold chain, patient allergy cross-reference, and auto-reorder.", ["Radiographer", "Inventory Officer"], "Receive Contrast → Log Lot → Monitor Expiry → Check Allergy → Issue → Reorder", "inventory", "/consumables"),
  M("Maintenance Scheduling", "inventory", "Preventive maintenance scheduling for MRI, CT, and X-ray with vendor coordination and downtime impact tracking.", ["Biomedical Engineer"], "Schedule PM → Notify Vendor → Perform → Document → Update PM Record", "inventory", "/maintenance"),
  M("Procurement", "inventory", "Contrast, film, and equipment parts procurement with RFQ, PO, and goods receipt workflow.", ["Procurement Officer"], "Requisition → Approve → RFQ → PO → Receive → Match Invoice → Pay", "inventory", "/procurement"),
  M("Radiology Reports & Dashboards", "reports", "Study volume by modality, TAT, critical finding rate, equipment utilization, and financial KPIs.", ["Radiology Manager", "All"], "Open Dashboard → Filter Modality → TAT Report → Utilization → Export", "manager", "/reports"),
  M("Equipment Utilization", "reports", "MRI/CT scanner uptime, scan count per day, downtime hours, and revenue per equipment unit reports.", ["Radiology Manager"], "Select Equipment → Utilization Rate → Downtime Hours → Revenue → Export", "manager", "/reports/equipment"),
  M("Financial Reports", "reports", "Revenue by procedure type, payer mix, cost per study, and profitability by modality.", ["Finance Officer", "Manager"], "Select Period → Revenue by Modality → Payer Mix → Cost per Study → Export", "finance", "/reports/finance"),
];

const imagingWorkflows: RoleWorkflow[] = [
  {
    role: "Radiologist",
    description: "Reads and reports imaging studies, using AI assistance, structured templates, and teleradiology tools.",
    steps: [
      { action: "Worklist Review", detail: "Open modality-filtered worklist; AI urgency scoring prioritizes STAT and emergent studies." },
      { action: "Image Interpretation", detail: "Open DICOM study in PACS viewer; apply hanging protocol; review with AI overlay findings." },
      { action: "Structured Report", detail: "Select template; AI pre-fills based on clinical indication and image findings; edit and refine." },
      { action: "Critical Finding Alert", detail: "If critical finding: trigger physician alert system; document direct communication; timestamp." },
      { action: "Sign & Distribute", detail: "Electronic signature applies radiologist credentials; report routes to ordering provider and EMR." },
    ],
  },
  {
    role: "Radiographer",
    description: "Acquires diagnostic images, prepares patients, manages equipment, and performs QA on acquired studies.",
    steps: [
      { action: "Worklist Pickup", detail: "Claim next patient from modality worklist; review clinical indication, positioning notes, and allergies." },
      { action: "Patient Preparation", detail: "Explain procedure; confirm contrast allergies; position patient; apply safety protocols (MRI metal screening)." },
      { action: "Image Acquisition", detail: "Execute scan protocol; monitor for motion artifacts; acquire required sequences or views." },
      { action: "AI Quality Check", detail: "AI flags positioning errors or image quality issues; repeat acquisition if flagged and radiologist not yet reading." },
      { action: "DICOM Upload", detail: "Push completed study to PACS; confirm worklist status updates to 'Read'; notify radiologist of STAT." },
    ],
  },
  {
    role: "Radiology Manager",
    description: "Manages imaging operations, equipment uptime, staff scheduling, and quality compliance.",
    steps: [
      { action: "Daily Operations", detail: "Review study volume, worklist backlog, equipment status, and staff availability on dashboard." },
      { action: "Equipment Oversight", detail: "Monitor PM schedule; coordinate planned downtime with vendor and scheduling team to minimize impact." },
      { action: "Workflow Optimization", detail: "Analyze TAT by modality; identify bottlenecks; adjust technologist and radiologist assignments." },
      { action: "Quality Assurance", detail: "Review peer review discrepancy rates; manage QA cases; ensure ACR/MOH accreditation compliance." },
      { action: "Performance Reporting", detail: "Generate study volume, TAT, equipment utilization, and financial reports for hospital leadership." },
    ],
  },
  {
    role: "Finance Officer",
    description: "Manages imaging billing, insurance claims, and radiology revenue analytics.",
    steps: [
      { action: "Charge Capture", detail: "Review completed studies; assign correct CPT/RVU codes per modality and number of views." },
      { action: "Authorization Verification", detail: "Confirm prior authorization numbers are documented before claim submission." },
      { action: "Claim Submission", detail: "Submit electronic batch claims to insurance payers with complete procedure documentation." },
      { action: "ERA Posting", detail: "Receive remittance; post payments; flag denied or down-coded studies for appeal." },
      { action: "Revenue Reporting", detail: "Produce monthly revenue by modality, payer mix breakdown, and RVU productivity report." },
    ],
  },
  {
    role: "HR Officer",
    description: "Manages radiology staff credentials, shift scheduling, payroll, and regulatory compliance.",
    steps: [
      { action: "Credential Management", detail: "Track ACR, ARRT, or MOH credentials; schedule renewal 90 days before expiry." },
      { action: "Privileging", detail: "Manage radiologist reading privileges by subspecialty (neuro, body, MSK, pediatric)." },
      { action: "Shift Scheduling", detail: "Build 24/7 technologist and on-call radiologist schedule; manage holiday and emergency coverage." },
      { action: "Payroll Processing", detail: "Calculate on-call differentials and after-hours pay; generate payslips; submit WPS file." },
      { action: "HR Reporting", detail: "Generate credential compliance, headcount, and payroll cost reports for management." },
    ],
  },
];

const imagingPermissions: PermissionRole[] = [
  { role: "System Admin", level: "full", categories: ["clinical", "ai", "finance", "hr", "inventory", "reports", "admin"], description: "Full platform access." },
  { role: "Radiology Manager", level: "operations", categories: ["clinical", "ai", "finance", "hr", "inventory", "reports"], description: "Full operational oversight of imaging department." },
  { role: "Radiologist", level: "clinical", categories: ["clinical", "ai", "reports"], description: "Worklist, DICOM viewer, structured reporting, and critical alerts." },
  { role: "Radiographer", level: "limited", categories: ["clinical", "ai"], description: "Worklist pickup, image acquisition, and PACS upload." },
  { role: "Finance Officer", level: "finance", categories: ["finance", "reports"], description: "Billing, claims, and revenue reporting." },
  { role: "HR Officer", level: "hr", categories: ["hr", "reports"], description: "Staff credentials, scheduling, and payroll." },
];

// ─────────────────────────────────────────────────────────────────────────────
// CyShop
// ─────────────────────────────────────────────────────────────────────────────
const cyshopModules: ProductModule[] = [
  M("Point of Sale (POS)", "operations", "Touch-screen POS with multi-tender checkout, split bills, discount engine, kitchen routing, and drawer management.", ["Cashier", "Store Manager"], "Open Shift → Take Order → Apply Discount → Multi-Tender → Close Shift", "cashier", "/pos"),
  M("Kitchen Display System (KDS)", "operations", "Real-time order routing to kitchen stations with bump-bar confirmation, FIFO prioritization, and prep time tracking.", ["Kitchen Staff"], "Receive Order → Station Route → Prep → Bump Complete → Notify Cashier", "kitchen", "/kds"),
  M("Table Management & Reservations", "operations", "Visual floor plan, table assignment, cover count, reservation booking, and walk-in waitlist management.", ["Cashier", "Host"], "View Floor Plan → Assign Table → Start Tab → Reserve → Waitlist Manage", "cashier", "/tables"),
  M("Self-Service Kiosk", "operations", "Customer-facing order kiosk with menu browsing, customization, upsell prompts, and integrated payment terminal.", ["Customer", "Store Manager"], "Browse Menu → Customize → Add to Cart → Pay → Kitchen Route → Collect", "all", "/kiosk"),
  M("Online Ordering (QR/Web/App)", "operations", "QR table ordering, branded web ordering, and mobile app with real-time menu sync and order injection to KDS.", ["Customer", "Store Manager"], "Scan QR → Browse → Add Items → Checkout → Kitchen Route → Ready Alert", "all", "/online-ordering"),
  M("Delivery Management", "operations", "Delivery order dispatch, driver assignment, GPS tracking, delivery ETA, and proof-of-delivery capture.", ["Delivery Manager", "Driver"], "Accept Order → Assign Driver → Track GPS → Deliver → POD Capture → Close", "delivery", "/delivery"),
  M("Customer Loyalty & Rewards", "operations", "Points earning, tier management, voucher issuance, birthday rewards, and redemption at POS.", ["Cashier", "Marketing"], "Earn Points → Tier Upgrade → Issue Voucher → Redeem at POS → Report", "cashier", "/loyalty"),
  M("Menu & Catalog Management", "operations", "Multi-branch menu management with item modifiers, pricing tiers, time-limited offers, and category display order.", ["Store Manager", "Menu Manager"], "Create Item → Set Modifiers → Price by Branch → Schedule Offer → Publish", "manager", "/menu"),
  M("Franchise Management", "operations", "Multi-branch operations: central menu control, per-branch pricing override, performance benchmarking, and royalty reporting.", ["Chain Manager"], "Set Brand Standards → Branch Config → Monitor Performance → Royalty Report", "chain-manager", "/franchise"),
  M("Central Kitchen", "operations", "Central prep production orders, batch recipe management, and distribution to branches with transfer tracking.", ["Central Kitchen Manager"], "Production Order → Recipe Scale → Prepare → Transfer to Branch → Confirm Receipt", "kitchen-manager", "/central-kitchen"),
  M("Demand Forecasting", "ai", "ML model predicting item-level demand by hour and day using sales history, weather, and events data.", ["Store Manager", "Chain Manager"], "Pull History → Input Events → Run Model → Forecast → Adjust Prep & Order", "manager", "/ai-demand"),
  M("Waste Prevention AI", "ai", "AI recommends optimal prep quantities and identifies slow-moving items to minimize food waste and spoilage.", ["Store Manager", "Kitchen Manager"], "Analyze Sales Velocity → AI Recommend Prep Qty → Adjust → Track Waste Reduction", "manager", "/ai-waste"),
  M("KDS Smart Routing", "ai", "AI dynamically routes orders to optimal kitchen stations based on station load, prep time, and item type.", ["Kitchen Manager"], "Receive Order → AI Route → Balance Stations → Bump → Track TAT", "kitchen", "/ai-routing"),
  M("Delivery ETA Prediction", "ai", "Real-time delivery ETA using driver location, traffic, and historical delivery time data to improve customer experience.", ["Delivery Manager", "Driver"], "Accept Delivery → Track Driver → Predict ETA → Notify Customer → Confirm", "delivery", "/ai-eta"),
  M("Menu Engineering AI", "ai", "Analyzes menu item profitability vs popularity to recommend pricing adjustments, upsell pairings, and item placement.", ["Chain Manager", "Store Manager"], "Analyze Items → Score Profitability/Popularity → Recommend → Adjust → Monitor", "manager", "/ai-menu"),
  M("Customer Insights AI", "ai", "Customer purchase pattern analysis, lifetime value scoring, churn risk detection, and personalized offer generation.", ["Marketing Manager", "Chain Manager"], "Analyze Customers → Score LTV → Flag Churn Risk → Generate Offers → Send", "manager", "/ai-customers"),
  M("Finance & Accounting (ZATCA)", "finance", "ZATCA-compliant e-invoicing, VAT calculation, financial journal entries, trial balance, and monthly close.", ["Finance Officer", "Accountant"], "POS Sale → ZATCA e-Invoice → VAT Calculation → Post Journal → Month-End Close", "finance", "/finance"),
  M("Accounting (AP/AR)", "finance", "Supplier accounts payable, franchise receivables, general ledger, and financial statement generation.", ["Accountant"], "Post Entry → Approve Invoice → Pay Supplier → Reconcile → Report", "finance", "/accounting"),
  M("Cash Reconciliation", "finance", "End-of-shift cash count, POS vs actual reconciliation, variance reporting, and deposit slip generation.", ["Store Manager", "Cashier"], "Count Cash → Match POS → Log Variance → Generate Deposit Slip → Submit", "finance", "/cash-reconciliation"),
  M("HR & Staff Management", "hr", "Staff profiles, contract management, department assignment, and organizational structure for all branches.", ["HR Officer", "Store Manager"], "Hire → Create Profile → Set Role → Assign Branch → Onboard", "hr", "/hr/employees"),
  M("Payroll (WPS)", "hr", "WPS-compliant payroll with tips, service charge distribution, overtime, and automated payslip delivery.", ["Payroll Officer"], "Lock Attendance → Calculate Tips & OT → Slips → WPS Submit", "hr", "/hr/payroll"),
  M("Attendance & Shift Scheduling", "hr", "Shift scheduling by branch, biometric check-in/out, leave management, and overtime tracking.", ["HR Officer", "Store Manager"], "Set Shift → Assign Staff → Import Biometric → Approve Leave → Report", "hr", "/hr/attendance"),
  M("Real-Time Inventory", "inventory", "Item-level stock tracking with depletion per sale, branch transfers, and low-stock alerts.", ["Inventory Officer", "Store Manager"], "Set Par → POS Deducts → Monitor Qty → Alert Low → Request Transfer", "inventory", "/inventory"),
  M("Supplier Management", "inventory", "Supplier registry, pricing agreements, delivery schedule tracking, and performance scoring.", ["Procurement Officer"], "Register Supplier → Set Terms → Track Delivery → Score Performance", "inventory", "/suppliers"),
  M("Procurement & Purchasing", "inventory", "Purchase requisition, approval, PO generation, goods receipt, and invoice matching for food and supplies.", ["Procurement Officer"], "Requisition → Approve → PO → Receive → Match Invoice → Pay", "inventory", "/procurement"),
  M("Cold Chain / Expiry", "inventory", "Temperature logging for cold-chain items, expiry date alerts, FEFO rotation, and waste documentation.", ["Inventory Officer"], "Receive Item → Log Temp → Set Expiry → FEFO Alert → Rotate → Document", "inventory", "/cold-chain"),
  M("Customer CRM & Loyalty", "erp", "Customer database, loyalty tier management, purchase history, and targeted marketing list management.", ["Marketing Manager", "Store Manager"], "Segment Customers → Tier Update → Generate List → Launch Campaign → Track Response", "manager", "/crm"),
  M("Leads", "erp", "Franchise inquiry tracking, sales pipeline for B2B catering, and corporate account acquisition workflow.", ["Sales Manager"], "Capture Lead → Qualify → Propose → Follow-up → Convert → Onboard", "sales", "/leads"),
  M("Quotations", "erp", "Catering and corporate event quotation builder with itemized pricing, approval workflow, and e-signature.", ["Sales Manager"], "Create Quote → Add Items → Price → Send → Approve → Convert to Order", "sales", "/quotations"),
  M("Customer Portal", "erp", "Customer self-service portal for viewing order history, loyalty points, invoices, and corporate account management.", ["Customer"], "Login → View Orders → Check Points → Download Invoices → Manage Account", "all", "/portal"),
  M("Roles & Permissions", "admin", "User role management with Odoo-style RBAC: assign roles per user, per branch, with module-level visibility controls.", ["System Admin"], "Create Role → Assign Permissions → Set Branch Scope → Assign User → Activate", "admin", "/settings/roles"),
  M("User Management", "admin", "User account creation, password policies, two-factor authentication, and access audit logs.", ["System Admin"], "Create User → Assign Role → MFA Setup → Audit Login → Deactivate if Needed", "admin", "/settings/users"),
  M("Settings", "admin", "Global platform settings: branch configuration, tax rates, receipt layout, integrations, and system preferences.", ["System Admin", "Chain Manager"], "Select Setting → Configure → Test → Save → Apply to Branches", "admin", "/settings"),
  M("Sales Dashboard", "reports", "Real-time sales by branch, hour, item, and cashier with revenue, basket size, and transaction count KPIs.", ["Store Manager", "Chain Manager", "All"], "Open Dashboard → Filter Branch/Period → Drill Item → Export → Share", "manager", "/reports/sales"),
  M("Financial Reports", "reports", "Revenue, cost of goods, gross margin, and ZATCA VAT reports with export for accounting system integration.", ["Finance Officer", "Manager"], "Select Period → Revenue → COGS → Margin → VAT Report → Export", "finance", "/reports/finance"),
  M("Inventory Reports", "reports", "Stock on hand, usage vs waste, supplier performance, and procurement spend analytics.", ["Inventory Officer", "Manager"], "Select Period → Stock Report → Waste Analysis → Supplier Report → Export", "inventory", "/reports/inventory"),
  M("Delivery Performance", "reports", "Delivery TAT, driver performance, on-time rate, customer rating, and failed delivery analysis.", ["Delivery Manager", "Manager"], "Select Period → TAT Report → Driver Scores → On-Time Rate → Failed Deliveries → Export", "manager", "/reports/delivery"),
  M("Customer Analytics", "reports", "Customer retention, LTV distribution, churn rate, loyalty redemption, and campaign ROI reports.", ["Marketing Manager", "Chain Manager"], "Segment → Retention Rate → LTV Chart → Campaign ROI → Export", "manager", "/reports/customers"),
];

const cyshopWorkflows: RoleWorkflow[] = [
  {
    role: "Cashier",
    description: "Processes dine-in, takeaway, and online orders at the POS with payment collection and KDS routing.",
    steps: [
      { action: "Open Shift", detail: "Login, perform opening count, and open cash drawer; confirm POS connected to KDS and printer." },
      { action: "Take Order", detail: "Select items from touch-screen menu; apply modifiers; add loyalty number if applicable." },
      { action: "Route to Kitchen", detail: "Submit order — KDS receives instantly; kitchen station assigned by item type." },
      { action: "Multi-Tender Checkout", detail: "Select payment: cash, card, Apple Pay, loyalty points, or split; print or send e-receipt." },
      { action: "Close Shift", detail: "Count cash; match against POS total; submit variance report; log with store manager signature." },
    ],
  },
  {
    role: "Kitchen Staff",
    description: "Receives and fulfills orders on the KDS, manages prep prioritization, and coordinates pickup or delivery.",
    steps: [
      { action: "Order Received", detail: "New order appears on KDS station screen with item, modifiers, and urgency flag (ASAP vs scheduled)." },
      { action: "Prep Execution", detail: "Prepare items in order; KDS smart routing has already assigned to optimal station." },
      { action: "Bump Complete", detail: "Tap bump bar to mark item ready; POS and customer app receive ready notification." },
      { action: "Quality Check", detail: "Manager spot-checks presentation and temperature before runner takes to table or delivery picks up." },
      { action: "Pickup Coordination", detail: "For delivery orders: confirm driver presence before handing; attach delivery bag with order label." },
    ],
  },
  {
    role: "Delivery Driver",
    description: "Accepts delivery assignments, collects orders, delivers to customers, and confirms proof of delivery.",
    steps: [
      { action: "Assignment Accept", detail: "Receive delivery assignment in driver app; review order details, address, and customer instructions." },
      { action: "Order Pickup", detail: "Arrive at branch; confirm order number; accept sealed bag; depart for customer." },
      { action: "En-Route Navigation", detail: "Follow GPS navigation; app predicts and communicates ETA to customer in real time." },
      { action: "Delivery Confirmation", detail: "Arrive at customer; hand over order; capture photo proof of delivery or digital signature." },
      { action: "Sync & Next", detail: "Mark delivery complete in app; location and timestamp synced; available for next assignment." },
    ],
  },
  {
    role: "Store Manager",
    description: "Manages daily store operations, staff, inventory, and financial performance for their branch.",
    steps: [
      { action: "Opening Dashboard", detail: "Review today's bookings, pending prep quantity (AI-suggested), staff schedule, and equipment status." },
      { action: "Inventory Check", detail: "Review stock alerts; approve or place quick POs for short items; confirm delivery ETAs." },
      { action: "Staff Coordination", detail: "Brief team, assign stations, review previous shift handover, resolve any pending incidents." },
      { action: "Live Monitoring", detail: "Monitor real-time POS sales, KDS wait times, delivery performance, and customer queue." },
      { action: "End-of-Day Report", detail: "Review daily revenue, waste, labor cost, and delivery KPIs; submit report to chain management." },
    ],
  },
  {
    role: "Franchise / Chain Manager",
    description: "Oversees multi-branch operations, brand compliance, financial performance, and franchise development.",
    steps: [
      { action: "Chain Dashboard", detail: "Open consolidated view: revenue by branch, top performers, and underperforming locations." },
      { action: "Menu Management", detail: "Push menu updates, pricing changes, or LTO items centrally to all branches simultaneously." },
      { action: "Performance Benchmarking", detail: "Compare KPIs across branches: revenue/sqft, avg basket size, waste %, and customer ratings." },
      { action: "Franchise Reporting", detail: "Generate royalty calculation report; export to finance; distribute to franchisee portal." },
      { action: "Growth Planning", detail: "Analyze AI demand forecast to identify new location opportunities and expansion timing." },
    ],
  },
];

const cyshopPermissions: PermissionRole[] = [
  { role: "System Admin", level: "full", categories: ["operations", "erp", "ai", "finance", "hr", "inventory", "reports", "admin"], description: "Full platform access — all branches, all modules." },
  { role: "Chain Manager", level: "operations", categories: ["operations", "erp", "ai", "finance", "hr", "inventory", "reports"], description: "Full multi-branch operational and financial visibility." },
  { role: "Store Manager", level: "operations", categories: ["operations", "ai", "finance", "hr", "inventory", "reports"], description: "Single-branch operations, staff, inventory, and financial reporting." },
  { role: "Cashier", level: "limited", categories: ["operations"], description: "POS, loyalty, and table management only." },
  { role: "Kitchen Staff", level: "limited", categories: ["operations"], description: "KDS order view and bump-bar confirmation only." },
  { role: "Delivery Driver", level: "limited", categories: ["operations"], description: "Delivery assignments and GPS tracking only." },
  { role: "Finance Officer", level: "finance", categories: ["finance", "reports"], description: "Billing, reconciliation, ZATCA, and financial reporting." },
  { role: "HR Officer", level: "hr", categories: ["hr", "reports"], description: "Staff management, payroll, and attendance." },
  { role: "Inventory Officer", level: "inventory", categories: ["inventory", "reports"], description: "Stock management, procurement, and inventory reporting." },
];

// ─────────────────────────────────────────────────────────────────────────────
// CyCom ERP
// ─────────────────────────────────────────────────────────────────────────────
const erpModules: ProductModule[] = [
  // Finance
  M("Accounts Payable (AP)", "finance", "Full AP lifecycle: supplier invoices, 3-way match, payment runs, aging reports, and early payment discount tracking.", ["Accountant", "Finance Manager"], "Invoice Receive → 3-Way Match → Approve → Payment Run → Reconcile", "finance", "/finance/ap"),
  M("Accounts Receivable (AR)", "finance", "Customer invoicing, payment collection, credit limits, collection workflow, and AR aging analysis.", ["Finance Officer", "Accountant"], "Invoice → Send → Collect Payment → Post → Aging Report → Escalate", "finance", "/finance/ar"),
  M("Accounting", "finance", "Double-entry general ledger with multi-currency, multi-company, period locking, and automated reconciliation.", ["Accountant", "Finance Manager"], "Post Entry → Allocate → Reconcile → Period Lock → Financial Statements", "finance", "/finance/accounting"),
  M("Banking & Reconciliation", "finance", "Bank statement import (CSV/OFX), auto-match transactions, reconciliation wizard, and outstanding item management.", ["Accountant"], "Import Statement → Auto-Match → Review Unmatched → Reconcile → Close", "finance", "/finance/banking"),
  M("Chart of Accounts (COA)", "finance", "Multi-level COA setup with account types, tax positions, and IFRS-compliant hierarchy for multi-entity reporting.", ["Finance Manager"], "Create Account → Assign Type → Tax Position → Map Entity → Publish", "admin", "/finance/coa"),
  M("Journals", "finance", "Manual journal entries, recurring journals, accrual automation, and journal reversal with approval workflow.", ["Accountant"], "Create Journal → Post Lines → Approve → Reverse if Needed → Report", "finance", "/finance/journals"),
  M("Financials", "finance", "Real-time P&L, balance sheet, cash flow statement, and multi-entity consolidation with drilldown to transactions.", ["Finance Manager", "CFO"], "Open Report → Select Entity → Period → Drill Down → Export PDF", "finance", "/finance/financials"),
  M("Expenses", "finance", "Employee expense submission, manager approval, policy checks, GL posting, and reimbursement payment.", ["Employee", "Manager", "Finance"], "Submit Expense → Attach Receipt → Manager Approve → Finance Post → Reimburse", "all", "/finance/expenses"),
  M("Budget & Forecasting", "finance", "Annual budget setup, department-level budget control, variance reporting, and rolling 12-month forecast.", ["Finance Manager", "Department Head"], "Create Budget → Assign Lines → Monitor Actuals → Flag Variance → Reforecast", "finance", "/finance/budget"),
  M("Fixed Assets", "finance", "Asset register, depreciation schedules (straight-line, declining balance), disposal, revaluation, and asset audit.", ["Finance Manager", "Asset Officer"], "Register Asset → Set Depreciation → Monthly Run → Dispose → Audit Report", "finance", "/finance/assets"),
  // HR
  M("Employees", "hr", "Central employee database: personal data, documents, contracts, job grades, and organizational chart.", ["HR Officer", "HR Manager"], "Hire → Profile → Contract → Grade → Org Chart → Onboard", "hr", "/hr/employees"),
  M("HR Management", "hr", "HR policy management, disciplinary actions, performance appraisals, succession planning, and employee self-service.", ["HR Manager"], "Set Policy → Appraise → Succession Plan → Self-Service → Report", "hr", "/hr/management"),
  M("Payroll (WPS)", "hr", "MOCI/WPS-compliant payroll with salary structures, allowances, gratuity, and automated payslip distribution.", ["Payroll Officer"], "Lock Attendance → Calculate → Gratuity → Slips → WPS File → Bank Transfer", "hr", "/hr/payroll"),
  M("Attendance", "hr", "Biometric or app-based attendance tracking with real-time dashboards, overtime, and absence exception reports.", ["HR Officer"], "Import Biometric → Review → Approve OT → Exception Report → Finalize", "hr", "/hr/attendance"),
  M("Leave Management", "hr", "Leave request, balance tracking, multi-type leave policies (annual, sick, maternity, hajj), and approval workflow.", ["Employee", "Manager", "HR"], "Request Leave → Manager Approve → HR Validate → Balance Deduct → Calendar", "all", "/hr/leave"),
  M("Recruitment", "hr", "Job vacancy publishing, applicant tracking, interview scheduling, offer generation, and onboarding initiation.", ["HR Manager", "Recruiter"], "Post Job → Screen → Interview → Offer → Accept → Onboard", "hr", "/hr/recruitment"),
  M("Performance Management", "hr", "Goal setting, mid-year check-in, annual performance review, rating calibration, and promotion workflow.", ["Manager", "HR Manager"], "Set Goals → Mid-Year Review → Annual Appraisal → Calibrate → Promote", "hr", "/hr/performance"),
  // Inventory
  M("Inventory Management", "inventory", "Real-time stock by warehouse, location, and lot with FIFO/FEFO/AVCO costing and reorder rules.", ["Inventory Officer", "Warehouse Manager"], "Receive Stock → Move → Adjust → Reorder Rule → Report", "inventory", "/inventory"),
  M("Warehouses", "inventory", "Multi-warehouse management with bin locations, inbound routes, putaway strategies, and wave picking.", ["Warehouse Manager"], "Configure Warehouse → Bin Setup → Route → Putaway → Wave Pick → Ship", "inventory", "/inventory/warehouses"),
  M("Procurement & Purchasing", "inventory", "Purchase requisition, approval, RFQ, PO, receipt, and 3-way invoice matching with vendor performance scoring.", ["Procurement Officer", "Finance"], "Requisition → Approve → RFQ → PO → Receive → 3-Way Match → Pay", "inventory", "/procurement"),
  M("Goods Receiving", "inventory", "Inbound shipment verification, barcode scan-to-receive, quality inspection gate, and putaway task generation.", ["Warehouse Staff", "QC Officer"], "PO Arrive → Scan → Verify Qty/Quality → Putaway Task → Update Stock → AP Match", "inventory", "/inventory/receiving"),
  // Operations
  M("Fleet Management", "operations", "Vehicle registry, driver assignments, mileage tracking, fuel cost, PM schedules, and insurance renewal alerts.", ["Fleet Manager"], "Register Vehicle → Assign Driver → Log Trip → Fuel → PM Schedule → Renew Insurance", "operations", "/fleet"),
  M("Maintenance Management", "operations", "Preventive and corrective maintenance for equipment, technician assignment, SLA tracking, and asset downtime reporting.", ["Maintenance Manager", "Technician"], "Schedule PM → Assign Tech → Perform → Document → Close → Asset Report", "operations", "/maintenance"),
  M("Project Management", "operations", "Project planning with tasks, milestones, Gantt chart, time tracking, resource allocation, and budget monitoring.", ["Project Manager", "Team Member"], "Create Project → Assign Tasks → Track Progress → Time Log → Budget Alert → Close", "operations", "/projects"),
  M("Planning (Production)", "operations", "Manufacturing production planning: work orders, routing, work centers, capacity planning, and lead time calculation.", ["Production Planner"], "Demand → Work Order → Routing → Capacity Check → Schedule → Execute → Close", "operations", "/planning"),
  M("Quality Management", "operations", "Quality control check points, non-conformance reports, corrective actions, and supplier quality rating.", ["QC Manager", "QC Officer"], "Define CP → Inspect → NCR → CAPA → Verify → Close → Supplier Score", "operations", "/quality"),
  // Sales & CRM
  M("Sales", "operations", "Sales order management from quotation to delivery and invoice with discount approvals and margin alerts.", ["Sales Rep", "Sales Manager"], "Lead → Quote → Order → Confirm → Deliver → Invoice → Collect", "sales", "/sales/orders"),
  M("CRM", "operations", "Customer relationship management with pipeline kanban, activity scheduling, call log, and forecast reporting.", ["Sales Rep", "Sales Manager"], "Add Lead → Qualify → Opportunity → Activity → Proposal → Won/Lost", "sales", "/crm"),
  M("Leads", "operations", "Inbound and outbound lead capture, automatic scoring, assignment rules, and nurture sequence tracking.", ["Sales Rep", "Marketing"], "Capture Lead → Auto-Score → Assign → Nurture → Convert → Opportunity", "sales", "/crm/leads"),
  M("Quotations", "operations", "Professional quotation builder with product catalog, pricelist, discount matrix, and e-signature request.", ["Sales Rep"], "Create Quote → Select Products → Apply Pricelist → E-Sign → Convert to Order", "sales", "/sales/quotations"),
  M("Customer Portal", "erp", "Self-service customer portal: view quotations, sign contracts, download invoices, and track delivery status.", ["Customer"], "Login → View Quote → Sign → Track Order → Download Invoice", "all", "/portal"),
  M("Subscriptions", "erp", "Recurring revenue management with plan setup, auto-renewal, usage billing, churn detection, and MRR reporting.", ["Sales Manager", "Finance"], "Create Plan → Subscribe → Auto-Renew → Usage Bill → Churn Alert → MRR Report", "sales", "/subscriptions"),
  M("Marketing Automation", "erp", "Email campaign management, audience segmentation, A/B testing, lead scoring, and campaign ROI reporting.", ["Marketing Manager"], "Segment → Campaign → A/B Test → Send → Track Opens → Score → Report ROI", "sales", "/marketing"),
  // Collaboration
  M("Discuss", "erp", "Internal messaging, group channels, direct messages, and threaded discussions integrated with ERP records.", ["All Users"], "Open Channel → Message → @Mention → Thread → React → Pin → Archive", "all", "/discuss"),
  M("Documents", "erp", "Document management with folder structure, version control, access permissions, tagging, and full-text search.", ["All Users", "Manager"], "Upload → Tag → Permission → Version → Share → Search → Archive", "all", "/documents"),
  M("Knowledge Base", "erp", "Internal wiki for SOPs, training materials, product docs, and policy documentation with structured navigation.", ["All Users", "Manager"], "Create Article → Link Media → Organize → Share → Feedback → Update", "all", "/knowledge"),
  M("Todo", "erp", "Personal and team task management with deadlines, priorities, assignees, and ERP record links.", ["All Users"], "Create Task → Assign → Deadline → Link ERP Record → Complete → Report", "all", "/todo"),
  M("Surveys", "erp", "Customer satisfaction, employee engagement, and vendor evaluation surveys with analytics and response tracking.", ["HR Manager", "Marketing", "Manager"], "Create Survey → Set Questions → Distribute → Collect → Analyze → Report", "all", "/surveys"),
  M("Helpdesk", "erp", "Customer support ticket management with SLA rules, agent assignment, escalation, and CSAT measurement.", ["Support Agent", "Support Manager"], "Ticket Arrives → Assign Agent → SLA Start → Resolve → Close → CSAT Survey", "operations", "/helpdesk"),
  M("Sign (e-Signatures)", "erp", "Digital document signing workflow: template creation, signature request, audit trail, and legally-binding e-signature.", ["Manager", "HR", "Sales"], "Upload Doc → Template → Add Signature Fields → Send → Sign → Audit Trail", "all", "/sign"),
  // Manufacturing
  M("PLM (Product Lifecycle Management)", "operations", "Product engineering change management: ECO workflow, BOM versioning, revision control, and production handoff.", ["Product Engineer", "Production Manager"], "Create ECO → Review → Approve → BOM Update → Release → Production", "operations", "/plm"),
  // Reports / Admin
  M("Reports & Dashboards", "reports", "Customizable BI dashboards with real-time KPIs, pivot tables, drill-down, and scheduled report delivery.", ["All Managers", "Admin"], "Select Dashboard → Drag KPIs → Filter → Drill Down → Schedule Report → Share", "manager", "/reports"),
  M("BI Analytics", "reports", "Advanced analytics with multi-dimensional cube, cohort analysis, funnel charts, and predictive trend lines.", ["Finance Manager", "Executive"], "Load Data → Build Cube → Cohort → Funnel → Trend → Export → Present", "manager", "/analytics"),
  M("Settings", "admin", "Global ERP configuration: company setup, fiscal year, currencies, email servers, and integration API keys.", ["System Admin"], "Company Setup → Fiscal Year → Currency → Email Config → API Keys → Save", "admin", "/settings"),
  M("User Management", "admin", "User account creation, role assignment, 2FA enforcement, login audit, and active session management.", ["System Admin"], "Create User → Assign Role → Enable 2FA → Audit Logins → Deactivate", "admin", "/settings/users"),
  M("Roles & Permissions", "admin", "Granular RBAC: module-level, record-level, and field-level permissions configurable per role and per user.", ["System Admin"], "Create Role → Set Module Perms → Record Rules → Field Access → Assign → Test", "admin", "/settings/roles"),
  M("Audit Log", "admin", "Immutable audit trail: who changed what, when, and from where — across all ERP modules.", ["System Admin", "Compliance Officer"], "Select Module → Filter Period → View Changes → Export → Compliance Report", "admin", "/settings/audit"),
  M("Point of Sale (POS)", "operations", "ERP-integrated POS for retail, restaurants, and service businesses with full accounting and inventory sync.", ["Cashier", "Store Manager"], "Open Session → Take Order → Checkout → Sync Inventory → Post Revenue → Close", "cashier", "/pos"),
];

const erpWorkflows: RoleWorkflow[] = [
  {
    role: "Finance Manager",
    description: "Manages accounting, financial close, budget control, and financial reporting across all entities.",
    steps: [
      { action: "Month-End Preparation", detail: "Review open AP and AR; post accruals; reconcile bank statements; lock sub-ledgers." },
      { action: "Period Close", detail: "Run depreciation for fixed assets; post payroll costs; review and post all journal entries." },
      { action: "Financial Statements", detail: "Generate P&L, balance sheet, and cash flow statement; review for anomalies; approve." },
      { action: "Budget Variance Review", detail: "Compare actuals to budget by department; flag variances over threshold; investigate with heads." },
      { action: "Management Reporting", detail: "Produce executive financial package with consolidated view, KPIs, and commentary for board." },
    ],
  },
  {
    role: "HR Manager",
    description: "Manages workforce strategy, talent acquisition, employee development, and HR compliance.",
    steps: [
      { action: "Headcount Planning", detail: "Review org chart, open requisitions, and approved HC plan; align with finance budget." },
      { action: "Recruitment Workflow", detail: "Post vacancies, screen applicants, schedule interviews, generate offer letters, and initiate onboarding." },
      { action: "Payroll Approval", detail: "Review payroll officer's calculated payroll; approve payslips; authorize WPS file for bank transfer." },
      { action: "Performance Management", detail: "Launch annual review cycle, calibrate ratings with department heads, process promotions and increments." },
      { action: "HR Compliance Report", detail: "Generate MOCI labor compliance, Emiratization/Saudization, and leave liability reports for management." },
    ],
  },
  {
    role: "Inventory Manager",
    description: "Manages multi-warehouse stock, procurement planning, and supplier relationships to ensure availability.",
    steps: [
      { action: "Demand Review", detail: "Analyze MRP-generated replenishment suggestions based on lead times and reorder rules." },
      { action: "Purchase Order", detail: "Convert approved requisitions to POs; select supplier by price and lead time; confirm and send." },
      { action: "Goods Receipt", detail: "Receive inbound shipment; scan or manually verify quantities; QC gate inspection if applicable." },
      { action: "Stock Adjustment", detail: "Perform cycle count; enter counted qty; system auto-creates adjustment journal for variance." },
      { action: "Inventory Reporting", detail: "Generate stock valuation, slow-mover, and warehouse utilization reports for operations review." },
    ],
  },
  {
    role: "Sales Manager",
    description: "Manages the sales pipeline, quota attainment, customer negotiations, and revenue forecasting.",
    steps: [
      { action: "Pipeline Review", detail: "Open CRM kanban; review stage distribution, deal age, and win probability by rep." },
      { action: "Quota Monitoring", detail: "Compare closed deals to monthly quota; identify reps at risk; plan coaching sessions." },
      { action: "Quote Approval", detail: "Review rep-generated quotations above discount threshold; approve or negotiate pricing and terms." },
      { action: "Forecast Submission", detail: "Enter committed and best-case forecast for the month; review AI-assisted prediction; submit to CFO." },
      { action: "Revenue Report", detail: "Generate closed revenue by product, region, and rep; analyze win/loss reasons; plan next sprint." },
    ],
  },
  {
    role: "Operations Manager",
    description: "Manages cross-functional operations: projects, fleet, maintenance, and quality assurance.",
    steps: [
      { action: "Project Oversight", detail: "Review all active projects on Gantt; flag delayed milestones; reallocate resources as needed." },
      { action: "Fleet Monitoring", detail: "Check vehicle utilization, upcoming PM, and insurance renewals; dispatch drivers for assignments." },
      { action: "Maintenance Review", detail: "Review open maintenance tickets; confirm PMs are on schedule; resolve overdue corrective actions." },
      { action: "Quality Audit", detail: "Review NCR log and CAPA status; close overdue corrective actions; update supplier quality scores." },
      { action: "Operations Report", detail: "Compile weekly operations summary: project KPIs, fleet cost, maintenance backlog, and QC metrics." },
    ],
  },
  {
    role: "System Admin",
    description: "Configures and maintains the ERP platform: users, roles, integrations, and system security.",
    steps: [
      { action: "User Provisioning", detail: "Create user account; assign role; set module-level permissions; enforce 2FA; send welcome email." },
      { action: "Role Configuration", detail: "Define or modify role permissions at module, record, and field level; test with staging user." },
      { action: "Integration Management", detail: "Configure API keys for bank feeds, e-commerce, and external systems; test webhook connectivity." },
      { action: "Audit Review", detail: "Review audit log for suspicious changes; export compliance report; escalate anomalies to management." },
      { action: "System Maintenance", detail: "Monitor system performance, apply updates, test in staging, and deploy to production during off-peak." },
    ],
  },
];

const erpPermissions: PermissionRole[] = [
  { role: "System Admin", level: "full", categories: ["finance", "hr", "inventory", "operations", "erp", "reports", "admin"], description: "Full ERP access — all modules, all settings, user management." },
  { role: "Finance Manager", level: "finance", categories: ["finance", "reports"], description: "All accounting, AP/AR, budgeting, assets, and financial reporting." },
  { role: "HR Manager", level: "hr", categories: ["hr", "reports"], description: "All HR modules: employees, payroll, recruitment, performance." },
  { role: "Inventory Manager", level: "inventory", categories: ["inventory", "reports"], description: "Stock management, warehouses, procurement, and inventory reporting." },
  { role: "Sales Manager", level: "operations", categories: ["operations", "erp", "reports"], description: "CRM, sales orders, quotations, subscriptions, and revenue reports." },
  { role: "Operations Manager", level: "operations", categories: ["operations", "inventory", "reports"], description: "Projects, fleet, maintenance, quality, and operations reporting." },
  { role: "Employee", level: "limited", categories: ["erp"], description: "Expenses, leave requests, timesheets, discuss, todo, and portal — self-service only." },
];

// ─────────────────────────────────────────────────────────────────────────────
// Export
// ─────────────────────────────────────────────────────────────────────────────
export const PRODUCT_MODULES_DATA: Record<string, ProductModulesData> = {
  "cymed-hospital": {
    modules: hospitalModules,
    roleWorkflows: hospitalWorkflows,
    permissionRoles: hospitalPermissions,
  },
  "cymed-clinic": {
    modules: clinicModules,
    roleWorkflows: clinicWorkflows,
    permissionRoles: clinicPermissions,
  },
  "cymed-pharmacy": {
    modules: pharmacyModules,
    roleWorkflows: pharmacyWorkflows,
    permissionRoles: pharmacyPermissions,
  },
  "cymed-laboratory": {
    modules: laboratoryModules,
    roleWorkflows: laboratoryWorkflows,
    permissionRoles: laboratoryPermissions,
  },
  "cymed-imaging": {
    modules: imagingModules,
    roleWorkflows: imagingWorkflows,
    permissionRoles: imagingPermissions,
  },
  "cyshop": {
    modules: cyshopModules,
    roleWorkflows: cyshopWorkflows,
    permissionRoles: cyshopPermissions,
  },
  "cycom-erp": {
    modules: erpModules,
    roleWorkflows: erpWorkflows,
    permissionRoles: erpPermissions,
  },
  "cycom": {
    modules: erpModules,
    roleWorkflows: erpWorkflows,
    permissionRoles: erpPermissions,
  },
};
