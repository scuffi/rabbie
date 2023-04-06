from rabbie import consumer

from loguru import logger as log

# consumer = Consumer(
#     host="queue_service",
#     port=5672,
#     username="user",
#     password="password",
#     default_decoder=JSONDecoder(),
# )


@consumer.listen(queue="test", workers=1)
def example_callback():
    log.debug("hit this with no params")


@consumer.listen(queue="test2", workers=2)
def example2(body):
    log.debug(body)


if __name__ == "__main__":
    log.success("Starting consumers...")
    consumer.start(reload=True)