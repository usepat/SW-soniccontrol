from enum import Enum
from marshmallow_annotations.ext.attrs import AttrsSchema
from marshmallow_annotations.scheme import AnnotationSchemaMeta
from marshmallow_annotations import BaseConverter, registry
import json
import attrs
import typing
import types
from marshmallow import Schema, fields, ValidationError
from sonic_protocol.protocol import protocol
import traceback

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


class ClassTypeField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, type):
            raise ValidationError("Value must be a class type")
        return value.__class__.__name__
    
    def _deserialize(self, value, attr, data):
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        
        ret = getattr(defs, value, None)
        if ret is None:
            ret = getattr(globals(), value)
        return ret


def create_field_type_schema_for_type(field_type: type) -> type:
    schema_name = f"FieldTypeSchema_{field_type.__name__}"
    field_factory = registry.get(target=field_type)
    def make_type_field(**opts):
        return field_factory(BaseConverter(), tuple([]), opts)
    
    schema = type(schema_name, (Schema,), {
        "field_type": ClassTypeField(),
        "allowed_values": fields.List(make_type_field(), required=False),
        "max_value": make_type_field(required=False),
        "min_value": make_type_field(required=False),
        "si_unit": fields.Nested("SIUnitSchema"),
        "si_prefix": fields.Nested("SIPrefixSchema"),
        "converter_ref": fields.Nested("ConverterTypeSchema"),
    })
    return schema

field_type_schemas = {}

class FieldTypeField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, defs.FieldType):
            raise ValidationError("Value must be FieldType")
        schema = field_type_schemas[value.field_type]
        return schema.dump(value).data

    def _deserialize(self, value, attr, data):
        if not isinstance(value, dict):
            raise ValidationError("Value must be a dictionary")
        
        field_type = getattr(value, "field_type", None)
        if field_type is None:
            raise ValidationError("The dictionary must contain a 'field_type' key")
        
        schema = field_type_schemas[field_type]
        return schema.load(value).data
    
class UnionField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        attr_type_args = typing.get_args(value)
        for type_arg in attr_type_args:
            if issubclass(value, type_arg):
                field_factory = registry.get(target=type_arg)
                field = field_factory(BaseConverter(), tuple([]), {})
                return field.serialize(attr, obj)
        raise ValidationError("Value must be one of the types in the Union")


class MetaExportField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, defs.MetaExport):
            raise ValidationError("Value must be MetaExport")

        type_args = typing.get_args(value)
        e_field_factory = registry.get(target=type_args[0])
        e_field = e_field_factory(BaseConverter(), tuple([]), {})
        exports_data = e_field.serialize("exports", value)

        descriptor_scheme = globals()["MetaExportDescriptorSchema"]
        descriptor_data = descriptor_scheme().dump(value.descriptor).data
        return {
            "exports": exports_data,
            "descriptor": descriptor_data,
        }

def create_schema_to_definition(def_class: type):
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
        registry.register_scheme_factory(def_class, schema_name)
    else:
        raise TypeError(f"Unsupported class type: {def_class}")

    globals()[schema_name] = schema_class


def_classes = [
    defs.AnswerFieldDef,
    defs.AnswerDef,
    defs.CommandParamDef,
    defs.CommandDef,
    defs.CommandContract,
    defs.ConverterType,
    defs.DeviceParamConstants,
    defs.DeviceParamConstantType,
    defs.MetaExportDescriptor,
    defs.Protocol,
    defs.SonicTextAnswerFieldAttrs,
    defs.SonicTextAnswerAttrs,
    defs.SonicTextCommandAttrs,
    defs.UserManualAttrs,
]

def_enums = [
    defs.DeviceType,
    defs.InputSource,
    defs.SIPrefix,
    defs.SIUnit,
    defs.CommunicationChannel,
    defs.CommunicationProtocol,
    defs.EFieldName,
    defs.CommandCode,
]
for def_enum in def_enums:
    create_schema_to_definition(def_enum)

# dynamically create schema classes for each def class
create_schema_to_definition(defs.Version)
registry.register(typing.Union, UnionField)
registry.register(types.UnionType, UnionField)
registry.register(defs.MetaExport, MetaExportField)
registry.register(type, ClassTypeField)
registry.register(defs.FieldType, FieldTypeField)
types = [defs.Version, int, float, bool, str,
    defs.InputSource, defs.CommunicationProtocol, defs.CommunicationChannel, defs.DeviceType]
field_type_schemas = {
    field_type: create_field_type_schema_for_type(field_type)
    for field_type in types
}
for def_class in def_classes:
   create_schema_to_definition(def_class)


if __name__ == "__main__":
    try:
        protocol_schema = globals()["ProtocolSchema"]()
        data = protocol_schema.dump(protocol).data
        with open("protocol.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        traceback.print_exc()
        raise e