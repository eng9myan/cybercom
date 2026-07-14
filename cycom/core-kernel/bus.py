# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List

logger = logging.getLogger(__name__)

# Global registry of event handlers
_subscribers: Dict[str, List[Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]]] = defaultdict(list)


class EventBus:
    """Asynchronous CQRS Global Event Bus for decoupled inter-module messaging."""

    @staticmethod
    def subscribe(event_name: str, handler: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]):
        """Registers an asynchronous callback handler for a specific event type."""
        _subscribers[event_name].append(handler)
        logger.info(f"Handler '{handler.__name__}' successfully subscribed to event: {event_name}")

    @staticmethod
    async def publish(event_name: str, payload: Dict[str, Any]):
        """Dispatches an event payload asynchronously to all active subscribers."""
        logger.info(f"Publishing event '{event_name}' with payload: {payload}")
        handlers = _subscribers.get(event_name, [])
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as e:
                logger.error(f"Event handler execution failure on event '{event_name}': {str(e)}")
