from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class TerminologyProvider(ABC):
    """
    Abstract base interface for all Clinical Terminology Providers on the CyberCom Platform.
    Ensures a standardized set of terminology operations.
    """

    @abstractmethod
    def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Search for concepts matching a text query.
        """
        pass

    @abstractmethod
    def lookup(self, code: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieve full details (display name, properties, definition) of a specific code.
        """
        pass

    @abstractmethod
    def validate(self, code: str, **kwargs) -> bool:
        """
        Validate whether a code is syntactically and semantically correct in this system.
        """
        pass

    @abstractmethod
    def translate(self, code: str, target_system: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Translate a code from this terminology system to a target system.
        """
        pass

    @abstractmethod
    def expand(self, value_set: str, filter_str: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Expand a ValueSet (retrieve its constituent concepts, optionally filtered).
        """
        pass

    @abstractmethod
    def get_children(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve immediate child concepts in the hierarchy.
        """
        pass

    @abstractmethod
    def get_parents(self, code: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve immediate parent concepts in the hierarchy.
        """
        pass

    @abstractmethod
    def get_synonyms(self, code: str, **kwargs) -> List[str]:
        """
        Retrieve synonyms or alternative terms for a concept.
        """
        pass

    @abstractmethod
    def get_mappings(self, code: str, target_system: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Retrieve all registered cross-system mappings for a code.
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """
        Retrieve the active version of this terminology database/provider.
        """
        pass
