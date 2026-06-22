import uuid
import json
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
import jwt

from platform.terminology.models import TerminologyAuditLog
from platform.terminology.providers.registry import TerminologyProviderRegistry
from platform.terminology.providers.base import TerminologyProvider
from platform.terminology.providers.icd11 import ICD11Provider
from platform.terminology.providers.snomed import SNOMEDProvider
from platform.terminology.providers.loinc import LOINCProvider
from platform.terminology.providers.icf import ICFProvider
from platform.terminology.providers.fhir import FHIRTerminologyProvider
from platform.terminology.services import TerminologyService

# Dummy RxNorm provider for hot-swapping verification
class RxNormProvider(TerminologyProvider):
    def search(self, query: str, limit: int = 10, **kwargs):
        return [{"code": "863671", "display": "Lisinopril 10 MG Oral Tablet", "type": "drug"}]
    
    def lookup(self, code: str, **kwargs):
        if code == "863671":
            return {"code": "863671", "display": "Lisinopril 10 MG Oral Tablet", "definition": "Mock RxNorm drug details"}
        return None

    def validate(self, code: str, **kwargs) -> bool:
        return code == "863671"

    def translate(self, code: str, target_system: str, **kwargs):
        return {"code": "rx-lisinopril", "system": target_system, "relationship": "equivalent"}

    def expand(self, value_set: str, filter_str: str = None, **kwargs):
        return [{"code": "863671", "display": "Lisinopril 10 MG"}]

    def get_children(self, code: str, **kwargs):
        return []

    def get_parents(self, code: str, **kwargs):
        return []

    def get_synonyms(self, code: str, **kwargs):
        return ["Lisinopril"]

    def get_mappings(self, code: str, target_system: str, **kwargs):
        return [self.translate(code, target_system)]

    def get_version(self) -> str:
        return "2025-RxNorm"


@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def auth_client(test_tenant_id):
    client = APIClient()
    payload = {
        "sub": "22222222-2222-2222-2222-222222222222",
        "email": "doctor@cybercom.io",
        "tenant_id": str(test_tenant_id),
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    }
    token = jwt.encode(payload, "dummy-secret", algorithm="HS256")
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_TENANT_ID=str(test_tenant_id),
    )
    return client


@pytest.mark.django_db
class TestTerminologyRegistry:
    def test_registry_registration_and_retrieval(self):
        # Default providers should be registered automatically via apps.py
        # But we can test manual registration too
        registry = TerminologyProviderRegistry()
        
        # Test default registration retrieval
        icd11 = registry.get_provider("icd11")
        assert isinstance(icd11, ICD11Provider)
        
        # Test error for unregistered provider
        with pytest.raises(ValueError, match="is not registered"):
            registry.get_provider("invalid-provider")

        # Test hot-swapping a custom provider (RxNorm)
        rxnorm = RxNormProvider()
        registry.register_provider("rxnorm", rxnorm)
        
        provider = registry.get_provider("rxnorm")
        assert isinstance(provider, RxNormProvider)
        assert provider.get_version() == "2025-RxNorm"
        
        # Test list providers
        providers_list = registry.list_providers()
        assert "rxnorm" in providers_list
        assert "icd11" in providers_list
        
        # Test deregister provider
        registry.deregister_provider("rxnorm")
        with pytest.raises(ValueError):
            registry.get_provider("rxnorm")


