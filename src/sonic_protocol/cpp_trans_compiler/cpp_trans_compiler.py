from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Dict, Generic, List, Tuple, TypeVar

import attrs
import numpy as np
from sonic_protocol.protocol import protocol_list
from sonic_protocol.protocols.protocol_base.protocol_base import Protocol_base
from sonic_protocol.schema import BuildType, DeviceParamConstantType, DeviceParamConstants, IEFieldName, Protocol, ProtocolType, AnswerDef, AnswerFieldDef, CommandDef, CommandParamDef, DeviceType, FieldType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, Timestamp, Version
import importlib.resources as rs
import shutil
import os
import sonic_protocol.cpp_trans_compiler

from sonic_protocol.command_codes import ICommandCode

CPP_NULLOPT = "std::nullopt"


def nullopt_if_none(value):
    return CPP_NULLOPT if value is None else value

def convert_to_cpp_literal(value: Any) -> str:
    if isinstance(value, str):
        return '"' + value + '"'
    elif isinstance(value, (int, float, np.integer, np.unsignedinteger)):
        return str(value)
    
    else:
        assert False, f"Unknown literal type: {type(value)}"

def convert_to_cpp_initializer_list(value: List[Any] | Tuple[Any]) -> str:
    literals = map(convert_to_cpp_literal, value)
    return "{" + ", ".join(literals) + "}"

def find_value_in_dictionary(dictionary: dict, value):
    keys = filter(lambda k: dictionary[k] == value, dictionary.keys())
    return next(keys, None)

def convert_to_cpp_field_name(enum_member: IEFieldName) -> str:
    return f"FieldName::{enum_member.name}"

def py_type_to_cpp_type(data_type: type) -> str:
    if data_type is np.uint32:
        return "uint32_t"
    elif data_type is np.uint16:
        return "uint16_t"
    elif data_type is np.uint8:
        return "uint8_t"
    elif data_type is float:
        return "float"
    else:
        return "uint32_t"
    
def py_type_to_ir_value_type(data_type: type) -> str:
    if data_type is np.uint32:
        return "uint32_t"
    elif data_type is np.uint16:
        return "uint16_t"
    elif data_type is np.uint8:
        return "uint8_t"
    elif data_type is float:
        return "float"
    elif data_type is bool:
        return "bool"
    elif data_type is str:
        return "std::string_view"
    elif issubclass(data_type, Enum):
        return "IREnum"
    elif data_type is Version:
        return "Version"
    else:
        return "uint32_t"


def create_protocol_info_cpp_var_name(info: ProtocolType) -> str:
    return f"{info.device_type.name}v{info.version.major}_{info.version.minor}_{info.version.patch}"

T = TypeVar("T")
@attrs.define(hash=True)
class FieldLimits(Generic[T]):
    minimum: T | None = attrs.field()
    maximum: T | None = attrs.field()
    allowed_values: Tuple[T] | None = attrs.field()
    data_type: type[T] = attrs.field()
    
    def cpp_data_type(self) -> str:
        return py_type_to_cpp_type(self.data_type)

