from enum import Enum


class Status(Enum):
    STARTING = 0
    CONNECTED = 1
    STOPPED = 2
    DISCONNECTED = 3
