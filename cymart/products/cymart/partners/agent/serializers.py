import json

from rest_framework import serializers

from ..planner.serializers import MEALS, PoolItemSerializer
from ..serializers import LANGUAGE_CHOICES, PartnerRankProfileSerializer
from . import tools as T

MAX_MESSAGES = 60
MAX_BYTES = 300_000


class AgentToolCallSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=80)
    name = serializers.CharField(max_length=60)
    arguments = serializers.DictField(required=False, default=dict)


class AgentMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant", "tool"])
    content = serializers.JSONField(required=False, allow_null=True, default=None)
    tool_calls = AgentToolCallSerializer(many=True, required=False)
    tool_call_id = serializers.CharField(required=False, max_length=80)
    name = serializers.CharField(required=False, max_length=60)

    def validate(self, attrs):
        role = attrs["role"]
        if role == "user":
            if not isinstance(attrs.get("content"), str) or not attrs["content"].strip():
                raise serializers.ValidationError("A user message needs text content.")
            if len(attrs["content"]) > 2000:
                raise serializers.ValidationError("A user message is limited to 2000 characters.")
        elif role == "assistant":
            if attrs.get("content") is not None and not isinstance(attrs["content"], str):
                raise serializers.ValidationError("Assistant content must be text.")
            if len(attrs.get("tool_calls") or []) > 1:
                raise serializers.ValidationError("At most one tool call per assistant message.")
        else:
            if not attrs.get("tool_call_id") or not attrs.get("name"):
                raise serializers.ValidationError("A tool message needs tool_call_id and name.")
        return attrs


class AgentTriggerSerializer(serializers.Serializer):
    """Starts a conversation from the platform's own schedule, e.g. the customer's planned lunch time."""

    type = serializers.ChoiceField(choices=["meal_time"])
    meal = serializers.ChoiceField(choices=MEALS)
    calories = serializers.FloatField(required=False, min_value=50, max_value=3000)
    candidates = PoolItemSerializer(many=True, required=False, default=list)

    def validate_candidates(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("At most 50 candidates.")
        return value


class AgentTurnRequestSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, required=False, default="en")
    profile = PartnerRankProfileSerializer()
    # Which platform tools this platform has implemented. Anything else is never offered or accepted.
    platform_tools = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(T.CLIENT_TOOLS)), required=False, default=list, max_length=len(T.CLIENT_TOOLS)
    )
    messages = AgentMessageSerializer(many=True, required=False, default=list)
    trigger = AgentTriggerSerializer(required=False)
    # Confirmation ids the customer approved in the app (from an earlier needs_confirmation).
    confirmed = serializers.ListField(child=serializers.CharField(max_length=120), required=False, default=list, max_length=20)

    def validate(self, attrs):
        if attrs.get("trigger") and attrs["messages"]:
            raise serializers.ValidationError("A trigger starts a new conversation: send it with no messages.")
        if not attrs.get("trigger") and not attrs["messages"]:
            raise serializers.ValidationError({"messages": ["At least one message is required."]})
        return attrs

    def validate_messages(self, value):
        if not value:
            return value
        if len(value) > MAX_MESSAGES:
            raise serializers.ValidationError(f"At most {MAX_MESSAGES} messages; send a shorter transcript.")
        if len(json.dumps(value, default=str)) > MAX_BYTES:
            raise serializers.ValidationError("The transcript is too large.")
        called: set[str] = set()
        answered: set[str] = set()
        for m in value:
            if m["role"] == "assistant":
                called |= {c["id"] for c in m.get("tool_calls") or []}
            elif m["role"] == "tool":
                if m["tool_call_id"] not in called:
                    raise serializers.ValidationError("A tool result has no matching tool call before it.")
                answered.add(m["tool_call_id"])
        last = value[-1]
        ends_ok = last["role"] in ("user", "tool") or (last["role"] == "assistant" and last.get("tool_calls"))
        if not ends_ok:
            raise serializers.ValidationError("The transcript must end with a user message, a tool result, or an unanswered tool call.")
        return value