@pytest.mark.django_db
class TestICD11Provider:
    def test_icd11_operations(self):
        provider = ICD11Provider()
        
        # Search
        results = provider.search("diabetes")
        assert len(results) >= 2
        assert any(r["code"] == "1B10.0" for r in results)

        # Lookup stem code
        details = provider.lookup("FA81")
        assert details is not None
        assert details["display"] == "Osteoarthritis of knee"
        assert details["is_post_coordinated"] is False

        # Lookup post-coordinated cluster code
        cluster_details = provider.lookup("FA81&XY1Y&XS17")
        assert cluster_details is not None
        assert cluster_details["is_post_coordinated"] is True
        assert cluster_details["stem_code"] == "FA81"
        assert len(cluster_details["extensions"]) == 2
        assert "Right side" in cluster_details["display"]
        assert "Present on admission" in cluster_details["display"]

        # Validate valid
        assert provider.validate("FA81&XY1Y&XS17") is True
        # Validate invalid stem
        assert provider.validate("INVALID&XY1Y") is False
        # Validate invalid extension
        assert provider.validate("FA81&INVALID") is False

        # Translate ICD-11 to ICD-10
        translation = provider.translate("FA81", "icd10")
        assert translation is not None
        assert translation["code"] == "M17"

        # Translate ICD-10 to ICD-11
        translation_rev = provider.translate("E10", "icd11")
        assert translation_rev is not None
        assert translation_rev["code"] == "1B10.0"

        # Expand
        expansion = provider.expand("diabetes")
        assert len(expansion) == 2
        assert expansion[0]["code"] == "1B10.0"

        # Hierarchy
        assert len(provider.get_children("FA80")) > 0
        assert len(provider.get_parents("1B10.0")) == 1
        assert "1B10" in provider.get_parents("1B10.0")[0]["code"]

        # Synonyms
        assert "IDDM" in provider.get_synonyms("1B10.0")

        # Mappings
        mappings = provider.get_mappings("FA81", "icd10")
        assert len(mappings) == 1
        assert mappings[0]["code"] == "M17"


@pytest.mark.django_db
class TestSNOMEDProvider:
    def test_snomed_operations(self):
        provider = SNOMEDProvider()

        # Search
        results = provider.search("diabetes")
        assert len(results) >= 2
        
        # Lookup
        details = provider.lookup("111553001")
        assert details is not None
        assert "Type 1 diabetes" in details["display"]

        # Validate
        assert provider.validate("111553001") is True
        assert provider.validate("invalid") is False

        # Translate SNOMED to ICD-11
        translation = provider.translate("111553001", "icd11")
        assert translation is not None
        assert translation["code"] == "1B10.0"

        # Hierarchy
        children = provider.get_children("73211009")
        assert len(children) == 2
        parents = provider.get_parents("111553001")
        assert len(parents) == 1

        # Synonyms
        assert "Coxarthrosis" in provider.get_synonyms("239720000")


@pytest.mark.django_db
class TestLOINCProvider:
    def test_loinc_operations(self):
        provider = LOINCProvider()

        # Search
        results = provider.search("glucose")
        assert len(results) == 1
        assert results[0]["code"] == "2339-0"

        # Lookup
        details = provider.lookup("2339-0")
        assert details is not None
        assert details["class"] == "CHEM"

        # Validate
        assert provider.validate("2339-0") is True

        # Translate (LOINC to SNOMED mapping)
        translation = provider.translate("2339-0", "snomed")
        assert translation is not None
        assert translation["code"] == "365812005"

        # Expand
        expansion = provider.expand("chemistry")
        assert len(expansion) == 2


@pytest.mark.django_db
class TestICFProvider:
    def test_icf_operations(self):
        provider = ICFProvider()

        # Search
        results = provider.search("walking")
        assert len(results) == 1
        assert results[0]["code"] == "d450"

        # Lookup
        details = provider.lookup("d450")
        assert details is not None
        assert details["component"] == "Activities and Participation"

        # Translate (ICF to WHODAS mapping)
        translation = provider.translate("d450", "whodas")
        assert translation is not None
        assert translation["code"] == "WHODAS-D4.1"


@pytest.mark.django_db
class TestFHIRTerminologyProvider:
    def test_fhir_operations(self):
        provider = FHIRTerminologyProvider()

        # Search
        results = provider.search("male")
        assert len(results) >= 1

        # Lookup ($lookup)
        details = provider.lookup("male", system="http://hl7.org/fhir/administrative-gender")
        assert details is not None
        assert details["display"] == "Male"

        # Validate ($validate-code)
        assert provider.validate("male", system="http://hl7.org/fhir/administrative-gender") is True
        assert provider.validate("invalid", system="http://hl7.org/fhir/administrative-gender") is False
        assert provider.validate("male", value_set="http://hl7.org/fhir/ValueSet/administrative-gender") is True

        # Translate ($translate)
        translation = provider.translate("male", "http://terminology.hl7.org/CodeSystem/v3-AdministrativeGender")
        assert translation is not None
        assert translation["code"] == "M"

        # Expand ($expand)
        expansion = provider.expand("http://hl7.org/fhir/ValueSet/administrative-gender", filter_str="female")
        assert len(expansion) == 1
        assert expansion[0]["code"] == "female"

        # Subsumes ($subsumes)
        assert provider.subsumes("parent-concept", "child-concept") == "subsumes"
        assert provider.subsumes("child-concept", "parent-concept") == "subsumed-by"
        assert provider.subsumes("concept-a", "concept-a") == "equivalent"
        assert provider.subsumes("concept-a", "concept-b") == "not-subsumed"


