
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, List, Literal

import attrs
from sonic_protocol import protocol
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import DerivedFromParam, FieldPath, AnswerDef, AnswerFieldDef, CommandDef, CommandParamDef, CommunicationChannel, DeviceType, FieldType, InputSource, CommunicationProtocol, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_builder import CommandLookUpTable, ProtocolBuilder
import importlib.resources as rs
import shutil
import sonic_protocol.cpp_transpiler.sonic_protocol_lib as sonic_protocol_lib

CPP_NULLOPT_T = "std::nullopt"

def nullopt_if_none(value):
    return CPP_NULLOPT_T if value is None else value

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
        enum_member = "INT"
    elif data_type is float:
        enum_member = "DOUBLE"
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

def convert_field_path_to_cpp(field_path: FieldPath) -> str:
    converted_fields = []
    for field_name in field_path:
        if isinstance(field_name, DerivedFromParam):
            # derived fields are just saved as the negative field_name enum value
            converted_field =  "-(FieldName_t)" + convert_to_cpp_field_name(field_name.param)
        else:
            converted_field = "(FieldName_t)" + convert_to_cpp_field_name(field_name)
        converted_fields.append(converted_field)
    return "{" + ", ".join(converted_fields) + "}"

@attrs.define()
class ProtocolVersion:
    version: Version = attrs.field()
    device_type: DeviceType = attrs.field()
    is_release: bool = attrs.field(default=True)

class CppTransCompiler:
    def __init__(self):
        self._var_id_counter: int = 0
        self._transpiled_output: str = ""

    def generate_transpiled_protocol_lib(self, protocol_versions: List[ProtocolVersion], output_dir: Path): 
        self._var_id_counter = 0
        self._transpiled_output = ""
        
        # copy protocol definitions to output directory
        for source_file in rs.files(sonic_protocol_lib).iterdir():
            with rs.as_file(source_file) as file_path:
                shutil.copy(file_path, output_dir)
    
        protocol_count = len(protocol_versions)
        protocols = self._transpile_protocols(protocol_versions)
        self._inject_code_into_file(
            output_dir / "protocol.hpp", 
            PROTOCOLS=protocols, 
            PROTOCOL_COUNT=protocol_count, 
            TRANSPILED_OUTPUT=self._transpiled_output
        )

        field_name_members = convert_to_cpp_enum_members(EFieldName)
        self._inject_code_into_file(
            output_dir / "field_names.hpp",
            FIELD_NAME_MEMBERS=field_name_members
        )

        command_code_members = convert_to_cpp_enum_members(CommandCode)
        self._inject_code_into_file(
            output_dir / "command_code.hpp",
            COMMAND_CODE_MEMBERS=command_code_members
        )
        
    def _inject_code_into_file(self, file_path: Path, **kwargs) -> None:
        with open(file_path, "r") as source_file:
            content = source_file.read()
        for key, value in kwargs.items():
            content = content.replace(f"/**/{key.upper()}/**/", str(value))
        with open(file_path, "w") as source_file:
            source_file.write(content)

    def _transpile_protocols(self, protocol_versions: List[ProtocolVersion]) -> str:
        protocol_builder = ProtocolBuilder(protocol.protocol)
        transpiled_protocols = []
        for protocol_version in protocol_versions:
            command_lookup_table = protocol_builder.build(protocol_version.device_type, protocol_version.version, protocol_version.is_release)
            transpiled_protocol = self._transpile_command_contracts(command_lookup_table)
            transpiled_protocols.append(transpiled_protocol)
        return "{" + ", ".join(transpiled_protocols) + "}"

    def _transpile_command_contracts(
            self, command_list: CommandLookUpTable) -> str:
        answer_defs = []
        command_defs = []
        for code, command_lookup in command_list.items():
            command_defs.append(self._transpile_command_def(code, command_lookup.command_def))
            answer_defs.append(self._transpile_answer_def(code, command_lookup.answer_def))

        protocol_def = f"""
            Protocol {{
                .commands = {{
                    {", ".join(command_defs)}
                }},
                .answers = {{
                    {", ".join(answer_defs)}
                }}
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
                .path = {convert_field_path_to_cpp(field.field_path)},
                .type = {self._transpile_field_type(field.field_type)},
                .prefix = "{field.sonic_text_attrs.prefix}",
                .postfix = "{field.sonic_text_attrs.postfix}"
            }}
        """
        return cpp_answer_field_def

    def _transpile_field_type(self, field_type: FieldType) -> str:
        allowed_values = convert_to_cpp_initializer_list(field_type.allowed_values) if field_type.allowed_values else CPP_NULLOPT_T  
        cpp_field_limits: str = f"""
            FieldLimits<uint32_t> {{
                .min = {nullopt_if_none(field_type.min_value)},
                .max = {nullopt_if_none(field_type.max_value)},
                .allowed_values = {allowed_values}
            }}
        """ 
        self._var_id_counter += 1
        cpp_limits_var: str = f"limits_{self._var_id_counter}"
        self._transpiled_output += f"constexpr auto {cpp_limits_var} {{ {cpp_field_limits} }};\n"
        cpp_field_type_def: str = f"""
            FieldTypeDef {{
                .type = {convert_to_enum_data_type(field_type.field_type)},
                .converter_reference = ConverterReference::{field_type.converter_ref.name},
                .limits = static_cast<const void *>(&{cpp_limits_var}),
                .si_unit = {f"SIUnit::{field_type.si_unit.name}" if field_type.si_unit is not None else CPP_NULLOPT_T},
                .si_prefix = {f"SIPrefix::{field_type.si_prefix.name}" if field_type.si_prefix is not None else CPP_NULLOPT_T}
            }}
        """
        
        return cpp_field_type_def

if __name__ == "__main__":
    compiler = CppTransCompiler()
    compiler.generate_transpiled_protocol_lib(
        protocol_versions=[
            ProtocolVersion(Version(1, 0, 0), DeviceType.MVP_WORKER),
            ProtocolVersion(Version(1, 0, 0), DeviceType.DESCALE),
        ],
        output_dir=Path("./generated")
    )
