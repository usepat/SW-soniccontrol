from marshmallow import ValidationError, fields
from marshmallow_annotations.ext.attrs import AttrsSchema
from marshmallow_annotations import registry
from enum import Enum

from sonic_protocol.defs import DeviceType, Version
from soniccontrol.data_capturing.capture_target import CaptureTargets
from soniccontrol.data_capturing.experiment import Experiment, ExperimentMetaData
from soniccontrol.device_data import FirmwareInfo
from soniccontrol.procedures.holder import HolderArgs
from soniccontrol.procedures.procedure import ProcedureType



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
        
class HolderArgsField(fields.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, HolderArgs):
            raise ValidationError(f"Invalid value: {value}. Must be of type HolderArgs")
        return float(value.duration_in_ms) 

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return HolderArgs(value, unit="ms") 
        except (ValueError, TypeError) as e:
            raise ValidationError(e)


# register fields for the different types
registry.register_field_for_type(Version, VersionField) #type: ignore
registry.register_field_for_type(HolderArgs, HolderArgsField) #type: ignore
registry.register(CaptureTargets, lambda converter, hints, opts: EnumField(CaptureTargets, **opts))
registry.register(DeviceType, lambda converter, hints, opts: EnumField(DeviceType, **opts))
registry.register(ProcedureType, lambda converter, hints, opts: EnumField(ProcedureType, **opts))


class ExperimentMetaDataSchema(AttrsSchema):
    class Meta: # type: ignore
        target = ExperimentMetaData
        register_as_scheme = True

class FirmwareInfoSchema(AttrsSchema):
    class Meta: # type: ignore
        target = FirmwareInfo
        register_as_scheme = True


class ExperimentSchema(AttrsSchema):
    class Meta: # type: ignore
        target = Experiment
        register_as_scheme = True


