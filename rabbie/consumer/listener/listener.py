from multiprocessing import Process
from typing import Callable, Optional
import sys
import time

from loguru import logger as log

from ...decoder import Decoder

import pika
from pika.exceptions import AMQPError


class Listener:
    def __init__(
        self,
        queue_name: str,
        callback: Callable,
        connection_parameters: pika.ConnectionParameters,
        workers: int = None,
        decoder: Decoder = None,
    ) -> None:
        self.queue_name = queue_name
        self.callback = callback
        self.connection_parameters = connection_parameters
        self.workers = workers
        self.decoder: Optional[Decoder] = decoder

    def _callback(self, channel, method, properties, body):
        log.info(f"Received new message on queue '{self.queue_name}'")
        # log.info(channel)
        # log.info(method)
        # log.info(properties)
        # Run the configured Job in a new Process, pass the arguments down
        if self.decoder:
            body = self.decoder.decode(body)

        # TODO: Change this to work off of types rather than variable names
        callback_arguments = list(self.callback.__code__.co_varnames)
        all_arguments = {
            "channel": channel,
            "method": method,
            "properties": properties,
            "body": body,
        }

        arguments = {k: v for k, v in all_arguments.items() if k in callback_arguments}

        # TODO: This should be pooled
        p = Process(target=self.callback, kwargs=arguments)
        p.start()
        p.join()

    def _start_worker(self, index: int):
        log.debug("Opening new connection")
        try:
            # Create a BlockingConnection into the queue
            connection = pika.BlockingConnection(self.connection_parameters)

            # Open a channel to receive messages through
            channel = connection.channel()

            channel.queue_declare(queue=self.queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=self.queue_name, on_message_callback=self._callback
            )

            log.success(
                f" [*] Waiting for messages from worker [{index + 1}]. To exit press CTRL+C"
            )

            channel.start_consuming()
        except AMQPError as e:
            log.error("Connection failed, retrying in 2s...")
            time.sleep(2)
            self._start_worker(index)

    def start(self):
        """
        Execute each consumer in a new process in a PoolExecutor

        Args:
          workers (int): The amount of workers to start.
        """
        # If an amount of workers has been passed in, use that, else, use the maximum amount of CPUs.
        workers = self.workers or self._get_max_workers()

        for i in range(workers):
            p = Process(target=self._start_worker, args=(i,))
            p.start()
