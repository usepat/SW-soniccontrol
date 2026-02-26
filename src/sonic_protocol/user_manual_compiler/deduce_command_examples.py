from typing import List, Optional
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.schema import (
    DeviceType,
    ProtocolType,
    Version,
)
from sonic_protocol.protocol import protocol_list as operator_protocol_factory
from sonic_protocol.user_manual_compiler.command_example_utils import (
    deduce_command_examples_for_contract,
    deduce_single_command_example_for_contract,
)
    

def _build_protocol(protocol_version: Version, device_type: DeviceType, is_release: bool):
    from soniccontrol_gui.plugins.device_plugin import DevicePluginRegistry, register_device_plugins

    register_device_plugins()
    protocol_factories = {
        plugin.device_type: plugin.protocol_factory
        for plugin in DevicePluginRegistry.get_device_plugins()
    }
    protocol_factory = protocol_factories.get(device_type, operator_protocol_factory)
    return protocol_factory.build_protocol_for(ProtocolType(protocol_version, device_type, is_release))


def deduce_command_examples(
    protocol_version: Version,
    device_type: DeviceType,
    is_release: bool = False,
    options: str = "",
    skip_command_codes: Optional[List[CommandCode]] = None,
) -> List[str]:
    """
    description:
    This function generates example commands, based on the command_identifiers and limits specified in the protocol.
    Those commands should then be used by parameterized tests in the robot framework to test against.
    returns:
    Returns a list of example command strings that can directly be send to the device
    """
    _ = options
    if skip_command_codes is None:
        skip_command_codes = []

    command_examples: List[str] = []
    protocol = _build_protocol(protocol_version, device_type, is_release)
            

    for command_contract in protocol.command_contracts.values():
        if command_contract.command_def is None:
            continue
        if command_contract.code in skip_command_codes:
            continue

        command_examples.extend(
            deduce_command_examples_for_contract(protocol.consts, command_contract)
        )

    return command_examples


def deduce_single_command_example(
    protocol_version: Version,
    device_type: DeviceType,
    command_code: CommandCode,
    is_release: bool = False,
) -> Optional[str]:
    protocol = _build_protocol(protocol_version, device_type, is_release)
    command_contract = protocol.command_contracts.get(command_code)
    if command_contract is None:
        return None

    return deduce_single_command_example_for_contract(protocol.consts, command_contract)
