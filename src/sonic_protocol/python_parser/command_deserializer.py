from typing import Any, Tuple, Union
import numpy as np
from typing_extensions import Dict
from sonic_protocol.command_codes import ICommandCode
from sonic_protocol.schema import CommandContract, SonicTextCommandAttrs
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.schema import Protocol
import re

class DeserializedCommand(Command):
    def __init__(self, code: ICommandCode, args: Dict[str, Any]):
        super().__init__(code)
        self._args = args

    @property
    def args(self) -> Dict[str, Any]:
        return self._args


class CommandDeserializer:
    def __init__(self, protocol: Protocol):
        self._command_contracts = protocol.command_contracts
        self._compiled_command_regex = self._compile_command_regex()
        self._compiled_param_regex = self._compile_param_regex()

    def _find_command_contract_for_identifier(self, command_identifier: str) -> CommandContract | None:
        for command_code, command_contract in self._command_contracts.items():
            # We need this because of notify command contract
            if command_contract.command_def is None:
                continue

            string_identifiers = command_contract.command_def.sonic_text_attrs.string_identifier
            string_identifiers = string_identifiers if isinstance(string_identifiers, list) else [string_identifiers]
            if command_identifier in string_identifiers:
                return command_contract
        return None

    def _compile_command_regex(self):
        command_identifier_regex = r"(?P<command_identifier>([\!\?\-\=][_a-zA-Z]*)|([_a-zA-Z]+))"
        index_regex = r"(?P<index>((\d+)|(\[.+\])))"
        command_regex = rf"{command_identifier_regex}{index_regex}?(\=.+)?"
        compiled_pattern = re.compile(command_regex)
        return compiled_pattern

    def _compile_param_regex(self):
        param_regex = r"(?P<command>[^=]+)(?:=(?P<param>.+))?"
        compiled_pattern = re.compile(param_regex)
        return compiled_pattern

    def get_deserialized_command_code(self, command_str: str) -> ICommandCode | None:
        match_result = re.match(self._compiled_command_regex, command_str)
        
        if match_result is None:
            return None
    
        command_identifier = match_result.group("command_identifier")
        command_contract = self._find_command_contract_for_identifier(command_identifier)

        return command_contract.code if command_contract else None
    
    def get_command_struct(self, command_str: str) -> Tuple[Command, CommandContract] | None:
        match_result = re.match(self._compiled_command_regex, command_str)
        
        if match_result is None:
            return None
    
        command_identifier = match_result.group("command_identifier")
        index = match_result.group("index") if match_result.group("index") else None
        command_contract = self._find_command_contract_for_identifier(command_identifier)
        if command_contract is None:
            return None
        match_result = re.match(self._compiled_param_regex, command_str)
        if match_result is None:
            return None
        param_string = match_result.group("param")
        param = self.deserialize_param(command_contract, param_string)
        args: Dict[str, Any] = {}
        if index is not None:
            args["index"] = index
        if param is not None:
            args["value"] = param
        command = DeserializedCommand(command_contract.code, args)
        return command, command_contract 
    
    def deserialize_param(self, contract: CommandContract, param_str: str) -> Any | None:
        if contract.command_def is None:
            return None
        if contract.command_def.setter_param is None:
            return None
        try:
            param = contract.command_def.setter_param.param_type.field_type(param_str)
        except Exception as e:
            return None
        return param
        