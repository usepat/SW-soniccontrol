from enum import Enum
from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.schema import Anomaly, SystemState, TransducerState, AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, ControlMode, ConverterType, DeviceParamConstantType, DeviceType, FieldType, IEFieldName, ProtocolType, SonicTextCommandAttrs, UserManualAttrs, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList

# Import latest protocol
#from ..protocol_v2_0_0.protocol_v2_0_0 import Protocol_v2_0_0

# from .commands.commands import (
#     {commands}
# )

# from .types.types import {
#     {types}
# }




class Protocol_Template(ProtocolList):
    """
        TODO: Description of changes in this protocol and why they were necessary


    """
    def __init__(self):
        self._previous_protocol = Protocol_Template()
        assert(False) # Point to the correct protocol


    @property
    def version(self) -> Version:
        assert(False)
        return Version(0, 0, 0)
    
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
    
        return data_types

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return self._previous_protocol.supports_device_type(device_type)

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract | None]:
        command_contract_list: List[CommandContract] = [
            
        ]
        if protocol_type.device_type == DeviceType.DESCALE:
            pass
        if protocol_type.device_type == DeviceType.MVP_WORKER:
            pass
        command_contract_dict: Dict[ICommandCode, CommandContract | None] = {
            command_contract.code: command_contract for command_contract in command_contract_list 
        } 

        return command_contract_dict

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        return {}