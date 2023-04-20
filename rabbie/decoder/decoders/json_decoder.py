import json

from ..decoder import Decoder


class JSONDecoder(Decoder):
    def decode(self, body: bytes):
        return json.loads(body)
