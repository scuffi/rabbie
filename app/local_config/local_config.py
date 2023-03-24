from typing import Callable, Optional


class Queue:
    CONNECTION_URL: str = "amqp://queue_service"

    QUEUE_NAME: str = "topic"

    JOB: Optional[Callable] = None
