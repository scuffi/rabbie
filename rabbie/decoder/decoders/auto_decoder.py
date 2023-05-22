import json

from ..decoder import Decoder


class AutoDecoder(Decoder):
    def decode(self, body: bytes):
        try:
            return json.loads(body)
        except ValueError:
            return body.decode("utf-8")
