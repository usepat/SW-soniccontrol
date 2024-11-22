
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Generic, List, Literal, Tuple, TypeVar

import attrs
import numpy as np
from sonic_protocol import protocol as prot
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import Procedure, AnswerDef, AnswerFieldDef, CommandDef, CommandParamDef, CommunicationChannel, DeviceType, FieldType, InputSource, CommunicationProtocol, Protocol, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_builder import CommandLookUpTable, ProtocolBuilder
import importlib.resources as rs
import shutil
import sonic_protocol.cpp_trans_compiler

CPP_NULLOPT = "std::nullopt"

def nullopt_if_none(value):
    return CPP_NULLOPT if value is None else value

def convert_to_cpp_literal(value: Any) -> str:
    if isinstance(value, str):
        return '"' + value + '"'
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        assert False, f"Unknown literal type: {type(value)}"

def convert_to_cpp_initializer_list(value: List[Any]) -> str:
    literals = map(convert_to_cpp_literal, value)
    return "{" + ", ".join(literals) + "}"

def convert_to_enum_data_type(data_type: type[Any]) -> str:
    if data_type is int:
        enum_member = "UINT32"
    elif data_type is np.uint32:
        enum_member = "UINT32"
    elif data_type is np.uint16:
        enum_member = "UINT16"
    elif data_type is np.uint8:
        enum_member = "UINT8"
    elif data_type is float:
        enum_member = "FLOAT"
    elif data_type is str:
        enum_member = "STRING"
    elif data_type is bool:
        enum_member = "BOOL"
    elif issubclass(data_type, DeviceType):  # Use issubclass for custom classes
        enum_member = "E_DEVICE_TYPE"
    elif issubclass(data_type, CommunicationChannel):
        enum_member = "E_COMMUNICATION_CHANNEL"
    elif issubclass(data_type, CommunicationProtocol):
        enum_member = "E_COMMUNICATION_PROTOCOL"
    elif issubclass(data_type, InputSource):
        enum_member = "E_INPUT_SOURCE"
    elif issubclass(data_type, Version):
        enum_member = "VERSION"
    elif issubclass(data_type, Procedure):
        enum_member = "E_PROCEDURE"
    else:
        raise ValueError(f"Unknown data type: {data_type}")

    return f"DataType::{enum_member}"

def convert_to_cpp_field_name(enum_member: EFieldName) -> str:
    return f"FieldName::{enum_member.name}"

def convert_to_cpp_enum_members(enum: type[Enum]) -> str: 
    is_int_enum = issubclass(enum, IntEnum)
    enum_member_assignments = [
        f"\t{member.name} = {member.value if is_int_enum else i}" 
        for i, member in enumerate(enum)
    ]
    enum_members = ",\n".join(enum_member_assignments)

    return enum_members

def create_string_to_enum_conversions(enum: type[Enum]) -> str:
    enum_member_assignments = [
        f'\tif (str == "{member.value}") return {enum.__name__}::{member.name};'
        for member in enum
    ]
    enum_member_assignments = "\n".join(enum_member_assignments)

    return f"""
        {enum_member_assignments}
    """

def create_enum_to_string_conversions(enum: type[Enum]) -> str:
    enum_member_assignments = [
        f'\tcase {enum.__name__}::{member.name}: return "{member.value}";'
        for member in enum
    ]
    enum_member_assignments = "\n".join(enum_member_assignments)

    return f"""
        switch (value) {{
            {enum_member_assignments}
        }}
        assert(false);
    """

@attrs.define()
class ProtocolVersion:
    version: Version = attrs.field()
    device_type: DeviceType = attrs.field()
    is_release: bool = attrs.field(default=True)

T = TypeVar("T")
@attrs.define(hash=True)
class FieldLimits(Generic[T]):
    minimum: T | None = attrs.field()
    maximum: T | None = attrs.field()
    allowed_values: List[T] | None = attrs.field()

