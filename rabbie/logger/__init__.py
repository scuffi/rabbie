import logging
from rich.logging import RichHandler


class RabbieLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
        self.setLevel(logging.INFO)  # Set the minimum level for logging

        # Create a handler and set its level
        handler = RichHandler(markup=True)
        handler.setLevel(logging.INFO)

        # Create a formatter and add it to the handler
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        # Add the handler to the logger
        self.addHandler(handler)


logger = RabbieLogger(__name__)
