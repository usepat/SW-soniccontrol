import logging
from typing import Any, Dict


from sonic_protocol import protocol
from sonic_protocol.defs import DeviceType, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_builder import ProtocolBuilder
from soniccontrol.communication.communicator import Communicator
from soniccontrol.sonic_device import (
    Info,
    SonicDevice,
)
import sonic_protocol.python_parser.commands as cmds


class DeviceBuilder:

    async def build_amp(self, comm: Communicator, logger: logging.Logger = logging.getLogger(), open_in_rescue_mode: bool = False) -> SonicDevice:
        """!
        @param open_in_rescue_mode This param can be set to False, so that it does not try to deduce which protocol to use. Used for the rescue window
        """
        
        builder_logger = logging.getLogger(logger.name + "." + DeviceBuilder.__name__)
        
        # connect
        await comm.connection_opened.wait()
        builder_logger.debug("Serial connection is open, start building device")

        result_dict: Dict[EFieldName, Any] = {}
        
        protocol_version: Version = Version(0, 0, 0)
        device_type: DeviceType = DeviceType.UNKNOWN
        is_release: bool = True

        info = Info()

        protocol_builder = ProtocolBuilder(protocol.protocol)

        # deduce the right protocol version, device_type and build_type
        if not open_in_rescue_mode:
            builder_logger.debug("Try to figure out which protocol to use with ?protocol")

            protocol_version: Version = Version(1, 0, 0)
            base_command_lookups = protocol_builder.build(device_type, protocol_version, is_release)

            device = SonicDevice(comm, base_command_lookups, info, logger=logger)
            answer = await device.execute_command(cmds.GetProtocol())
            if answer.valid:
                assert(EFieldName.DEVICE_TYPE in answer.field_value_dict)
                assert(EFieldName.PROTOCOL_VERSION in answer.field_value_dict)
                assert(EFieldName.IS_RELEASE in answer.field_value_dict)
                device_type = answer.field_value_dict[EFieldName.DEVICE_TYPE]
                protocol_version = answer.field_value_dict[EFieldName.PROTOCOL_VERSION]
                is_release = answer.field_value_dict[EFieldName.IS_RELEASE]
            else:
                builder_logger.debug("Device does not understand ?protocol command")
        else:
            builder_logger.warning("Device uses unknown protocol")

        # create device
        builder_logger.info("The device is a %s with a %s build and understands the protocol %s", device_type.value, "release" if is_release else "build", str(protocol_version))
        command_lookups = protocol_builder.build(device_type, protocol_version, is_release)

        device = SonicDevice(comm, command_lookups, info, 
                             is_in_rescue_mode=open_in_rescue_mode, logger=logger)

        # update info
        if protocol_version >= Version(1, 0, 0):
            answer = await device.execute_command(cmds.GetInfo(), should_log=False)
            result_dict.update(answer.field_value_dict)
        
        info.device_type = device_type
        info.protocol_version = protocol_version
        info.is_release = is_release
        info.firmware_version = result_dict.get(EFieldName.FIRMWARE_VERSION, Version(0, 0, 0))
        info.hardware_version = result_dict.get(EFieldName.HARDWARE_VERSION, Version(0, 0, 0))
        # TODO: firmware info

        builder_logger.info("Device type: %s", info.device_type)
        builder_logger.info("Firmware version: %s", info.firmware_version)
        builder_logger.info("Firmware info: %s", info.firmware_info)
        builder_logger.info("Protocol version: %s", info.protocol_version)

        return device
