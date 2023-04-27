from typing import Optional

import pika


from ..connection import Details
from ..encoder import Encoder
from .publisher import Publisher


class Producer:
    def __init__(
        self,
        *,
        # All parameters below must be passed in as KW args
        host: Optional[str] = Details.HOST,
        port: Optional[str] = Details.PORT,
        username: Optional[str] = Details.USERNAME,
        password: Optional[str] = Details.PASSWORD,
        encoder: Optional[Encoder] = None,
        connection_type: pika.BaseConnection = pika.BlockingConnection,
        **kwargs,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password

        self.encoder = encoder

        credentials = pika.PlainCredentials(self._username, self._password)

        # Create the parameters for connection to the Queue
        self.connection_parameters = pika.ConnectionParameters(
            port=self._port,
            host=self._host,
            credentials=credentials,
            **kwargs,
        )

        self.connection = connection_type(self.connection_parameters)

    def connect(self, queue: str = None, exchange: str = None, encoder: Encoder = None):
        return Publisher(
            connection=self.connection,
            default_queue=queue,
            default_exchange=exchange,
            default_encoder=encoder,
        )
