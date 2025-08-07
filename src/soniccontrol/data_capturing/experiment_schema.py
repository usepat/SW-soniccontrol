from typing import Tuple
from marshmallow import ValidationError, fields
from marshmallow_annotations.ext.attrs import AttrsSchema
from marshmallow_annotations.base import AbstractConverter
from marshmallow_annotations import registry
from enum import Enum

from sonic_protocol.schema import DeviceType, Version
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


class TupleField(fields.Field):
    def __init__(self, converter: AbstractConverter, sub_types, *args, **kwargs):
        self._tuple_member_classes: Tuple[type] = sub_types
        self._fields = [ converter.convert(t) for t in self._tuple_member_classes]
        super().__init__(*args, **kwargs)
    
    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, tuple):
            raise ValidationError(f"Invalid value: {value}. Must be a tuple")
        expected_length = len(self._tuple_member_classes)
        if len(value) != expected_length:
            raise ValidationError(f"Mismatch in the length of the tuple. Expected {expected_length} elements got {len(value)}")
        for i in range(expected_length):
            val_member_class = value[i].__class__
            expected_class = self._tuple_member_classes[i]
            if val_member_class is not expected_class:
                raise ValidationError(f"Mismatch in the {i}-th element of the tuple. Expected the class {expected_class} got {val_member_class}")

        return [ field._serialize(val_member, attr=None, obj=None) for val_member, field in zip(value, self._fields) ]

    def _deserialize(self, value, attr, data, **kwargs):
        expected_length = len(self._tuple_member_classes)
        if len(value) != expected_length:
            raise ValidationError(f"Mismatch in the length of the tuple. Expected {expected_length} elements got {len(value)}")
        
        result = []
        for i in range(expected_length):
            expected_class = self._tuple_member_classes[i]
            try:
                result.append(expected_class(value[i]))
            except (TypeError, ValueError) as e:
                raise ValidationError(
                    f"Element {i} could not be converted to {expected_class.__name__}: {e}"
                )

        return tuple(field.deserialize(val_member) for val_member, field in zip(value, self._fields))
    

class VersionField(fields.Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, Version):
            raise ValidationError(f"Invalid value: {value}. Must be of type Version")
        return str(value)  

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return Version.to_version(value)  
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
registry.register(Tuple, TupleField)

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


