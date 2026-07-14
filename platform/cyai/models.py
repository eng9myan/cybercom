import uuid

from django.db import models
from django.utils import timezone

from platform.common.models import PlatformModel


class ModelConfig(PlatformModel):
    """
    Registry of configured AI models and LLM API providers (Gemini, OpenAI, Anthropic, OpenSource).
    """

    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=50)  # gemini, openai, azure, anthropic, ollama
    model_name = models.CharField(max_length=200)  # gemini-1.5-pro, gpt-4o, claude-3-sonnet
    api_key_ref = models.CharField(max_length=255, blank=True)  # Vault path reference
    api_base_url = models.URLField(blank=True)
    active = models.BooleanField(default=True)
    temperature = models.DecimalField(max_digits=3, decimal_places=2, default=0.7)

    class Meta:
        db_table = "platform_ai_model_configs"

    def __str__(self) -> str:
        return f"ModelConfig({self.name}, {self.provider}/{self.model_name})"


class PromptTemplate(PlatformModel):
    """
    Versioned prompt templates with variables injection.
    """

    name = models.CharField(max_length=255, unique=True)
    template_text = models.TextField()
    variables = models.JSONField(default=list)  # List of expected placeholders
    version = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_ai_prompt_templates"

    def __str__(self) -> str:
        return f"Prompt({self.name}, v{self.version})"


class GuardrailPolicy(PlatformModel):
    """
    Guardrail rules verifying prompts and responses (PII/PHI filter, toxicity, hallucination).
    """

    name = models.CharField(max_length=255)
    policy_type = models.CharField(
        max_length=50
    )  # pii_detection, phi_scrub, sentiment, clinical_safety
    parameters = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_ai_guardrail_policies"

    def __str__(self) -> str:
        return f"GuardrailPolicy({self.name}, {self.policy_type})"


class InferenceLog(models.Model):
    """
    Audit ledger tracking LLM queries, tokens, safety status, and output.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    model = models.ForeignKey(ModelConfig, on_delete=models.SET_NULL, null=True, blank=True)
    prompt_used = models.TextField()
    response_text = models.TextField(blank=True)
    tokens_prompt = models.PositiveIntegerField(default=0)
    tokens_completion = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    safety_verdict = models.CharField(
        max_length=50, default="passed", db_index=True
    )  # passed, flagged, blocked
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "platform_ai_inference_logs"
        ordering = ["-created_at"]
