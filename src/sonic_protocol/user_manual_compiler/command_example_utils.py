import numbers
from enum import Enum
from typing import Any, List, Optional

from sonic_protocol.schema import (
    AnswerFieldDef,
    CommandContract,
    CommandParamDef,
    DeviceParamConstantType,
    DeviceParamConstants,
    Timestamp,
    Version,
)
from sonic_protocol.python_parser.command_deserializer import DeserializedCommand
from sonic_protocol.python_parser.commands import Command


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


def _append_unique(target: List[Any], value: object) -> None:
    if any(existing == value for existing in target):
        return
    target.append(value)


def _append_numeric_bound_examples(param_limits: List[Any], value: object, delta: int) -> None:
    _append_unique(param_limits, value)
    if isinstance(value, numbers.Integral) and not isinstance(value, bool):
        _append_unique(param_limits, int(value) + delta)


def _schema_name_label(name: object) -> str:
    symbolic_name = getattr(name, "name", None)
    if isinstance(symbolic_name, str) and symbolic_name != "":
        return symbolic_name
    return str(name)


def _example_value_from_bounds(field_type, consts: DeviceParamConstants) -> Any:
    if field_type.allowed_values:
        return field_type.allowed_values[0]
    if field_type.min_value is not None:
        if isinstance(field_type.min_value, DeviceParamConstantType):
            return consts.get_constant_value_from_type(field_type.min_value)
        return field_type.min_value
    if field_type.max_value is not None:
        if isinstance(field_type.max_value, DeviceParamConstantType):
            return consts.get_constant_value_from_type(field_type.max_value)
        return field_type.min_value
    return None


def _example_value_for_field_type(field_def: AnswerFieldDef) -> Any:
    field_type = field_def.field_type.field_type

    if field_type is bool:
        return "true"
    if _is_enum_field_type(field_type):
        enum_members = [member.value for member in getattr(field_type, "__members__", {}).values()]
        return enum_members[0]
    if issubclass(field_type, Version):
        return str(Version(1, 0, 0))
    if issubclass(field_type, str):
        return f"<{_schema_name_label(field_def.field_name)}_str>"
    if issubclass(field_type, Timestamp):
        return str(Timestamp(12, 30, 15, 15, 10, 2000))
    if issubclass(field_type, numbers.Integral):
        return "0"
    if issubclass(field_type, numbers.Real):
        return "0.0"
    return None


def _field_type_identity(field_type) -> object:
    return getattr(field_type, "field_type", field_type)


def _answer_field_matches_setter_param(field_def: AnswerFieldDef, setter_param: CommandParamDef | None) -> bool:
    if setter_param is None:
        return False

    setter_name = _schema_name_label(setter_param.name).lower()
    field_name = _schema_name_label(field_def.field_name).lower()
    if setter_name == field_name:
        return True

    return _field_type_identity(field_def.field_type) is _field_type_identity(setter_param.param_type)


def _append_type_specific_examples(param_limits: List[Any], param_def: CommandParamDef) -> None:
    field_type = param_def.param_type.field_type
    if field_type is bool:
        _append_unique(param_limits, True)
        _append_unique(param_limits, False)
        
    elif field_type is str:
        _append_unique(param_limits, f"<{_schema_name_label(param_def.name)}_str>")

    elif _is_enum_field_type(field_type):
        enum_members = list(getattr(field_type, "__members__", {}))
        for enum in enum_members:
            _append_unique(param_limits, enum.lower() if isinstance(enum, str) else enum)


def deduce_param_limit_values(consts: DeviceParamConstants, param_def: CommandParamDef | None) -> List[Any]:
    if param_def is None:
        return []

    allowed_values = param_def.param_type.allowed_values
    max_val = _resolve_device_param_constant(consts, param_def.param_type.max_value)
    min_val = _resolve_device_param_constant(consts, param_def.param_type.min_value)

    param_limits: List[Any] = []

    if max_val is not None:
        _append_numeric_bound_examples(param_limits, max_val, 1)
    if min_val is not None:
        _append_numeric_bound_examples(param_limits, min_val, -1)
    if allowed_values is not None:
        for value in allowed_values:
            _append_unique(param_limits, value)

    _append_type_specific_examples(param_limits, param_def)

    return param_limits


def deduce_param_limits(consts: DeviceParamConstants, param_def: CommandParamDef | None) -> List[str]:
    return [str(value) for value in deduce_param_limit_values(consts, param_def)]


def deduce_single_param_example_value(consts: DeviceParamConstants, param_def: CommandParamDef | None) -> Any:
    param_limits = deduce_param_limit_values(consts, param_def)
    if len(param_limits) == 0:
        return None
    return param_limits[0]


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


def deduce_command_examples_for_contract_as_commands(
    consts: DeviceParamConstants,
    command_contract: CommandContract,
) -> List[Command]:
    command_def = command_contract.command_def
    if command_def is None:
        return []

    examples: List[Command] = []
    index_limits = deduce_param_limit_values(consts, command_def.index_param)
    if len(index_limits) == 0:
        index_limits = [None]

    setter_limits = deduce_param_limit_values(consts, command_def.setter_param)

    for index_limit in index_limits:
        if len(setter_limits) == 0:
            args = {} if index_limit is None else {"index": index_limit}
            examples.append(DeserializedCommand(command_contract.code, args))
            continue

        for setter_limit in setter_limits:
            args = {"value": setter_limit}
            if index_limit is not None:
                args["index"] = index_limit
            examples.append(DeserializedCommand(command_contract.code, args))

    return examples


def deduce_single_command_example_for_contract(
    consts: DeviceParamConstants,
    command_contract: CommandContract,
) -> Optional[str]:
    examples = deduce_command_examples_for_contract(consts, command_contract)
    if len(examples) == 0:
        return None
    return examples[0]


def deduce_single_command_example_for_contract_as_command(
    consts: DeviceParamConstants,
    command_contract: CommandContract,
) -> Optional[Command]:
    examples = deduce_command_examples_for_contract_as_commands(consts, command_contract)
    if len(examples) == 0:
        return None
    return examples[0]



def generate_answer_field_example(
    field_def: AnswerFieldDef,
    consts: DeviceParamConstants,
    preferred_value: Any = None,
) -> str:
    field_example = field_def.sonic_text_attrs.prefix
    field_type = field_def.field_type
    example_value = preferred_value
    if example_value is None:
        example_value = _example_value_from_bounds(field_type, consts)
    if example_value is None:
        example_value = _example_value_for_field_type(field_def)
    if example_value is None:
        raise ValueError("Answer field example value missing")
    field_example += str(example_value) + " "
    if field_type.si_prefix:
        field_example += field_type.si_prefix.value
    if field_type.si_unit:
        field_example += field_type.si_unit.value
    return field_example


def deduce_answer_example_for_contract(
    consts: DeviceParamConstants,
    command_contract: CommandContract,
) -> Optional[str]:
    ans_prefix = f"ANS#0={command_contract.code}#"
    answer = ans_prefix
    setter_param = None
    setter_value = None
    if command_contract.command_def is not None:
        setter_param = command_contract.command_def.setter_param
        setter_value = deduce_single_param_example_value(consts, setter_param)
    for field in command_contract.answer_def.fields:
        preferred_value = setter_value if _answer_field_matches_setter_param(field, setter_param) else None
        answer += generate_answer_field_example(field, consts, preferred_value) + "#"
    return answer[:-1]
    