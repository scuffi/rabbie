from multiprocessing import Process, cpu_count
import concurrent.futures
from typing import Callable, Optional

import pika

from loguru import logger as log

from .consumer_config import Queue


class Consumer:
    """
    Listener holds all of the workers (processes) that will consume from the queue.
    When the consume function is called it will create n number of processes where n is the number of processors on the machine.
    Each will operate independently and consume from the queue.


    The whole point of this is to allow the consumer to scale horizontally.
    """

    def __init__(
        self,
        job: Callable,
        # All parameters below must be passed in as KW args
        *,
        queue_name: Optional[str] = None,
        host: Optional[str],
        port: Optional[str],
        username: Optional[str],
        password: Optional[str],
    ):
        self.job = job
        self.queue_name = queue_name or Queue.QUEUE_NAME
        self._host = host or Queue.HOST
        self._port = port or Queue.PORT
        self._username = username or Queue.USERNAME
        self._password = password or Queue.PASSWORD

    def _get_max_workers(self, _default: int = 4):
        """
        If the number of workers can be determined, return that number, otherwise return the default
        value

        Args:
          _default (int): int = 4. Defaults to 4

        Returns:
          The number of workers on the system.
        """
        try:
            return cpu_count()
        except NotImplementedError:
            return _default

    def _callback(self, channel, method, properties, body):
        log.info(f"Received new message on queue '{self.queue_name}'")
        log.info(channel)
        log.info(method)
        log.info(properties)

        if self.job is None:
            log.critical("Received a new message, but no process job is defined!")
            return

        # Run the configured Job in a new Process, pass the arguments down
        # TODO: If we are always pushing JSON data, this should deserialize into an object here
        p = Process(target=self.job, args=(body))
        p.start()
        p.join()

    def _start_worker(self, index: int):
        try:
            credentials = pika.PlainCredentials("user", "password")
            # Create the parameters for connection to the Queue
            parameters = pika.ConnectionParameters(
                port=5672,
                host="queue_service",
                credentials=credentials,
            )

            # Create a BlockingConnection into the queue
            connection = pika.BlockingConnection(parameters)

            # Open a channel to receive messages through
            channel = connection.channel()

            channel.queue_declare(queue=self.queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)

            # TODO: Add the worker that consumed the data in here
            channel.basic_consume(
                queue=self.queue_name, on_message_callback=self._callback
            )

            log.success(
                f" [*] Waiting for messages from worker [{index + 1}]. To exit press CTRL+C"
            )

            channel.start_consuming()
        except Exception as e:
            log.error(e)

    def consume(self, workers: int = None):
        """
        Execute each consumer in a new process in a PoolExecutor

        Args:
          workers (int): The amount of workers to start.
        """
        # If an amount of workers has been passed in, use that, else, use the maximum amount of CPUs.
        workers = workers or self._get_max_workers()

        # Execute each worker in a new process in a PoolExecutor
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for i in range(workers):
                executor.submit(self._start_worker, i)
