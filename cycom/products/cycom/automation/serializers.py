from rest_framework import serializers

from products.cycom.automation.models import AutomationRule, AutomationRun
from products.cycom.automation.registry import (
    ACTION_TYPES,
    OPERATORS,
    TRIGGER_EVENTS,
    resolve_field,
    source_config,
)


class AutomationRunSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = AutomationRun
        fields = "__all__"
        read_only_fields = [f.name for f in AutomationRun._meta.fields]


class AutomationRuleSerializer(serializers.ModelSerializer):
    runs_recent = serializers.SerializerMethodField()

    class Meta:
        model = AutomationRule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "run_count", "last_run_at", "created_at", "updated_at"]

    def get_runs_recent(self, obj):
        return AutomationRunSerializer(obj.runs.all()[:5], many=True).data

    def validate_trigger_source(self, value):
        if source_config(value) is None:
            raise serializers.ValidationError(f"Unknown trigger source '{value}'.")
        return value

    def validate_trigger_event(self, value):
        if value not in TRIGGER_EVENTS:
            raise serializers.ValidationError(f"Unknown trigger event '{value}'.")
        return value

    def validate(self, attrs):
        # Conditions and actions are validated together against the source,
        # so a rule can never be saved naming a field/operator/action that
        # the engine would then silently fail on at trigger time.
        source = attrs.get("trigger_source") or getattr(self.instance, "trigger_source", None)
        if not source:
            return attrs

        for cond in attrs.get("conditions", []) or []:
            field_key, operator = cond.get("field"), cond.get("operator")
            resolved = resolve_field(source, field_key)
            if not resolved:
                raise serializers.ValidationError(
                    {"conditions": f"'{field_key}' is not a readable field on {source}."}
                )
            if operator not in OPERATORS:
                raise serializers.ValidationError({"conditions": f"Unknown operator '{operator}'."})
            _lbl, _path, ftype = resolved
            if OPERATORS[operator][1] and ftype != "number":
                raise serializers.ValidationError(
                    {"conditions": f"Operator '{operator}' needs a numeric field, '{field_key}' is {ftype}."}
                )

        for action in attrs.get("actions", []) or []:
            atype = action.get("type")
            if atype not in ACTION_TYPES:
                raise serializers.ValidationError({"actions": f"Unknown action type '{atype}'."})
            if atype == "set_field" and not resolve_field(source, action.get("field"), writable=True):
                raise serializers.ValidationError(
                    {"actions": f"'{action.get('field')}' is not a writable field on {source}."}
                )
            if atype == "send_email" and not (action.get("to") or "").strip():
                raise serializers.ValidationError({"actions": "send_email needs at least one recipient."})

        return attrs
