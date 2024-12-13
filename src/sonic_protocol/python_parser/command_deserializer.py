from typing import Any
from typing_extensions import Dict
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import SonicTextCommandAttrs
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.protocol_builder import CommandLookUpTable
import re

class DeserializedCommand(Command):
    def __init__(self, code: CommandCode, args: Dict[str, Any]):
        super().__init__(code)
        self._args = args

    @property
    def args(self) -> Dict[str, Any]:
        return self._args


class CommandDeserializer:
    def __init__(self, command_lookup_table: CommandLookUpTable):
        self._command_lookup_table = command_lookup_table
        self._compiled_command_regex = self._compile_command_regex()

    def _find_command_in_lookup_table(self, command_identifier: str) -> CommandCode | None:
        for command_code, command_lookup in self._command_lookup_table.items():
            assert isinstance(command_lookup.command_def.sonic_text_attrs, SonicTextCommandAttrs)
            string_identifiers = command_lookup.command_def.sonic_text_attrs.string_identifier
            string_identifiers = string_identifiers if isinstance(string_identifiers, list) else [string_identifiers]
            if command_identifier in string_identifiers:
                return command_code
        return None

    def _compile_command_regex(self):
        command_identifier_regex = r"(?P<command_identifier>([\!\?\-\=][_a-zA-Z]*)|([_a-zA-Z]+))"
        command_regex = rf"{command_identifier_regex}(\d+)?(\=[\+\-a-zA-Z0-9]+)?"
        compiled_pattern = re.compile(command_regex)
        return compiled_pattern

    def get_deserialized_command_code(self, command_str: str) -> CommandCode | None:
        match_result = re.match(self._compiled_command_regex, command_str)
        
        if match_result is None:
            return None
    
        command_identifier = match_result.group("command_identifier")
        command_code = self._find_command_in_lookup_table(command_identifier)

        return command_code

    
