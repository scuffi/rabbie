from rabbie import MicroConsumer

from loguru import logger as log

consumer = MicroConsumer()

@consumer.listen(queue="test2", workers=1)
def example2(channel, body):
    log.debug(body)