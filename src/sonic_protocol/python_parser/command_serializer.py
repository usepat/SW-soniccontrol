from enum import Enum
from typing import Any
from sonic_protocol.python_parser.commands import Command
from sonic_protocol.schema import CommandDef, CommandParamDef, Protocol
import numpy as np
from base64 import b64encode

class CommandSerializer:
    def __init__(self, protocol: Protocol):
        self._command_contracts = protocol.command_contracts

    def _serialize_field(self, obj: Any) -> str:
        if isinstance(obj, Enum):
            return str(obj.value)
        elif isinstance(obj, bytes):
            return str(b64encode(obj, altchars=b"-_"))
        else:
            return str(obj)

    def _is_int(self, param: CommandParamDef) -> bool:
        field_type = param.param_type.field_type
        return field_type is np.uint8 or field_type is np.uint16 or field_type is np.uint32 or field_type is int

    def serialize_command_args(self, command: Command, command_def: CommandDef) -> str:
        """
        This function is also used for deducing command examples with different identifiers
        """
        request_msg = ""
        if command_def.index_param:
            assert "index"in command.args
            
            index_str = self._serialize_field(command.args["index"])
            if not self._is_int(command_def.index_param):
                #  we have to provide brackets for the case that the index is not a string
                index_str = f"[{index_str}]"
            request_msg += index_str

        if len(command_def.params) != 0:
            request_msg += "("
            for i in range(len(command_def.params)):
                request_msg += self._serialize_field(command.args[f"arg{i}"])
                if i != len(command_def.params) - 1:
                    request_msg += ", "
            request_msg += ")"
        
        if command_def.setter_param:
            assert "value"in command.args 
            request_msg += "=" + self._serialize_field(command.args["value"])

        return request_msg

    def serialize_command(self, command: Command) -> str:
        command_contract = self._command_contracts.get(command.code, None)
        assert command_contract is not None, f"The command {command} is not known for the protocol" # throw error?
        assert command_contract.command_def is not None, f"There exists no command definition for {command}"

        command_def = command_contract.command_def
        
        identifier = command_def.sonic_text_attrs.string_identifier
        identifier_str: str = identifier[0] if isinstance(identifier, list) else identifier
        request_msg = identifier_str
        request_msg += self.serialize_command_args(command, command_def)
        return request_msg
