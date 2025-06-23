from enum import Enum
from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.defs import CommandContract, DeviceParamConstantType, DeviceType, ProtocolType, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.protocols.protocol_v1_0_0.protocol_v1_0_0 import Protocol_v1_0_0
from sonic_protocol.protocols.protocol_v2_0_0.commands import (
    clear_errors, restart_device, get_adc
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
    
    @property
    def FieldName(self) -> type[Enum]:
        return EFieldName

    @property
    def CommandCode(self) -> type[ICommandCode]:
        return CommandCode

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return self._previous_protocol.supports_device_type(device_type)

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract | None]:
        command_contract_list: List[CommandContract] = [clear_errors, restart_device]
        if protocol_type.device_type == DeviceType.DESCALE:
            command_contract_list.extend([get_adc])
        return { command_contract.code: command_contract for command_contract in command_contract_list } 
    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        return {}