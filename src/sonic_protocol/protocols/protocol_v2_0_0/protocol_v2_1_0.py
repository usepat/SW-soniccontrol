import copy
from enum import Enum
from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.protocols.protocol_v2_0_0.protocol_v2_0_0 import Protocol_v2_0_0
from sonic_protocol.schema import Anomaly, AnswerFieldDef, CommandContract, ConverterType, DeviceParamConstantType, DeviceType, FieldType, IEFieldName, ProtocolType, SystemState, TransducerState, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_commands import (
    get_update_worker
) 

get_update_worker_v2_1_0 = copy.deepcopy(get_update_worker)

field_anomaly_detection = AnswerFieldDef(
    field_name=EFieldName.ANOMALY_DETECTION,
    field_type=FieldType(field_type=Anomaly, converter_ref=ConverterType.ENUM),
)

field_system_state = AnswerFieldDef(
    field_name=EFieldName.TRANSDUCER_STATE,
    field_type=FieldType(SystemState, converter_ref=ConverterType.ENUM),
)

field_transducer_state = AnswerFieldDef(
    field_name=EFieldName.SYSTEM_STATE,
    field_type=FieldType(TransducerState, converter_ref=ConverterType.ENUM),
)

get_update_worker_v2_1_0.answer_def.fields.extend([
    field_anomaly_detection, field_transducer_state
])

for idx, field in enumerate(get_update_worker_v2_1_0.answer_def.fields):
    if field.field_name == EFieldName.ERROR_CODE:
        get_update_worker_v2_1_0.answer_def.fields[idx] = field_transducer_state
        break


class Protocol_v2_1_0(ProtocolList):
    """
        TODO: Description of changes in this protocol and why they were necessary


    """
    def __init__(self):
        self._previous_protocol = Protocol_v2_0_0()

    @property
    def version(self) -> Version:
        return Version(2, 1, 0)
    
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
        data_types["E_ANOMALY"] = Anomaly
        data_types["E_TRANSDUCER_STATE"] = TransducerState
        data_types["E_SYSTEM_STATE"] = SystemState
        
        return data_types

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return self._previous_protocol.supports_device_type(device_type)

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract | None]:
        command_contract_list: List[CommandContract] = []
        if protocol_type.device_type == DeviceType.MVP_WORKER:
            command_contract_list.extend([get_update_worker_v2_1_0])
        command_contract_dict: Dict[ICommandCode, CommandContract | None] = {
            command_contract.code: command_contract for command_contract in command_contract_list 
        } 

        return command_contract_dict

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        return {}