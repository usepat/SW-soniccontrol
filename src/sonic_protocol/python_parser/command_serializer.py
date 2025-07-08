from sonic_protocol.python_parser.commands import Command
from sonic_protocol.schema import Protocol

class CommandSerializer:
    def __init__(self, protocol: Protocol):
        self._command_contracts = protocol.command_contracts

    def serialize_command(self, command: Command) -> str:
        command_contract = self._command_contracts.get(command.code, None)
        assert command_contract is not None, f"The command {command} is not known for the protocol" # throw error?
        assert command_contract.command_def is not None, f"There exists no command definition for {command}"

        command_def = command_contract.command_def
        
        identifier = command_def.sonic_text_attrs.string_identifier
        request_msg: str = identifier[0] if isinstance(identifier, list) else identifier
        if command_def.index_param:
            assert "index"in command.args
            request_msg += str(command.args["index"])
        if command_def.setter_param:
            assert "value"in command.args 
            request_msg += "=" + str(command.args["value"])

        return request_msg
