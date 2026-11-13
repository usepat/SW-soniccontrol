from enum import Enum
from typing import Any, Dict, List
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.schema import CommandContract, DeviceParamConstantType, DeviceType, IEFieldName, ProtocolType, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_list import ProtocolList

from .commands.commands import (
    PluginVarType, get_plugin_action_info, get_num_plugins, get_plugin_bool_var, get_plugin_float_var,
    get_plugin_info, get_plugin_str_var, get_plugin_uint_var,
    get_plugin_var_info, set_plugin_bool_var, set_plugin_float_var, 
    set_plugin_uint_var, do_plugin_action, enable_plugin, run_proc
)

# Import latest protocol
from ..protocol_v3_1_0.protocol_v3_1_0 import Protocol_v3_1_0

# from .commands.commands import (
#     {commands}
# )

# from .types.types import {
#     {types}
# }


class Protocol_v3_2_0(ProtocolList):
    """
        Each Protocol should contain a doc string comment about:
        changes in this protocol and why they were necessary
    """
    def __init__(self):
        self._previous_protocol = Protocol_v3_1_0()


    @property
    def version(self) -> Version:
        # TODO determine the next version we need
        return Version(3, 2, 0)
    
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
        data_types = {
            "E_PLUGIN_VAR_TYPE": PluginVarType
        }
        data_types.update(self._previous_protocol.custom_data_types)
    
        return data_types

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return self._previous_protocol.supports_device_type(device_type)

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract]:
        command_contract_list: List[CommandContract] = []

        if protocol_type.device_type in [DeviceType.DESCALE, DeviceType.MVP_WORKER, DeviceType.POSTMAN]:
            command_contract_list.extend([
                get_plugin_action_info, get_num_plugins, get_plugin_bool_var, get_plugin_float_var,
                get_plugin_info, get_plugin_str_var, get_plugin_uint_var,
                get_plugin_var_info, set_plugin_bool_var, set_plugin_float_var, 
                set_plugin_uint_var, do_plugin_action, enable_plugin, run_proc
            ])
        command_contract_dict = self._previous_protocol._get_command_contracts_for(protocol_type)
        command_contract_dict.update({
            command_contract.code: command_contract for command_contract in command_contract_list 
        })

        return command_contract_dict

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        constants =  self._previous_protocol._get_device_constants_for(protocol_type)
        return constants