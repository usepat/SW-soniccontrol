from enum import Enum
from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.schema import AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, ControlMode, ConverterType, DeviceParamConstantType, DeviceType, FieldType, IEFieldName, ProtocolType, SonicTextCommandAttrs, UserManualAttrs, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.protocols.protocol_v1_0_0.protocol_v1_0_0 import Protocol_v1_0_0
from sonic_protocol.protocols.protocol_v2_0_0.commands import (
    clear_errors, restart_device, get_adc, start_configurator
)
from sonic_protocol.protocols.protocol_v2_0_0.procedure_commands.procedure_commands import all_proc_commands

# Move to protocol 3.0.0
field_type_control_mode = FieldType(
    field_type=ControlMode, 
    converter_ref=ConverterType.ENUM
)
field_control_mode = AnswerFieldDef(
    field_name=EFieldName.INPUT_SOURCE,
    field_type=field_type_control_mode
)

set_control_mode = CommandContract(
    code=CommandCode.SET_INPUT_SOURCE,
    command_def=CommandDef(
        setter_param=CommandParamDef(
            name=EFieldName.INPUT_SOURCE,
            param_type=field_type_control_mode
        ),
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!control", "!control_mode", "set_control_mode"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_control_mode]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to set the input source. Where to get commands from"
    ),
    is_release=True,
    tags=["communication"]
)

get_control_mode = CommandContract(
    code=CommandCode.GET_CONTROL_MODE,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["?control", "?control_mode", "get_control_mode"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_control_mode]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Command to get the input source. Where to get commands from"
    ),
    is_release=True,
    tags=["communication"]
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
        data_types["E_CONTROL_MODE"] = ControlMode
        
        return data_types

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return self._previous_protocol.supports_device_type(device_type)

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract | None]:
        command_contract_list: List[CommandContract] = [clear_errors, restart_device, start_configurator, get_control_mode]
        if protocol_type.device_type == DeviceType.DESCALE:
            command_contract_list.extend([get_adc])
        if protocol_type.device_type == DeviceType.MVP_WORKER:
            command_contract_list.extend(all_proc_commands)
        command_contract_dict: Dict[ICommandCode, CommandContract | None] = {
            command_contract.code: command_contract for command_contract in command_contract_list 
        } 

        # setting the input source should be done in the configurator and not operator
        # Not really. But we changed to control mode?
        command_contract_dict[CommandCode.SET_INPUT_SOURCE] = set_control_mode

        return command_contract_dict

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        return {}