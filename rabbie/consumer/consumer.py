from functools import wraps
import logging
from typing import Optional, List, Union, Callable, TYPE_CHECKING
import time
from multiprocess import Manager

import pika
from pika.connection import Parameters

from .microconsumer import MicroConsumer
from ..connection import Details
from .listener import Listener, ListenerDetails, Status

from ..supervisor import Supervisor

from ..decoder import AutoDecoder
from ..encoder import AutoEncoder
from ..logger import logger as log

if TYPE_CHECKING:
    from ..decoder import Decoder
    from ..encoder import Encoder


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

        self.suppress_internal_logs()

    def listen(
        self,
        queue: str = Details.QUEUE_NAME,
        workers: int = 1,
        decoder: Optional["Decoder"] = None,
        restart: bool = True,
        return_queue: Optional[str] = None,
        encoder: Optional["Encoder"] = AutoEncoder(),
        auto_acknowledge: bool = True,
        qos_prefetch_size: int = 0,
        qos_prefetch_count: int = 0,
        global_qos: bool = False,
        passive_queue: bool = False,
        durable_queue: bool = False,
        exclusive_queue: bool = False,
        auto_delete_queue: bool = False,
        # Must accept a single argument 'channel', to allow for any further manipulation that is not supported here
        configuration_callback: Callable = None,
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
                    workers=workers,
                    decoder=decoder or self.default_decoder,
                    restart=restart,
                    auto_ack=auto_acknowledge,
                    queue_name=queue,
                    queue_durable=durable_queue,
                    queue_exclusive=exclusive_queue,
                    queue_passive=passive_queue,
                    queue_auto_delete=auto_delete_queue,
                    qos_prefetch_size=qos_prefetch_size,
                    qos_prefetch_count=qos_prefetch_count,
                    global_qos=global_qos,
                    configuration_callback=configuration_callback,
                    return_queue=return_queue,
                    encoder=encoder,
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

    def suppress_internal_logs(self, suppress: bool = True):
        """Suppress internal Pika logs.

        Helpful to toggle if something is going wrong.

        Args:
            suppress (bool, optional): If internal logs should be suppressed. Defaults to True.
        """
        # Revisit this; not sure why logger.disabled = True isn't working here?
        if suppress:
            logging.getLogger("pika").setLevel(logging.CRITICAL + 1)
        else:
            logging.getLogger("pika").setLevel(0)

    def start(self, reload: bool = False, halt: bool = True):
        """
        Start listening for messages across all the created listeners

        Args:
          halt (bool): bool = True. Should calling this function halt the main thread?
        """
        log.info("Starting Service...")

        # Temporarily disabling reloading
        reload = False

        self._create_shared_registry()

        if reload:
            supervisor = Supervisor(
                "./",
                start_function=self._start_listeners,
                stop_function=self._stop_listeners,
            )

            supervisor.listen()
        else:
            self._start_listeners()

        self._await_startup(self.shared_registry)

        workers_amount = len(self.shared_registry.keys())

        log.info(
            f"[green]Started {len(self.listeners)} listeners ({workers_amount} {'worker' if workers_amount == 1 else 'workers'})"
        )

        self._halt(halt)

    def _create_shared_registry(self):
        """Create a shared registry for all workers to interact with.

        Note: This must be protected by __name__ == "__main__" check, ensure consumer.start() is protected
        or else an error will arise.
        """
        # Create a manager instance so all workers can have a central registry
        manager = Manager()
        self.shared_registry = manager.dict()

    def _start_listeners(self):
        """Start all the listeners & their workers"""
        workers_amount = sum(listener.details.workers for listener in self.listeners)
        log.info(
            f"Starting {len(self.listeners)} listeners ({workers_amount} {'worker' if workers_amount == 1 else 'workers'})"
        )
        for listener in self.listeners:
            listener.start(self.shared_registry)

    def _stop_listeners(self):
        """Stop all the currently running listeners & workers"""
        workers_amount = sum(len(listener.workers) for listener in self.listeners)
        log.info(
            f"[red]Stopping {len(self.listeners)} listeners ({workers_amount} {'worker' if workers_amount == 1 else 'workers'})"
        )
        for listener in self.listeners:
            listener.stop()

    def _await_startup(self, registry):
        """Wait for all known listeners to be started, then continue."""
        while not all(
            enum_value == Status.CONNECTED for enum_value in registry.values()
        ):
            ...

    def _halt(self, halt: bool):
        """Halt the code for good

        Args:
            halt (bool): Halt or not
        """
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
