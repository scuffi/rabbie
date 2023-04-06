from functools import wraps
from typing import Optional, List, TYPE_CHECKING
import time
from multiprocessing import Manager
from multiprocessing.managers import ListProxy

from loguru import logger as log

import pika

from .consumer_config import ConsumerConfig
from .listener import Listener

from ..supervisor import Supervisor

from ..decoder import JSONDecoder

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

        self.manager = Manager()
        # self.listeners: ListProxy = self.manager.list()
            
        self.listeners: List[Listener] = []
        self.running: List[Listener] = []

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
            
            log.info("Registered new listener")
            log.info(self.listeners)
            log.info(function)
            log.error(self)

            @wraps(function)
            def listener(*args, **kwargs):
                # TODO: Check to see if when we call with arguments we can filter them out here -> if so, filter out based on type
                return function(*args, **kwargs)

            return listener

        return decorator

    def start(self, reload: bool = False, halt: bool = True):
        """
        Start listening for messages across all the created listeners

        Args:
          halt (bool): bool = True. Should calling this function halt the main thread?
        """
        # from watchdog.observers.polling import PollingObserverVFS
        # from watchdog.events import FileSystemEventHandler


        # class Event(FileSystemEventHandler):
        #     def on_any_event(self, event):
        #         print(f"Reloading {event.src_path}")

        # event_handler = Event()
        # # observer = Observer()
        # observer = PollingObserverVFS(
        #     stat=os.stat, listdir=os.scandir, polling_interval=0.1
        # )

        # observer.schedule(event_handler, "./", recursive=True)
        # # observer.start()
        
        log.success("Starting Service...")

        if reload:
            # TODO: Pass the consumer in here, the consumer must be part of a Manager.
            # TODO: This means that each process created, will refer to the same function, as this would create a new instance per process
            
            # TODO: This may mean that a Consumer must have ProcessListeners class, which is a manager that stores all of the listeners,
            # TODO: this way it would allow for multiple places, including this main consumer, to refer to the same listener list.
            supervisor = Supervisor("./", start_function=self._start_listeners, stop_function=self._stop_listeners)
            
            supervisor.listen()
        else:
            self._start_listeners()

        self._halt(halt)
        
    def _start_listeners(self):
        log.info(f"Starting {len(self.listeners)} listeners")
        log.error(self)
        for listener in self.listeners.copy():
            log.debug("Starting new listener")
            listener.start()
            
            self.listeners.remove(listener)
            self.running.append(listener)
            
        
    def _stop_listeners(self):
        for listener in self.running:
            listener.stop()
            
        self.running.clear()

    def _halt(self, halt: bool):
        while halt:
            time.sleep(1)


consumer = Consumer(
    host="queue_service",
    port=5672,
    username="user",
    password="password",
    default_decoder=JSONDecoder(),
)