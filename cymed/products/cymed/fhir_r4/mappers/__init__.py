"""Register all built-in mappers on module import."""
from .patient import PatientMapper
from .observation import ObservationMapper
from .coverage import CoverageMapper
from .claim import ClaimMapper

from ..registry import register

register(PatientMapper())
register(ObservationMapper())
register(CoverageMapper())
register(ClaimMapper())
