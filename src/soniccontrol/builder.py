import logging
from typing import Any, Dict


from sonic_protocol.protocol import protocol_list as operator_protocol_factory
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.schema import BuildType, DeviceType, ProtocolType, Version
from sonic_protocol.field_names import EFieldName, IEFieldName
from soniccontrol.communication.connection import Connection
from soniccontrol.communication.legacy_communicator import LegacyCommunicator
from soniccontrol.communication.serial_communicator import SerialCommunicator
from soniccontrol.sonic_device import FirmwareInfo, SonicDevice
import sonic_protocol.python_parser.commands as cmds


class DeviceBuilder:
    def __init__(self, protocol_factories: Dict[DeviceType, ProtocolList] = {}, logger: logging.Logger = logging.getLogger()):
        self._logger = logger
        self._builder_logger = logging.getLogger(logger.name + "." + DeviceBuilder.__name__)
        self._protocol_factories = protocol_factories


    async def _update_info(self, device: SonicDevice) -> None:
        info = device.info
        result_dict: Dict[IEFieldName, Any] = {}
        if device.has_command(cmds.GetInfo()):
            answer = await device.execute_command(cmds.GetInfo(), raise_exception=False, should_log=False)
            result_dict.update(answer.field_value_dict)
        
        info.firmware_version = result_dict.get(EFieldName.FIRMWARE_VERSION, Version(0, 0, 0))
        info.hardware_version = result_dict.get(EFieldName.HARDWARE_VERSION, Version(0, 0, 0))

        self._builder_logger.info("Device type: %s", info.device_type)
        self._builder_logger.info("Firmware version: %s", info.firmware_version)
        self._builder_logger.info("Firmware info: %s", info.firmware_info)
        self._builder_logger.info("Protocol version: %s", info.protocol_version)


    async def build_legacy_crystal(self, connection: Connection) -> SonicDevice:
        protocol_version: Version = Version(1, 0, 0)
        device_type: DeviceType = DeviceType.CRYSTAL
        is_release: bool = True

        comm = LegacyCommunicator(_logger=self._logger)
        await comm.open_communication(connection)
        
        # create device
        self._builder_logger.info("The device is a %s with a %s build and understands the protocol %s", device_type.value, "release", str(protocol_version))
        protocol = operator_protocol_factory.build_protocol_for(ProtocolType(protocol_version, device_type, is_release))
            
        info = FirmwareInfo()
        device = SonicDevice(comm, protocol, info, logger=self._logger)
    
        # update info
        info.device_type = device_type
        info.protocol_version = protocol_version
        info.is_release = is_release
        await self._update_info(device)

        return device


    async def build_amp(self, connection: Connection, try_deduce_protocol_used: bool = True) -> SonicDevice:
        """!
        @param open_in_rescue_mode This param can be set to False, so that it does not try to deduce which protocol to use. Used for the rescue window
        """
        
        protocol_version: Version = Version(0, 0, 0)
        device_type: DeviceType = DeviceType.UNKNOWN
        is_release: bool = True

        comm = SerialCommunicator(logger=self._logger) #type: ignore
        await comm.open_communication(connection)

        self._builder_logger.debug("Serial connection is open, start building device")

        info = FirmwareInfo()
        # deduce the right protocol version, device_type and build_type
        if try_deduce_protocol_used:
            self._builder_logger.debug("Try to figure out which protocol to use with ?protocol")

            protocol_version: Version = Version(1, 0, 0)
            protocol = operator_protocol_factory.build_protocol_for(ProtocolType(protocol_version, device_type, is_release))

            device = SonicDevice(comm, protocol, info, logger=self._logger)
            answer = await device.execute_command(cmds.GetProtocol(), raise_exception=False)
            if answer.valid:
                assert(EFieldName.DEVICE_TYPE in answer.field_value_dict)
                assert(EFieldName.PROTOCOL_VERSION in answer.field_value_dict)
                assert(EFieldName.IS_RELEASE in answer.field_value_dict)
                device_type = answer.field_value_dict[EFieldName.DEVICE_TYPE]
                protocol_version = answer.field_value_dict[EFieldName.PROTOCOL_VERSION]
                is_release = answer.field_value_dict[EFieldName.IS_RELEASE] == BuildType.RELEASE.name
            else:
                self._builder_logger.debug("Device does not understand ?protocol command")
        else:
            self._builder_logger.warning("Device uses unknown protocol")

        # create device
        self._builder_logger.info("The device is a %s with a %s build and understands the protocol %s", device_type.value, "release" if is_release else "build", str(protocol_version))
        
        protocol_factory = self._protocol_factories.get(device_type, operator_protocol_factory)
        protocol = protocol_factory.build_protocol_for(ProtocolType(protocol_version, device_type, is_release))
            
        # If we did not deduce the protocol then we should also not try to validate the answers, because we do not know how they look like
        device = SonicDevice(comm, protocol, info, 
                             should_validate_answers=try_deduce_protocol_used, logger=self._logger)
    
        # update info
        info.device_type = device_type
        info.protocol_version = protocol_version
        info.is_release = is_release
        await self._update_info(device)

        return device
