from sonic_protocol.protocol import protocol_list
from sonic_protocol.schema import DeviceType, ProtocolType, Version
from sonic_protocol.user_manual_compiler.manual_compiler import ManualCompiler


class BetterManualCompiler(ManualCompiler):
    def compile_manual_for_specific_device(self, device_type: DeviceType, protocol_version: Version, is_release: bool = True) -> str:
        try:
            protocol = protocol_list.build_protocol_for(ProtocolType(protocol_version, device_type, is_release))
        except Exception as e:
            return "Error constructing manual: " + str(e)

        return "" 