

from typing import Any, Dict

import numpy as np
from sonic_protocol.command_codes import BaseCommandCode
from sonic_protocol.schema import BuildType, CommandContract, DeviceParamConstantType, DeviceType, ICommandCode, IEFieldName, ProtocolType, Timestamp, Version
from sonic_protocol.field_names import BaseFieldName
from sonic_protocol.protocol_list import ProtocolList




class Protocol_base(ProtocolList):
    @property
    def version(self) -> Version:
        return Version(0, 0, 0)
    
    @property
    def previous_protocol(self) -> ProtocolList | None:
        return None
    
    @property
    def field_name_cls(self) -> type[IEFieldName]:
        return BaseFieldName

    @property
    def command_code_cls(self) -> type[ICommandCode]:
        return BaseCommandCode
    
    @property
    def custom_data_types(self) -> Dict[str, type]:
        return {
            "E_DEVICE_TYPE": DeviceType,
            "E_BUILD_TYPE": BuildType,
        }

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return True

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract]:
        return {}

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        return {}
        