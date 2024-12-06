from enum import Enum
from typing import List
from sonic_protocol import protocol
from sonic_protocol.defs import CommandParamDef, DeviceType, Version
from sonic_protocol.protocol_builder import ProtocolBuilder

# TODO: we could from max and min values also deduce commands that should fail
def deduce_param_limits(param_def: CommandParamDef | None) -> List[str]:
    if param_def is None:
        return []
    
    allowed_values = param_def.param_type.allowed_values
    max_val = param_def.param_type.max_value
    min_val = param_def.param_type.min_value

    param_limits = []
    if max_val is not None:
        param_limits.append(max_val)
        # Also create example commands that should be wrong, but not fail. Commands should never fail
        param_limits.append(int(max_val) + 1) #type: ignore
    if min_val is not None:
        param_limits.append(min_val)
        # Also create example commands that should be wrong, but not fail. Commands should never fail
        param_limits.append(int(min_val) - 1) #type: ignore
    if allowed_values is not None:
        param_limits.extend(allowed_values)
    
    field_type = param_def.param_type.field_type
    if field_type is bool:
        param_limits.append("true")
        param_limits.append("false")
    if issubclass(field_type, Enum):
        enum_members = [ member.value for member in field_type ]
        param_limits.extend(enum_members)
    
    return list(map(str, param_limits))
    

def deduce_command_examples(protocol_version: Version, device_type: DeviceType, is_release: bool = False, options: str = "") -> List[str]:
    """
    description:
    This function generates example commands, based on the command_identifiers and limits specified in the protocol.
    Those commands should then be used by parameterized tests in the robot framework to test against.
    returns:
    Returns a list of example command strings that can directly be send to the device
    """
    command_examples: List[str] = []

    command_table = ProtocolBuilder(protocol.protocol).build(device_type, protocol_version, is_release)

    for command_lookup in command_table.values():
        command_def = command_lookup.command_def
        
        assert (not isinstance(command_def.sonic_text_attrs, list))
        string_identifiers = command_def.sonic_text_attrs.string_identifier
        if not isinstance(string_identifiers, list):
            string_identifiers = [string_identifiers]
        
        index_param = command_def.index_param
        index_limits = deduce_param_limits(index_param)
        if len(index_limits) == 0:
            index_limits = [""] # Hacky solution, so that empty index_limits does not skip setter_limits 

        setter_param = command_def.setter_param
        setter_limits = deduce_param_limits(setter_param)

        for string_identifier in string_identifiers:
            for index_limit in index_limits:
                if len(setter_limits) == 0:
                    command_examples.append(f"{string_identifier}{index_limit}")
                else:
                    for setter_limit in setter_limits:
                        command_examples.append(f"{string_identifier}{index_limit}={setter_limit}")

    return command_examples
