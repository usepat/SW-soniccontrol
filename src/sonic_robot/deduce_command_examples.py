from enum import Enum
from typing import List
from sonic_protocol.schema import CommandParamDef, DeviceParamConstantType, DeviceParamConstants, DeviceType, ProtocolType, Version
from sonic_protocol.protocol import protocol_list as operator_protocol_factory
from soniccontrol_gui.plugins.device_plugin import DevicePluginRegistry, register_device_plugins

# TODO: we could from max and min values also deduce commands that should fail
def deduce_param_limits(consts: DeviceParamConstants, param_def: CommandParamDef | None) -> List[str]:
    if param_def is None:
        return []
    
    allowed_values = param_def.param_type.allowed_values
    max_val = param_def.param_type.max_value
    min_val = param_def.param_type.min_value

    param_limits = []
    if max_val is not None:
        if isinstance(max_val, DeviceParamConstantType):
            max_val = getattr(consts, max_val.value)

        param_limits.append(max_val)
        # Also create example commands that should be wrong, but not fail. Commands should never fail
        param_limits.append(int(max_val) + 1) #type: ignore
    if min_val is not None:
        if isinstance(min_val, DeviceParamConstantType):
            min_val = getattr(consts, min_val.value)

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
    register_device_plugins()
    protocol_factories = { plugin.device_type: plugin.protocol_factory for plugin in DevicePluginRegistry.get_device_plugins() }
    protocol_factory = protocol_factories.get(device_type, operator_protocol_factory)
    protocol = protocol_factory.build_protocol_for(ProtocolType(protocol_version, device_type, is_release))
            

    for command_contract in protocol.command_contracts.values():
        command_def = command_contract.command_def

        if command_def is None:
            continue
        
        assert (not isinstance(command_def.sonic_text_attrs, list))
        string_identifiers = command_def.sonic_text_attrs.string_identifier
        if not isinstance(string_identifiers, list):
            string_identifiers = [string_identifiers]
        
        index_param = command_def.index_param
        index_limits = deduce_param_limits(protocol.consts, index_param)
        if len(index_limits) == 0:
            index_limits = [""] # Hacky solution, so that empty index_limits does not skip setter_limits 

        setter_param = command_def.setter_param
        setter_limits = deduce_param_limits(protocol.consts, setter_param)

        for string_identifier in string_identifiers:
            for index_limit in index_limits:
                if index_limit != "" and not index_limit.isdecimal():
                    index_limit = f"[{index_limit}]"

                if len(setter_limits) == 0:
                    command_examples.append(f"{string_identifier}{index_limit}")
                else:
                    for setter_limit in setter_limits:
                        command_examples.append(f"{string_identifier}{index_limit}={setter_limit}")

    return command_examples