class CppTransCompiler:
    _DATA_TYPES = {
        "UINT8": np.uint8,
        "UINT16": np.uint16,
        "UINT32": np.uint32,
        "FLOAT": float,
        "BOOL": bool,
        "STRING": str,
        "ENUM": Enum,
        "TIMESTAMP": Timestamp,
        "VERSION": Version,
    }
        
    def __init__(self):
        self._field_limits_id_counter: int = 0
        self._allowed_values_id_counter: int = 0
        self._field_limits_cache: dict[FieldLimits, str] = {}
        self._param_definitions: dict[CommandParamDef, str] = {}
        self._field_definitions: dict[AnswerFieldDef, str] = {}
        self._allowed_values: dict[Tuple[Any], str] = {}

    def transpile_base(self, output_dir: Path):
        lib_path = rs.files(sonic_protocol.cpp_trans_compiler).joinpath("sonic_protocol_lib")
        
        schema_src_dir = Path(str(lib_path)) / "include" / "sonic_protocol_lib" / "schema"
        schema_lib_dir = output_dir / "include" / "sonic_protocol_lib" / "schema"
        shutil.rmtree(schema_lib_dir, ignore_errors=True)
        shutil.copytree(schema_src_dir, schema_lib_dir)

        correspondence_src_dir = Path(str(lib_path)) / "include" / "correspondence" / "schema"
        correspondence_lib_dir = output_dir / "include" / "correspondence" / "schema"
        shutil.rmtree(correspondence_lib_dir, ignore_errors=True)
        shutil.copytree(correspondence_src_dir, correspondence_lib_dir)

        base_correspondence_src_dir = Path(str(lib_path)) / "include" / "correspondence" / "base"
        base_correspondence_lib_dir = output_dir / "include" / "correspondence" / "base"
        shutil.rmtree(base_correspondence_lib_dir, ignore_errors=True)
        shutil.copytree(base_correspondence_src_dir, base_correspondence_lib_dir)

        self._inject_code_into_file(
            schema_lib_dir / "si_units.hpp",
            SI_UNIT=self._transpile_enum(SIUnit),
            SI_PREFIX=self._transpile_enum(SIPrefix),
        )

        self._inject_code_into_file(
            schema_lib_dir / "protocol_def.hpp",
            DEVICE_TYPE=self._transpile_enum(DeviceType),
            BUILD_TYPE=self._transpile_enum(BuildType),
        )

        self._inject_code_into_file(
            schema_lib_dir / "field_type_def.hpp",
            BASE_DATA_TYPE=self._transpile_data_types_dict_to_enum("BaseDataType", CppTransCompiler._DATA_TYPES),
        )

        protocol_descriptor = ProtocolType(Version(0, 0, 0), DeviceType.UNKNOWN)
        protocol = Protocol_base().build_protocol_for(protocol_descriptor)

        self.transpile_protocol(protocol, output_dir, "base")

        

    def transpile_protocol(self, protocol: Protocol, output_dir: Path, protocol_name: str = "default"):
        # copy protocol definitions to output directory
        assert protocol_name != "schema", "The name 'schema' is not allowed for a protocol"

        # Uff, I really do not want to pass this down to _transpile_field.
        # Think of refactoring this a bit to use state.
        self._protocol_custom_data_types = protocol.custom_data_types
        
        lib_path = rs.files(sonic_protocol.cpp_trans_compiler).joinpath("sonic_protocol_lib")
    
        src_template_dir = Path(str(lib_path)) / "protocol_template"
        protocol_lib_dir = output_dir / "include" / "sonic_protocol_lib" / protocol_name
        
        shutil.rmtree(protocol_lib_dir, ignore_errors=True)
        os.makedirs(protocol_lib_dir)

        self._inject_code_into_template(
            src_template_dir / "field_names.hpp",
            protocol_lib_dir / "field_names.hpp",
            PROTOCOL_NAMESPACE=protocol_name,
            CODE_INJECTION=self._transpile_enum(protocol.field_name_cls, "FieldName_t"),
        )

        self._inject_code_into_template(
            src_template_dir / "command_code.hpp",
            protocol_lib_dir / "command_code.hpp",
            PROTOCOL_NAMESPACE=protocol_name,
            COMMAND_CODE=self._transpile_enum(protocol.command_code_cls, "CommandCode_t"),
            IS_VALID_CODE=self._generate_is_valid_code_cpp_function(protocol.command_code_cls)
        )

        data_type_defs = ""
        data_type_defs += self._transpile_data_types_dict_to_enum("TypeDefRef", protocol.custom_data_types)

        for data_type in protocol.custom_data_types.values():
            # ignore DeviceType and BuildType, because they are defined in the protocol schema hpp file
            if issubclass(data_type, Enum) and not issubclass(data_type, (DeviceType, BuildType)):
                data_type_defs += self._transpile_enum(data_type)

        data_type_defs += self._transpile_dynamic_enum_conversion_func(protocol.custom_data_types)

        self._inject_code_into_template(
            src_template_dir / "data_types.hpp",
            protocol_lib_dir / "data_types.hpp",
            PROTOCOL_NAMESPACE=protocol_name,
            CODE_INJECTION=data_type_defs
        )
        
        self.consts = protocol.consts 
        protocol_class, command_defs, answer_defs,  = self._transpile_protocol(protocol)

        param_defs = self._transpile_param_defs_from_cache()
        field_defs = self._transpile_field_defs_from_cache()
        field_limits = self._transpile_field_limits_from_cache()
        allowed_values = self._transpile_allowed_values_from_cache()
        self._inject_code_into_template(
            src_template_dir / "protocol.hpp", 
            protocol_lib_dir / "protocol.hpp",
            PROTOCOL_NAMESPACE=protocol_name,
            PROTOCOL_CLASS=protocol_class,
            FIELD_LIMITS=field_limits,
            FIELD_DEFS = field_defs,
            PARAM_DEFS = param_defs,
            ALLOWED_VALUES = allowed_values,
            COMMAND_DEFS = command_defs,
            ANSWER_DEFS = answer_defs
        )

        consts_defs = self._transpile_consts(self.consts)
        self._inject_code_into_template(
            src_template_dir / "consts.hpp",
            protocol_lib_dir / "consts.hpp",
            PROTOCOL_NAMESPACE=protocol_name,
            CONSTS=consts_defs
        )

    def transpile_correspondence(self, protocol: Protocol, output_dir: Path, protocol_name: str = "default"):
        lib_path = rs.files(sonic_protocol.cpp_trans_compiler).joinpath("sonic_protocol_lib")
        
        api_template_dir = Path(str(lib_path)) / "api_template"
        api_lib_dir = output_dir / "include" / "correspondence" / protocol_name

        self._inject_code_into_template(
            api_template_dir / "command_calls.hpp",
            api_lib_dir / "command_calls.hpp",
            PROTOCOL_NAMESPACE=protocol_name,
            COMMAND_CALLS=self._transpile_command_calls_api(protocol)
        )

        self._inject_code_into_template(
            api_template_dir / "answers.hpp",
            api_lib_dir / "answers.hpp",
            PROTOCOL_NAMESPACE=protocol_name,
            ANSWERS=self._transpile_answers_api(protocol)
        )
         
    def _inject_code_into_file(self, file_path: Path, **kwargs) -> None:
        with open(file_path, "r") as source_file:
            content = source_file.read()
        for key, value in kwargs.items():
            content = content.replace(f"/**/{key.upper()}/**/", str(value))
        with open(file_path, "w") as source_file:
            source_file.write(content)
            #
    def _inject_code_into_template(self, template_path: Path, file_path: Path, copy: bool = True, **kwargs) -> None:
        if copy:
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(template_path, file_path)
        with open(file_path, "r") as source_file:
            content = source_file.read()
        for key, value in kwargs.items():
            content = content.replace(f"/**/{key.upper()}/**/", str(value))
        with open(file_path, "w") as source_file:
            source_file.write(content)

    def _transpile_consts(self, consts: DeviceParamConstants) -> str:
        const_defs: List[str] = []
        for const_name, const_attr in attrs.fields_dict(DeviceParamConstants).items():
            assert const_attr.type
            const_defs.append(f"constexpr {py_type_to_cpp_type(const_attr.type)} {const_name.upper()} {{ {getattr(consts, const_name)} }};")
        return "\n".join(const_defs)

    def _transpile_protocol(
            self, protocol: Protocol) -> Tuple[str, str, str]:
        protocol_info = protocol.info
        command_list = protocol.command_contracts
        protocol_cpp_name = f"protocol_{create_protocol_info_cpp_var_name(protocol_info)}"
        
        answer_defs = []
        command_defs = []
        param_defs = []
        string_identifiers = []
        field_defs = []
        for code, command_lookup in sorted(command_list.items()):
            # In Transpile Command and answer def add single definition to a set an only return the names of the instances
            command_param_str_identifier_defs_tuple = self._transpile_command_def(code, command_lookup.command_def, protocol_cpp_name)
            command_defs.append(command_param_str_identifier_defs_tuple[0])
            param_defs.append(command_param_str_identifier_defs_tuple[1])
            string_identifiers.append(command_param_str_identifier_defs_tuple[2])
            answer_field_defs_tuple = self._transpile_answer_def(code, command_lookup.answer_def, protocol_cpp_name)
            answer_defs.append(answer_field_defs_tuple[0])
            field_defs.append(answer_field_defs_tuple[1])
        
        command_defs_cpp_var_name = protocol_cpp_name + "_command_defs"
        answer_defs_cpp_var_name = protocol_cpp_name + "_answer_defs"
        command_defs_array = f"""
{"".join(param_defs)}
{"".join(string_identifiers)}
inline constexpr std::array<std::optional<CommandDef>, {len(command_defs)}> {command_defs_cpp_var_name} = {{{", ".join(command_defs)}
}};
        """
        answer_defs_array = f"""
{"".join(field_defs)}
inline constexpr std::array<AnswerDef, {len(answer_defs)}> {answer_defs_cpp_var_name} = {{{", ".join(answer_defs)}
}};"""
        version = protocol_info.version

        protocol_cpp_class = f"""
            struct Protocol {{
                using CommandCode = {protocol.command_code_cls.__name__};
                using FieldName = {protocol.field_name_cls.__name__};
                using TypeDefRef = TypeDefRef;

                inline static constexpr auto version = Version {{
                    .major = {version.major},
                    .minor = {version.minor},
                    .patch = {version.patch},
                }};
                inline static constexpr auto device = DeviceType::{protocol_info.device_type.name};
                inline static constexpr auto isRelease = {str(protocol_info.is_release).lower()};
                inline static constexpr auto options = "{protocol_info.additional_opts}";
                inline static constexpr auto commands = {command_defs_cpp_var_name};
                inline static constexpr auto answers = {answer_defs_cpp_var_name};
            }};
        """

        return (protocol_cpp_class, command_defs_array, answer_defs_array)

    def _transpile_command_def(self, code: ICommandCode, command_def: CommandDef | None, protocol_name: str) -> Tuple[str, str, str]:
        if command_def is None:
            return "std::nullopt",  "", ""
        
        assert isinstance(command_def.sonic_text_attrs, SonicTextCommandAttrs)
        string_identifiers = command_def.sonic_text_attrs.string_identifier
        string_identifiers = [string_identifiers] if isinstance(string_identifiers, str) else string_identifiers
        param_defs_cpp_var_name = protocol_name + f"_{code.name}_param_defs"
        string_identifiers_cpp_var_name = protocol_name + f"_{code.name}_string_identifiers"
        param_references = []
        if command_def.index_param is not None:
            if command_def.index_param in self._param_definitions:
                param_references.append(self._param_definitions[command_def.index_param]) 
            else:    
                param_def_refernce_cpp_name = command_def.index_param.to_cpp_var_name() + "_INDEX"
                self._param_definitions[command_def.index_param] = param_def_refernce_cpp_name
                param_references.append(param_def_refernce_cpp_name)
        if command_def.setter_param is not None:
            if command_def.setter_param in self._param_definitions:
                param_references.append(self._param_definitions[command_def.setter_param]) 
            else:    
                param_def_refernce_cpp_name = command_def.setter_param.to_cpp_var_name() + "_SETTER"
                self._param_definitions[command_def.setter_param] = param_def_refernce_cpp_name
                param_references.append(param_def_refernce_cpp_name)
        if param_references == []:
            param_def_cpp_var = ""
            param_defs_cpp_var_name = "EMPTY_PARAMS"#This is the cpp variable name for empty params, defined in the generate_protocol.hpp template file
        else:   
            formatted_references = ",\n    ".join(param_references)
            param_def_cpp_var = f"""
inline constexpr std::array<ParamDef, {len(param_references)}> {param_defs_cpp_var_name} = {{
    {formatted_references}
}};"""
        string_identifiers_cpp = f"""
inline constexpr std::array<std::string_view, {len(string_identifiers)}> {string_identifiers_cpp_var_name} = {convert_to_cpp_initializer_list(string_identifiers)};        
"""
        cpp_command_def = f"""
    CommandDef {{
        .code = CommandCode::{code.name},
        .string_identifiers = {string_identifiers_cpp_var_name},
        .params = {param_defs_cpp_var_name}
    }}"""
        return cpp_command_def, param_def_cpp_var, string_identifiers_cpp

    def _transpile_param_def(self, param_def: CommandParamDef, var_name: str) -> str:
        if "SETTER" in var_name:
            param_type = "SETTER"
        elif "INDEX" in var_name:
            param_type = "INDEX"
        else:
            assert False, f"Unknown param type: {var_name}"
        cpp_param_def: str = f"""
inline constexpr ParamDef {var_name} = {{
    .field_name = {convert_to_cpp_field_name(param_def.name)},
    .param_type = ParamType::{param_type},
    .field_type = {self._transpile_field_type(param_def.param_type)}
}};"""
        return cpp_param_def

    def _transpile_answer_def(self, code: ICommandCode, answer_def: AnswerDef, protocol_name: str) -> Tuple[str,str]:
        transpiled_field_references = []
        for field in answer_def.fields:
            if field in self._field_definitions:
                transpiled_field_references.append(self._field_definitions[field])
            else:  
                field_def_cpp_var_name = field.to_cpp_var_name()
                self._field_definitions[field] = field_def_cpp_var_name
                transpiled_field_references.append(field_def_cpp_var_name)    
        answer_fields_cpp_var_name = protocol_name + f"_{code.name}_answer_fields"
        formatted_transpiled_field_references = ",\n    ".join(transpiled_field_references)
        param_def_array_cpp_var = f"""
inline constexpr std::array<AnswerFieldDef, {len(transpiled_field_references)}> {answer_fields_cpp_var_name} = {{
    {formatted_transpiled_field_references}
}};"""
        cpp_answer_def = f"""
    AnswerDef {{
        .code = CommandCode::{code.name},
        .fields = {answer_fields_cpp_var_name}
    }}"""
        return cpp_answer_def, param_def_array_cpp_var

    def _transpile_answer_field(self, field: AnswerFieldDef, var_name: str) -> str:
        assert isinstance(field.sonic_text_attrs, SonicTextAnswerFieldAttrs)
        cpp_answer_field_def: str = f"""
inline constexpr AnswerFieldDef {var_name} = {{
    .name = {convert_to_cpp_field_name(field.field_name)},
    .type = {self._transpile_field_type(field.field_type)},
    .prefix = "{field.sonic_text_attrs.prefix}",
    .postfix = "{field.sonic_text_attrs.postfix}"
}};
        """
        return cpp_answer_field_def

    def _transpile_field_type(self, field_type: FieldType) -> str:
        data_type =  np.uint32
        if field_type.field_type in (np.uint32, np.uint16, np.uint8, float):
            data_type = field_type.field_type

        min_val = field_type.min_value
        if isinstance(min_val, DeviceParamConstantType):
            min_val = getattr(self.consts, min_val.value)

        max_val = field_type.max_value
        if isinstance(max_val, DeviceParamConstantType):
            max_val = getattr(self.consts, max_val.value)

        field_limits = FieldLimits(
            minimum=min_val,
            maximum=max_val,
            allowed_values=field_type.allowed_values,
            data_type=data_type
        )
        if field_limits in self._field_limits_cache:
            cpp_limits_var: str = self._field_limits_cache[field_limits]
        else:
            self._field_limits_id_counter += 1
            cpp_limits_var: str = f"limits_{self._field_limits_id_counter}"
            self._field_limits_cache[field_limits] = cpp_limits_var

        base_type = field_type.field_type
        if issubclass(base_type, Enum):
            base_type = Enum

        base_type_name = find_value_in_dictionary(CppTransCompiler._DATA_TYPES, base_type)
        sub_type_name = find_value_in_dictionary(self._protocol_custom_data_types, field_type.field_type)
        if sub_type_name:
            type_def_ref = f"static_cast<TypeDefinitionRef_t>(TypeDefRef::{sub_type_name})"
        else:
            type_def_ref = CPP_NULLOPT

        cpp_field_type_def: str = f"""FieldTypeDef {{
            .data_type = BaseDataType::{base_type_name},
            .type_def_ref = {type_def_ref},
            .limits = static_cast<const void *>(&{cpp_limits_var}),
            .si_unit = {f"SIUnit::{field_type.si_unit.name}" if field_type.si_unit is not None else CPP_NULLOPT},
            .si_prefix = {f"SIPrefix::{field_type.si_prefix.name}" if field_type.si_prefix is not None else CPP_NULLOPT}
        }}""" 
        return cpp_field_type_def

    def _transpile_field_limits_from_cache(self) -> str:
        transpilation_output = ""
        for field_limits, var_name in self._field_limits_cache.items():
            transpilation_output += self._transpile_field_limits(field_limits, var_name)
        return transpilation_output
    
    def _transpile_param_defs_from_cache(self) -> str:
        transpilation_output = ""
        for param_def, var_name in self._param_definitions.items():
            transpilation_output += self._transpile_param_def(param_def, var_name)
        return transpilation_output
    
    def _transpile_field_defs_from_cache(self) -> str:
        transpilation_output = ""
        for field, var_name in self._field_definitions.items():
            transpilation_output += self._transpile_answer_field(field, var_name)
        return transpilation_output
    
    def _transpile_allowed_values_from_cache(self) -> str:
        transpilation_output = ""
        for allowed_values, var_name in self._allowed_values.items():
            transpilation_output += f"constexpr std::array<{py_type_to_cpp_type(type(allowed_values))}, {len(allowed_values)}> {var_name} = {convert_to_cpp_initializer_list(allowed_values)};\n"
        return transpilation_output

    def _transpile_dynamic_enum_conversion_func(self, data_types: Dict[str, type]) -> str:
        enum_to_str_conversion_cases = ""
        str_to_enum_conversion_cases = ""
        
        for data_type_name, data_type in data_types.items():
            if not issubclass(data_type, Enum):
                continue

            enum_to_str_conversion_cases += f"""
                case TypeDefRef::{data_type_name}:
                return convert_enum_to_str<{data_type.__name__}>(static_cast<{data_type.__name__}>(enum_member));
            """
            str_to_enum_conversion_cases += f"""
                case TypeDefRef::{data_type_name}:
                return static_cast<std::optional<{data_type.__name__}>>(convert_str_to_enum<{data_type.__name__}>(str));
            """

        return f"""
            namespace enum_str_conversions {{

                template<>
                etl::string_view data_type_dispatch_convert_enum_to_str<TypeDefRef>(const TypeDefRef data_type, const EnumValue_t enum_val) {{
                    switch (data_type) {{
                        {enum_to_str_conversion_cases}
                        default:
                            std::unreachable();
                    }}
                }}

                template<>
                std::optional<EnumValue_t> data_type_dispatch_convert_str_to_enum<TypeDefRef>(const TypeDefRef data_type, const etl::string_view& str) {{
                    switch (data_type) {{
                        {str_to_enum_conversion_cases}
                        default:
                            return std::nullopt;
                    }}
                }}

            }}
        """

    def _transpile_enum(self, enum: type[Enum], underlying_type: str = "EnumValue_t") -> str:
        enum_name = enum.__name__

        NEW_LINE = "\n" #  backslashes are not allowed inside f-strings interpolations

        is_int_enum = issubclass(enum, IntEnum)
        enum_member_assignments = [
            f"\t{member.name} = {member.value if is_int_enum else i}" 
            for i, member in enumerate(enum)
        ]
        enum_members = ",\n".join(enum_member_assignments)

        enum_class_def_cpp = f"""
            enum class {enum_name} : {underlying_type} {{
                {enum_members}
            }};
        """

        str_to_enum_cases = [
            f'\tif (str == "{member.value}") return {enum_name}::{member.name};'
            for member in enum
        ]
        string_to_enum_conversion_function_cpp = f"""
            template<>
            inline std::optional<{enum_name}> convert_string_to_enum<{enum_name}>(const etl::string_view &str) 
            {{
                {NEW_LINE.join(str_to_enum_cases)}
                return std::nullopt;
            }}
        """

        enum_to_str_cases = [
                f'\tcase {enum_name}::{member.name}: return "{member.value}";'
                for member in enum
            ]
        enum_to_string_conversion_function_cpp = f"""
            template<>
            inline etl::string_view convert_enum_to_string<{enum_name}>(const {enum_name} &val) 
            {{
                switch (val) {{
                    {NEW_LINE.join(enum_to_str_cases)}
                }}
                std::unreachable();
            }}
        """

        return f"""
            {enum_class_def_cpp}

            namespace enum_str_conversions {{
                {string_to_enum_conversion_function_cpp}
                {enum_to_string_conversion_function_cpp}
            }}
        """
        

    def _transpile_data_types_dict_to_enum(self, enum_name: str, data_types: Dict[str, type]) -> str:
        enum_members = ",\n".join(data_types.keys())
        return f"""
            enum class {enum_name} : EnumValue_t {{
                {enum_members}
            }};
        """
    
    def _generate_is_valid_code_cpp_function(self, enum: type[IntEnum]) -> str:
        enum_name = enum.__name__
        cases = "\n".join([f"case {enum_name}::{enum_member}:" for enum_member in enum])
        return f"""
            inline bool isValidCode(std::uint16_t value) {{
                {enum_name} code = static_cast<{enum_name}>(value);
                switch (code) {{
                        { cases }
                        return true;
                    default:
                        return false;
                }}
            }}
        """

    def _transpile_field_limits(self, field_limits: FieldLimits, var_name: str) -> str:
        if field_limits.allowed_values is None:
            allowed_values_ref = CPP_NULLOPT
        else:
            if field_limits.allowed_values in self._allowed_values:
                allowed_values_ref = self._allowed_values[field_limits.allowed_values]
            else:
                num_allowed_values = len(field_limits.allowed_values)
                allowed_values_ref = f"{var_name}_{num_allowed_values}_allowed_values"
                self._allowed_values[field_limits.allowed_values] = allowed_values_ref
        

        cpp_field_limits: str = f"""
            FieldLimits<{field_limits.cpp_data_type()}> {{
                .min = {nullopt_if_none(field_limits.minimum)},
                .max = {nullopt_if_none(field_limits.maximum)},
                .allowed_values = {allowed_values_ref}
            }}
        """ 
        return f"inline constexpr auto {var_name} {{ {cpp_field_limits} }};\n"

    def _transpile_answers_api(self, protocol: Protocol) -> str:
        transpiled_code = ""
        for command_code, command_contract in protocol.command_contracts.items():
            answer_fields: List[AnswerFieldDef] =  command_contract.answer_def.fields

            arguments = ""
            temp_variables = ""
            irvalue_list = "{\n"
            for answer_field in answer_fields:
                if arguments != "":
                    arguments += ", "

                field_name = answer_field.field_name.value
                field_type = answer_field.field_type.field_type
                ir_value_type = py_type_to_ir_value_type(field_type)

                if not issubclass(field_type, Enum):
                    arguments += f"const {ir_value_type}& {field_name}"
                    var_name = field_name
                    type_ref = CPP_NULLOPT
                else:
                    arguments += f"const {field_type.__name__}& {field_name}"
                    var_name = "irenum_" + field_name
                    temp_variables += f"const IREnum {var_name} {{ .enum_member=static_cast<EnumValue_t>({field_name}) }};\n"
                    type_ref = f"TypeDefRef::{find_value_in_dictionary(protocol.custom_data_types, field_type)}"
                    
                field_name_code = list(protocol.field_name_cls).index(answer_field.field_name)
                irvalue_list += f"{{ {field_name_code}, {var_name}, {type_ref} }},\n"
            irvalue_list += "}"

            transpiled_code += f"""
                inline Answer create_{command_code.name.lower()}({arguments}) {{
                    {temp_variables}
                    return Answer({command_code.value}, IRObjectAnswer({irvalue_list}));
                }}
            """
        
        return transpiled_code

    def _transpile_command_calls_api(self, protocol: Protocol) -> str:
        transpiled_code = ""
        for command_code, command_contract in protocol.command_contracts.items():
            if command_contract.command_def is None:
                continue

            params_: List[CommandParamDef | None] = [command_contract.command_def.index_param, command_contract.command_def.setter_param]
            params: List[CommandParamDef] =  [p for p in params_ if p is not None]

            arguments = ""
            temp_variables = ""
            irvalue_list = "{\n"
            for param in params:
                if arguments != "":
                    arguments += ", "

                param_name = param.name.value
                field_type = param.param_type.field_type
                ir_value_type = py_type_to_ir_value_type(field_type)

                if not issubclass(field_type, Enum):
                    arguments += f"const {ir_value_type}& {param_name}"
                    var_name = param_name
                    type_ref = CPP_NULLOPT
                else:
                    arguments += f"const {field_type.__name__}& {param_name}"
                    var_name = "irenum_" + param_name
                    temp_variables += f"const IREnum {var_name} {{ .enum_member=static_cast<EnumValue_t>({param_name}) }};\n"
                    type_ref = f"TypeDefRef::{find_value_in_dictionary(protocol.custom_data_types, field_type)}"
                    
                field_name_code = list(protocol.field_name_cls).index(param.name)
                irvalue_list += f"{{ {field_name_code}, {var_name}, {type_ref} }},\n"
            irvalue_list += "}"

            transpiled_code += f"""
                inline CommandCall create_{command_code.name.lower()}({arguments}) {{
                    {temp_variables}
                    return CommandCall({command_code.value}, IRObjectCommandCall({irvalue_list}));
                }}
            """
        
        return transpiled_code

if __name__ == "__main__":
    compiler = CppTransCompiler()

    output_dir=Path("./output/generated")
    compiler.transpile_base(output_dir)

    protocol_descriptor = ProtocolType(Version(2, 0, 0), DeviceType.MVP_WORKER)
    protocol = protocol_list.build_protocol_for(protocol_descriptor)
    compiler.transpile_protocol(
        protocol=protocol,
        output_dir=output_dir
    )
    compiler.transpile_correspondence(
        protocol=protocol,
        output_dir=output_dir
    )
