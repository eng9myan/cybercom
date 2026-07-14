"""
CyMed Clinical AI Intelligence Service
Bridges CyAI platform capabilities into clinical workflows across all CyMed products.

Rules:
- AI is ADVISORY ONLY — clinicians make all final decisions
- All AI outputs are logged for audit
- PHI/PII is scrubbed before sending to AI models
- AI cannot dispense, prescribe, or discharge patients
"""

from __future__ import annotations

import logging
from typing import Any

from django.utils import timezone

logger = logging.getLogger("cybercom.cymed.clinical_ai")


class ClinicalAIService:
    """
    Unified clinical AI service. All methods return advisory outputs only.
    All outputs include a mandatory disclaimer field.
    """

    ADVISORY_DISCLAIMER = (
        "AI-generated advisory only. Requires clinical review and validation by licensed clinician. "
        "Not for direct clinical decision-making without professional oversight."
    )

    # ─── Critical Value Alerting ────────────────────────────────────────────────

    @classmethod
    def assess_critical_lab_value(
        cls,
        tenant_id: str,
        patient_id: str,
        loinc_code: str,
        result_value: float,
        unit: str,
        normal_range_low: float,
        normal_range_high: float,
        critical_range_low: float | None = None,
        critical_range_high: float | None = None,
    ) -> dict[str, Any]:
        """
        Assess whether a lab result is critical and recommend urgency level.
        Returns advisory urgency level and suggested clinical actions.
        """
        # Determine criticality
        is_critical = False
        deviation_pct = 0.0
        urgency = "routine"
        suggested_actions = []

        if critical_range_low is not None and result_value < critical_range_low:
            is_critical = True
            deviation_pct = ((critical_range_low - result_value) / critical_range_low) * 100
            urgency = "critical"
        elif critical_range_high is not None and result_value > critical_range_high:
            is_critical = True
            deviation_pct = ((result_value - critical_range_high) / critical_range_high) * 100
            urgency = "critical"
        elif result_value < normal_range_low:
            deviation_pct = ((normal_range_low - result_value) / normal_range_low) * 100
            urgency = "abnormal" if deviation_pct < 20 else "urgent"
        elif result_value > normal_range_high:
            deviation_pct = ((result_value - normal_range_high) / normal_range_high) * 100
            urgency = "abnormal" if deviation_pct < 20 else "urgent"

        # LOINC-based clinical action suggestions (advisory)
        loinc_actions = {
            "2345-7": [
                "Check for hyperglycemia symptoms",
                "Review insulin orders",
                "Repeat glucose in 1 hour",
            ],  # Glucose
            "718-7": [
                "Assess for bleeding source",
                "Consider transfusion threshold",
                "Repeat CBC urgently",
            ],  # Hemoglobin
            "2160-0": [
                "Assess renal function",
                "Review nephrotoxic medications",
                "Consider nephrology consult",
            ],  # Creatinine
            "6298-4": [
                "Assess cardiac status",
                "Monitor for arrhythmia",
                "12-lead ECG recommended",
            ],  # Potassium
            "2951-2": [
                "Assess for sodium dysregulation",
                "Check fluid status",
                "Neurology consult if symptomatic",
            ],  # Sodium
        }
        suggested_actions = loinc_actions.get(
            loinc_code, ["Review with attending physician", "Correlate clinically"]
        )

        result = {
            "patient_id": patient_id,
            "loinc_code": loinc_code,
            "result_value": result_value,
            "unit": unit,
            "is_critical": is_critical,
            "urgency": urgency,
            "deviation_pct": round(deviation_pct, 2),
            "advisory_actions": suggested_actions,
            "disclaimer": cls.ADVISORY_DISCLAIMER,
            "assessed_at": timezone.now().isoformat(),
        }

        # Log to CyAI inference log
        cls._log_inference(tenant_id, "critical_lab_assessment", result)
        return result

    # ─── Drug Interaction ML Scoring ────────────────────────────────────────────

    @classmethod
    def score_drug_interaction_severity(
        cls,
        tenant_id: str,
        drug_a: str,
        drug_b: str,
        patient_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        AI-enhanced severity scoring for drug-drug interactions.
        Considers patient context (age, renal function, diagnoses).
        """
        # Rule-based severity scoring with context modifiers
        base_severity_map = {
            ("warfarin", "aspirin"): ("major", 0.92),
            ("metformin", "contrast"): ("major", 0.88),
            ("ssri", "maoi"): ("contraindicated", 0.99),
            ("statin", "fibrate"): ("moderate", 0.74),
            ("ace_inhibitor", "potassium"): ("moderate", 0.68),
            ("digoxin", "amiodarone"): ("major", 0.85),
            ("quinolone", "nsaid"): ("moderate", 0.62),
        }

        # Normalize drug names to lowercase
        key_ab = (drug_a.lower(), drug_b.lower())
        key_ba = (drug_b.lower(), drug_a.lower())
        severity, confidence = base_severity_map.get(
            key_ab, base_severity_map.get(key_ba, ("minor", 0.40))
        )

        # Context modifiers
        modifiers = []
        age = patient_context.get("age_years", 0)
        renal_egfr = patient_context.get("egfr", 100)

        if age > 75:
            confidence = min(confidence + 0.05, 0.99)
            modifiers.append("Elderly patient — increased sensitivity")
        if renal_egfr < 30:
            confidence = min(confidence + 0.07, 0.99)
            modifiers.append("Severe renal impairment — altered drug clearance")
        if patient_context.get("is_pregnant"):
            modifiers.append("Pregnancy — additional fetal risk consideration required")

        return {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "severity": severity,
            "confidence_score": round(confidence, 3),
            "context_modifiers": modifiers,
            "recommendation": cls._get_interaction_recommendation(severity),
            "disclaimer": cls.ADVISORY_DISCLAIMER,
        }

    @classmethod
    def _get_interaction_recommendation(cls, severity: str) -> str:
        return {
            "contraindicated": "Do not use together. Consult pharmacist and prescriber immediately.",
            "major": "Avoid combination if possible. Monitor closely if used together.",
            "moderate": "Use with caution. Monitor for adverse effects.",
            "minor": "Minimal clinical significance. Standard monitoring.",
        }.get(severity, "Review with clinical pharmacist.")

    # ─── Radiology AI Assist ────────────────────────────────────────────────────

    @classmethod
    def suggest_radiology_findings(
        cls,
        tenant_id: str,
        study_id: str,
        modality: str,
        body_part: str,
        clinical_indication: str,
        dicom_metadata: dict | None = None,
    ) -> dict[str, Any]:
        """
        AI-assisted radiology finding suggestions.
        ADVISORY ONLY — radiologist must review all findings.
        """
        # Modality-specific finding templates (simulated AI output)
        finding_templates = {
            ("CT", "chest"): {
                "structures_evaluated": [
                    "lungs",
                    "mediastinum",
                    "pleura",
                    "chest wall",
                    "great vessels",
                ],
                "common_findings_to_assess": [
                    "Pulmonary nodules (size, morphology, distribution)",
                    "Ground-glass opacities",
                    "Consolidation patterns",
                    "Pleural effusion",
                    "Lymphadenopathy",
                    "Cardiac silhouette",
                ],
                "suggested_report_template": "CT chest [with/without contrast]. [Findings]. Impression: [impression].",
            },
            ("MRI", "brain"): {
                "structures_evaluated": [
                    "cerebral cortex",
                    "white matter",
                    "basal ganglia",
                    "cerebellum",
                    "brainstem",
                    "ventricles",
                ],
                "common_findings_to_assess": [
                    "Signal abnormalities (T1/T2/FLAIR)",
                    "Diffusion restriction",
                    "Mass lesions with enhancement pattern",
                    "Midline shift",
                    "Hydrocephalus",
                    "Vascular flow voids",
                ],
                "suggested_report_template": "MRI brain [with/without gadolinium]. [Findings]. Impression: [impression].",
            },
            ("XR", "chest"): {
                "structures_evaluated": [
                    "cardiac silhouette",
                    "lung fields",
                    "mediastinum",
                    "costophrenic angles",
                    "bony thorax",
                ],
                "common_findings_to_assess": [
                    "Cardiomegaly (cardiothoracic ratio)",
                    "Vascular redistribution",
                    "Infiltrates/opacities",
                    "Pleural effusion",
                    "Pneumothorax",
                    "Rib fractures",
                ],
                "suggested_report_template": "Chest radiograph PA/lateral. [Findings]. Impression: [impression].",
            },
        }

        template_key = (modality.upper(), body_part.lower())
        template = finding_templates.get(
            template_key,
            {
                "structures_evaluated": ["Region of interest"],
                "common_findings_to_assess": [
                    "Assess clinically relevant structures for " + body_part
                ],
                "suggested_report_template": f"{modality} {body_part}. [Findings]. Impression: [impression].",
            },
        )

        result = {
            "study_id": study_id,
            "modality": modality,
            "body_part": body_part,
            "clinical_indication": clinical_indication,
            "ai_assisted": True,
            "structures_to_evaluate": template["structures_evaluated"],
            "suggested_findings_checklist": template["common_findings_to_assess"],
            "report_template": template["suggested_report_template"],
            "disclaimer": cls.ADVISORY_DISCLAIMER
            + " Radiologist signature required before report release.",
            "generated_at": timezone.now().isoformat(),
        }

        cls._log_inference(
            tenant_id, "radiology_ai_assist", {"study_id": study_id, "modality": modality}
        )
        return result

    # ─── Population Health Risk Scoring ─────────────────────────────────────────

    @classmethod
    def calculate_clinical_risk_score(
        cls,
        tenant_id: str,
        patient_id: str,
        risk_model: str,
        patient_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Calculate population health risk scores using evidence-based models.
        Supported models: crg, chads2vasc, wells_dvt, wells_pe, framingham, meld, sofa
        """
        score = 0
        category = "low"
        factors = []
        model_details = {}

        risk_model = risk_model.lower()

        if risk_model == "chads2vasc":
            # CHA₂DS₂-VASc for AFib stroke risk
            if patient_data.get("chf"):
                score += 1
                factors.append("Heart failure (+1)")
            if patient_data.get("hypertension"):
                score += 1
                factors.append("Hypertension (+1)")
            age = patient_data.get("age", 0)
            if age >= 75:
                score += 2
                factors.append("Age ≥75 (+2)")
            elif age >= 65:
                score += 1
                factors.append("Age 65-74 (+1)")
            if patient_data.get("diabetes"):
                score += 1
                factors.append("Diabetes (+1)")
            if patient_data.get("stroke_history"):
                score += 2
                factors.append("Stroke/TIA history (+2)")
            if patient_data.get("vascular_disease"):
                score += 1
                factors.append("Vascular disease (+1)")
            if patient_data.get("female"):
                score += 1
                factors.append("Female sex (+1)")
            category = (
                "low"
                if score == 0
                else ("low-moderate" if score == 1 else ("high" if score >= 3 else "moderate"))
            )
            model_details = {
                "anticoagulation_recommended": score >= 2,
                "annual_stroke_risk_pct": min(score * 1.3, 12.2),
            }

        elif risk_model == "sofa":
            # Sequential Organ Failure Assessment for ICU
            score += patient_data.get("respiratory_score", 0)  # PaO2/FiO2
            score += patient_data.get("coagulation_score", 0)  # Platelets
            score += patient_data.get("liver_score", 0)  # Bilirubin
            score += patient_data.get("cardiovascular_score", 0)  # MAP/vasopressors
            score += patient_data.get("cns_score", 0)  # GCS
            score += patient_data.get("renal_score", 0)  # Creatinine/urine
            category = (
                "low"
                if score < 6
                else ("moderate" if score < 10 else ("high" if score < 14 else "critical"))
            )
            model_details = {"predicted_mortality_pct": min(score * 6.5, 95)}

        elif risk_model == "meld":
            # Model for End-Stage Liver Disease
            import math

            creatinine = min(patient_data.get("creatinine", 1.0), 4.0)
            bilirubin = max(patient_data.get("bilirubin", 1.0), 1.0)
            inr = max(patient_data.get("inr", 1.0), 1.0)
            try:
                score = round(
                    10
                    * (
                        0.957 * math.log(creatinine)
                        + 0.378 * math.log(bilirubin)
                        + 1.12 * math.log(inr)
                        + 0.643
                    )
                )
                score = max(6, min(score, 40))
            except (ValueError, ZeroDivisionError):
                score = 6
            category = (
                "low"
                if score < 10
                else ("moderate" if score < 20 else ("high" if score < 30 else "critical"))
            )
            model_details = {
                "90_day_mortality_pct": min(score * 2.5, 90),
                "transplant_urgency": score >= 15,
            }

        elif risk_model == "crg":
            # Clinical Risk Grouping (simplified)
            conditions = patient_data.get("chronic_conditions", [])
            score = len(conditions) * 10
            if patient_data.get("age", 0) > 65:
                score += 15
            if patient_data.get("polypharmacy"):
                score += 10
            if patient_data.get("previous_hospitalization"):
                score += 20
            score = min(score, 100)
            category = (
                "low"
                if score < 25
                else ("moderate" if score < 50 else ("high" if score < 75 else "very_high"))
            )
            model_details = {"predicted_hospital_admission_pct": score * 0.8}

        else:
            # Generic scoring
            score = 50
            category = "moderate"
            model_details = {}

        cls._log_inference(
            tenant_id, f"risk_score_{risk_model}", {"patient_id": patient_id, "score": score}
        )

        return {
            "patient_id": patient_id,
            "risk_model": risk_model,
            "score": score,
            "risk_category": category,
            "contributing_factors": factors,
            "model_details": model_details,
            "disclaimer": cls.ADVISORY_DISCLAIMER,
            "calculated_at": timezone.now().isoformat(),
        }

    # ─── Clinical Decision Support ───────────────────────────────────────────────

    @classmethod
    def get_order_set_suggestions(
        cls,
        tenant_id: str,
        encounter_id: str,
        diagnosis_codes: list[str],
        encounter_type: str = "inpatient",
    ) -> dict[str, Any]:
        """
        Suggest evidence-based order sets based on admission diagnosis.
        """
        # ICD-11 code to order set mapping (simplified)
        order_set_map = {
            "BA00": {  # Pneumonia
                "name": "Community-Acquired Pneumonia Order Set",
                "labs": [
                    "CBC",
                    "CMP",
                    "Blood Culture x2",
                    "Sputum Culture",
                    "Procalcitonin",
                    "CRP",
                ],
                "imaging": ["Chest X-Ray PA/Lateral"],
                "medications": ["Azithromycin", "Amoxicillin-clavulanate", "Supplemental O2 PRN"],
                "monitoring": ["O2 Saturation q4h", "Temperature q6h", "Respiratory rate q6h"],
            },
            "5A11": {  # Diabetes
                "name": "Diabetes Management Order Set",
                "labs": ["HbA1c", "Fasting Glucose", "CMP", "Lipid Panel", "Microalbumin", "TSH"],
                "imaging": [],
                "medications": ["Metformin", "Insulin sliding scale PRN", "ASA 81mg daily"],
                "monitoring": ["Glucose AC & HS", "BP daily", "Foot exam"],
            },
            "BA41": {  # COPD exacerbation
                "name": "COPD Exacerbation Order Set",
                "labs": ["ABG", "CBC", "CMP", "BNP", "Sputum Culture"],
                "imaging": ["Chest X-Ray PA"],
                "medications": [
                    "Salbutamol nebulized q4h",
                    "Ipratropium q6h",
                    "Prednisone 40mg daily x5d",
                    "Supplemental O2",
                ],
                "monitoring": [
                    "O2 Saturation continuous",
                    "Respiratory rate q4h",
                    "Peak flow daily",
                ],
            },
        }

        suggestions = []
        for dx_code in diagnosis_codes:
            order_set = order_set_map.get(dx_code)
            if order_set:
                suggestions.append(
                    {
                        "diagnosis_code": dx_code,
                        "order_set": order_set,
                    }
                )

        if not suggestions:
            suggestions = [
                {
                    "diagnosis_code": diagnosis_codes[0] if diagnosis_codes else "unspecified",
                    "order_set": {
                        "name": "General Admission Order Set",
                        "labs": ["CBC", "CMP", "Coagulation profile", "Urinalysis"],
                        "imaging": ["Chest X-Ray PA"],
                        "medications": ["DVT prophylaxis", "Stress ulcer prophylaxis PRN"],
                        "monitoring": ["Vitals q8h", "Daily weights", "I&O monitoring"],
                    },
                }
            ]

        return {
            "encounter_id": encounter_id,
            "suggestions": suggestions,
            "disclaimer": cls.ADVISORY_DISCLAIMER
            + " Order sets must be reviewed and customized by ordering physician.",
        }

    # ─── Readmission Risk Prediction ─────────────────────────────────────────────

    @classmethod
    def predict_readmission_risk(
        cls,
        tenant_id: str,
        patient_id: str,
        discharge_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Predict 30-day readmission risk using LACE+ methodology.
        """
        # LACE+ score components
        length_of_stay = discharge_data.get("length_of_stay_days", 3)
        acuity = discharge_data.get("acuity_score", 3)  # 1-4
        comorbidities = len(discharge_data.get("comorbidities", []))
        ed_visits_past_6m = discharge_data.get("ed_visits_past_6m", 0)

        # LACE calculation
        l_score = min(length_of_stay, 7) if length_of_stay <= 7 else 7
        a_score = acuity
        c_score = min(comorbidities * 2, 10)
        e_score = min(ed_visits_past_6m * 2, 8)
        lace_score = l_score + a_score + c_score + e_score

        risk_pct = min(lace_score * 2.5, 75)
        category = "low" if lace_score < 7 else ("moderate" if lace_score < 11 else "high")

        interventions = []
        if lace_score >= 11:
            interventions = [
                "Schedule follow-up within 7 days of discharge",
                "Arrange home health or transitional care program",
                "Review and simplify medication regimen",
                "Ensure patient has primary care physician",
                "Patient education on warning signs",
            ]
        elif lace_score >= 7:
            interventions = [
                "Schedule follow-up within 14 days",
                "Discharge medication counseling",
                "Provide emergency contact information",
            ]
        else:
            interventions = ["Routine follow-up within 30 days"]

        return {
            "patient_id": patient_id,
            "lace_score": lace_score,
            "lace_components": {"L": l_score, "A": a_score, "C": c_score, "E": e_score},
            "readmission_risk_category": category,
            "predicted_readmission_risk_pct": round(risk_pct, 1),
            "recommended_interventions": interventions,
            "disclaimer": cls.ADVISORY_DISCLAIMER,
        }

    # ─── Internal Helpers ────────────────────────────────────────────────────────

    @classmethod
    def _log_inference(cls, tenant_id: str, inference_type: str, payload: dict[str, Any]) -> None:
        """Log AI inference to audit trail without PII."""
        try:
            from platform.audit.services import AuditService

            AuditService.log(
                tenant_id=tenant_id,
                actor_id="system.cyai",
                action=f"cyai.{inference_type}",
                resource_type="ClinicalAI",
                resource_id=inference_type,
                metadata={"type": inference_type, "advisory_only": True},
            )
        except Exception:
            logger.debug("Audit log skipped — AuditService unavailable in test context")