class CppTransCompiler:
    def __init__(self):
        self._var_id_counter: int = 0
        self._field_limits_cache: dict[FieldLimits, str] = {}

    def generate_sonic_protocol_lib(self, output_dir: Path):
        # copy protocol definitions to output directory
        shutil.rmtree(output_dir, ignore_errors=True)
        lib_path = rs.files(sonic_protocol.cpp_trans_compiler).joinpath("sonic_protocol_lib")
        shutil.copytree(Path(str(lib_path)), output_dir)
    
        lib_dir = output_dir / "include" / "sonic_protocol_lib"

        field_name_members = convert_to_cpp_enum_members(EFieldName)
        self._inject_code_into_file(
            lib_dir / "field_names.hpp",
            FIELD_NAME_MEMBERS=field_name_members
        )

        command_code_members = convert_to_cpp_enum_members(CommandCode)
        self._inject_code_into_file(
            lib_dir / "command_code.hpp",
            COMMAND_CODE_MEMBERS=command_code_members
        )

        si_unit_members = convert_to_cpp_enum_members(SIUnit)
        si_prefix_members = convert_to_cpp_enum_members(SIPrefix)
        si_unit_to_str_conversions = create_enum_to_string_conversions(SIUnit)
        si_prefix_to_str_conversions = create_enum_to_string_conversions(SIPrefix)
        self._inject_code_into_file(
            lib_dir / "si_units.hpp",
            SI_UNIT_MEMBERS=si_unit_members,
            SI_PREFIX_MEMBERS=si_prefix_members,
            SI_UNIT_TO_STR_CONVERSIONS=si_unit_to_str_conversions,
            SI_PREFIX_TO_STR_CONVERSIONS=si_prefix_to_str_conversions
        )

        device_type_members = convert_to_cpp_enum_members(DeviceType)
        communication_channel_members = convert_to_cpp_enum_members(CommunicationChannel)
        communication_protocol_members = convert_to_cpp_enum_members(CommunicationProtocol)
        input_source_members = convert_to_cpp_enum_members(InputSource)
        procedure_members = convert_to_cpp_enum_members(Procedure)
        
        device_type_to_str_conversions = create_enum_to_string_conversions(DeviceType)
        communication_channel_to_str_conversions = create_enum_to_string_conversions(CommunicationChannel)
        communication_protocol_to_str_conversions = create_enum_to_string_conversions(CommunicationProtocol)
        input_source_to_str_conversions = create_enum_to_string_conversions(InputSource)
        
        str_to_communication_channel_conversions = create_string_to_enum_conversions(CommunicationChannel)
        str_to_communication_protocol_conversions = create_string_to_enum_conversions(CommunicationProtocol)
        str_to_input_source_conversions = create_string_to_enum_conversions(InputSource)
        procedure_to_str_conversions = create_enum_to_string_conversions(Procedure)

        self._inject_code_into_file(
            lib_dir / "enums.hpp",
            DEVICE_TYPE_MEMBERS=device_type_members,
            COMMUNICATION_CHANNEL_MEMBERS=communication_channel_members,
            COMMUNICATION_PROTOCOL_MEMBERS=communication_protocol_members,
            INPUT_SOURCE_MEMBERS=input_source_members,
            PROCEDURE_MEMBERS=procedure_members,

            DEVICE_TYPE_TO_STR_CONVERSIONS=device_type_to_str_conversions,
            COMMUNICATION_CHANNEL_TO_STR_CONVERSIONS=communication_channel_to_str_conversions,
            COMMUNICATION_PROTOCOL_TO_STR_CONVERSIONS=communication_protocol_to_str_conversions,
            INPUT_SOURCE_TO_STR_CONVERSIONS=input_source_to_str_conversions,

            STR_TO_COMMUNICATION_CHANNEL_CONVERSIONS=str_to_communication_channel_conversions,
            STR_TO_COMMUNICATION_PROTOCOL_CONVERSIONS=str_to_communication_protocol_conversions,
            STR_TO_INPUT_SOURCE_CONVERSIONS=str_to_input_source_conversions,
            PROCEDURE_TO_STR_CONVERSIONS=procedure_to_str_conversions
        )

    def generate_transpiled_protocol(self, protocol: Protocol, protocol_versions: List[ProtocolVersion], output_dir: Path): 
        self._var_id_counter = 0
        
        protocol_template_path = rs.files(sonic_protocol.cpp_trans_compiler).joinpath("sonic_protocol_lib").joinpath("generated_protocol.hpp")
        generated_protocol_path = output_dir / "generated_protocol.hpp"
        shutil.copyfile(str(protocol_template_path), generated_protocol_path)

        protocol_count = len(protocol_versions)
        protocols, max_command_count = self._transpile_protocols(protocol, protocol_versions)
        field_limits = self._transpile_field_limits_from_cache()
        self._inject_code_into_file(
            generated_protocol_path, 
            PROTOCOLS=protocols, 
            PROTOCOL_COUNT=protocol_count, 
            FIELD_LIMITS=field_limits,
        )
        
    def _inject_code_into_file(self, file_path: Path, **kwargs) -> None:
        with open(file_path, "r") as source_file:
            content = source_file.read()
        for key, value in kwargs.items():
            content = content.replace(f"/**/{key.upper()}/**/", str(value))
        with open(file_path, "w") as source_file:
            source_file.write(content)

    def _transpile_protocols(self, protocol: Protocol, protocol_versions: List[ProtocolVersion]) -> Tuple[str, int]:
        protocol_builder = ProtocolBuilder(protocol)
        transpiled_protocols = []
        max_command_count = 0
        for protocol_version in protocol_versions:
            command_lookup_table = protocol_builder.build(protocol_version.device_type, protocol_version.version, protocol_version.is_release)
            max_command_count = max(max_command_count, len(command_lookup_table))
            transpiled_protocol = self._transpile_command_contracts(protocol_version, command_lookup_table)
            transpiled_protocols.append(transpiled_protocol)
        return "(" + ", ".join(transpiled_protocols) + ")", max_command_count

    def _transpile_command_contracts(
            self, protocol_version: ProtocolVersion, command_list: CommandLookUpTable) -> str:
        answer_defs = []
        command_defs = []
        for code, command_lookup in sorted(command_list.items()):
            command_defs.append(self._transpile_command_def(code, command_lookup.command_def))
            answer_defs.append(self._transpile_answer_def(code, command_lookup.answer_def))

        version = protocol_version.version
        protocol_def = f"""
            Protocol {{
                .version = Version {{
                    .major = {version.major},
                    .minor = {version.minor},
                    .patch = {version.patch},
                }},
                .device = DeviceType::{protocol_version.device_type.name},
                .isRelease = {str(protocol_version.is_release).lower()},
                .options = "",
                .commands = {{
                    {", ".join(command_defs)}
                }},
                .answers = {{
                    {", ".join(answer_defs)}
                }}
                .commandCount = {len(command_defs)}
            }}
        """
        return protocol_def

    def _transpile_command_def(self, code: CommandCode, command_def: CommandDef) -> str:
        assert isinstance(command_def.sonic_text_attrs, SonicTextCommandAttrs)
        string_identifiers = command_def.sonic_text_attrs.string_identifier
        string_identifiers = [string_identifiers] if isinstance(string_identifiers, str) else string_identifiers
        
        params = []
        if command_def.index_param is not None:
            params.append(self._transpile_param_def(command_def.index_param, "INDEX"))
        if command_def.setter_param is not None:
            params.append(self._transpile_param_def(command_def.setter_param, "SETTER"))

        cpp_command_def = f"""
            CommandDef {{
                .code = CommandCode::{code.name},
                .string_identifiers = {convert_to_cpp_initializer_list(string_identifiers)},
                .params = {{
                    { ", ".join(params) }
                }}
            }}
        """
        return cpp_command_def

    def _transpile_param_def(self, param_def: CommandParamDef, param_type: Literal["SETTER", "INDEX"]) -> str:
        cpp_param_def: str = f"""
            ParamDef {{
                .field_name = {convert_to_cpp_field_name(param_def.name)},
                .param_type = ParamType::{param_type},
                .field_type = {self._transpile_field_type(param_def.param_type)}
            }}
        """
        return cpp_param_def

    def _transpile_answer_def(self, code: CommandCode, answer_def: AnswerDef) -> str:
        transpiled_fields = [self._transpile_answer_field(field) for field in answer_def.fields]
        cpp_answer_def = f"""
            AnswerDef {{
                .code = CommandCode::{code.name},
                .fields = {{ 
                    {", ".join(transpiled_fields)} 
                }}
            }}
        """
        return cpp_answer_def

    def _transpile_answer_field(self, field: AnswerFieldDef) -> str:
        assert isinstance(field.sonic_text_attrs, SonicTextAnswerFieldAttrs)
        cpp_answer_field_def: str = f"""
            AnswerFieldDef {{
                .name = {convert_to_cpp_field_name(field.field_name)},
                .type = {self._transpile_field_type(field.field_type)},
                .prefix = "{field.sonic_text_attrs.prefix}",
                .postfix = "{field.sonic_text_attrs.postfix}"
            }}
        """
        return cpp_answer_field_def

    def _transpile_field_type(self, field_type: FieldType) -> str:
        field_limits = FieldLimits(
            minimum=field_type.min_value,
            maximum=field_type.max_value,
            allowed_values=field_type.allowed_values
        )
        if field_limits in self._field_limits_cache:
            cpp_limits_var: str = self._field_limits_cache[field_limits]
        else:
            self._var_id_counter += 1
            cpp_limits_var: str = f"limits_{self._var_id_counter}"
            self._field_limits_cache[field_limits] = cpp_limits_var

        cpp_field_type_def: str = f"""
            FieldTypeDef {{
                .type = {convert_to_enum_data_type(field_type.field_type)},
                .converter_reference = ConverterReference::{field_type.converter_ref.name},
                .limits = static_cast<const void *>(&{cpp_limits_var}),
                .si_unit = {f"SIUnit::{field_type.si_unit.name}" if field_type.si_unit is not None else CPP_NULLOPT},
                .si_prefix = {f"SIPrefix::{field_type.si_prefix.name}" if field_type.si_prefix is not None else CPP_NULLOPT}
            }}
        """
        
        return cpp_field_type_def

    def _transpile_field_limits_from_cache(self) -> str:
        transpilation_output = ""
        for field_limits, var_name in self._field_limits_cache.items():
            transpilation_output += self._transpile_field_limits(field_limits, var_name)
        return transpilation_output

    def _transpile_field_limits(self, field_limits: FieldLimits, var_name: str) -> str:
        allowed_values = convert_to_cpp_initializer_list(field_limits.allowed_values) if field_limits.allowed_values else CPP_NULLOPT  
        cpp_field_limits: str = f"""
            FieldLimits<uint32_t> {{
                .min = {nullopt_if_none(field_limits.minimum)},
                .max = {nullopt_if_none(field_limits.maximum)},
                .allowed_values = {allowed_values}
            }}
        """ 
        return f"constexpr auto {var_name} {{ {cpp_field_limits} }};\n"



if __name__ == "__main__":
    compiler = CppTransCompiler()
    output_dir=Path("./generated")
    compiler.generate_sonic_protocol_lib(
        output_dir=output_dir
    )
    compiler.generate_transpiled_protocol(
        protocol=prot.protocol,
        protocol_versions=[
            ProtocolVersion(Version(1, 0, 0), DeviceType.MVP_WORKER),
            ProtocolVersion(Version(1, 0, 0), DeviceType.DESCALE),
        ],
        output_dir=output_dir
    )
