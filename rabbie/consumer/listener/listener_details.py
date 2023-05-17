from typing import Optional, Callable
from dataclasses import dataclass

from ...decoder import Decoder


@dataclass
class ListenerDetails:
    """
    This stores the static details of a listener.
    """

    callback: Callable
    queue_name: str
    queue_passive: bool
    queue_durable: bool
    queue_exclusive: bool
    queue_auto_delete: bool
    qos_prefetch_size: int
    qos_prefetch_count: int
    global_qos: bool
    workers: int
    decoder: Optional[Decoder]
    restart: bool
    auto_ack: bool
    configuration_callback: Callable
