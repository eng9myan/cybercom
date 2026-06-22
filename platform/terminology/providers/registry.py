from typing import Dict, Optional
from platform.terminology.providers.base import TerminologyProvider

class TerminologyProviderRegistry:
    """
    Registry for clinical terminology providers. Enables hot-swappable upgrades,
    dynamic discovery, and version management of terminology adapters.
    """
    _instance: Optional['TerminologyProviderRegistry'] = None
    _providers: Dict[str, TerminologyProvider] = {}

    def __new__(cls) -> 'TerminologyProviderRegistry':
        if cls._instance is None:
            cls._instance = super(TerminologyProviderRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register_provider(cls, name: str, provider: TerminologyProvider) -> None:
        """
        Registers (or updates/overwrites) a terminology provider.
        """
        cls._providers[name.lower()] = provider

    @classmethod
    def get_provider(cls, name: str) -> TerminologyProvider:
        """
        Retrieves a registered provider by name.
        Raises ValueError if the provider is not found.
        """
        provider_key = name.lower()
        if provider_key not in cls._providers:
            raise ValueError(f"Terminology provider '{name}' is not registered.")
        return cls._providers[provider_key]

    @classmethod
    def deregister_provider(cls, name: str) -> None:
        """
        Removes a provider from the registry.
        """
        cls._providers.pop(name.lower(), None)

    @classmethod
    def clear(cls) -> None:
        """
        Clears all registered providers.
        """
        cls._providers.clear()

    @classmethod
    def list_providers(cls) -> Dict[str, str]:
        """
        Lists all registered providers and their active versions.
        """
        return {name: provider.get_version() for name, provider in cls._providers.items()}
