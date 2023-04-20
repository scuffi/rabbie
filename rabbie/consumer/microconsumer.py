from typing import Optional, List

from functools import wraps

from pika.connection import ConnectionParameters

from .listener import Listener, ListenerDetails
from .consumer_config import ConsumerConfig
from ..decoder import Decoder

from ..logger import logger as log


class MicroConsumer:
    def __init__(
        self,
        default_decoder: Optional["Decoder"] = None,
    ) -> None:
        self.default_decoder = default_decoder

        self._listener_details: List[ListenerDetails] = []

    def listen(
        self,
        queue: str = ConsumerConfig.QUEUE_NAME,
        workers: int = 1,
        decoder: Optional["Decoder"] = None,
    ):
        def decorator(function):
            ls = ListenerDetails(
                callback=function,
                queue_name=queue,
                workers=workers,
                decoder=decoder or self.default_decoder,
            )

            # Add the listener details to ListenerDetails list
            self._listener_details.append(ls)

            @wraps(function)
            def listener(*args, **kwargs):
                # TODO: Check to see if when we call with arguments we can filter them out here -> if so, filter out based on type
                return function(*args, **kwargs)

            return listener

        return decorator

    def _build_listeners(
        self, connection_details: ConnectionParameters
    ) -> List[Listener]:
        return [
            Listener(connection_parameters=connection_details, details=listener_details)
            for listener_details in self._listener_details
        ]
