from typing import Optional

import pika


from ..connection import Details
from ..encoder import Encoder
from .publisher import Publisher


class Producer:
    """
    Producer is a simple class that holds details required to connect to a message broker.

    This can be instantiated once, and called multiple times without worry.
    """

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
        """
        Connect to a message broker. This does NOT open a connection, unless you are using a context manager.

        You should always use this function like: `with producer.connect() as channel:`

        Args:
          queue (str): The name of the default queue to use for publishing messages. If not specified, the
        publisher will use the default queue of the connection.
          exchange (str): The exchange parameter is used to specify the default exchange to be used by the
        Publisher. An exchange is a message routing agent that receives messages from producers and routes
        them to message queues based on rules defined by the exchange type. The exchange parameter can be
        set to a string value representing the name of the exchange
          encoder (Encoder): The encoder parameter is an optional argument that specifies the encoding
        format to be used for the messages being published. It is an instance of the Encoder class, which is
        responsible for serializing the message data into a format that can be transmitted over the network.
        If no encoder is specified, the default encoder for

        Returns:
          A Publisher object is being returned.
        """
        return Publisher(
            connection=self.connection,
            default_queue=queue,
            default_exchange=exchange,
            default_encoder=encoder,
        )
