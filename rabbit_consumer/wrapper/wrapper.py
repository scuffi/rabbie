from functools import wraps

from ..consumer import Consumer

def consume(
    queue: str,
    workers: int = 1,
):
    def decorator(function):
        @wraps(function)
        def consumer(*args, **kwargs):
            # If no credentials are passed in, use the consumer_config preconfigured variables
            # Instantiate a consumer object
            con = Consumer(callback=function, queue_name=queue)
            # Initialise the consumer with the callback as the passed function
            con.consume(workers=workers)

        return consumer

    return decorator
