import time
from typing import Any, Dict, List, Optional
from django.utils import timezone
from platform.terminology.providers.registry import TerminologyProviderRegistry
from platform.terminology.models import TerminologyAuditLog

# OpenTelemetry Tracing setup
try:
    from opentelemetry import trace
    tracer = trace.get_tracer("cybercom.terminology")
except ImportError:
    class DummyTracer:
        def start_as_current_span(self, name, *args, **kwargs):
            import contextlib
            @contextlib.contextmanager
            def dummy_span():
                class DummySpan:
                    def set_attribute(self, k, v):
                        pass
                yield DummySpan()
            return dummy_span()
    tracer = DummyTracer()

def _publish_event(tenant_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    try:
        from platform.events.models import OutboxEvent
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="platform.terminology.events",
            event_type=event_type,
            payload=payload
        )
    except Exception:
        pass

class TerminologyService:
    """
    Unified entry point for all clinical terminology operations.
    Enforces the Provider and Adapter pattern rules (audited, multi-tenant, instrumented).
    """

    @classmethod
    def search(
        cls,
        provider: str,
        query: str,
        tenant_id: str,
        requested_by: str = "system",
        limit: int = 10,
        **kwargs
    ) -> List[Dict[str, Any]]:
        start_time = time.monotonic()
        with tracer.start_as_current_span("terminology.search") as span:
            span.set_attribute("tenant_id", str(tenant_id))
            span.set_attribute("provider", provider)
            span.set_attribute("query", query)
            
            adapter = TerminologyProviderRegistry.get_provider(provider)
            results = adapter.search(query, limit=limit, **kwargs)
            
            elapsed = int((time.monotonic() - start_time) * 1000)
            TerminologyAuditLog.objects.create(
                tenant_id=tenant_id,
                provider=provider.lower(),
                operation="search",
                query=query,
                records_returned=len(results),
                duration_ms=elapsed,
                requested_by=requested_by
            )
            _publish_event(
                tenant_id=tenant_id,
                event_type="cyterminology.search.executed",
                payload={"provider": provider, "query": query, "records_returned": len(results), "requested_by": requested_by}
            )
            return results

    @classmethod
    def lookup(
        cls,
        provider: str,
        code: str,
        tenant_id: str,
        requested_by: str = "system",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        start_time = time.monotonic()
        with tracer.start_as_current_span("terminology.lookup") as span:
            span.set_attribute("tenant_id", str(tenant_id))
            span.set_attribute("provider", provider)
            span.set_attribute("code", code)
            
            adapter = TerminologyProviderRegistry.get_provider(provider)
            res = adapter.lookup(code, **kwargs)
            
            elapsed = int((time.monotonic() - start_time) * 1000)
            TerminologyAuditLog.objects.create(
                tenant_id=tenant_id,
                provider=provider.lower(),
                operation="lookup",
                code=code,
                records_returned=1 if res else 0,
                duration_ms=elapsed,
                requested_by=requested_by
            )
            _publish_event(
                tenant_id=tenant_id,
                event_type="cyterminology.lookup.executed",
                payload={"provider": provider, "code": code, "found": res is not None, "requested_by": requested_by}
            )
            return res

    @classmethod
    def validate(
        cls,
        provider: str,
        code: str,
        tenant_id: str,
        requested_by: str = "system",
        **kwargs
    ) -> bool:
        start_time = time.monotonic()
        with tracer.start_as_current_span("terminology.validate") as span:
            span.set_attribute("tenant_id", str(tenant_id))
            span.set_attribute("provider", provider)
            span.set_attribute("code", code)
            
            adapter = TerminologyProviderRegistry.get_provider(provider)
            is_valid = adapter.validate(code, **kwargs)
            
            elapsed = int((time.monotonic() - start_time) * 1000)
            TerminologyAuditLog.objects.create(
                tenant_id=tenant_id,
                provider=provider.lower(),
                operation="validate",
                code=code,
                records_returned=1,
                duration_ms=elapsed,
                requested_by=requested_by
            )
            _publish_event(
                tenant_id=tenant_id,
                event_type="cyterminology.validation.executed",
                payload={"provider": provider, "code": code, "valid": is_valid, "requested_by": requested_by}
            )
            return is_valid

    @classmethod
    def translate(
        cls,
        provider: str,
        code: str,
        target_system: str,
        tenant_id: str,
        requested_by: str = "system",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        start_time = time.monotonic()
        with tracer.start_as_current_span("terminology.translate") as span:
            span.set_attribute("tenant_id", str(tenant_id))
            span.set_attribute("provider", provider)
            span.set_attribute("code", code)
            span.set_attribute("target_system", target_system)
            
            adapter = TerminologyProviderRegistry.get_provider(provider)
            res = adapter.translate(code, target_system, **kwargs)
            
            elapsed = int((time.monotonic() - start_time) * 1000)
            TerminologyAuditLog.objects.create(
                tenant_id=tenant_id,
                provider=provider.lower(),
                operation="translate",
                code=code,
                query=target_system,
                records_returned=1 if res else 0,
                duration_ms=elapsed,
                requested_by=requested_by
            )
            _publish_event(
                tenant_id=tenant_id,
                event_type="cyterminology.translation.executed",
                payload={"provider": provider, "code": code, "target_system": target_system, "found": res is not None, "requested_by": requested_by}
            )
            return res

    @classmethod
    def expand(
        cls,
        provider: str,
        value_set: str,
        tenant_id: str,
        requested_by: str = "system",
        filter_str: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        start_time = time.monotonic()
        with tracer.start_as_current_span("terminology.expand") as span:
            span.set_attribute("tenant_id", str(tenant_id))
            span.set_attribute("provider", provider)
            span.set_attribute("value_set", value_set)
            
            adapter = TerminologyProviderRegistry.get_provider(provider)
            results = adapter.expand(value_set, filter_str=filter_str, **kwargs)
            
            elapsed = int((time.monotonic() - start_time) * 1000)
            TerminologyAuditLog.objects.create(
                tenant_id=tenant_id,
                provider=provider.lower(),
                operation="expand",
                query=f"{value_set}:{filter_str or ''}",
                records_returned=len(results),
                duration_ms=elapsed,
                requested_by=requested_by
            )
            _publish_event(
                tenant_id=tenant_id,
                event_type="cyterminology.expansion.executed",
                payload={"provider": provider, "value_set": value_set, "records_returned": len(results), "requested_by": requested_by}
            )
            return results

    @classmethod
    def get_children(cls, provider: str, code: str, **kwargs) -> List[Dict[str, Any]]:
        adapter = TerminologyProviderRegistry.get_provider(provider)
        return adapter.get_children(code, **kwargs)

    @classmethod
    def get_parents(cls, provider: str, code: str, **kwargs) -> List[Dict[str, Any]]:
        adapter = TerminologyProviderRegistry.get_provider(provider)
        return adapter.get_parents(code, **kwargs)

    @classmethod
    def get_synonyms(cls, provider: str, code: str, **kwargs) -> List[str]:
        adapter = TerminologyProviderRegistry.get_provider(provider)
        return adapter.get_synonyms(code, **kwargs)

    @classmethod
    def get_mappings(cls, provider: str, code: str, target_system: str, **kwargs) -> List[Dict[str, Any]]:
        adapter = TerminologyProviderRegistry.get_provider(provider)
        return adapter.get_mappings(code, target_system, **kwargs)

    @classmethod
    def subsumes(
        cls,
        provider: str,
        code_a: str,
        code_b: str,
        tenant_id: str,
        requested_by: str = "system",
        **kwargs
    ) -> str:
        start_time = time.monotonic()
        with tracer.start_as_current_span("terminology.subsumes") as span:
            span.set_attribute("tenant_id", str(tenant_id))
            span.set_attribute("provider", provider)
            span.set_attribute("code_a", code_a)
            span.set_attribute("code_b", code_b)
            
            adapter = TerminologyProviderRegistry.get_provider(provider)
            if hasattr(adapter, "subsumes"):
                res = adapter.subsumes(code_a, code_b, **kwargs)
            else:
                res = "not-subsumed"
                
            elapsed = int((time.monotonic() - start_time) * 1000)
            TerminologyAuditLog.objects.create(
                tenant_id=tenant_id,
                provider=provider.lower(),
                operation="subsumes",
                code=f"{code_a}:{code_b}",
                records_returned=1,
                duration_ms=elapsed,
                requested_by=requested_by
            )
            _publish_event(
                tenant_id=tenant_id,
                event_type="cyterminology.subsumes.executed",
                payload={"provider": provider, "code_a": code_a, "code_b": code_b, "outcome": res, "requested_by": requested_by}
            )
            return res