@pytest.mark.django_db
class TestTerminologyService:
    def test_service_delegation_and_audit(self, test_tenant_id):
        # Test service search with auditing
        results = TerminologyService.search(
            provider="icd11",
            query="common cold",
            tenant_id=str(test_tenant_id),
            requested_by="test-user"
        )
        assert len(results) == 1
        assert results[0]["code"] == "CA00"

        # Verify audit log entry
        logs = TerminologyAuditLog.objects.filter(tenant_id=test_tenant_id, operation="search")
        assert logs.count() == 1
        log = logs.first()
        assert log.provider == "icd11"
        assert log.query == "common cold"
        assert log.requested_by == "test-user"
        assert log.records_returned == 1

        # Test service lookup
        details = TerminologyService.lookup(
            provider="snomed",
            code="111553001",
            tenant_id=str(test_tenant_id)
        )
        assert details is not None
        assert "Type 1 diabetes" in details["display"]
        assert TerminologyAuditLog.objects.filter(tenant_id=test_tenant_id, operation="lookup").count() == 1

        # Test service validate
        is_valid = TerminologyService.validate(
            provider="loinc",
            code="2339-0",
            tenant_id=str(test_tenant_id)
        )
        assert is_valid is True
        assert TerminologyAuditLog.objects.filter(tenant_id=test_tenant_id, operation="validate").count() == 1

        # Test service translate
        translation = TerminologyService.translate(
            provider="icf",
            code="d450",
            target_system="whodas",
            tenant_id=str(test_tenant_id)
        )
        assert translation is not None
        assert translation["code"] == "WHODAS-D4.1"
        assert TerminologyAuditLog.objects.filter(tenant_id=test_tenant_id, operation="translate").count() == 1

        # Test service expand
        expansion = TerminologyService.expand(
            provider="fhir",
            value_set="http://hl7.org/fhir/ValueSet/administrative-gender",
            tenant_id=str(test_tenant_id)
        )
        assert len(expansion) == 4
        assert TerminologyAuditLog.objects.filter(tenant_id=test_tenant_id, operation="expand").count() == 1

        # Test service subsumes
        outcome = TerminologyService.subsumes(
            provider="fhir",
            code_a="parent-concept",
            code_b="child-concept",
            tenant_id=str(test_tenant_id)
        )
        assert outcome == "subsumes"
        assert TerminologyAuditLog.objects.filter(tenant_id=test_tenant_id, operation="subsumes").count() == 1

        # Verify OutboxEvents were published (Event Driven)
        from platform.events.models import OutboxEvent
        events = OutboxEvent.objects.filter(tenant_id=test_tenant_id)
        assert events.count() == 6
        assert events.filter(event_type="cyterminology.search.executed").count() == 1
        assert events.filter(event_type="cyterminology.lookup.executed").count() == 1
        assert events.filter(event_type="cyterminology.validation.executed").count() == 1
        assert events.filter(event_type="cyterminology.translation.executed").count() == 1
        assert events.filter(event_type="cyterminology.expansion.executed").count() == 1
        assert events.filter(event_type="cyterminology.subsumes.executed").count() == 1



