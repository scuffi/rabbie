from functools import wraps
from typing import Optional, List, Union, TYPE_CHECKING
import time

import pika
from pika.connection import Parameters

from .microconsumer import MicroConsumer
from ..connection import Details
from .listener import Listener, ListenerDetails

from ..supervisor import Supervisor

from ..decoder import AutoDecoder
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
        host: Optional[str] = Details.HOST,
        port: Optional[str] = Details.PORT,
        username: Optional[str] = Details.USERNAME,
        password: Optional[str] = Details.PASSWORD,
        default_decoder: Optional["Decoder"] = AutoDecoder(),
        connection_parameters: Optional[Parameters] = None,
        **kwargs,
    ):
        """Instantiate a new Consumer object with the given connection details.

        Args:
            host (Optional[str], optional): The host of the broker. Defaults to Details.HOST.
            port (Optional[str], optional): The port of the broker. Defaults to Details.PORT.
            username (Optional[str], optional): The authenticated username. Defaults to Details.USERNAME.
            password (Optional[str], optional): The authenticated password. Defaults to Details.PASSWORD.
            default_decoder (Optional[Decoder], optional): The default decoder for decoding messages. Defaults to AutoDecoder
            connection_parameters (Optional[ConnectionParameters]): Override the default connection parameters, helpful if using URLParams

            Any other arguments are passed directly in to the connection parameters.
        """
        self._host = host
        self._port = port
        self._username = username
        self._password = password

        self.default_decoder = default_decoder

        credentials = pika.PlainCredentials(self._username, self._password)

        # Create the parameters for connection to the Queue
        self.connection_parameters = connection_parameters or pika.ConnectionParameters(
            port=self._port,
            host=self._host,
            credentials=credentials,
            **kwargs,
        )

        self.listeners: List[Listener] = []

    def listen(
        self,
        queue: str = Details.QUEUE_NAME,
        workers: int = 1,
        decoder: Optional["Decoder"] = None,
        restart: bool = True,
        auto_acknowledge: bool = True,
    ):
        """Listen for messages on a specific queue

        Args:
            queue (str, optional): The queue to listen to. Defaults to Details.QUEUE_NAME.
            workers (int, optional): The amount of workers to listen simultaneously. Defaults to 1.
            decoder (Optional[Decoder], optional): The decoder for this specific listener. Defaults to None.
            restart (bool, optional): Should we attempt to restart this listener if connection fails?. Defaults to True.
        """

        def decorator(function):
            ls = Listener(
                connection_parameters=self.connection_parameters,
                details=ListenerDetails(
                    callback=function,
                    queue_name=queue,
                    workers=workers,
                    decoder=decoder or self.default_decoder,
                    restart=restart,
                    auto_ack=auto_acknowledge,
                ),
            )

            # Add the configured listener to the list of listeners to be called later
            self.listeners.append(ls)

            @wraps(function)
            def listener(*args, **kwargs):
                return function(*args, **kwargs)

            return listener

        return decorator

    def add_consumer(self, consumer: Union["Consumer", MicroConsumer]):
        """Merge a consumer into this consumer, adds all registered listeners
        to this consumer

        Args:
            consumer (Union[Consumer, MicroConsumer]): The Consumer/MicoConsumer to merge
        """
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

        # Temporarily disabling reloading
        reload = False

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

        # ? We don't want to clear this list, or else when we reload some files don't get reloaded and will get cleared here
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
    default_decoder=AutoDecoder(),
)
