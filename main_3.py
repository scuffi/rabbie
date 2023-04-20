from rabbie import consumer

from loguru import logger as log

@consumer.listen(queue="test2", workers=1)
def example3(channel, body):
    log.info(body)