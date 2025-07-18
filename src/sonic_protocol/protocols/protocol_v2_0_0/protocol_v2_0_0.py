from enum import Enum
from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.schema import CommandContract, DeviceParamConstantType, DeviceType, IEFieldName, ProtocolType, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.protocols.protocol_v1_0_0.protocol_v1_0_0 import Protocol_v1_0_0
from sonic_protocol.protocols.protocol_v2_0_0.commands import (
    clear_errors, restart_device, get_adc
)


class Protocol_v2_0_0(ProtocolList):
    """
        TODO: Description of changes in this protocol and why they were necessary


    """
    def __init__(self):
        self._previous_protocol = Protocol_v1_0_0()

    @property
    def version(self) -> Version:
        return Version(2, 0, 0)
    
    @property
    def previous_protocol(self) -> ProtocolList | None:
        return self._previous_protocol
    
    @property
    def field_name_cls(self) -> type[IEFieldName]:
        return EFieldName

    @property
    def command_code_cls(self) -> type[ICommandCode]:
        return CommandCode

    @property
    def custom_data_types(self) -> Dict[str, type]:
        data_types = {}
        data_types.update(self._previous_protocol.custom_data_types)

        # We remove Input source, because we refactored it in the firmware into ControlMode and CommunicationChannel
        data_types.pop("E_INPUT_SOURCE")
        
        return data_types

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return self._previous_protocol.supports_device_type(device_type)

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract | None]:
        command_contract_list: List[CommandContract] = [clear_errors, restart_device]
        if protocol_type.device_type == DeviceType.DESCALE:
            command_contract_list.extend([get_adc])

        command_contract_dict: Dict[ICommandCode, CommandContract | None] = {
            command_contract.code: command_contract for command_contract in command_contract_list 
        } 

        # setting the input source should be done in the configurator and not operator
        command_contract_dict[CommandCode.SET_INPUT_SOURCE] = None

        return command_contract_dict

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        return {}