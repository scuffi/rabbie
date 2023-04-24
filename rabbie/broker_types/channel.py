from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties


class Channel:
    def __init__(self, blocking_channel: BlockingChannel) -> None:
        self._channel = blocking_channel

    def acknowledge(self, delivery_tag: int = 0, multiple: bool = False):
        """
        This function acknowledges the receipt of a message from a RabbitMQ channel.

        Args:
          delivery_tag (int): The delivery tag is a unique identifier assigned by the message broker to each
        message that is delivered to a consumer. It is used to acknowledge receipt of the message and to
        indicate which message(s) have been processed by the consumer. Defaults to 0
          multiple (bool): A boolean value that indicates whether to acknowledge multiple messages at once.
        If set to True, all messages up to and including the delivery_tag will be acknowledged. If set to
        False, only the message with the specified delivery_tag will be acknowledged. Defaults to False
        """
        self._channel.basic_ack(delivery_tag, multiple)

    def reject(
        self, requeue: bool = True, delivery_tag: int = 0, multiple: bool = False
    ):
        self._channel.basic_nack(
            delivery_tag=delivery_tag,
            multiple=multiple,
            requeue=requeue,
        )

    def publish(
        self,
        queue: str,
        body: str,
        exchange: str = None,
        properties: BasicProperties = None,
        mandatory: bool = False,
    ):
        self._channel.basic_publish(
            exchange=exchange or "",
            routing_key=queue,
            body=str(body),
            properties=properties,
            mandatory=mandatory,
        )
