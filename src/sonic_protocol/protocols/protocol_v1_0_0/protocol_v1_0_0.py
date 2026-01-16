from enum import Enum
from typing import Any, Dict
import numpy as np
from sonic_protocol.protocols.contract_generators import create_version_field
from sonic_protocol.schema import (
    BuildType, CommunicationChannel, CommunicationProtocol, ConverterType, DeviceParamConstantType, FieldType, IEFieldName, InputSource, LoggerName, Loglevel, Procedure, 
    ProtocolType, Signal, SonicTextCommandAttrs, Activation, UserManualAttrs, Version, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract, DeviceType, Waveform,
)
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.protocols.protocol_base.protocol_base import Protocol_base
from sonic_protocol.protocols.protocol_v1_0_0.generic_commands.generic_commands import field_device_type
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocols.protocol_v1_0_0.procedure_commands.procedure_commands import all_proc_commands, duty_cycle_proc_commands
from sonic_protocol.protocol_list import ProtocolList

from sonic_protocol.protocols.protocol_v1_0_0.crystal_commands.crystal_command_contracts import crystal_commands, crystal_constants
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.descaler_commands import descale_command_contract_list
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_commands import transducer_command_contract_list
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.generic_commands import transducer_generic_command_contract_list
from sonic_protocol.protocols.protocol_v1_0_0.unknown_commands.unknown_commands import unknown_command_contract_list
from sonic_protocol.protocols.protocol_v1_0_0.flashing_commands.flashing_commands import flashing_command_contracts
from sonic_protocol.protocols.protocol_v1_0_0.generic_commands.generic_commands import get_info, generic_command_contract_list
from sonic_protocol.protocols.protocol_v1_0_0.communication_commands.communication_commands import communication_command_contract_list


# TODO: move version and fields into own files 

# Version instance
version = Version(major=1, minor=0, patch=0)

"""!
    The ?protocol command is the most important command
    Without ?protocol there is no way to determine which protocol is used.
    So this command is needed.
    There should also only exist one version of this command. Because else determining the protocol version would be a nightmare.
    If you want to extend the ?protocol command. consider adding other commands
"""



get_protocol = CommandContract(
    code=CommandCode.GET_PROTOCOL,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier="?protocol"
        )
    ),
    answer_def=AnswerDef(
        fields=[
            field_device_type,
            create_version_field(EFieldName.PROTOCOL_VERSION),
            AnswerFieldDef(
                field_name=EFieldName.IS_RELEASE, 
                field_type=FieldType(BuildType, converter_ref=ConverterType.ENUM), 
            ),
            AnswerFieldDef(
                EFieldName.ADDITIONAL_OPTIONS,
                str,
                user_manual_attrs=UserManualAttrs("additional options used for future extensions of the protocol")
            )
        ]
    ),
    is_release=True,
    user_manual_attrs= UserManualAttrs(
        description="Used to retrieve the protocol version the device understands"
    )
)

class Protocol_v1_0_0(ProtocolList):
    def __init__(self):
        self._previous_protocol = Protocol_base()

    @property
    def version(self) -> Version:
        return Version(1, 0, 0)
    
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
        data_types = {
            "E_SIGNAL": Signal,
            "E_COMMUNICATION_CHANNEL": CommunicationChannel,
            "E_COMMUNICATION_PROTOCOL": CommunicationProtocol,
            "E_INPUT_SOURCE": InputSource,
            "E_PROCEDURE": Procedure,
            "E_WAVEFORM": Waveform,
            "E_LOG_LEVEL": Loglevel,
            "E_LOGGER_NAME": LoggerName,
            "E_ACTIVATION": Activation,
        }
        data_types.update(self._previous_protocol.custom_data_types)
        return data_types

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return device_type in [DeviceType.MVP_WORKER, DeviceType.DESCALE, DeviceType.CRYSTAL, DeviceType.UNKNOWN]

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract | None]:
        command_contract_list =  [] 

        match protocol_type.device_type:
            case DeviceType.DESCALE:
                command_contract_list.extend(descale_command_contract_list)
                command_contract_list.extend(duty_cycle_proc_commands)
            case DeviceType.MVP_WORKER: 
                #command_contract_list.append(transducer_command_contract_list)
                command_contract_list.extend(transducer_command_contract_list)
                command_contract_list.extend(all_proc_commands)
            case DeviceType.UNKNOWN:
                command_contract_list.extend([get_protocol])
                command_contract_list.extend(unknown_command_contract_list)
            case DeviceType.CRYSTAL:
                command_contract_list.append(get_info)
                command_contract_list.extend(crystal_commands)
            case _:
                assert False, "Unreachable"

        if protocol_type.device_type in [DeviceType.DESCALE, DeviceType.MVP_WORKER]:
            command_contract_list.extend([get_protocol])
            command_contract_list.extend(transducer_generic_command_contract_list)
            command_contract_list.extend(communication_command_contract_list)
            command_contract_list.extend(generic_command_contract_list)
            command_contract_list.extend(flashing_command_contracts)

        return { command_contract.code: command_contract for command_contract in command_contract_list }

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        match protocol_type.device_type:
            case DeviceType.DESCALE:
                return { DeviceParamConstantType.MAX_GAIN: 101 }
            case DeviceType.CRYSTAL:
                return crystal_constants
            case _:
                return {}
