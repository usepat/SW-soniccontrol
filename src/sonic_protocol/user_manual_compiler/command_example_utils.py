from enum import Enum
from typing import List, Optional

from sonic_protocol.schema import (
    CommandContract,
    CommandParamDef,
    DeviceParamConstantType,
    DeviceParamConstants,
)


def _resolve_device_param_constant(consts: DeviceParamConstants, value):
    if isinstance(value, DeviceParamConstantType):
        return getattr(consts, value.value)
    return value


def _is_enum_field_type(field_type) -> bool:
    try:
        return issubclass(field_type, Enum)
    except TypeError:
        return False


def _normalize_string_identifiers(command_contract: CommandContract) -> List[str]:
    assert command_contract.command_def is not None
    string_identifiers = command_contract.command_def.sonic_text_attrs.string_identifier
    if isinstance(string_identifiers, list):
        return string_identifiers
    return [string_identifiers]


def _format_index_value(index_value: str) -> str:
    if index_value == "":
        return ""
    if index_value.isdecimal():
        return index_value
    return f"[{index_value}]"


def deduce_param_limits(consts: DeviceParamConstants, param_def: CommandParamDef | None) -> List[str]:
    if param_def is None:
        return []

    def _append_unique(target: List[str], value: object) -> None:
        value_str = str(value)
        if value_str not in target:
            target.append(value_str)

    allowed_values = param_def.param_type.allowed_values
    max_val = _resolve_device_param_constant(consts, param_def.param_type.max_value)
    min_val = _resolve_device_param_constant(consts, param_def.param_type.min_value)

    param_limits: List[str] = []

    if max_val is not None:
        _append_unique(param_limits, max_val)
        _append_unique(param_limits, int(max_val) + 1)  # type: ignore
    if min_val is not None:
        _append_unique(param_limits, min_val)
        _append_unique(param_limits, int(min_val) - 1)  # type: ignore
    if allowed_values is not None:
        for value in allowed_values:
            _append_unique(param_limits, value)

    field_type = param_def.param_type.field_type
    if field_type is bool:
        _append_unique(param_limits, "true")
        _append_unique(param_limits, "false")
    if _is_enum_field_type(field_type):
        enum_members = [member.value for member in getattr(field_type, "__members__", {}).values()]
        for value in enum_members:
            _append_unique(param_limits, value)

    return param_limits


def deduce_single_param_example(consts: DeviceParamConstants, param_def: CommandParamDef | None) -> str:
    param_limits = deduce_param_limits(consts, param_def)
    if len(param_limits) == 0:
        return ""
    return param_limits[0]


def deduce_command_examples_for_contract(consts: DeviceParamConstants, command_contract: CommandContract) -> List[str]:
    command_def = command_contract.command_def
    if command_def is None:
        return []

    examples: List[str] = []
    string_identifiers = _normalize_string_identifiers(command_contract)

    index_limits = deduce_param_limits(consts, command_def.index_param)
    if len(index_limits) == 0:
        index_limits = [""]

    setter_limits = deduce_param_limits(consts, command_def.setter_param)

    for string_identifier in string_identifiers:
        for index_limit in index_limits:
            formatted_index = _format_index_value(index_limit)
            if len(setter_limits) == 0:
                examples.append(f"{string_identifier}{formatted_index}")
            else:
                for setter_limit in setter_limits:
                    examples.append(f"{string_identifier}{formatted_index}={setter_limit}")

    return examples


def deduce_single_command_example_for_contract(
    consts: DeviceParamConstants,
    command_contract: CommandContract,
) -> Optional[str]:
    examples = deduce_command_examples_for_contract(consts, command_contract)
    if len(examples) == 0:
        return None
    return examples[0]
