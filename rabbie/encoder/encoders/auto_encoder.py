import json
from dataclasses import is_dataclass, asdict

from ..encoder import Encoder


class AutoEncoder(Encoder):
    def encode(self, body: object):
        if isinstance(body, dict) or isinstance(body, list) or isinstance(body, tuple):
            return json.dumps(body)

        if is_dataclass(body):
            return json.dumps(asdict(body))

        return str(body)

    def content_type(self):
        return "application/json"
