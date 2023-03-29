from rabbit_consumer import consume

@consume(queue="test", workers=1)
def example_callback():
    ...
