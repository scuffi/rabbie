from functools import wraps


def consume(
    queue: str,
    workers: int = 1,
):
    def decorator(function):
        @wraps(function)
        def consumer(*args, **kwargs):
            # If no credentials are passed in, use the consumer_config preconfigured variables
            # Instantiate a consumer object
            # Initialise the consumer with the callback as the passed function
            ...

        return consumer

    return decorator


@consume(queue="my_queue", workers=4)
def example():
    ...
