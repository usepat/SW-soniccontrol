from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import CommandContract, DeviceParamConstantType, DeviceType, ProtocolType, Version
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.protocols.protocol_v1_0_0.protocol_v1_0_0 import Protocol_v1_0_0
from sonic_protocol.protocols.protocol_v2_0_0.commands import (
    clear_errors, restart_device
)


class Protocol_v2_0_0(ProtocolList):
    def __init__(self):
        self._previous_protocol = Protocol_v1_0_0()

    @property
    def version(self) -> Version:
        return Version(2, 0, 0)
    
    @property
    def previous_protocol(self) -> ProtocolList | None:
        return self._previous_protocol

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return self._previous_protocol.supports_device_type(device_type)

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[CommandCode, CommandContract | None]:
        command_contract_list: List[CommandContract] = [clear_errors, restart_device]
        return { command_contract.code: command_contract for command_contract in command_contract_list } 
    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        return {}