from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.schema import  CommandContract, DeviceParamConstantType, DeviceType, IEFieldName, ProtocolType, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList

from ..protocol_v3_0_0.protocol_v3_0_0 import Protocol_v3_0_0
from .commands import debug_test_command

class Protocol_v3_1_0(ProtocolList):
    """
    TODO
    """
    def __init__(self):
        self._previous_protocol = Protocol_v3_0_0()

    @property
    def version(self) -> Version:
        return Version(3, 1, 0)
    
    @property
    def previous_protocol(self) -> ProtocolList | None:
        return self._previous_protocol
    
    @property
    def field_name_cls(self) -> type[IEFieldName]:
        return EFieldName

    @property
    def command_code_cls(self) -> type[ICommandCode]:
        return CommandCode
    
    def convert_command_code_for_validation(self, code: int) -> int:
        return code

    @property
    def custom_data_types(self) -> Dict[str, type]:
        return self._previous_protocol.custom_data_types

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return self._previous_protocol.supports_device_type(device_type)
    
    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract]:
        command_contract_dict = self._previous_protocol._get_command_contracts_for(protocol_type)

        if protocol_type.device_type in [DeviceType.MVP_WORKER, DeviceType.DESCALE]:
            command_contract_dict[debug_test_command.code] = debug_test_command

        # get_adc is deprecated and not used anymore
        # we can remove it "safely", because it is no release command 
        # and was never used programmatically. Only for debugging purposes
        command_contract_dict.pop(CommandCode.GET_ADC, None)

        return command_contract_dict

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        constants =  self._previous_protocol._get_device_constants_for(protocol_type)
        return constants
