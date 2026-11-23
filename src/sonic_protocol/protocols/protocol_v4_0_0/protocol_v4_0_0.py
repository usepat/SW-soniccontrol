from enum import Enum
from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.schema import Anomaly, SystemState, TransducerState, AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, ControlMode, DeviceParamConstantType, DeviceType, FieldType, IEFieldName, ProtocolType, SonicTextCommandAttrs, UserManualAttrs, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList

# Import latest protocol
from ..protocol_v3_2_0.protocol_v3_2_0 import Protocol_v3_2_0
from .commands.commands import (
    get_duty_cycle, save_log_levels, set_duty_cycle_proc, set_duty_cycle_disable_psu_during_off,
)

# from .commands.commands import (
#     {commands}
# )

# from .types.types import {
#     {types}
# }


class Protocol_v4_0_0(ProtocolList):
    """
        Added 115200 option to set modbus_baudrate command.
        Added duty-cycle procedure and PSU-off settings.
        Added a command to save the current log levels.
    """
    def __init__(self):
        self._previous_protocol = Protocol_v3_2_0()


    @property
    def version(self) -> Version:
        return Version(4, 0, 0)
    
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
        data_types = {}
        data_types.update(self._previous_protocol.custom_data_types)
    
        return data_types

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return self._previous_protocol.supports_device_type(device_type)

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract]:
        command_contract_list: List[CommandContract] = [
            
        ]
        if protocol_type.device_type == DeviceType.DESCALE:
            pass
        if protocol_type.device_type == DeviceType.MVP_WORKER:
            pass
        command_contract_list.extend([
            get_duty_cycle, save_log_levels, set_duty_cycle_proc, set_duty_cycle_disable_psu_during_off,
        ])
        command_contract_dict = self._previous_protocol._get_command_contracts_for(protocol_type)
        command_contract_dict.update({
            command_contract.code: command_contract for command_contract in command_contract_list 
        })

        if command_contract_dict.get(CommandCode.SET_MODBUS_BAUDRATE) is not None:
            command_def = command_contract_dict[CommandCode.SET_MODBUS_BAUDRATE].command_def
            assert command_def is not None
            assert command_def.setter_param is not None
            allowed_values = command_def.setter_param.param_type.allowed_values
            assert allowed_values is not None
            command_contract_dict[CommandCode.SET_MODBUS_BAUDRATE].command_def.setter_param.param_type.allowed_values = (*allowed_values, 115200)

        return command_contract_dict

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        constants =  self._previous_protocol._get_device_constants_for(protocol_type)
        constants[DeviceParamConstantType.MIN_DUTY_CYCLE_T_OFF] = 0
        return constants