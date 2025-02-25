from marshmallow import Schema, ValidationError, fields
from enum import Enum

import pandas as pd

from sonic_protocol.defs import DeviceType, Version
from soniccontrol.data_capturing.capture_target import CaptureTargets

class EnumField(fields.Field):
    def __init__(self, enum: type[Enum], *args, **kwargs):
        self._enum = enum
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, self._enum):
            raise ValidationError(f"Invalid value: {value}. Must be a {self._enum}.")
        return value.value  # Convert Enum to string for serialization

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return self._enum(value)  # Convert string to Enum during deserialization
        except ValueError:
            raise ValidationError(f"Invalid choice: {value}. Must be one of {[e.value for e in self._enum]}")


class VersionField(fields.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, Version):
            raise ValidationError(f"Invalid value: {value}. Must be of type Version")
        return str(value)  # Convert Enum to string for serialization

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return Version.to_version(value)  # Convert string to Enum during deserialization
        except (ValueError, TypeError) as e:
            raise ValidationError(e)


class DataFrameField(fields.Field):
    def __init__(self, schema_class, *args, **kwargs):
        self.schema = schema_class(many=True)  # Marshmallow schema for validation
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, pd.DataFrame):
            raise ValidationError("Expected a Pandas DataFrame.")
        
        data = value.to_dict(orient='records')  # Convert DataFrame to list of dicts
        return self.schema.dump(data)  # Serialize using Marshmallow

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, list):
            raise ValidationError("Expected a list of dictionaries.")
        
        validated_data = self.schema.load(value)  # Validate each row
        return pd.DataFrame(validated_data)  # Convert back to DataFrame


class ExperimentData(Schema):
    time = fields.Time(required=True)
    frequency = fields.Integer()
    gain = fields.Integer()
    urms = fields.Float()
    irms = fields.Float()
    phase = fields.Float()
    temperature = fields.Float()


class ExperimentSchema(Schema):
    experiment_name = fields.String(required=True)
    authors = fields.List(fields.String, required=True)
    datetime = fields.DateTime(required=True) # can be deduced
    location = fields.String()
    description = fields.String()

    transducer_id = fields.String(required=True) # in future deducible
    add_on_id = fields.String(required=True)
    connector_type = fields.String(required=True)
    medium = fields.String(required=True)
    medium_temperature = fields.Float()
    gap = fields.Float() # in mm
    reflector = fields.String()
    cable_length = fields.Float() # in m
    cable_type = fields.String()

    additional_metadata = fields.Dict(default={})

    # deducible
    serial_number = fields.String(required=True)
    hardware_version = VersionField(required=True)
    firmware_version = VersionField(required=True)
    device_type = EnumField(DeviceType, required=True)
    sonic_control_version = VersionField(required=True)
    operating_system = fields.String(required=True)
    
    capture_target = EnumField(CaptureTargets, required=True)
    target_parameters = fields.Dict(required=True, default={})