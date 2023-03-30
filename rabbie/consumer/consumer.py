from functools import wraps
from typing import Optional, List, TYPE_CHECKING
import time
import os

from loguru import logger as log

import pika

from .consumer_config import ConsumerConfig
from .listener import Listener

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
        from watchdog.observers import Observer
        from watchdog.observers.polling import PollingObserver, PollingObserverVFS
        from watchdog.events import LoggingEventHandler, FileSystemEventHandler
        import importlib
        import sys
        from pydoc import importfile

        for listener in self.listeners:
            log.debug("Starting new listener")
            listener.start()

        class Event(FileSystemEventHandler):
            def on_any_event(self, event):
                print(f"Reloading {event.src_path}")
                print(event.is_directory)

                if event.is_directory:
                    return

                path: str = event.src_path

                if path.endswith(".pyc"):
                    return

                # file_name = path.split("/")[-1]
                # mname = os.path.splitext(file_name)[0]
                # self.import2(event.src_path)
                # self.import_file(mname, file_name)
                module = importfile(path)
                log.warning(f"Module: {module}")
                importlib.reload(module)
                return print(event)

            def import_file(self, module_name, path):
                from importlib import util

                log.warning(f"Module Name: {module_name}")
                log.warning(f"Path: {path}")

                spec = util.spec_from_file_location(module_name, path)

                log.warning(f"Spec: {spec}")
                mod = util.module_from_spec(spec)

                log.warning(f"Module: {mod}")

                spec.loader.exec_module(mod)
                return mod

            def import2(self, path: str):
                name = path.split("/")[-1]
                sys.path.append(os.path.dirname(name))
                mname = os.path.splitext(name)[0]
                print(f"reimporting {mname}")
                imported = importlib.import_module(mname)
                sys.path.pop()

        event_handler = Event()
        # observer = Observer()
        observer = PollingObserverVFS(
            stat=os.stat, listdir=os.scandir, polling_interval=0.1
        )

        observer.schedule(event_handler, "./", recursive=True)
        observer.start()

        if reload:
            # TODO: Either we get this jurigged working or some reload
            # TODO: Or we operate the entire code in a Thread, and when a change is detected, the thread should stop & start with the new code

            # Only import if we are using reload to ignore this package in production
            import jurigged

            log.info("Watching for changes'")
            # watcher = jurigged.watch("/", poll=0.1, autostart=False)
            # watcher.observer.schedule(Event(), "./", recursive=True)
            # watcher.start()

        self._halt(halt)

    def _halt(self, halt: bool):
        while halt:
            time.sleep(1)