@pytest.mark.django_db
class TestTerminologyAPIs:
    def test_endpoints_unauthenticated(self):
        client = APIClient()
        
        # Test unauthenticated access returns 401
        assert client.post("/api/v1/terminology/search/", {}).status_code == 401
        assert client.post("/api/v1/terminology/lookup/", {}).status_code == 401
        assert client.post("/api/v1/terminology/validate/", {}).status_code == 401
        assert client.post("/api/v1/terminology/translate/", {}).status_code == 401
        assert client.post("/api/v1/terminology/expand/", {}).status_code == 401
        assert client.post("/api/v1/terminology/subsumes/", {}).status_code == 401
        assert client.get("/api/v1/terminology/logs/").status_code == 401

    def test_search_endpoint(self, auth_client, test_tenant_id):
        resp = auth_client.post(
            "/api/v1/terminology/search/",
            {
                "provider": "icd11",
                "tenant_id": str(test_tenant_id),
                "query": "common cold",
                "limit": 5
            },
            format="json"
        )
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["code"] == "CA00"

    def test_lookup_endpoint(self, auth_client, test_tenant_id):
        resp = auth_client.post(
            "/api/v1/terminology/lookup/",
            {
                "provider": "snomed",
                "tenant_id": str(test_tenant_id),
                "code": "111553001"
            },
            format="json"
        )
        assert resp.status_code == 200
        assert "Type 1 diabetes" in resp.data["display"]

        # Concept not found
        resp_404 = auth_client.post(
            "/api/v1/terminology/lookup/",
            {
                "provider": "snomed",
                "tenant_id": str(test_tenant_id),
                "code": "invalid-code"
            },
            format="json"
        )
        assert resp_404.status_code == 404

    def test_validate_endpoint(self, auth_client, test_tenant_id):
        resp = auth_client.post(
            "/api/v1/terminology/validate/",
            {
                "provider": "loinc",
                "tenant_id": str(test_tenant_id),
                "code": "2339-0"
            },
            format="json"
        )
        assert resp.status_code == 200
        assert resp.data["valid"] is True

    def test_translate_endpoint(self, auth_client, test_tenant_id):
        resp = auth_client.post(
            "/api/v1/terminology/translate/",
            {
                "provider": "icf",
                "tenant_id": str(test_tenant_id),
                "code": "d450",
                "target_system": "whodas"
            },
            format="json"
        )
        assert resp.status_code == 200
        assert resp.data["code"] == "WHODAS-D4.1"

        # Translation not found
        resp_404 = auth_client.post(
            "/api/v1/terminology/translate/",
            {
                "provider": "icf",
                "tenant_id": str(test_tenant_id),
                "code": "d450",
                "target_system": "invalid-target"
            },
            format="json"
        )
        assert resp_404.status_code == 404

    def test_expand_endpoint(self, auth_client, test_tenant_id):
        resp = auth_client.post(
            "/api/v1/terminology/expand/",
            {
                "provider": "fhir",
                "tenant_id": str(test_tenant_id),
                "value_set": "http://hl7.org/fhir/ValueSet/administrative-gender",
                "filter_str": "female"
            },
            format="json"
        )
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]["code"] == "female"

    def test_subsumes_endpoint(self, auth_client, test_tenant_id):
        resp = auth_client.post(
            "/api/v1/terminology/subsumes/",
            {
                "provider": "fhir",
                "tenant_id": str(test_tenant_id),
                "code_a": "parent-concept",
                "code_b": "child-concept"
            },
            format="json"
        )
        assert resp.status_code == 200
        assert resp.data["outcome"] == "subsumes"

    def test_audit_logs_endpoint(self, auth_client, test_tenant_id):
        # Trigger an operation to generate a log
        TerminologyService.search(
            provider="icd11",
            query="diabetes",
            tenant_id=str(test_tenant_id),
            requested_by="test-user"
        )

        resp = auth_client.get("/api/v1/terminology/logs/")
        assert resp.status_code == 200
        results = resp.data.get("results", resp.data)
        assert len(results) >= 1
        assert any(str(log["tenant_id"]) == str(test_tenant_id) for log in results)


@pytest.mark.django_db
class TestTerminologyHotSwapping:
    def test_hot_swapping_via_service(self, test_tenant_id):
        # Register new provider
        TerminologyProviderRegistry.register_provider("rxnorm", RxNormProvider())

        # Query custom RxNorm provider through the service layer
        results = TerminologyService.search(
            provider="rxnorm",
            query="Lisinopril",
            tenant_id=str(test_tenant_id)
        )
        assert len(results) == 1
        assert results[0]["code"] == "863671"
        assert results[0]["display"] == "Lisinopril 10 MG Oral Tablet"

        # Deregister to restore clean state
        TerminologyProviderRegistry.deregister_provider("rxnorm")
