import multiprocessing as mp

import dill
import pika
from pika.exceptions import AMQPError
import sys
import time
import signal

from ...logger import logger as log

class Worker(mp.Process):
    def __init__(self,  callback, connection_parameters, queue_name, index: int):
        mp.Process.__init__(self)
        self.callback = callback
        self.connection_parameters = connection_parameters
        self.queue_name = queue_name
        self.index = index

    def run(self):
        self._start_worker()
            
    def _callback(self, channel, method, properties, body):
        log.info(f"Received new message on queue '{self.queue_name}'")
        # log.info(channel)
        # log.info(method)
        # log.info(properties)
        # Run the configured Job in a new Process, pass the arguments down
        # if self.decoder:
        #     body = self.decoder.decode(body)
            
        callback = dill.loads(self.callback)

        # TODO: Change this to work off of types rather than variable names
        callback_arguments = list(callback.__code__.co_varnames)
        all_arguments = {
            "channel": channel,
            "method": method,
            "properties": properties,
            "body": body,
        }

        arguments = {k: v for k, v in all_arguments.items() if k in callback_arguments}

        callback(**arguments)
            
    def _start_worker(self):
        try:
            # TODO: Unpickle (dill) the callback function, so it becomes a callable, then pass that callable into on_message_callback?
            # callback = dill.loads(callback)
            # Create a BlockingConnection into the queue
            connection = pika.BlockingConnection(self.connection_parameters)

            # Open a channel to receive messages through
            channel = connection.channel()
            
            channel.queue_declare(queue=self.queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=self.queue_name, on_message_callback=self._callback, auto_ack=True
            )
            
            # for method, properties, body in channel.consume(self.queue_name):
            #         self._callback(channel, method, properties, body)
            
            # Create a signal handler to close the connection when we receive a SIGINT
            def handle_sigterm(sig, frame):
                log.warning(f"Received signal {sig}, closing connection...")
                # self.stop_event.set()
                channel.close()
                connection.close()
                log.warning("Connection closed")
                sys.exit(0)
                
            # Register the signal handler for SIGTERM
            signal.signal(signal.SIGTERM, handle_sigterm)
            
            channel.start_consuming()
            
            # while not stop_event.is_set():
            #     channel.connection.process_data_events()
                
            log.error("Closing connection...")
            channel.close()
            connection.close()
        except AMQPError as e:
            log.error("Connection failed, retrying in 2s...")
            time.sleep(2)
            # cls._start_worker(index)
            self._start_worker()