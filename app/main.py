from loguru import logger as log

from local_config import Queue
from consumer import Consumer


if __name__ == "__main__":
    log.success("Connecting workers to queue...")

    # Instantiate our listener with the correct details
    consume = Consumer(
        connection_string=Queue.CONNECTION_URL,
        queue_name=Queue.QUEUE_NAME,
        job=Queue.JOB,
    )

    # Start listening for messages
    consume.consume(4)
