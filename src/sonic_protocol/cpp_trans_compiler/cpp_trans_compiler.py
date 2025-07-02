from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

import attrs
import numpy as np
from sonic_protocol.defs import CommandContract, DeviceParamConstantType, DeviceParamConstants, IEFieldName, ProtocolType, AnswerDef, AnswerFieldDef, CommandDef, CommandParamDef, DeviceType, FieldType, SIPrefix, SIUnit, SonicTextAnswerFieldAttrs, SonicTextCommandAttrs, Version
import importlib.resources as rs
import shutil
import sonic_protocol.cpp_trans_compiler
import re

from sonic_protocol.command_codes import ICommandCode
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.protocol import protocol_list as prot_list

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
        #raise ValueError(f"Unknown data type: {data_type}")

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
    def __init__(self):
        self._field_limits_id_counter: int = 0
        self._allowed_values_id_counter: int = 0
        self._field_limits_cache: dict[FieldLimits, str] = {}
        self._param_definitions: dict[CommandParamDef, str] = {}
        self._field_definitions: dict[AnswerFieldDef, str] = {}
        self._allowed_values: dict[Tuple[Any], str] = {}

    def generate_sonic_protocol_lib(self, protocol_list: ProtocolList, protocol_info: ProtocolType, output_dir: Path, options: Optional[List[str]] = None, protocol_name: str = "default", additional_enums: Optional[Dict[str, type[Enum]]] = None):
        # copy protocol definitions to output directory
        shutil.rmtree(output_dir, ignore_errors=True)
        lib_path = rs.files(sonic_protocol.cpp_trans_compiler).joinpath("sonic_protocol_lib")
        shutil.copytree(Path(str(lib_path)), output_dir)
    
        base_lib_dir = output_dir / "include" / "sonic_protocol_lib" / "base"
        template_lib_dir = output_dir / "protocol_template"
        protocol_lib_dir = output_dir / "include" / "sonic_protocol_lib" / protocol_name


        self._inject_code_into_file(
            base_lib_dir / "si_units.hpp",
            SI_UNIT=self._transpile_enum(SIUnit),
            SI_PREFIX=self._transpile_enum(SIPrefix),
        )

        self._inject_code_into_template(
            template_lib_dir / "field_names.hpp",
            protocol_lib_dir / "field_names.hpp",
            CODE_INJECTION=self._transpile_enum(protocol_list.FieldName, "FieldName_t")
        )

        self._inject_code_into_template(
            template_lib_dir / "command_code.hpp",
            protocol_lib_dir / "command_code.hpp",
            COMMAND_CODE=self._transpile_enum(protocol_list.CommandCode, "CommandCode_t"),
            IS_VALID_CODE=self._generate_is_valid_code_cpp_function(protocol_list.CommandCode)
        )

        data_type_defs = ""
        data_type_defs += self._transpile_data_types_dict_to_enum(protocol_list.DataTypes)
        for data_type in protocol_list.DataTypes.values():
            if issubclass(data_type, Enum):
                data_type_defs += self._transpile_enum(data_type)

        self._inject_code_into_template(
            template_lib_dir / "data_types.hpp",
            protocol_lib_dir / "data_types.hpp",
            CODE_INJECTION=data_type_defs
        )
        
        protocol_cpp_name = f"protocol_{create_protocol_info_cpp_var_name(protocol_info)}"
        protocol = protocol_list.build_protocol_for(protocol_info)

        self.consts = protocol.consts 
        protocol_instance, command_defs, answer_defs,  = self._transpile_command_contracts(protocol_info, protocol.command_contracts, protocol_cpp_name, options=options)

        param_defs = self._transpile_param_defs_from_cache()
        field_defs = self._transpile_field_defs_from_cache()
        field_limits = self._transpile_field_limits_from_cache()
        allowed_values = self._transpile_allowed_values_from_cache()
        self._inject_code_into_template(
            template_lib_dir / "protocol_instance.hpp", 
            protocol_lib_dir / "protocol_instance.hpp",
            PROTOCOL_INSTANCE_NAME=protocol_name.capitalize() + "ProtocolInstance",
            PROTOCOL_INSTANCE=protocol_instance,
            FIELD_LIMITS=field_limits,
            FIELD_DEFS = field_defs,
            PARAM_DEFS = param_defs,
            ALLOWED_VALUES = allowed_values,
            COMMAND_DEFS = command_defs,
            ANSWER_DEFS = answer_defs
        )

        consts_defs = self._transpile_consts(self.consts)
        self._inject_code_into_template(
            template_lib_dir / "consts.hpp",
            protocol_lib_dir / "consts.hpp",
            CONSTS=consts_defs
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

    def _transpile_command_contracts(
            self, protocol_version: ProtocolType, command_list: Dict[ICommandCode, CommandContract], protocol_name: str, options: Optional[List[str]] = None) -> Tuple[str, str, str]:
        answer_defs = []
        command_defs = []
        param_defs = []
        string_identifiers = []
        field_defs = []
        for code, command_lookup in sorted(command_list.items()):
            # In Transpile Command and answer def add single definition to a set an only return the names of the instances
            command_param_str_identifier_defs_tuple = self._transpile_command_def(code, command_lookup.command_def, protocol_name)
            command_defs.append(command_param_str_identifier_defs_tuple[0])
            param_defs.append(command_param_str_identifier_defs_tuple[1])
            string_identifiers.append(command_param_str_identifier_defs_tuple[2])
            answer_field_defs_tuple = self._transpile_answer_def(code, command_lookup.answer_def, protocol_name)
            answer_defs.append(answer_field_defs_tuple[0])
            field_defs.append(answer_field_defs_tuple[1])
        
        command_defs_cpp_var_name = protocol_name + "_command_defs"
        answer_defs_cpp_var_name = protocol_name + "_answer_defs"
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
        version = protocol_version.version
        protocol_def = f"""    Protocol {{
        .version = Version {{
            .major = {version.major},
            .minor = {version.minor},
            .patch = {version.patch},
        }},
        .device = DeviceType::{protocol_version.device_type.name},
        .isRelease = {str(protocol_version.is_release).lower()},
        .options = "{", ".join(options) if options else ""}",
        .commands = {command_defs_cpp_var_name},
        .answers = {answer_defs_cpp_var_name}
    }}"""
        return (protocol_def, command_defs_array, answer_defs_array)

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

        cpp_field_type_def: str = f"""FieldTypeDef {{
            .type = DataType::{find_value_in_dictionary(prot_list.DataTypes, field_type.field_type)},
            .converter_reference = ConverterReference::{field_type.converter_ref.name},
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

    def _transpile_enum(self, enum: type[Enum], underlying_type: str = "std::uint16_t") -> str:
        enum_name = enum.__name__

        NEW_LINE = "\n" #  backslashes are not allowed inside f-strings interpolations

        result_str, _ = re.subn(r"(.)([A-Z][a-z]+)", r"\1_\2", enum_name)
        snake_case_enum_name = result_str.lower()

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
            inline {enum_name} convert_string_to_{snake_case_enum_name}(const etl::string_view &str) 
            {{
                {NEW_LINE.join(str_to_enum_cases)}
            }}
        """

        enum_to_str_cases = [
                f'\tcase {enum_name}::{member.name}: return "{member.value}";'
                for member in enum
            ]
        enum_to_string_conversion_function_cpp = f"""
            inline etl::string_view convert_{snake_case_enum_name}_to_string(const {enum_name} &val) 
            {{
                switch (val) {{
                    {NEW_LINE.join(enum_to_str_cases)}
                }}
                std::unreachable();
            }}
        """

        return enum_class_def_cpp + string_to_enum_conversion_function_cpp + enum_to_string_conversion_function_cpp

    def _transpile_data_types_dict_to_enum(self, data_types: Dict[str, type]) -> str:
        enum_members = ",\n".join(data_types.keys())
        return f"""
            enum class DataType : DataType_t {{
                {enum_members}
            }};
        """
    
    def _generate_is_valid_code_cpp_function(self, enum: type[IntEnum]) -> str:
        enum_name = enum.__name__
        cases = "\n".join([f"case {enum_name}::{enum_member}:" for enum_member in enum])
        return f"""
            template<>
            inline bool isValidCode<{enum_name}>(std::uint16_t value) {{
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



if __name__ == "__main__":
    compiler = CppTransCompiler()
    output_dir=Path("./output/generated")
    compiler.generate_sonic_protocol_lib(
        protocol_list=prot_list,
        protocol_info=ProtocolType(Version(2, 0, 0), DeviceType.MVP_WORKER),
        output_dir=output_dir
    )
