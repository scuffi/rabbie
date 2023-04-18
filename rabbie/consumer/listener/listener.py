import os
import sys
import signal
from multiprocess import Process, Manager

from typing import Callable, Optional, List
import time

from ...decoder import Decoder
from ...logger import logger as log

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
        self.workers_amount = workers
        self.decoder: Optional[Decoder] = decoder
        
        self.workers: List[Process] = []

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

        self.callback(**arguments)

    def _start_worker(self, index: int):
        try:
            # Create a BlockingConnection into the queue
            connection = pika.BlockingConnection(self.connection_parameters)

            # Open a channel to receive messages through
            channel = connection.channel()
            
            channel.queue_declare(queue=self.queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=self.queue_name, on_message_callback=self._callback, auto_ack=True
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
        except AMQPError as e:
            log.error("Connection failed, retrying in 2s...")
            time.sleep(2)
            self._start_worker(index)
            
    def stop(self):
        """
        This function stops all workers by killing them.
        """
        for worker in self.workers:
            # log.debug("Killing worker")
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
        workers = self.workers_amount or self._get_max_workers()
        
        for i in range(workers):
            p = Process(target=self._start_worker, args=(i,))
            p.start()
            self.workers.append(p)
            
        log.info(f"[green]Started listening to [bold cyan]{self.queue_name}[/bold cyan] with {workers} {'workers' if workers > 1 else 'worker'}")
