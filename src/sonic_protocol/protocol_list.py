from typing import Any, Dict
from sonic_protocol.defs import DeviceParamConstantType, DeviceType, ProtocolInfo, Protocol, Version, CommandContract, CommandCode
import abc
import attrs



class ProtocolList:
    """
        This class is the base class for protocol classes.
        They are like a linked list. Each protocol points to the previous versions.
        On constructing the protocol, it does a recursive call, where it constructs the protocol from the previous version and then modifies it.
    """
    @property
    @abc.abstractmethod
    def version(self) -> Version:
        ...
    
    @property
    @abc.abstractmethod
    def previous_protocol(self) -> "ProtocolList | None":
        ...

    @abc.abstractmethod
    def _get_command_contracts_for(self, info: ProtocolInfo) -> Dict[CommandCode, CommandContract | None]:
        """
            returns a dict, where command contracts are mapped to a command code. 
            Those will overwrite then the command contracts of the previous protocol.
            You can also map None to a command_code to remove the command_contract in the new version.
        """
        ...

    @abc.abstractmethod
    def _get_device_constants_for(self, info: ProtocolInfo) -> Dict[DeviceParamConstantType, Any]:
        ...

    @abc.abstractmethod
    def supports_device_type(self, device_type: DeviceType) -> bool:
        """
            Has to define which device types are supported by the protocol.
            Is needed in case, that we will have new devices in the future.
            Also this function should call self.previous_protocol.supports_device_type
        """
        ...

    def build_protocol_for2(self, device_type: DeviceType, version: Version, is_release: bool = True, opts: str | None = None) -> Protocol:
        return self.build_protocol_for(ProtocolInfo(version, device_type, is_release, opts))

    def build_protocol_for(self, info: ProtocolInfo) -> Protocol:
        if not self.supports_device_type(info.device_type):
            raise Exception("This version of SonicControl does not understand the protocol used by the device. Please update it!")

        if self.previous_protocol is not None and self.previous_protocol.supports_device_type(info.device_type):
            protocol = self.previous_protocol.build_protocol_for(info)
            assert protocol is not None
        else:
            protocol = Protocol(info, {})

        if self.version <= info.version:
            device_consts = self._get_device_constants_for(info)
            # map DeviceParamConstantType to str (name of device param constant)
            device_consts_mapped = { key.value: val for key, val in device_consts.items() }
            protocol.consts = attrs.evolve(protocol.consts, ** device_consts_mapped)

            command_contracts = self._get_command_contracts_for(info)
            for command_code, command_contract in command_contracts.items():
                if command_contract is None:
                    del protocol.command_contracts[command_code]
                elif not info.is_release:
                    protocol.command_contracts[command_code] = command_contract
                elif command_contract.is_release and info.is_release:
                    protocol.command_contracts[command_code] = command_contract

        return protocol


