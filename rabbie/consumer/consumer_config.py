import os


class ConsumerConfig:
    @staticmethod
    def _unset_property(property: str):
        """
        If the property is not set, raise an error

        Args:
          property (str): The name of the property that was not set.
        """
        raise AttributeError(
            f"{property} was unset when trying to connect to queue, exiting program."
        )

    USERNAME: str = os.environ.get("QUEUE_USERNAME")
    PASSWORD: str = os.environ.get("QUEUE_PASSWORD")

    HOST: str = os.environ.get("QUEUE_HOST")
    PORT: str = os.environ.get("QUEUE_PORT")

    QUEUE_NAME: str = os.environ.get("QUEUE_LISTEN_NAME")
