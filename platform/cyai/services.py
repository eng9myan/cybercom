import time
import re
from typing import Any, Dict, List, Optional
from django.utils import timezone
from platform.cyai.models import ModelConfig, PromptTemplate, GuardrailPolicy, InferenceLog

class GuardrailEngine:
    """
    Enforces privacy and clinical safety policies by scrubbing PII, PHI, and checking content bounds.
    """
    # Regex patterns for basic PII/PHI scrubbing
    EMAIL_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
    PHONE_PATTERN = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
    MRN_PATTERN = re.compile(r"\bMRN\d{6,10}\b", re.IGNORECASE)  # Medical Record Number (PHI)

    @classmethod
    def validate_content(cls, content: str, policies: List[GuardrailPolicy]) -> Dict[str, Any]:
        verdict = "passed"
        flagged_reasons = []
        scrubbed_content = content

        for policy in policies:
            if not policy.active:
                continue

            policy_type = policy.policy_type.lower()
            if policy_type in ("pii_detection", "phi_scrub"):
                # Scrub Emails
                if cls.EMAIL_PATTERN.search(scrubbed_content):
                    scrubbed_content = cls.EMAIL_PATTERN.sub("[CONFIDENTIAL_EMAIL]", scrubbed_content)
                    flagged_reasons.append(f"{policy.name}: PII Email detected and scrubbed")
                
                # Scrub Phones
                if cls.PHONE_PATTERN.search(scrubbed_content):
                    scrubbed_content = cls.PHONE_PATTERN.sub("[CONFIDENTIAL_PHONE]", scrubbed_content)
                    flagged_reasons.append(f"{policy.name}: PII Phone number detected and scrubbed")

                # Scrub Medical Record Numbers (PHI)
                if cls.MRN_PATTERN.search(scrubbed_content):
                    scrubbed_content = cls.MRN_PATTERN.sub("[PHI_MRN]", scrubbed_content)
                    flagged_reasons.append(f"{policy.name}: PHI MRN detected and scrubbed")

            elif policy_type == "clinical_safety":
                blocked_keywords = policy.parameters.get("blocked_keywords", [])
                for kw in blocked_keywords:
                    if kw.lower() in scrubbed_content.lower():
                        verdict = "blocked"
                        flagged_reasons.append(f"Clinical Safety Block: prohibited term '{kw}' found")

        return {
            "verdict": verdict,
            "flagged_reasons": flagged_reasons,
            "scrubbed_content": scrubbed_content
        }


class ModelGateway:
    """
    Unified router to invoke LLM completion providers.
    """
    @classmethod
    def generate_completion(
        cls,
        tenant_id: str,
        config: ModelConfig,
        prompt: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        start_time = time.monotonic()
        
        # Formulate final prompt
        final_prompt = prompt
        if variables:
            for k, v in variables.items():
                final_prompt = final_prompt.replace(f"{{{k}}}", str(v))

        # 1. Pre-inference guardrails validation
        policies = list(GuardrailPolicy.objects.filter(active=True))
        guardrail_res = GuardrailEngine.validate_content(final_prompt, policies)
        
        if guardrail_res["verdict"] == "blocked":
            log = InferenceLog.objects.create(
                tenant_id=tenant_id,
                model=config,
                prompt_used=final_prompt,
                response_text="Blocked by safety guardrail policies.",
                safety_verdict="blocked",
                error_message="Prompt blocked by Clinical Safety guardrail policy",
                latency_ms=0
            )
            return {"text": log.response_text, "status": "blocked", "log_id": log.id}

        scrubbed_prompt = guardrail_res["scrubbed_content"]
        response_text = ""
        error_msg = ""
        verdict = "passed"

        try:
            # Simulate external API call
            provider = config.provider.lower()
            if provider == "gemini":
                response_text = f"[Gemini {config.model_name}] Response to: {scrubbed_prompt[:40]}..."
            elif provider == "openai":
                response_text = f"[GPT {config.model_name}] Response to: {scrubbed_prompt[:40]}..."
            elif provider == "anthropic":
                response_text = f"[Claude {config.model_name}] Response to: {scrubbed_prompt[:40]}..."
            else:
                response_text = f"[Ollama {config.model_name}] Response to: {scrubbed_prompt[:40]}..."
        except Exception as exc:
            error_msg = str(exc)
            verdict = "flagged"

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # 2. Post-inference output guardrails
        output_guardrail_res = GuardrailEngine.validate_content(response_text, policies)
        final_response = output_guardrail_res["scrubbed_content"]
        if output_guardrail_res["verdict"] == "blocked":
            final_response = "Blocked by safety guardrail policies."
            verdict = "blocked"

        log = InferenceLog.objects.create(
            tenant_id=tenant_id,
            model=config,
            prompt_used=final_prompt,
            response_text=final_response,
            tokens_prompt=len(scrubbed_prompt) // 4,
            tokens_completion=len(final_response) // 4,
            latency_ms=elapsed_ms,
            safety_verdict=verdict,
            error_message=error_msg
        )

        return {
            "text": final_response,
            "status": verdict,
            "tokens_prompt": log.tokens_prompt,
            "tokens_completion": log.tokens_completion,
            "latency_ms": elapsed_ms,
            "log_id": log.id
        }


class RAGService:
    """
    Simulates Retrieval-Augmented Generation (context search & template rendering).
    """
    @classmethod
    def query_context_and_generate(
        cls,
        tenant_id: str,
        config: ModelConfig,
        template: PromptTemplate,
        query: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Mimic retrieving semantic context from Vector Database (Milvus/pgvector)
        simulated_context = f"[Context: Search result for query '{query}': User medical records and consent policies match.]"
        
        merged_variables = {
            **variables,
            "context": simulated_context,
            "query": query
        }

        return ModelGateway.generate_completion(
            tenant_id=tenant_id,
            config=config,
            prompt=template.template_text,
            variables=merged_variables
        )
