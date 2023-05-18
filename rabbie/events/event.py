from typing import Callable
from collections import defaultdict
from functools import wraps


class Event:
    def __init__(self) -> None:
        self._registry = defaultdict(list)

    def register(self, event_id: str):
        """Register a function with an event_id

        Args:
            event_id (str): The event ID this function is tied to

        """

        def decorator(func):
            # Actually register the event
            self._add_event(event_id, func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def _add_event(self, event: str, callback: Callable):
        """Register a new callback to be called when event is triggered

        Args:
            event (str): The event id
            callback (Callable): The callback function
        """
        self._registry[event].append(callback)

    def _call(self, event: str, *args, **kwargs):
        """Call all the registered callbacks for an event sequentially

        Args:
            event (str): The event ID to trigger
        """
        for callback in self._registry[event]:
            callback(*args, **kwargs)
