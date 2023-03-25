import os


class Queue:
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

    USERNAME: str = os.environ.get("QUEUE_USERNAME") or _unset_property(
        "QUEUE_USERNAME"
    )
    PASSWORD: str = os.environ["QUEUE_PASSWORD"] or _unset_property("QUEUE_PASSWORD")

    HOST: str = os.environ["QUEUE_HOST"] or _unset_property("QUEUE_HOST")
    PORT: str = os.environ["QUEUE_PORT"] or _unset_property("QUEUE_PORT")

    QUEUE_NAME: str = os.environ["QUEUE_LISTEN_NAME"] or _unset_property(
        "QUEUE_LISTEN_NAME"
    )
