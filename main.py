from rabbie import consumer

from loguru import logger as log

import main_2


@consumer.listen(queue="test", workers=1)
def example_callback(body: dict):
    log.debug(body)
    raise Exception("nooo")


if __name__ == "__main__":
    log.success("Starting consumers...")
    consumer.add_consumer(main_2.consumer)
    consumer.start(reload=False)
