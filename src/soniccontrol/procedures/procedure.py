import abc
from enum import Enum
from typing import Any, Dict, Type

import attrs

from sonic_protocol.field_names import EFieldName
from soniccontrol.interfaces import Scriptable
from soniccontrol.procedures.holder import HolderArgs


class ProcedureType(Enum):
    SPECTRUM_MEASURE = "Spectrum Measure"
    RAMP = "Ramp"
    SCAN = "Scan"
    TUNE = "Tune"
    AUTO = "Auto"
    WIPE = "Wipe"

@attrs.define(init=False)
class ProcedureArgs:
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
    def __init__(self, **kwargs: dict[str, Any]):
        for field in attrs.fields(self.__class__):
            assert (field.type is not None)
            if issubclass(field.type, ProcedureArgs):
                # If field is a nested ProcedureArgs, recurse
                nested_instance = field.type(**kwargs)  # Value must itself be a dict
                setattr(self, field.name, nested_instance)
            else:

                enum = field.metadata.get("enum", None)
                # Check if the enum value (str) is in the provided data
                if enum:
                    assert (isinstance(enum, EFieldName))
                    key = enum.value
                else:
                    key = field.name  # fallback

                if key not in kwargs:
                    continue  # Field is missing in input dict; skip it

                value = kwargs[key] 
                if field.converter is not None:
                    value = field.converter(value)
                if field.validator is not None:
                    field.validator(self, field, value)

                setattr(self, field.name, value)
        

    @classmethod
    def fields_dict_with_alias(cls) -> dict[str, Any]:
        """Converts a ProcedureArgs class to a dictionary, where the keys are the string literals of the used EFieldName enum,
            so it can be used for the Form Widget."""
        result = {}
        for field in attrs.fields(cls):
            if issubclass(field.type, ProcedureArgs):
                result.update(field.type.fields_dict_with_alias())
            else:
                alias = field.metadata.get("enum", field.name).value
                result[alias] = field
        return result
    
    @classmethod
    def to_dict_with_holder_args(cls, answer_dict) -> dict[str, Any]:
        """Converts a answer_dict to a dict, where HolderArgs are converted correctly.
            This is used to create a dictionary that can be used for the Form Widget.
            The AnswerDefinition of the ?<protocol>/(Get<Protocol>) command should include all FieldNames related to it.
            Likewise the ProcedureArgs class should implement the same arguments and reference the with the EFieldName enum in the metadata field.
        """
        arg_dict = {}
        for field in attrs.fields(cls):
            if issubclass(field.type, ProcedureArgs):
                arg_dict.update(field.type.to_dict_with_holder_args(answer_dict))
            else:
                enum = field.metadata.get("enum", field.name)

                if enum in answer_dict.field_value_dict:
                    value = answer_dict.field_value_dict.get(enum)

                    # If it's a _t_ field, wrap in HolderArgs
                    if value is None:
                        continue
                    if field.type == HolderArgs:
                        value = HolderArgs(float(value), "ms") 

                    # Set the new key with the alias
                    arg_dict[enum.value] = value
        return arg_dict
    
class Procedure(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def get_args_class(cls) -> Type: ...

    @property
    @abc.abstractmethod
    def is_remote(self) -> bool: ...

    @abc.abstractmethod
    async def execute(self, device: Scriptable, args: Any) -> None: ...

    @abc.abstractmethod
    async def fetch_args(self, device: Scriptable) -> Dict[str, Any]: ...
