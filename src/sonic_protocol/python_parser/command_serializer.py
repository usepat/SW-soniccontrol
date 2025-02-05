from sonic_protocol.python_parser.commands import Command
from sonic_protocol.protocol_builder import CommandLookUpTable

class CommandSerializer:
    def __init__(self, command_lookup_table: CommandLookUpTable):
        self._command_lookup_table = command_lookup_table

    def serialize_command(self, command: Command) -> str:
        lookup_command = self._command_lookup_table.get(command.code, None)
        assert lookup_command is not None, f"The command {command} is not known for the protocol" # throw error?
        
        command_def = lookup_command.command_def
        assert not isinstance(command_def.sonic_text_attrs, list)
        
        identifier = command_def.sonic_text_attrs.string_identifier
        request_msg: str = identifier[0] if isinstance(identifier, list) else identifier
        if command_def.index_param:
            assert "index"in command.args
            request_msg += str(command.args["index"])
        if command_def.setter_param:
            assert "value"in command.args 
            request_msg += "=" + str(command.args["value"])

        return request_msg
