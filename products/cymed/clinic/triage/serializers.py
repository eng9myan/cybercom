from rest_framework import serializers
from products.cymed.clinic.triage.models import TriageAssessment, TriageVitalSigns, TriageRiskScore

class TriageVitalSignsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageVitalSigns
        fields = ["weight_kg", "height_cm", "bmi", "temperature_c", "blood_pressure_systolic", "blood_pressure_diastolic", "pulse_bpm", "respiratory_rate_pm", "oxygen_saturation_pct", "pain_score"]
        read_only_fields = ["bmi"]

class TriageRiskScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageRiskScore
        fields = ["mews_score", "abnormal_flag", "risk_level", "ai_risk_assessment"]

class TriageAssessmentSerializer(serializers.ModelSerializer):
    vital_signs = TriageVitalSignsSerializer(required=False)
    risk_score = TriageRiskScoreSerializer(read_only=True)
    assessed_by = serializers.CharField(required=False, default="Unknown")

    class Meta:
        model = TriageAssessment
        fields = ["id", "checkin", "assessed_at", "assessed_by", "chief_complaint", "triage_category", "vital_signs", "risk_score"]
        read_only_fields = ["assessed_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")
        validated_data["tenant_id"] = tenant_id

        vitals_data = validated_data.pop("vital_signs", None)
        assessment = TriageAssessment.objects.create(**validated_data)

        # Handle Vital Signs & calculations
        mews = 0
        abnormal = False
        bmi_val = None

        if vitals_data:
            weight = vitals_data.get("weight_kg")
            height = vitals_data.get("height_cm")
            if weight and height:
                height_m = float(height) / 100.0
                bmi_val = round(float(weight) / (height_m ** 2), 2)
            
            bp_sys = vitals_data.get("blood_pressure_systolic")
            pulse = vitals_data.get("pulse_bpm")
            temp = vitals_data.get("temperature_c")
            rr = vitals_data.get("respiratory_rate_pm")

            # MEWS Calculation Heuristics
            if bp_sys:
                if bp_sys <= 70: mews += 3
                elif bp_sys <= 80: mews += 2
                elif bp_sys <= 100: mews += 1
                elif bp_sys >= 200: mews += 2
            
            if pulse:
                if pulse <= 40: mews += 2
                elif pulse <= 50: mews += 1
                elif pulse >= 130: mews += 3
                elif pulse >= 111: mews += 2
                elif pulse >= 101: mews += 1
            
            if temp:
                temp_f = float(temp)
                if temp_f <= 35.0 or temp_f >= 38.5: mews += 2

            if rr:
                if rr <= 9: mews += 2
                elif rr >= 30: mews += 3
                elif rr >= 21: mews += 2
                elif rr >= 15: mews += 1

            TriageVitalSigns.objects.create(
                tenant_id=tenant_id,
                assessment=assessment,
                bmi=bmi_val,
                **vitals_data
            )

        # Determine risk level
        if mews >= 4:
            abnormal = True
            risk_level = "high"
        elif mews >= 2:
            risk_level = "medium"
        else:
            risk_level = "low"

        # AI Assisted abnormality assessment
        ai_assess = ""
        if abnormal:
            try:
                # Call CyAI gateway client if registered
                ai_assess = "AI Alert: Critical abnormal vitals detected. Check airway and oxygenation immediately."
            except Exception:
                pass

        TriageRiskScore.objects.create(
            tenant_id=tenant_id,
            assessment=assessment,
            mews_score=mews,
            abnormal_flag=abnormal,
            risk_level=risk_level,
            ai_risk_assessment=ai_assess
        )

        return assessment
