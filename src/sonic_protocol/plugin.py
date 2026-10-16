from typing import List, Set

import attrs

from .protocol import LatestProtocol
from .schema import DeviceType
from .protocol_list import ProtocolList


@attrs.define(hash=True)
class ProtocolPlugin:
    device_type: DeviceType
    protocol_factory: ProtocolList



class ProtocolPluginRegistry:
    _registered_plugins: Set[ProtocolPlugin] = set()

    @staticmethod
    def register_plugin(plugin: ProtocolPlugin):
        ProtocolPluginRegistry._registered_plugins.add(plugin)

    @staticmethod
    def get_plugins() -> List[ProtocolPlugin]:
        return list(ProtocolPluginRegistry._registered_plugins)
    



