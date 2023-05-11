from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties as Properties

from ..encoder import Encoder


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
        """
        This function rejects a message and optionally requeues it using the basic_nack method of the
        channel object.

        Args:
          requeue (bool): A boolean value indicating whether the rejected message should be requeued or not.
        If set to True, the message will be added back to the queue and can be consumed by another consumer.
        If set to False, the message will be discarded. Defaults to True
          delivery_tag (int): The delivery tag is a unique identifier assigned by the message broker to each
        message that is delivered to a consumer. It is used to acknowledge or reject messages and to ensure
        that messages are processed in the correct order. Defaults to 0
          multiple (bool): A boolean value indicating whether to reject multiple messages at once. If set to
        True, all messages up to and including the specified delivery tag will be rejected. If set to False,
        only the message with the specified delivery tag will be rejected. Defaults to False
        """
        self._channel.basic_nack(
            delivery_tag=delivery_tag,
            multiple=multiple,
            requeue=requeue,
        )

    def publish(
        self,
        body: str,
        queue: str,
        exchange: str = None,
        properties: Properties = None,
        mandatory: bool = False,
        encoder: Encoder = None,
        **kwargs,
    ):
        """
        This function publishes a message to a specified queue or exchange with optional properties and
        mandatory flag.

        Args:
          queue (str): The name of the queue to which the message will be published.
          body (str): The message body to be published to the queue. It should be a string.
          exchange (str): The exchange parameter is an optional parameter that specifies the exchange to
        which the message will be published. If no exchange is specified, the message will be published to
        the default exchange.
          properties (BasicProperties): The properties parameter is an optional argument that allows you to
        set additional properties for the message being published. These properties can include things like
        message headers, message expiration time, message priority, and more. The properties are defined
        using the BasicProperties class from the pika library. If no properties are specified,
          mandatory (bool): A boolean value indicating whether the message is mandatory or not. If set to
        True, the message will be returned to the sender if it cannot be delivered to any queue. If set to
        False, the message will be silently dropped if it cannot be delivered to any queue. Defaults to
        False
        Any other arguments will get passed into the queue declaration.
        """
        # If the encoder is not None, we need to reassign message to an 'Encoded' version
        if encoder:
            body = encoder.encode(body)

            # We also want to override the content_type, if properties are given
            if properties is not None:
                properties.content_type = encoder.content_type()

        self._channel.queue_declare(queue, **kwargs)

        self._channel.basic_publish(
            exchange=exchange or "",
            routing_key=queue,
            body=str(body),
            properties=properties,
            mandatory=mandatory,
        )
