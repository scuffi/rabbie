from functools import wraps
from typing import Optional, List, Union, TYPE_CHECKING
import time

import pika

from .microconsumer import MicroConsumer
from .consumer_config import ConsumerConfig
from .listener import Listener

from ..supervisor import Supervisor

from ..decoder import JSONDecoder
from ..logger import logger as log

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
        *,
        # All parameters below must be passed in as KW args
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
            log.warning(f"Registering {function.__name__} - {id(function)}")
            # log.debug(f"{function.__module__}{function.__class__}{function.__name__}")
            # TODO: Check if the function is already a listener, if so, we don't want to add a new one, we want to override the existing one
            # How do we do that if the function hashes aren't the same?
            
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
                # TODO: Check to see if when we call with arguments we can filter them out here -> if so, filter out based on type
                return function(*args, **kwargs)

            return listener

        return decorator
    
    def add_consumer(self, consumer: Union["Consumer", MicroConsumer]):
        if isinstance(consumer, MicroConsumer):
            self.listeners.extend(consumer._build_listeners(self.connection_parameters))
            return
        
        if isinstance(consumer, Consumer):
            self.listeners.extend(consumer.listeners)
            return

    def start(self, reload: bool = False, halt: bool = True):
        """
        Start listening for messages across all the created listeners

        Args:
          halt (bool): bool = True. Should calling this function halt the main thread?
        """
        log.info("Starting Service...")

        if reload:
            supervisor = Supervisor(
                "./",
                start_function=self._start_listeners,
                stop_function=self._stop_listeners,
            )

            supervisor.listen()
        else:
            self._start_listeners()

        self._halt(halt)

    def _start_listeners(self):
        log.info(f"Starting {len(self.listeners)} listeners")
        for listener in self.listeners:
            listener.start()

    def _stop_listeners(self):
        log.info(
            f"[red]Stopping {len(self.listeners)} listeners ({sum([len(listener.workers) for listener in self.listeners])} workers)"
        )
        for listener in self.listeners:
            listener.stop()

        # TODO: We don't want to clear this list, or else when we reload some files don't get reloaded and will get cleared here
        # self.listeners.clear()
        
    def _halt(self, halt: bool):
        try:
            while halt:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Exiting gracefully...")
            self._stop_listeners()
            exit()


consumer = Consumer(
    host="localhost",
    port=5672,
    username="user",
    password="password",
    default_decoder=JSONDecoder(),
)
