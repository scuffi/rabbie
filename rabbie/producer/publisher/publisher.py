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
        body: str,
        queue: str = None,
        properties: Properties = None,
        encoder: Encoder = None,
        exchange: str = None,
        mandatory: bool = False,
    ):
        """
        This function publishes a body to a specified queue or exchange using the RabbitMQ channel.

        Args:
          body (str): The body to be published to the queue or exchange.
          properties (Properties): An optional parameter that allows you to set additional properties for
        the body being published, such as body headers or delivery mode. It is an instance of the
        `pika.BasicProperties` class.
          queue (str): The name of the queue to which the body will be published. If not specified, the
        body will be published to the default queue.
          exchange (str): The exchange to which the body will be published. If not specified, the default
        exchange will be used.
          mandatory (bool): A boolean value indicating whether the body is mandatory or not. If set to
        True, the body will be returned to the sender if it cannot be delivered to any queue. If set to
        False, the body will be silently dropped if it cannot be delivered to any queue. Defaults to
        False
        """

        # Attempt to assign an encoder if the given is None
        encoder = encoder or self.default_encoder

        # If the encoder is not None, we need to reassign body to an 'Encoded' version
        if encoder:
            body = encoder.encode(body)

            # We also want to override the content_type, if properties are given
            if properties:
                properties.content_type = encoder.content_type()

        # Finally, publish the given body to the exchange with all parameters
        self.channel.basic_publish(
            exchange=exchange or self.default_exchange,
            routing_key=queue or self.default_queue,
            body=body,
            properties=properties,
            mandatory=mandatory,
        )

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
