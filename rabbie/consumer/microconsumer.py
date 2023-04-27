from typing import Optional, List

from functools import wraps

from pika.connection import ConnectionParameters

from .listener import Listener, ListenerDetails
from ..connection import Details
from ..decoder import Decoder


class MicroConsumer:
    def __init__(
        self,
        default_decoder: Optional["Decoder"] = None,
    ) -> None:
        """MicroConsumer object holds listeners for a Consumer to pick up

        Args:
            default_decoder (Optional[Decoder], optional): The default decoder for decoding messages. Defaults to None.
        """
        self.default_decoder = default_decoder

        self._listener_details: List[ListenerDetails] = []

    def listen(
        self,
        queue: str = Details.QUEUE_NAME,
        workers: int = 1,
        decoder: Optional["Decoder"] = None,
        restart: bool = True,
    ):
        """Listen for messages on a specific queue

        Args:
            queue (str, optional): The queue to listen to. Defaults to Details.QUEUE_NAME.
            workers (int, optional): The amount of workers to listen simultaneously. Defaults to 1.
            decoder (Optional[Decoder], optional): The decoder for this specific listener. Defaults to None.
            restart (bool, optional): Should we attempt to restart this listener if connection fails?. Defaults to True.
        """

        def decorator(function):
            ls = ListenerDetails(
                callback=function,
                queue_name=queue,
                workers=workers,
                decoder=decoder or self.default_decoder,
                restart=restart,
            )

            # Add the listener details to ListenerDetails list
            self._listener_details.append(ls)

            @wraps(function)
            def listener(*args, **kwargs):
                return function(*args, **kwargs)

            return listener

        return decorator

    def _build_listeners(
        self, connection_details: ConnectionParameters
    ) -> List[Listener]:
        """
        This function builds a list of listeners using the provided connection details and listener details.

        Args:
          connection_details (ConnectionParameters): The `connection_details` parameter is an instance of
        the `ConnectionParameters` class, which contains details about the connection to be established,
        such as the host, port, username, password, and virtual host.

        Returns:
          A list of Listener objects is being returned. The Listener objects are created using the
        connection_details parameter and iterating over the _listener_details attribute of the object to get
        the details for each listener.
        """
        return [
            Listener(connection_parameters=connection_details, details=listener_details)
            for listener_details in self._listener_details
        ]
