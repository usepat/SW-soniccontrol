from typing import Any, Dict
from sonic_protocol.command_codes import ICommandCode
from sonic_protocol.defs import DeviceParamConstantType, DeviceType, IEFieldName, ProtocolType, Protocol, Version, CommandContract
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

    @property
    @abc.abstractmethod
    def field_name_cls(self) -> type[IEFieldName]:
        ...

    @property
    @abc.abstractmethod
    def command_code_cls(self) -> type[ICommandCode]:
        ...

    @property
    @abc.abstractmethod
    def data_types(self) -> Dict[str, type]:
        ...

    @abc.abstractmethod
    def _get_command_contracts_for(self, protocol_type: ProtocolType) -> Dict[ICommandCode, CommandContract | None]:
        """
            returns a dict, where command contracts are mapped to a command code. 
            Those will overwrite then the command contracts of the previous protocol.
            You can also map None to a command_code to remove the command_contract in the new version.
        """
        ...

    @abc.abstractmethod
    def _get_device_constants_for(self, protocol_type: ProtocolType) -> Dict[DeviceParamConstantType, Any]:
        ...

    @abc.abstractmethod
    def supports_device_type(self, device_type: DeviceType) -> bool:
        """
            Has to define which device types are supported by the protocol.
            Is needed in case, that we will have new devices in the future.
            Also this function should call self.previous_protocol.supports_device_type
        """
        ...

    def build_protocol_for(self, protocol_type: ProtocolType) -> Protocol:
        if not self.supports_device_type(protocol_type.device_type):
            raise Exception("This version of SonicControl does not understand the protocol used by the device. Please update it!")

        if self.previous_protocol is not None and self.previous_protocol.supports_device_type(protocol_type.device_type):
            protocol = self.previous_protocol.build_protocol_for(protocol_type)
        else:
            protocol = Protocol(protocol_type, self.data_types, self.command_code_cls,
                                 self.field_name_cls, command_contracts={})

        if self.version <= protocol_type.version:
            # If this version is newer than the protocol wanted, we do not overwrite and add command contracts

            device_consts = self._get_device_constants_for(protocol_type)
            # map DeviceParamConstantType to str (name of device param constant)
            device_consts_mapped = { key.value: val for key, val in device_consts.items() }
            protocol.consts = attrs.evolve(protocol.consts, ** device_consts_mapped)

            command_contracts = self._get_command_contracts_for(protocol_type)
            for command_code, command_contract in command_contracts.items():
                if command_contract is None:
                    del protocol.command_contracts[command_code]
                elif not protocol_type.is_release:
                    protocol.command_contracts[command_code] = command_contract
                elif command_contract.is_release:
                    protocol.command_contracts[command_code] = command_contract

            protocol.data_types = self.data_types
            protocol.field_name_cls = self.field_name_cls
            protocol.command_code_cls = self.command_code_cls

        return protocol


