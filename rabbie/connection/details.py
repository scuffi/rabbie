import os


class Details:
    USERNAME: str = os.environ.get("QUEUE_USERNAME")
    PASSWORD: str = os.environ.get("QUEUE_PASSWORD")

    HOST: str = os.environ.get("QUEUE_HOST")
    PORT: str = os.environ.get("QUEUE_PORT")

    QUEUE_NAME: str = os.environ.get("QUEUE_LISTEN_NAME")
