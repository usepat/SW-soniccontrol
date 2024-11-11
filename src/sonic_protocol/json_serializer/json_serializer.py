from enum import Enum
import json
import attrs
from sonic_protocol.protocol import protocol

class ProtocolJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if attrs.has(cls=obj.__class__):
            attr_dict = attrs.asdict(obj)
            return { 
                attr_name: self.default(attr_value) for attr_name, attr_value in attr_dict.items() 
            }
        if isinstance(obj, Enum):
            return {
                "name": obj.name,
                "value": obj.value
            }
        if isinstance(obj, type):
            return obj.__name__
        if isinstance(obj, dict):
            return {
                key: self.default(value) for key, value in obj.items()
            }
        if isinstance(obj, (list, tuple)):
            return [self.default(value) for value in obj]
        if isinstance(obj, (int, float, str, bool)):
            return obj
        return json.dumps(obj=obj)

if __name__ == "__main__":
    json_data = json.dumps(protocol, cls=ProtocolJSONEncoder, indent=2)
    with open("generated/protocol.json", "w") as f:
        f.write(json_data)