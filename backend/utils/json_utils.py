from typing import Any, Dict
import dataclasses
import json

def delete_none(dct: Dict[Any, Any]) -> Dict[Any, Any]:
    for key, value in list(dct.items()):
        if value is None:
            del dct[key]
        elif isinstance(value, dict):
            delete_none(value)
    return dct

class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return delete_none(dataclasses.asdict(o))
        return super().default(o)

def dataclass_to_json(instance):
    return json.dumps(instance, cls=DataclassJSONEncoder)
