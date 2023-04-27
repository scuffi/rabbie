from abc import ABC, abstractmethod


class Encoder(ABC):
    @abstractmethod
    def encode(self, body: bytes):
        ...

    @abstractmethod
    def content_type(self):
        ...
