from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.schema import  CommandContract, DeviceParamConstantType, DeviceType, IEFieldName, ProtocolType, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList

from ..protocol_v2_0_0.protocol_v2_0_0 import Protocol_v2_0_0

from .commands.commands import (
    get_update_descale_v3_0_0, get_update_worker_v3_0_0,
    set_ramp_gain, get_ramp_v3_0_0, get_uipt_raw, set_log_level_v3_0_0,
    get_logger_list_item, get_logger_list_size, get_connection_status, 
    get_num_tests, get_test_info, run_test, abort_test,
    start_diagnostic_tool, start_operator, set_dac_mV
)
from .types.types import TestInteraction, TestResult


class Protocol_v3_0_0(ProtocolList):
    """
    This protocol changed the units of measurement values and the frequency parameter.
    The reason was, that the unit before were not "correct" since we didn't even have that good of a resolution.
    Additionally the fields are now 16 bits which are way nicer for modbus.
    """
    def __init__(self):
        self._previous_protocol = Protocol_v2_0_0()

    @property
    def version(self) -> Version:
        return Version(3, 0, 0)
    
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
            "E_TEST_RESULT": TestResult,
            "E_TEST_INTERACTION": TestInteraction,
        }
        data_types.update(self._previous_protocol.custom_data_types)
    
        # delete deprecated data_types
        data_types.pop("E_LOGGER_NAME") # enum got replaced by a string for more flexibility

        return data_types

    def supports_device_type(self, device_type: DeviceType) -> bool:
        if device_type == DeviceType.POSTMAN:
            return True
        if device_type == DeviceType.DIAGNOSTICS_TOOL:
            return True
        return self._previous_protocol.supports_device_type(device_type)

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract]:        
        if protocol_type.device_type == DeviceType.POSTMAN:
            command_contracts = self._get_command_contracts_for(ProtocolType(protocol_type.version, DeviceType.MVP_WORKER))
            
            command_contracts[CommandCode.GET_CONNECTION_STATUS] = get_connection_status
            return command_contracts 
        
        if protocol_type.device_type == DeviceType.DIAGNOSTICS_TOOL:
            command_contracts = self._get_command_contracts_for(ProtocolType(protocol_type.version, DeviceType.MVP_WORKER))

            diagnostics_tool_command_codes = [
                CommandCode.GET_PROTOCOL,
                CommandCode.GET_INFO,
                CommandCode.GET_HELP,
                CommandCode.SET_FLASH_115200,
                CommandCode.SET_FLASH_9600,
                CommandCode.SET_FLASH_USB,
                CommandCode.SET_LOG_LEVEL,
                CommandCode.GET_LOGGER_LIST_SIZE,
                CommandCode.GET_LOGGER_LIST_ITEM,
                CommandCode.SET_DATETIME,
                CommandCode.GET_DATETIME,
                CommandCode.RESTART_DEVICE,
                CommandCode.START_CONFIGURATOR,
                CommandCode.START_DIAGNOSTIC_TOOL,
                CommandCode.START_OPERATOR,
                CommandCode.GET_ERROR_HISTO_SIZE,
                CommandCode.POP_ERROR_HISTO_MESSAGE,
                CommandCode.GET_NUM_TESTS,
                CommandCode.GET_TEST_INFO,
                CommandCode.RUN_TEST,
                CommandCode.ABORT_TEST,
            ]
            return { key: value for key, value in command_contracts.items() if key in diagnostics_tool_command_codes }

        command_contract_list: List[CommandContract] = [
            get_logger_list_size,
            get_logger_list_item,
            get_num_tests, # FIXME: test commands should only be in Diagnostics Tool protocol
            get_test_info,
            run_test,
            abort_test,
            start_diagnostic_tool,
            start_operator,
        ]
        if protocol_type.device_type == DeviceType.DESCALE:
            command_contract_list.extend([get_update_descale_v3_0_0])
        if protocol_type.device_type == DeviceType.MVP_WORKER:
            command_contract_list.extend([
                get_update_worker_v3_0_0,
                set_ramp_gain,
                get_uipt_raw,
                set_dac_mV
            ])

        command_contract_dict = self._previous_protocol._get_command_contracts_for(protocol_type)
        command_contract_dict.update({
            command_contract.code: command_contract for command_contract in command_contract_list 
        })

        # overwrite existing contracts
        if CommandCode.GET_RAMP in command_contract_dict:
            command_contract_dict[CommandCode.GET_RAMP] = get_ramp_v3_0_0
            
        command_contract_dict[CommandCode.SET_LOG_LEVEL] = set_log_level_v3_0_0

        # delete unused commands
        command_contract_dict.pop(CommandCode.GET_DATETIME_PICO, None)
        command_contract_dict.pop(CommandCode.SET_COM_PROT, None)
        command_contract_dict.pop(CommandCode.SET_TERMINATION, None)

        return command_contract_dict

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        assert self.previous_protocol

        match protocol_type.device_type:
            case DeviceType.POSTMAN:
                return self._get_device_constants_for(ProtocolType(protocol_type.version, DeviceType.MVP_WORKER))
            # case DeviceType.MVP_WORKER:
            #     # Changed from Hz to hHz
            #     return { DeviceParamConstantType.MAX_FREQUENCY: 200000, DeviceParamConstantType.MIN_FREQUENCY: 1000 }
            case _:
                return self.previous_protocol._get_device_constants_for(protocol_type)
