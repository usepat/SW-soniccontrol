from typing import Any, List, Tuple, Union
import numpy as np
from typing_extensions import Dict
from sonic_protocol.command_codes import ICommandCode
from sonic_protocol.schema import CommandContract, CommandDef, CommandParamDef, SonicTextCommandAttrs
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
        arg_list_regex = r"\((?P<arg_list>.+(\,.+))\)"
        setter_param_regex = r"(?P<setter_param>.+)"
        command_regex = rf"{command_identifier_regex}{index_regex}?{arg_list_regex}?(\={setter_param_regex})?"
        compiled_pattern = re.compile(command_regex)
        return compiled_pattern


    def get_deserialized_command_code(self, command_str: str) -> ICommandCode | None:
        match_result = re.match(self._compiled_command_regex, command_str)
        
        if match_result is None:
            return None
    
        command_identifier = match_result.group("command_identifier")
        command_contract = self._find_command_contract_for_identifier(command_identifier)

        return command_contract.code if command_contract else None
    
    def get_command_struct(self, command_str: str) -> Tuple[Command, CommandContract] | None:
        """
        This function is only used for modbus. 
        It is quite permissive in parsing commands. 
        """
        match_result = re.match(self._compiled_command_regex, command_str)
        
        if match_result is None:
            return None
    
        command_identifier = match_result.group("command_identifier")
        command_contract = self._find_command_contract_for_identifier(command_identifier)
        if command_contract is None:
            return None
        if command_contract.command_def is None:
            return None 


        args: Dict[str, Any] = {}
        index = match_result.group("index") if match_result.group("index") else None
        setter_param_str = match_result.group("setter_param")
        setter_param = self._deserialize_settter_param(command_contract.command_def.setter_param, setter_param_str)
        if index is not None:
            args["index"] = index
        if setter_param is not None:
            args["value"] = setter_param

        arg_list_str = match_result.group("arg_list")
        self._deserialize_arg_list(command_contract.command_def, arg_list_str, args)

        command = DeserializedCommand(command_contract.code, args)
        return command, command_contract 
    
    def _deserialize_settter_param(self, param_def: CommandParamDef | None, param_str: str) -> Any | None:
        if param_def is None:
            return None
        try:
            param = param_def.param_type.field_type(param_str)
        except Exception as e:
            return None
        return param

    def _deserialize_arg_list(self, command_def: CommandDef, arg_list_str: str, args: Dict[str, Any]) -> None:
        args_strs = [arg_str.strip() for arg_str in arg_list_str.split(",")]

        if len(args_strs) == 0:
            return

        contains_index = False
        if command_def.index_param is not None and "index" not in args:
            contains_index = True
            try:
                args["index"] = command_def.index_param.param_type.field_type(args_strs[0])
            except Exception as e:
                pass

        contains_setter = False
        if command_def.setter_param is not None and "value" not in args:
            contains_setter = True
            try:
                args["value"] = command_def.setter_param.param_type.field_type(args_strs[-1])
            except Exception as e:
                pass

        if len(args_strs) != len(command_def.params) + contains_index + contains_setter:
            return

        for i, param in enumerate(command_def.params):
            try:
                args[f"arg{i}"] = param.param_type.field_type(args_strs[i + contains_index])
            except Exception as e:
                pass

        
        
