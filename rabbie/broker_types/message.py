from .relayed_types import Channel, Method, Properties

from ..encoder import Encoder, AutoEncoder


class Message:
    def __init__(
        self, body: object, channel: Channel, method: Method, properties: Properties
    ) -> None:
        self._body = body
        self._channel = channel
        self._method = method
        self._properties = properties

    @property
    def body(self):
        return self._body

    @property
    def channel(self) -> Channel:
        return self._channel

    @property
    def method(self) -> Method:
        return self._method

    @property
    def properties(self) -> Properties:
        return self._properties

    @property
    def headers(self) -> dict:
        return dict(self.properties.headers)

    def acknowledge(self):
        self.channel.basic_ack(self.method.delivery_tag)

    def reject(self, requeue: bool = True):
        self.channel.basic_nack(self.method.delivery_tag, requeue=requeue)

    def publish(
        self,
        body: str,
        queue: str,
        exchange: str = None,
        properties: Properties = None,
        mandatory: bool = False,
        encoder: Encoder = AutoEncoder(),
        **kwargs,
    ):
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
