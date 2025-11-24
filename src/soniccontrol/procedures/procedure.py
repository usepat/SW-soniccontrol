import abc
from enum import Enum
from typing import Any, Dict, Self, Tuple, Type

import attrs

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser.answer import Answer
from sonic_protocol.schema import SIPrefix
from soniccontrol.procedures.holder import HolderArgs
from soniccontrol.sonic_device import SonicDevice
from sonic_protocol.si_unit import SIVar

def custom_validator_factory(data_type, min, max):
    def custom_validator(instance, attribute, value):
        if value < min or value > max:
            #TODO improve messsage
            raise TypeError(f"{attribute.name} must be inside the range {min} - {max}. Got: {value}")
    return custom_validator

class ProcedureType(Enum):
    SPECTRUM_MEASURE = "Spectrum Measure"
    RAMP = "Ramp"
    SCAN = "Scan"
    TUNE = "Tune"
    AUTO = "Auto"
    WIPE = "Wipe"
    WIPE_LEGACY = "Wipe_Legacy"
    AUTO_LEGACY = "Auto_Legacy"
    DUTY_CYCLE = "DutyCycle"
    ANOMALY_ROUTINE = "AnomalyRoutine"

@attrs.define(init=False)
class ProcedureArgs:
    def to_dict(self) -> dict[str, Any]:
        """
        Recursively convert this ProcedureArgs instance to a nested dictionary,
        using attribute names as keys for nested ProcedureArgs fields.
        """
        result = {}
        for field in attrs.fields(self.__class__):
            value = getattr(self, field.name)
            if issubclass(field.type, ProcedureArgs):
                result[field.name] = value.to_dict() if value is not None else None
            else:
                result[field.name] = value
        return result
        

    """
        @brief Method used for getting a description of what the procedure does. Used for manuals
    """
    @classmethod
    def get_description(cls) -> str:
        return "No description"

    """
        In order to centralize the naming of procedure arguments, for example the keys of dictionaries,
        or the names of the Form Widget, or the command itself, we use a metadata field for each procedure argument field.
        This field should reference a corresponding EFieldName enum value.
        TODO check if the sonic_text_attributes for the ProcedureArgs command definition also use this enum
    """

    @classmethod
    def from_answer(cls, answer: Answer) -> Self:
        # This can probably done more effectively. Ask Thomas about help
        proc_dict = cls.to_dict_with_holder_args(answer)
        return cls.from_dict(use_enum_names=False, **proc_dict)

    @classmethod
    def from_dict(cls, use_enum_names: bool = True, **kwargs: dict[str, Any]):
        fields_dict = {}

        for field in attrs.fields(cls):
            assert (field.type is not None)
            if issubclass(field.type, ProcedureArgs):
                # If field is a nested ProcedureArgs, filter kwargs for keys starting with prefix_
                prefix = field.metadata.get("prefix", "")
                if prefix:
                    prefix_str = f"{prefix}_"
                else:
                    prefix_str = ""

                # Only treat as flattened if all values are not dicts
                is_flat = all(not isinstance(v, dict) for v in kwargs.values())
                if prefix and is_flat:
                    nested_kwargs = {k[len(prefix_str):]: v for k, v in kwargs.items() if k.startswith(prefix_str)}
                else:
                    # Use all keys that match the nested class's fields
                    nested_field_names = {f.name for f in attrs.fields(field.type)}
                    nested_kwargs = {k: v for k, v in kwargs.items() if k in nested_field_names}
                nested_instance = field.type.from_dict(use_enum_names, **nested_kwargs)
                fields_dict[field.name] = nested_instance
            else:
                enum = field.metadata.get("enum", None)
                # Check if the enum name (str) is in the provided data
                if use_enum_names and enum:
                    assert (isinstance(enum, EFieldName))
                    key = enum.name
                else:
                    key = field.name  # fallback

                if key not in kwargs:
                    continue  # Field is missing in input dict; skip it

                value = kwargs[key]
                if field.converter is not None:
                    value = field.converter(value)
                if issubclass(field.type, SIVar):
                    # No idea, why this is needed to lazy to debug this 
                    if isinstance(value, SIVar):
                        value = field.type(value=value.value, si_prefix=SIPrefix.NONE)
                    else:
                        value = field.type(value=value, si_prefix=SIPrefix.NONE)

                if field.validator is not None:
                    field.validator(cls, field, value)

                fields_dict[field.name] = value

        return cls(**fields_dict)

    @classmethod
    def from_tuple(cls, args: tuple):
        """
            Gets used for scripting, because we get there the procedure args as a flattened tuple of function arguments
        """
        if cls.count_args() != len(args):
            raise ValueError("Args count does not match")
        args_dict, _ = cls.tuple_to_dict(args)
        return cls.from_dict(**args_dict)
    

    @classmethod
    def tuple_to_dict(cls, args: tuple, index = 0) -> Tuple[dict[str, Any], int]:
        args_dict = {}
        for field in attrs.fields(cls):
            if issubclass(field.type, ProcedureArgs):
                    # If field is a nested ProcedureArgs, recurse
                _dict, _index = field.type.tuple_to_dict(args, index)
                index += _index
                args_dict.update(_dict)
            else:
                enum = field.metadata.get("enum", None)
                # Check if the enum name (str) is in the provided data
                if enum:
                    assert (isinstance(enum, EFieldName))
                    key = enum.name
                else:
                    key = field.name  # fallback
                args_dict[key] = args[index]
                index += 1
           
        return (args_dict, index)

    @classmethod
    def count_args(cls) -> int:
        count = 0
        for field in attrs.fields(cls):
                if issubclass(field.type, ProcedureArgs):
                    # If field is a nested ProcedureArgs, recurse
                    count += field.type.count_args()
                else:
                    count += 1
        return count
        
    # @classmethod
    # def fields_dict(cls) -> tuple

    @classmethod
    def fields_dict_with_alias(cls) -> dict[str, Any]:
        """Converts a ProcedureArgs class to a dictionary, where the keys are the string literals of the used EFieldName enum,
            so it can be used for the Form Widget."""
        result = {}
        for field in attrs.fields(cls):
            if issubclass(field.type, ProcedureArgs):
                result.update(field.type.fields_dict_with_alias())
            else:
                alias = field.metadata.get("enum", field.name).name
                result[alias] = field
        return result
    
    @classmethod
    def to_dict_with_holder_args(cls, answer_dict, attrs_prefix: str = "") -> dict[str, Any]:
        """Converts a answer_dict to a dict, where HolderArgs are converted correctly.
            This is used to create a dictionary that can be used for the Form Widget.
            The AnswerDefinition of the ?<protocol>/(Get<Protocol>) command should include all FieldNames related to it.
            Likewise the ProcedureArgs class should implement the same arguments and reference the with the EFieldName enum in the metadata field.
        """
        arg_dict = {}
        for field in attrs.fields(cls):
            prefix = field.metadata.get("prefix", "")
            if prefix:
                prefix = f"{prefix}_{attrs_prefix}" if attrs_prefix else prefix + "_"
            elif attrs_prefix:
                prefix = f"{attrs_prefix}"
            else:
                prefix = ""
            if issubclass(field.type, ProcedureArgs):
                arg_dict.update(field.type.to_dict_with_holder_args(answer_dict, prefix))
            else:
                enum = field.metadata.get("enum", field.name)

                if enum in answer_dict.field_value_dict:
                    value = answer_dict.field_value_dict.get(enum)

                    # If it's a _t_ field, wrap in HolderArgs
                    if value is None:
                        continue
                    if field.type == HolderArgs:
                        value = HolderArgs(float(value), "ms") 
                    if issubclass(field.type, SIVar):
                        value = field.type(value=value, si_prefix=SIPrefix.NONE)
                    # Set the new key with the alias
                    arg_dict[prefix + field.name] = value
        return arg_dict
    

    
class Procedure(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def get_args_class(cls) -> Type: ...

    @property
    @abc.abstractmethod
    def is_remote(self) -> bool: ...

    @abc.abstractmethod
    async def execute(self, device: SonicDevice, args: Any) -> None: ...

    @abc.abstractmethod
    async def fetch_args(self, device: SonicDevice) -> Dict[str, Any]: ...
