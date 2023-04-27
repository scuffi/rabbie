import pika

from pika import BasicProperties as Properties

from ...encoder import Encoder


class Publisher:
    def __init__(
        self,
        connection: pika.BaseConnection,
        default_queue: str = None,
        default_exchange: str = None,
        default_encoder: Encoder = None,
    ) -> None:
        self.connection = connection
        self.default_queue = default_queue or ""
        self.default_exchange = default_exchange or ""
        self.default_encoder = default_encoder

    def open(self):
        """
        This function opens a channel for communication in a connection.
        """
        self.channel = self.connection.channel()

    def close(self):
        """
        This function closes the channel.
        """
        self.channel.close()
        self.channel = None

    def publish(
        self,
        message: str,
        queue: str = None,
        properties: Properties = None,
        encoder: Encoder = None,
        exchange: str = None,
        mandatory: bool = False,
    ):
        """
        This function publishes a message to a specified queue or exchange using the RabbitMQ channel.

        Args:
          message (str): The message to be published to the queue or exchange.
          properties (Properties): An optional parameter that allows you to set additional properties for
        the message being published, such as message headers or delivery mode. It is an instance of the
        `pika.BasicProperties` class.
          queue (str): The name of the queue to which the message will be published. If not specified, the
        message will be published to the default queue.
          exchange (str): The exchange to which the message will be published. If not specified, the default
        exchange will be used.
          mandatory (bool): A boolean value indicating whether the message is mandatory or not. If set to
        True, the message will be returned to the sender if it cannot be delivered to any queue. If set to
        False, the message will be silently dropped if it cannot be delivered to any queue. Defaults to
        False
        """

        # Attempt to assign an encoder if the given is None
        encoder = encoder or self.default_encoder

        # If the encoder is not None, we need to reassign message to an 'Encoded' version
        if encoder:
            message = encoder.encode(message)

            # We also want to override the content_type, if properties are given
            if properties:
                properties.content_type = encoder.content_type()

        # Finally, publish the given message to the exchange with all parameters
        self.channel.basic_publish(
            exchange=exchange or self.default_exchange,
            routing_key=queue or self.default_queue,
            body=message,
            properties=properties,
            mandatory=mandatory,
        )

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
