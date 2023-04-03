from functools import wraps
from typing import Optional, List, TYPE_CHECKING
import time
import os

from loguru import logger as log

import pika

from .consumer_config import ConsumerConfig
from .listener import Listener
from ..supervisor import Supervisor

if TYPE_CHECKING:
    from ..decoder import Decoder


class Consumer:
    """
    Listener holds all of the workers (processes) that will consume from the queue.
    When the consume function is called it will create n number of processes where n is the number of processors on the machine.
    Each will operate independently and consume from the queue.


    The whole point of this is to allow the consumer to scale horizontally.
    """

    def __init__(
        self,
        # All parameters below must be passed in as KW args
        *,
        host: Optional[str] = ConsumerConfig.HOST,
        port: Optional[str] = ConsumerConfig.PORT,
        username: Optional[str] = ConsumerConfig.USERNAME,
        password: Optional[str] = ConsumerConfig.PASSWORD,
        default_decoder: Optional["Decoder"] = None,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password

        self.default_decoder = default_decoder

        credentials = pika.PlainCredentials(self._username, self._password)
        # Create the parameters for connection to the Queue
        self.connection_parameters = pika.ConnectionParameters(
            port=self._port,
            host=self._host,
            credentials=credentials,
        )

        self.listeners: List[Listener] = []

    def listen(
        self,
        queue: str = ConsumerConfig.QUEUE_NAME,
        workers: int = 1,
        decoder: Optional["Decoder"] = None,
    ):
        def decorator(function):
            # If no credentials are passed in, use the consumer_config preconfigured variables
            # Instantiate a consumer object
            ls = Listener(
                callback=function,
                queue_name=queue,
                connection_parameters=self.connection_parameters,
                workers=workers,
                decoder=decoder or self.default_decoder,
            )

            # Add the configured listener to the list of listeners to be called later
            self.listeners.append(ls)

            @wraps(function)
            def listener(*args, **kwargs):
                return function(*args, **kwargs)

            return listener

        return decorator

    def start(self, reload: bool = False, halt: bool = True):
        """
        Start listening for messages across all the created listeners

        Args:
          halt (bool): bool = True. Should calling this function halt the main thread?
        """
        for listener in self.listeners:
            log.debug("Starting new listener")
            listener.start()

        if reload:
            supervisor = Supervisor(path="./")
            
            supervisor.listen()
            supervisor.start(...) # TODO: Pass callable i.e. main loop here
            
        self._halt(halt)

    def _halt(self, halt: bool):
        while halt:
            time.sleep(1)