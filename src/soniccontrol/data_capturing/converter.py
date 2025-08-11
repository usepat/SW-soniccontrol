from enum import Enum
from pathlib import Path
from typing import Any
import cattrs
from sonic_protocol.schema import Version
from soniccontrol.procedures.holder import HolderArgs


def create_cattrs_converter_for_forms():
    # We do not want to convert enums and holder args and pathlib.Path
    # Because in the forms object we have own fields for it
    
    def enum_structure_hook(value: Any, t: type) -> Enum:
        if not isinstance(value, Enum):
            raise ValueError("Not a HolderArgs")
        return value

    def enum_unstructure_hook(value: Enum) -> Enum:
        return value

    def is_enum(cls: Any) -> bool:
        # here is instance is used to check if cls is a type (Needed because of generic types that are instantiated as objects)
        return isinstance(cls, type) and issubclass(cls, Enum)

    def holder_args_structure_hook(value: Any, t: type) -> HolderArgs:
        return HolderArgs.to_holder_args(value)

    def holder_args_unstructure_hook(value: HolderArgs) -> HolderArgs:
        return value

    def path_structure_hook(value: Any, t: type) -> Path:
        return value

    def path_unstructure_hook(value: Path) -> Path:
        return value

    converter = cattrs.Converter()
    converter.register_structure_hook_func(is_enum, enum_structure_hook)
    converter.register_unstructure_hook_func(is_enum, enum_unstructure_hook)
    converter.register_structure_hook(HolderArgs, holder_args_structure_hook)
    converter.register_unstructure_hook(HolderArgs, holder_args_unstructure_hook)
    converter.register_structure_hook(Path, path_structure_hook)
    converter.register_unstructure_hook(Path, path_unstructure_hook)

    return converter


def create_cattrs_converter_for_basic_serialization():
    def holder_args_structure_hook(value: Any, t: type) -> HolderArgs:
        return HolderArgs.to_holder_args(value)

    def holder_args_unstructure_hook(value: HolderArgs) -> float:
        return value.duration_in_ms # ensure that time is displayed in ms
    
    def version_structure_hook(value: Any, t: type) -> Version:
        return Version.to_version(value)

    def version_unstructure_hook(value: Version) -> str:
        return str(value)

    converter = cattrs.Converter()
    converter.register_structure_hook(HolderArgs, holder_args_structure_hook)
    converter.register_unstructure_hook(HolderArgs, holder_args_unstructure_hook)
    converter.register_structure_hook(Version, version_structure_hook)
    converter.register_unstructure_hook(Version, version_unstructure_hook)

    return converter