"""Gateway registry — pick by code."""
from .base import BaseGateway
from .hyperpay import HyperPayGateway
from .stripe_gw import StripeGateway


_registry: dict[str, BaseGateway] = {}


def register(gw: BaseGateway):
    _registry[gw.name] = gw


def get_gateway(name: str) -> BaseGateway:
    if name not in _registry:
        raise ValueError(f"Unknown gateway '{name}'. Registered: {list(_registry)}")
    return _registry[name]


# Register default set
register(HyperPayGateway())
register(StripeGateway())
