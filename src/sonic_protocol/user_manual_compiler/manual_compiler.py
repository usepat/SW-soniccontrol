import abc
import argparse
from enum import Enum
from pathlib import Path
from sonic_protocol.defs import AnswerFieldDef, CommandCode, CommandParamDef, ConverterType, DeviceParamConstantType, DeviceParamConstants, DeviceType, FieldType, SonicTextCommandAttrs, UserManualAttrs, Version, Protocol
from sonic_protocol.protocol_builder import CommandLookUp, ProtocolBuilder
from sonic_protocol.protocol import protocol as sonic_protocol



class ManualCompiler(abc.ABC):
    @abc.abstractmethod
    def compile_manual_for_specific_device(self, device_type: DeviceType, protocol_version: Version, is_release: bool = True) -> str: ...


class MarkdownManualCompiler(ManualCompiler):
    def __init__(self, protocol: Protocol):
        self._protocol_builder = ProtocolBuilder(protocol)
        

    def compile_manual_for_specific_device(self, device_type: DeviceType, protocol_version: Version, is_release: bool = True) -> str:
        command_list = self._protocol_builder.build(device_type, protocol_version, is_release)
        
        manual = ""
        manual += self.create_title(device_type, protocol_version, is_release)
        command_codes = sorted(command_list.keys())
        for command_code in command_codes:
            command_lookup = command_list[command_code]
            manual += self.create_command_entry(command_lookup, command_code)

        return manual

    def create_title(self, device_type: DeviceType, protocol_version: Version, is_release: bool) -> str:
        title = f"# Sonic Protocol for {device_type.value} - {protocol_version}.{ 'Release' if is_release else 'Beta'}\n"
        return title

    def create_command_entry(self, command_lookup: CommandLookUp, command_code: CommandCode) -> str:

        description = command_lookup.user_manual_attrs.description
        example = command_lookup.user_manual_attrs.example
        setter_param = command_lookup.command_def.setter_param
        index_param = command_lookup.command_def.index_param
        sonic_text_attrs = command_lookup.command_def.sonic_text_attrs
        assert isinstance(sonic_text_attrs, SonicTextCommandAttrs) 
        string_identifier = sonic_text_attrs.string_identifier
        string_identifier = string_identifier if isinstance(string_identifier, list) else [string_identifier]
        
        section_title = f"## **{command_code.value}**: {command_code.name}  \n"
        command_entry = section_title
        tags = " | ".join(map(lambda tag: f"<u>{tag}</u>", command_lookup.tags)) + "  \n\n"
        command_entry += tags
        command_entry += ("..." if description is None else description) + "  \n\n"
        
        command_entry += "### Command Names\n"
        command_entry += " | ".join(map(lambda id: f"`{id}`", string_identifier)) + "  \n"

        command_entry += "### Params\n"
        if index_param is None and setter_param is None:
            command_entry += "No parameters  \n"
        if index_param is not None:
            command_entry += self.create_param_entry(index_param)
        if setter_param is not None:
            command_entry += self.create_param_entry(setter_param)

        command_entry += "### Answer\n"
        for field in command_lookup.answer_def.fields:
            command_entry += self.create_answer_field_entry(field)

        if example is not None:
            command_entry += "### Example\n"
            command_entry += f"```\n{example}\n```  \n"

        return command_entry

    def create_param_entry(self, param_def: CommandParamDef) -> str:
        description = None
        description_attrs = param_def.user_manual_attrs
        if isinstance(description_attrs, UserManualAttrs):
            description = description_attrs.description

        param_entry = self.create_field_type_entry(param_def.name.value, param_def.param_type, description)
        return param_entry


    def create_answer_field_entry(self, field_def: AnswerFieldDef) -> str:
        description = None
        description_attrs = field_def.user_manual_attrs
        if isinstance(description_attrs, UserManualAttrs):
            description = description_attrs.description

        field_entry = self.create_field_type_entry(field_def.field_name.value, field_def.field_type, description)

        return field_entry

    def create_field_type_entry(self, name: str, field_type: FieldType, description: str | None = None) -> str:
        type_header = f"- **{name}**: *{field_type.field_type.__name__}*"
        if field_type.si_unit is not None or field_type.si_prefix is not None:
            type_header += " in ["
            if field_type.si_prefix is not None:
                type_header += field_type.si_prefix.value
            if field_type.si_unit is not None:
                type_header += field_type.si_unit.value
            type_header += "]"
        type_header += "  \n"


        possible_values = None if field_type.allowed_values is None else field_type.allowed_values
        if possible_values is None and field_type.converter_ref == ConverterType.ENUM:
            assert issubclass(field_type.field_type, Enum)
            possible_values = [ enum_member.value for enum_member in field_type.field_type ]
        if possible_values is not None:
            type_header += "\tPossible values:  \n"
            for value in possible_values:
                type_header += f"\t- {value}  \n"

        if field_type.min_value is not None:
            assert not isinstance(field_type.min_value, DeviceParamConstantType)
            type_header += f"\tMinimum value: {field_type.min_value}  \n"
        if field_type.max_value is not None:
            assert not isinstance(field_type.max_value, DeviceParamConstantType)
            type_header += f"\tMaximum value: {field_type.max_value}  \n"

        if description is not None:
            type_header += f"\t{description}  \n"

        return type_header


def build_manual():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("./"))
    parser.add_argument("--protocol-version", type=str,required=True)
    parser.add_argument("--device-type", type=DeviceType, required=True)
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()

    device_type: DeviceType = args.device_type
    protocol_version: Version = Version.to_version(args.protocol_version)
    is_release: bool = args.release
    output_dir: Path = args.output_dir

    version_str = args.protocol_version.replace('.', '_')
    build_str = "release" if is_release else "debug"
    file_name = output_dir / f"manual_{device_type.value}_{version_str}_{build_str}.md"
    
    if not output_dir.is_dir(): 
        raise Exception(f"The output-dir must be a directory, but is instead a file: {str(output_dir)}")


    manual_compiler = MarkdownManualCompiler(sonic_protocol)
    manual = manual_compiler.compile_manual_for_specific_device(device_type, protocol_version, is_release)

    with open(file_name, "w") as file:
        file.write(manual)