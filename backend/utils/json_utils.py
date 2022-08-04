import dataclasses
import json

class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

def dataclass_to_json(instance):
    return json.dumps(instance, cls=DataclassJSONEncoder)
