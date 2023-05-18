import os
import sys
import signal

from multiprocess import Process
from multiprocess.managers import DictProxy

from inspect import signature
import traceback

from typing import List, Any
import time

from .listener_details import ListenerDetails
from .listener_status import Status
from ...broker_types import Channel, Method, Properties
from ...logger import logger as log

import pika
from pika.exceptions import AMQPError
from pika.adapters.blocking_connection import BlockingChannel


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

    def is_listening(self) -> bool:
        return all([worker.is_alive() for worker in self.workers])

    def _change_status(self, registry: DictProxy, status: Status):
        """Change the status of the process we're inside of

        Args:
            registry (DictProxy): The shared registry
            status (Status): The new status
        """
        registry[os.getpid()] = status

    def _callback(
        self,
        channel: BlockingChannel,
        method: Method,
        properties: Properties,
        body: Any,
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
            # TODO: Wrap this channel in a custom channel, that provides utility functionality over acks, nacks, publishing, etc
            Channel: Channel(channel),
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
        self._run_safely(self.details, Channel(channel), **arguments)

    def _run_safely(self, details: ListenerDetails, channel: Channel, *args, **kwargs):
        """
        This function runs a callback function safely, whilst still printing any tracebacks.
        """
        try:
            # Call the function, and keep it's output incase it requires repushing to the channel
            output = details.callback(*args, **kwargs)

            # If there was data returned, we want to send this data back to the message broker
            if output is not None:
                # Use specified encoder and send back to same queue
                channel.publish(
                    body=output,
                    queue=self.details.return_queue or self.details.queue_name,
                    encoder=self.details.encoder,
                )
        except Exception:
            traceback.print_exc()

    def _start_worker(self, index: int, registry: DictProxy):
        # TODO: Change this function, it's ugly
        try:
            # Create a BlockingConnection into the queue
            connection = pika.BlockingConnection(self.connection_parameters)

            # Open a channel to receive messages through
            channel = connection.channel()

            channel.queue_declare(
                queue=self.details.queue_name,
                passive=self.details.queue_passive,
                durable=self.details.queue_passive,
                exclusive=self.details.queue_exclusive,
                auto_delete=self.details.queue_auto_delete,
            )

            channel.basic_qos(
                prefetch_count=self.details.qos_prefetch_count,
                prefetch_size=self.details.qos_prefetch_size,
                global_qos=self.details.global_qos,
            )

            channel.basic_consume(
                queue=self.details.queue_name,
                on_message_callback=self._callback,
                auto_ack=self.details.auto_ack,
            )

            # Allow for manipulation of channel before we start consuming incase we missed anything to do with configuration
            if self.details.configuration_callback:
                self.details.configuration_callback(channel)

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

            # Only log that we've 're'connected if the worker was previously down.
            if registry[os.getpid()] == Status.DISCONNECTED:
                log.info(f"[{os.getpid()}] [green]Reconnected to broker.")

            # We can assume now that we've connected successfully.
            self._change_status(registry, Status.CONNECTED)

            log.info(
                f"[{os.getpid()}] [green]Listening to [bold cyan]{self.details.queue_name}[/bold cyan]"
            )

            channel.start_consuming()

        except AMQPError:
            if self.details.restart:
                if registry[os.getpid()] != Status.DISCONNECTED:
                    log.error(
                        f"[{os.getpid()}] [red]Connection to broker failed. Worker will reconnect when possible."
                    )

                    # Set the status of this process to failed.
                    self._change_status(registry, Status.DISCONNECTED)

                time.sleep(2)
                self._start_worker(index, registry)

    def stop(self):
        """
        This function stops all workers by killing them.
        """
        for worker in self.workers:
            # Kill the thread
            os.kill(worker.pid, signal.SIGTERM)

            # Wait for the process to finish
            worker.join()

    def start(self, registry: DictProxy):
        """
        Execute each consumer in a new process in a PoolExecutor

        Args:
          workers (int): The amount of workers to start.
        """

        # If an amount of workers has been passed in, use that, else, use the maximum amount of CPUs.
        workers = self.details.workers or self._get_max_workers()

        self.workers.clear()

        for i in range(workers):
            p = Process(target=self._start_worker, args=(i, registry))
            p.start()

            # Add the process ID to the registry
            registry[p.pid] = Status.STARTING

            self.workers.append(p)
