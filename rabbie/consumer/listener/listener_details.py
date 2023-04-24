from typing import Optional, Callable
from dataclasses import dataclass

from ...decoder import Decoder


@dataclass
class ListenerDetails:
    """
    This stores the static details of a listener.
    """

    # TODO: Add more configurable things here
    callback: Callable
    queue_name: str
    workers: int
    decoder: Optional[Decoder]
    restart: bool
