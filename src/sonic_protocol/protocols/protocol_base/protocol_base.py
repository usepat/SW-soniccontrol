

from typing import Any, Dict

import numpy as np
from sonic_protocol.defs import CommandContract, DeviceParamConstantType, DeviceType, ICommandCode, IEFieldName, ProtocolType, Timestamp, Version
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
        return IEFieldName

    @property
    def command_code_cls(self) -> type[ICommandCode]:
        return ICommandCode
    
    @property
    def data_types(self) -> Dict[str, type]:
        return {
            "UINT8": np.uint8,
            "UINT16": np.uint16,
            "UINT32": np.uint32,
            "FLOAT": float,
            "STRING": str,
            "BOOL": bool,
            "TIMESTAMP": Timestamp,
            "VERSION": Version,
            "E_DEVICE_TYPE": DeviceType,
            
        }

    def supports_device_type(self, device_type: DeviceType) -> bool:
        return True

    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract | None]:
        return {}

    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        return {}
        