import os
import sys
import signal
from multiprocess import Process
from inspect import signature
import traceback

from typing import Callable, Optional, List, Any, get_origin
import time

from .listener_details import ListenerDetails
from ...broker_types import Channel, Method, Properties
from ...logger import logger as log

import pika
from pika.exceptions import AMQPError


class Listener:
    def __init__(
        self,
        details: ListenerDetails,
        connection_parameters: pika.ConnectionParameters,
    ) -> None:
        # ListenerDetails store all the configuration details for a listener
        self.details = details

        self.connection_parameters = connection_parameters
        self.workers: List[Process] = []

    def _callback(
        self, channel: Channel, method: Method, properties: Properties, body: Any
    ):
        """
        This function is called when a message is received on the queue.
        """

        log.info(
            f"[{os.getpid()}] Received new message on queue '{self.details.queue_name}'"
        )

        # Run the configured Job in a new Process, pass the arguments down
        if self.details.decoder:
            body = self.details.decoder.decode(body)

        # Get the signature of the function
        sig = signature(self.details.callback)

        all_arguments = {
            Channel: channel,
            Method: method,
            Properties: properties,
        }

        # Match variables to their types, and pass them in. Default to body
        arguments = {
            arg: all_arguments[sig.parameters[arg].annotation]
            if sig.parameters[arg].annotation in all_arguments
            else body
            for arg in sig.parameters.keys()
        }

        # Run the callback function safely, so if it errors, the listener won't stop
        self._run_safely(self.details.callback, **arguments)

    def _run_safely(self, callback: Callable, *args, **kwargs):
        """
        This function runs a callback function safely, whilst still printing any tracebacks.
        """
        try:
            callback(*args, **kwargs)
        except Exception:
            traceback.print_exc()

    def _start_worker(self, index: int):
        try:
            # Create a BlockingConnection into the queue
            connection = pika.BlockingConnection(self.connection_parameters)

            # Open a channel to receive messages through
            channel = connection.channel()

            channel.queue_declare(queue=self.details.queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=self.details.queue_name,
                on_message_callback=self._callback,
                auto_ack=True,
            )

            # TODO: Use this instead for more control of what variables to pass?
            # for method, properties, body in channel.consume(self.queue_name):
            #         self._callback(channel, method, properties, body)

            # Create a signal handler to close the connection when we receive a SIGINT
            def handle_sigterm(sig, frame):
                log.debug("Gracefully closing connection...")
                channel.close()
                connection.close()
                sys.exit(0)

            # Register the signal handler for SIGTERM
            signal.signal(signal.SIGTERM, handle_sigterm)

            channel.start_consuming()

            # TODO: Change how this entire thing works, it's not very elegant.
        except AMQPError as e:
            log.error("Connection failed, retrying in 2s...")
            time.sleep(2)
            self._start_worker(index)

    def stop(self):
        """
        This function stops all workers by killing them.
        """
        for worker in self.workers:
            # Kill the thread
            os.kill(worker.pid, signal.SIGTERM)

            # Wait for the process to finish
            worker.join()

    def start(self):
        """
        Execute each consumer in a new process in a PoolExecutor

        Args:
          workers (int): The amount of workers to start.
        """

        # If an amount of workers has been passed in, use that, else, use the maximum amount of CPUs.
        workers = self.details.workers or self._get_max_workers()

        self.workers.clear()

        for i in range(workers):
            p = Process(target=self._start_worker, args=(i,))
            p.start()
            self.workers.append(p)

        log.info(
            f"[green]Started listening to [bold cyan]{self.details.queue_name}[/bold cyan] with {workers} {'workers' if workers > 1 else 'worker'}"
        )
