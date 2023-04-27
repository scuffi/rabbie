import json

from ..encoder import Encoder


class JSONEncoder(Encoder):
    def encode(self, body: object):
        return json.dumps(body)

    def content_type(self):
        return "application/json"
