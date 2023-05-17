from enum import Enum


class Status(Enum):
    STARTING = 0
    RUNNING = 1
    STOPPED = 2
    FAILED = 3
