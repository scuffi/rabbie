import logging
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(markup=True)]
)

logger = logging.getLogger("rabbie")

# Disable pika logging
logging.getLogger("pika").setLevel(logging.WARNING)