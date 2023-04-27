from typing import Optional

import pika


from ..connection import Details


class Publisher:
    def __init__(
        self,
        *,
        # All parameters below must be passed in as KW args
        host: Optional[str] = Details.HOST,
        port: Optional[str] = Details.PORT,
        username: Optional[str] = Details.USERNAME,
        password: Optional[str] = Details.PASSWORD,
        encoder=None,
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
