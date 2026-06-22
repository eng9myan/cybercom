from platform.terminology.providers.registry import TerminologyProviderRegistry
from platform.terminology.providers.icd11 import ICD11Provider
from platform.terminology.providers.snomed import SNOMEDProvider
from platform.terminology.providers.loinc import LOINCProvider
from platform.terminology.providers.icf import ICFProvider
from platform.terminology.providers.fhir import FHIRTerminologyProvider

# Register default providers
TerminologyProviderRegistry.register_provider("icd11", ICD11Provider())
TerminologyProviderRegistry.register_provider("snomed", SNOMEDProvider())
TerminologyProviderRegistry.register_provider("loinc", LOINCProvider())
TerminologyProviderRegistry.register_provider("icf", ICFProvider())
TerminologyProviderRegistry.register_provider("fhir", FHIRTerminologyProvider())
