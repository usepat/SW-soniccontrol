from marshmallow import Schema, ValidationError, fields
from marshmallow_annotations.ext.attrs import AttrsSchema
from marshmallow_annotations import registry
from enum import Enum
import pandas as pd
import datetime

from sonic_protocol.defs import DeviceType, Version
from soniccontrol.data_capturing.capture_target import CaptureTargets
from soniccontrol.data_capturing.experiment import Experiment
from soniccontrol.device_data import FirmwareInfo



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
        self._schema = schema_class(many=True)  # Marshmallow schema for validation
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, pd.DataFrame):
            raise ValidationError("Expected a Pandas DataFrame.")
        
        data = value.to_dict(orient='records')  # Convert DataFrame to list of dicts
        return self._schema.dump(data).data  # Serialize using Marshmallow

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, list):
            raise ValidationError("Expected a list of dictionaries.")
        
        validated_data = self._schema.load(value)  # Validate each row
        return pd.DataFrame(validated_data)  # Convert back to DataFrame
    

class ExperimentDataRowSchema(Schema):
    timestamp = fields.Time(required=True)
    freq = fields.Integer(required=True, data_key="frequency")
    gain = fields.Integer(required=True)
    urms = fields.Float(required=True)
    irms = fields.Float(required=True)
    phase = fields.Float(required=True)
    temp = fields.Float(missing=float('nan'), data_key="temperature")


# register fields for the different types
registry.register_field_for_type(Version, VersionField) #type: ignore
registry.register(CaptureTargets, lambda converter, hints, opts: EnumField(CaptureTargets, **opts))
registry.register(DeviceType, lambda converter, hints, opts: EnumField(DeviceType, **opts))


class FirmwareInfoSchema(AttrsSchema):
    class Meta: # type: ignore
        target = FirmwareInfo
        register_as_scheme = True


class ExperimentSchema(AttrsSchema):
    class Meta: # type: ignore
        target = Experiment
        register_as_scheme = True

    data = DataFrameField(ExperimentDataRowSchema)


def main():
    experiment = Experiment("experiment", "DW, SS", "0001", "0001-ADD-ON-001", "some connector", "water", FirmwareInfo())
    experiment.data.loc[0] = [
        datetime.datetime.now(),
        100000,
        100,
        0.,
        0.,
        0.,
        float("nan")
    ]
    experiment.additional_metadata = {
        "info": "this is a test"
    }

    scheme = ExperimentSchema()
    marshal_result = scheme.dump(experiment)
    print(marshal_result.data)
    

if __name__ == "__main__":
    main()

