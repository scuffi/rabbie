from typing import Optional

import pika


from ..connection import Details
from ..encoder import Encoder, AutoEncoder
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
        encoder: Optional[Encoder] = AutoEncoder(),
        connection_type: pika.BaseConnection = pika.BlockingConnection,
        **kwargs,
    ):
        """
        This is a constructor function that initializes a connection to a RabbitMQ queue using the given
        parameters.

        Args:
          host (Optional[str]): The hostname or IP address of the RabbitMQ server to connect to.
          port (Optional[str]): The port number used to connect to the RabbitMQ server. If not provided, it
        will use the default port number specified in the Details.HOST constant.
          username (Optional[str]): The username used for authentication when connecting to the queue.
          password (Optional[str]): The password parameter is an optional string that represents the
        password used to authenticate the connection to the queue. It is one of the parameters that can be
        passed in as a keyword argument when initializing an instance of the class. If not provided, it
        defaults to the value of the PASSWORD constant defined in the Details
          encoder (Optional[Encoder]): The `encoder` parameter is an optional argument that specifies the
        encoding method to be used for messages sent to the queue. It defaults to an `AutoEncoder` instance,
        which automatically detects the appropriate encoding method based on the message content.
          connection_type (pika.BaseConnection): The type of connection to be established with the RabbitMQ
        server. It is set to `pika.BlockingConnection` by default, which means that the connection will
        block the execution of the program until it is established. Other options include
        `pika.SelectConnection` and `pika.AsyncioConnection
        """
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

        self.connection_type = connection_type

        # Assume that when connection is None we are not connected
        self.connection: pika.BlockingConnection = None

    def _is_connected(self):
        if self.connection is None or self.connection.is_closed:
            self.connection = self.connection_type(self.connection_parameters)

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
        self._is_connected()

        return Publisher(
            connection=self.connection,
            default_queue=queue,
            default_exchange=exchange,
            default_encoder=encoder,
        )
