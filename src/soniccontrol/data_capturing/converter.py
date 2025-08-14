from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, List
import cattrs
from sonic_protocol.schema import Version
from soniccontrol.data_capturing.experiment import ExperimentMetaData, convert_authors
from soniccontrol.procedures.holder import HolderArgs


def add_author_hooks_to_converter(c: cattrs.Converter):
    # We need to convert authors to a string,
    # because pytables (HDF5) cannot handle lists of variable length strings

    def authors_unstructure_hook(val: List[str]) -> str:
                return ", ".join(val)

    def authors_structure_hook(value: Any, t: type) -> List[str]:
        return convert_authors(value)

    overridden_author_attr = cattrs.gen.override(struct_hook=authors_structure_hook, unstruct_hook=authors_unstructure_hook)

    overridden_structure_hook = cattrs.gen.make_dict_structure_fn(ExperimentMetaData,  c, authors=overridden_author_attr)
    overridden_unstructure_hook = cattrs.gen.make_dict_unstructure_fn(ExperimentMetaData,  c, authors=overridden_author_attr)

    c.register_structure_hook(ExperimentMetaData, overridden_structure_hook)
    c.register_unstructure_hook(ExperimentMetaData, overridden_unstructure_hook)


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
    add_author_hooks_to_converter(converter)

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
    
    def datetime_structure_hook(value: Any, t: type) -> datetime:
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        if isinstance(value, datetime):
            return value
        raise TypeError(f"expected datetime or str, but got {t} instead")
    
    def datetime_unstructure_hook(value: datetime) -> str:
        return value.isoformat()

    converter = cattrs.Converter()
    converter.register_structure_hook(HolderArgs, holder_args_structure_hook)
    converter.register_unstructure_hook(HolderArgs, holder_args_unstructure_hook)
    converter.register_structure_hook(Version, version_structure_hook)
    converter.register_unstructure_hook(Version, version_unstructure_hook)
    converter.register_structure_hook(datetime, datetime_structure_hook)
    converter.register_unstructure_hook(datetime, datetime_unstructure_hook)
    add_author_hooks_to_converter(converter)

    return converter
