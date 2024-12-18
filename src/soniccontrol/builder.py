import asyncio
import logging
from typing import Any, Dict, List, Union


from sonic_protocol import protocol
from sonic_protocol.defs import CommandCode, DeviceType, Version
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_builder import CommandLookUpTable, ProtocolBuilder
from soniccontrol.command import LegacyAnswerValidator, LegacyCommand
from soniccontrol.command_executor import CommandExecutor
from soniccontrol.commands import CommandSet, CommandSetLegacy
from soniccontrol.communication.communicator import Communicator
from soniccontrol.communication.serial_communicator import LegacySerialCommunicator
from soniccontrol.sonic_device import (
    Info,
    SonicDevice,
)
import sonic_protocol.python_parser.commands as cmds


class DeviceBuilder:
    def _parse_legacy_handshake(self, ser: LegacySerialCommunicator) -> Dict[str, Any]:
        init_command = LegacyCommand(
            estimated_response_time=0.5,
            _validators=[
                LegacyAnswerValidator(pattern=r".*(khz|mhz).*", relay_mode=str),
                LegacyAnswerValidator(
                    pattern=r".*freq[uency]*\s*=?\s*([\d]+).*", frequency=int
                ),
                LegacyAnswerValidator(pattern=r".*gain\s*=?\s*([\d]+).*", gain=int),
                LegacyAnswerValidator(
                    pattern=r".*signal.*(on|off).*",
                    signal=lambda b: b.lower() == "on",
                ),
                LegacyAnswerValidator(
                    pattern=r".*(serial|manual).*",
                    communication_mode=str,
                ),
            ],
            serial_communication=ser,
        )
        init_command.answer.receive_answer(
            ser.handshake_result
        )
        init_command.validate()
        
        return init_command.status_result
        

    async def _deduce_protocol_of_legacy_device(self, comm: Communicator) -> Dict[str, Any]:
        """!
            We basically try to send ?info, ?type and ?.
            Then we try to iterate through all possible combinations of device types and protocol versions.
            We look if we find a validator that can parse the response and then save it in result_dict

            @return Returns a dict with all the information that were successfully parsed
        """
        
        result_dict: Dict[str, Any] = {}

        commands = ["?info", "?type", "?"]
        command_codes = [CommandCode.GET_INFO, CommandCode.GET_TYPE, CommandCode.QUESTIONMARK]
        coroutines_requests = [comm.send_and_wait_for_response(req) for req in commands]
        responses = await asyncio.gather(*coroutines_requests)
        responses = zip(command_codes, responses)

        versions: List[Version] = [
            Version(0, 3, 0),
            Version(0, 4, 0),
            Version(0, 5, 0),
        ]
        legacy_device_types = [
            DeviceType.UNKNOWN,
            DeviceType.CATCH,
            DeviceType.DESCALE,
            DeviceType.WIPE,
        ]
        for version in versions:
            for device_type in legacy_device_types:
                command_lookups = ProtocolBuilder(protocol.protocol).build(device_type, version, True)
                for command_code, response in responses:
                    if command_code not in command_lookups:
                        continue
                    validator = command_lookups[command_code].answer_validator
                    answer = validator.validate(response)
                    if answer.valid:
                        result_dict.update(**answer.value_dict)

        if "firmware_version" in result_dict:
            result_dict.update(protocol_version=result_dict["firmware_version"])             
        return result_dict


    async def build_amp(self, comm: Communicator, commands: Union[CommandSet, CommandSetLegacy], logger: logging.Logger = logging.getLogger(), try_deduce_protocol: bool = True) -> SonicDevice:
        """!
        @param try_deduce_protocol This param can be set to False, so that it does not try to deduce which protocol to use. Used for the rescue window
        """
        
        builder_logger = logging.getLogger(logger.name + "." + DeviceBuilder.__name__)
        
        # connect
        await comm.connection_opened.wait()
        builder_logger.debug("Serial connection is open, start building device")

        handshake: Dict[str, Any] = self._parse_legacy_handshake(comm) if isinstance(comm, LegacySerialCommunicator) else {}
        result_dict: Dict[EFieldName, Any] = { EFieldName(k): v for k, v in handshake.items() }
        
        device_type: DeviceType = DeviceType.UNKNOWN
        protocol_version: Version = Version(1, 0, 0)
        is_release: bool = True
        protocol_builder = ProtocolBuilder(protocol.protocol)
        base_command_lookups = protocol_builder.build(device_type, protocol_version, is_release)

        executor: CommandExecutor = CommandExecutor(base_command_lookups, comm)

        # deduce the right protocol version, device_type and build_type
        if try_deduce_protocol:
            builder_logger.debug("Try to figure out which protocol to use with ?protocol")
            answer = await executor.send_command(cmds.GetProtocol())
            if answer.valid:
                assert(EFieldName.DEVICE_TYPE in answer.field_value_dict)
                assert(EFieldName.PROTOCOL_VERSION in answer.field_value_dict)
                assert(EFieldName.IS_RELEASE in answer.field_value_dict)
                device_type = answer.field_value_dict[EFieldName.DEVICE_TYPE]
                protocol_version = answer.field_value_dict[EFieldName.PROTOCOL_VERSION]
                is_release = answer.field_value_dict[EFieldName.IS_RELEASE]
                result_dict.update(answer.field_value_dict)
            else:
                builder_logger.debug("Device does not understand ?protocol command. Try to figure out which device it is with ?info, ?type, ?")
                parsed_values = await self._deduce_protocol_of_legacy_device(comm)
                device_type = parsed_values.get("device_type", DeviceType.UNKNOWN)
                protocol_version = parsed_values.get("protocol_version", Version(0, 0, 0))
                is_release = True # old devices are not anymore in development. There exists only release versions of them
                result_dict.update({ EFieldName(k): v for k, v in parsed_values.items() })
                # TODO: we need to support strings that are also not in the enum EFieldName

        # create device
        builder_logger.info("The device is a %s with a %s build and understands the protocol %s", device_type.value, "release" if is_release else "build", str(protocol_version))
        command_lookups = protocol_builder.build(device_type, protocol_version, is_release)

        info = Info()
        device = SonicDevice(comm, command_lookups, info, logger)
    
        if device.command_executor.has_command(cmds.GetUpdate()):
            await device.execute_command(cmds.GetUpdate())

        # update info
        if protocol_version >= Version(1, 0, 0):
            answer = await device.execute_command(cmds.GetInfo(), should_log=False)
            result_dict.update(answer.field_value_dict)
        
        info.device_type = result_dict.get(EFieldName.DEVICE_TYPE, DeviceType.UNKNOWN)
        info.firmware_version = result_dict.get(EFieldName.FIRMWARE_VERSION, Version(0, 0, 0))
        # TODO: firmware info
        info.protocol_version = result_dict.get(EFieldName.PROTOCOL_VERSION, Version(0, 0, 0))

        builder_logger.info("Device type: %s", info.device_type)
        builder_logger.info("Firmware version: %s", info.firmware_version)
        builder_logger.info("Firmware info: %s", info.firmware_info)
        builder_logger.info("Protocol version: %s", info.protocol_version)

        return device

        # -----------------------------------------------
        # TODO: refactor old code into protocol
        # This is the old code used
        # Before we remove it, we need to add the command contracts into the protocol

        # if try_deduce_protocol:
        #     builder_logger.debug("Try to figure out which device it is with ?info, ?type, ?")
        #     if isinstance(commands, CommandSetLegacy):
        #         await commands.get_type.execute(should_log=False)
        #         if commands.get_type.answer.valid:
        #             result_dict.update(commands.get_type.status_result)

        #     await commands.get_info.execute(should_log=False)
        #     if commands.get_info.answer.valid:
        #         result_dict.update(commands.get_info.status_result)

        #     if isinstance(commands, CommandSetLegacy):
        #         await commands.get_overview.execute(should_log=False)
        #         if commands.get_overview.answer.valid:
        #             result_dict.update(commands.get_overview.status_result)
        # else:
        #     builder_logger.debug("Skip ?info and ?type")

        # info = Info()
        # await status.update(**result_dict)
        # info.update(**result_dict)
        # info.firmware_info = commands.get_info.answer.string
        # builder_logger.info("Device type: %s", info.device_type)
        # builder_logger.info("Firmware version: %s", info.firmware_version)
        # builder_logger.info("Firmware info: %s", info.firmware_info)

        # builder_logger.debug("Build device")
        # sonicamp: SonicDevice = SonicDevice(_communicator=comm, info=info, status=status, _logger=logger)

        # if isinstance(commands, CommandSet):
        #     builder_logger.debug("Get list of available commands of device")
        #     await commands.get_command_list.execute(should_log=False)
        #     if commands.get_command_list.answer.valid:
        #         self._add_commands_from_list_command_answer(
        #             commands, sonicamp, commands.get_command_list.answer
        #         )
        #         builder_logger.debug("List of the commands that are supported: %s", str(sonicamp.commands.keys()))
        #         return sonicamp
        #     else:
        #         raise Exception("Wtf, the new devices with Sonic Protocol v2 have to implement get_command_list")
        # else:

        #     basic_commands: Tuple[LegacyCommand, ...] = (
        #         commands.signal_on,
        #         commands.signal_off,
        #         commands.get_overview,
        #         commands.get_info,
        #     )

        #     basic_catch_commands: Tuple[LegacyCommand, ...] = (
        #         commands.set_frequency,
        #         commands.set_gain,
        #         commands.set_serial_mode,
        #         commands.set_khz_mode,
        #         commands.set_mhz_mode,
        #     )

        #     atf_commands: Tuple[LegacyCommand, ...] = (
        #         commands.set_atf1,
        #         commands.get_atf1,
        #         commands.set_atk1,
        #         commands.set_atf2,
        #         commands.get_atf2,
        #         commands.set_atk2,
        #         commands.set_atf3,
        #         commands.get_atf3,
        #         commands.set_atk3,
        #         commands.set_att1,
        #         commands.get_att1,
        #     )

        #     basic_wipe_commands: Tuple[LegacyCommand, ...] = (commands.set_frequency,)

        #     basic_descale_commands: Tuple[LegacyCommand, ...] = (
        #         commands.set_switching_frequency,
        #         commands.set_analog_mode,
        #         commands.set_serial_mode,
        #         commands.set_gain,
        #     )

        #     builder_logger.debug("Add commands depending on the version and type of the device")
        #     sonicamp.add_commands(basic_commands)
        #     if sonicamp.info.firmware_version >= Version(0, 3, 0):
        #         sonicamp.add_commands((commands.get_status, commands.get_type))

        #     if sonicamp.info.device_type == "catch":
        #         sonicamp.add_commands(basic_catch_commands)
        #         if sonicamp.info.firmware_version == Version(0, 3, 0):
        #             sonicamp.add_command(commands.get_sens)
        #         elif sonicamp.info.firmware_version == Version(0, 4, 0):
        #             sonicamp.add_command(commands.get_sens_factorised)
        #         elif sonicamp.info.firmware_version == Version(0, 5, 0):
        #             sonicamp.add_command(commands.get_sens_fullscale_values)

        #         if sonicamp.info.firmware_version >= Version(0, 4, 0):
        #             sonicamp.add_commands(atf_commands)
        #             for command in atf_commands:
        #                 await sonicamp.execute_command(command)

        #     elif sonicamp.info.device_type == "descale":
        #         sonicamp.add_commands(basic_descale_commands)

        #     elif sonicamp.info.device_type == "wipe":
        #         sonicamp.add_commands(basic_wipe_commands)

        #     builder_logger.debug("List of the commands that are supported: %s", str(sonicamp.commands.keys()))
        #     return sonicamp
