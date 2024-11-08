from enum import Enum
from marshmallow_annotations.ext.attrs import AttrsSchema
from marshmallow_annotations.scheme import AnnotationSchemaMeta
import json
import attrs
from marshmallow import Schema, fields
from sonic_protocol.protocol import protocol

import sonic_protocol.defs as defs

class EnumSchemaMeta(AnnotationSchemaMeta):
    def __new__(mcs, name, bases, attrs):
        klass = super().__new__(mcs, name, bases, attrs)
        meta = attrs.get('Meta')
        enum_class = getattr(meta, 'enum_class', None)
        if enum_class:
            setattr(klass, 'enum_class', enum_class)
        return klass
        

class EnumSchema(Schema, metaclass=EnumSchemaMeta):
    name = fields.String()
    value = fields.Raw()

    class Meta:
        pass

    def dump(self, obj, *args, **kwargs):
        """
        Convert an Enum member into a dictionary with 'name' and 'value'.
        """
        if isinstance(obj, self.enum_class):
            return {
                "name": obj.name,
                "value": obj.value,
            } 
        return super().dump(obj, *args, **kwargs)

    def load(self, data, *args, **kwargs):
        """
        Convert a dictionary with 'name' and 'value' into an Enum member.
        """
        if 'name' in data:
            return self.enum_class(data['name'])
        return super().load(data, *args, **kwargs)


def_classes = [
    defs.CommandCode,
    defs.AnswerFieldDef,
    defs.AnswerDef,
    defs.CommandParamDef,
    defs.CommandDef,
    defs.CommandContract,
    defs.CommunicationChannel,
    defs.CommunicationProtocol,
    defs.ConverterType,
    defs.DeviceParamConstants,
    defs.DeviceParamConstantType,
    defs.DeviceType,
    defs.EFieldName,
    defs.FieldType,
    defs.InputSource,
    defs.MetaExportDescriptor,
    defs.MetaExport,
    defs.Protocol,
    defs.SIPrefix,
    defs.SIUnit,
    defs.SonicTextAnswerFieldAttrs,
    defs.SonicTextAnswerAttrs,
    defs.SonicTextCommandAttrs,
    defs.UserManualAttrs,
    defs.Version,
]

# dynamically create schema classes for each def class
for def_class in def_classes:
    schema_name = f'{def_class.__name__}Schema'
    if attrs.has(def_class):
        schema_class = type(schema_name, (AttrsSchema,), {
            'Meta': type('Meta', (), {
                'target': def_class,
                'register_as_scheme': True
            })
        })
    elif issubclass(def_class, Enum):
        schema_class = type(schema_name, (EnumSchema,), {
            'Meta': type('Meta', (), {
                'enum_class': def_class,
                'register_as_scheme': True
            })
        })
    else:
        raise TypeError(f"Unsupported class type: {def_class}")

    globals()[schema_name] = schema_class


if __name__ == "__main__":
    protocol_schema = globals()["ProtocolSchema"]()
    data = protocol_schema.dump(protocol).data
    with open("protocol.json", "w") as f:
        json.dump(data, f, indent=2)