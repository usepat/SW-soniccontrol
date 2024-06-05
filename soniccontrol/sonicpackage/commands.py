import datetime
import attrs
from soniccontrol.sonicpackage.command import Command, CommandValidator
from soniccontrol.sonicpackage.serial_communicator import SerialCommunicator


class Commands:
    def __init__(self, serial: SerialCommunicator):
        
        # TODO: Ask about ?error, how do we validate errors, if there is not a known number of errors
        type_validator: CommandValidator = CommandValidator(pattern=r"sonic(catch|wipe|descale)", type_=str)
        version_validator: CommandValidator = CommandValidator(pattern=r".*([\d]\.[\d]\.[\d]).*", version=str)
        update_date_validator: CommandValidator = CommandValidator(
            pattern=r".*(\d{2}.\d{2}.\d{4}).*", date=lambda date: (
                datetime.datetime.strptime(date, "%d.%m.%Y").date()
            )
        )
        protocol_version_validator: CommandValidator = CommandValidator(
            pattern=r".*([\d]\.[\d]\.[\d]).*", protocol_version=str
        )
        pzt_validator: CommandValidator = CommandValidator(
            pattern=r"(.*)[#](\d+)", 
            id=str,
            frequency=int,
        )
        frequency_validator: CommandValidator = CommandValidator(pattern=r"(\d+)\s*Hz", frequency=int)
        gain_validator: CommandValidator = CommandValidator(pattern=r"(\d+)\s*%", gain=int)
        temp_validator: CommandValidator = CommandValidator(pattern=r"(\d+)\s* °C", temp=float)
        
        # TODO: What should be the units in sonicpackage?
        uipt_validator: CommandValidator = CommandValidator(
            pattern=r"(\d+)\s*uV[#](\d+)\s*uA[#](\d+)\s*mDeg[#](\d+)\s*mDegC",
            urms=int,
            irms=int,
            phase=int
            temperature=int
        )
        adc_validator: CommandValidator = CommandValidator(
            pattern=r"(\d+) uV", adc_voltage=int
        )
        
        
        self.set_frequency: Command = Command(
            message="!f=",
            validators=CommandValidator(
                pattern=r".*freq[uency]*\s*=?\s*([\d]+).*", frequency=int
            ),
            serial_communication=serial
        )

        self.set_gain: Command = Command(
            message="!g=",
            validators=CommandValidator(pattern=r".*gain\s*=?\s*([\d]+).*", gain=int),
            serial_communication=serial
        )

        self.set_switching_frequency: Command = Command(
            message="!swf=",
            validators=CommandValidator( 
                pattern=r".*freq[uency]*\s*=?\s*([\d]+).*", switching_frequency=int
            ),
            serial_communication=serial
        )

        self.get_overview: Command = Command(
            message="?",
            estimated_response_time=0.5,
            expects_long_answer=True,
            validators=(
                CommandValidator(pattern=r".*(khz|mhz).*", relay_mode=str),
                CommandValidator(pattern=r".*freq[uency]*\s*=?\s*([\d]+).*", frequency=int),
                CommandValidator(pattern=r".*gain\s*=?\s*([\d]+).*", gain=int),
                CommandValidator(
                    pattern=r".*signal.*(on|off).*",
                    signal=lambda b: bool(b.lower() == "on"),
                ),
            ),
            serial_communication=serial
        )

        self.get_type: Command = Command(
            message="?type",
            estimated_response_time=0.5,
            validators=CommandValidator(
                pattern=r"sonic(catch|wipe|descale)", device_type=str
            ),
            serial_communication=serial
        )

        self.get_info: Command = Command(
            message="?info",
            estimated_response_time=0.5,
            expects_long_answer=True,
            validators=(
                CommandValidator(pattern=r".*ver.*([\d]+[.][\d]+).*", version=float),
                CommandValidator(pattern=r"sonic(catch|wipe|descale)", type_=str),
            ),
            serial_communication=serial
        )

        self.get_command_list: Command = Command(
            message="?list_commands",
            estimated_response_time=0.5,
            expects_long_answer=True,
            validators=CommandValidator(pattern=r"(.+)(#(.+))+"),
            serial_communication=serial
        )

        # TODO: Ask if there are really 2 procedures sending like in the excel sheet
        self.get_status: Command = Command(
            message="-",
            estimated_response_time=0.35,
            validators=CommandValidator(
                pattern=r"([\d])(?:[-#])([\d]+)(?:[-#])([\d]+)(?:[-#])([\d]+)(?:[-#])([\d])(?:[-#])(?:[']?)([-]?[\d]+[.][\d]+)?(?:[']?)",
                error=int,
                frequency=int,
                signal=attrs.converters.to_bool,
                gain=int,
                procedure=int,
                temperature=float,
                urms=int,
                irms=int,
                phase=int,
            ),
            serial_communication=serial
        )

        self.get_sens: Command = Command(
            message="?sens",
            estimated_response_time=0.35,
            validators=(
                CommandValidator(
                    pattern=r"([\d]+)(?:[\s]+)([-]?[\d]+[.]?[\d]?)(?:[\s]+)([-]?[\d]+[.]?[\d]?)(?:[\s]+)([-]?[\d]+[.]?[\d]?)",
                    frequency=int,
                    urms=float,
                    irms=float,
                    phase=float,
                ),
                CommandValidator(
                    pattern=r".*(error).*",
                    signal=lambda error: False,
                    frequency=lambda error: 0,
                    urms=lambda error: 0,
                    irms=lambda error: 0,
                    phase=lambda error: 0,
                ),
            ),
            serial_communication=serial
        )

        self.get_sens_factorised: Command = Command(
            message="?sens",
            estimated_response_time=0.35,
            validators=(
                CommandValidator(
                    pattern=r"([\d]+)(?:[\s]+)([-]?[\d]+[.]?[\d]?)(?:[\s]+)([-]?[\d]+[.]?[\d]?)(?:[\s]+)([-]?[\d]+[.]?[\d]?)",
                    frequency=int,
                    urms=attrs.converters.pipe(float, lambda urms: urms / 1000),
                    irms=attrs.converters.pipe(float, lambda irms: irms / 1000),
                    phase=attrs.converters.pipe(float, lambda phase: phase / 1_000_000),
                ),
                CommandValidator(
                    pattern=r".*(error).*",
                    signal=lambda error: False,
                    frequency=lambda error: 0,
                    urms=lambda error: 0,
                    irms=lambda error: 0,
                    phase=lambda error: 0,
                ),
            ),
            serial_communication=serial
        )

        self.get_sens_fullscale_values: Command = Command(
            message="?sens",
            estimated_response_time=0.35,
            validators=(
                CommandValidator(
                    pattern=r"([\d]+)(?:[\s]+)([-]?[\d]+[.]?[\d]?)(?:[\s]+)([-]?[\d]+[.]?[\d]?)(?:[\s]+)([-]?[\d]+[.]?[\d]?)",
                    frequency=int,
                    urms=attrs.converters.pipe(
                        float,
                        lambda urms: urms if urms > 282_300 else 282_300,
                        lambda urms: (urms * 0.000_400_571 - 1_130.669_402) * 1000 + 0.5,
                    ),
                    irms=attrs.converters.pipe(
                        float,
                        lambda irms: irms if irms > 3_038_000 else 303_800,
                        lambda irms: (irms * 0.000_015_601 - 47.380671) * 1000 + 0.5,
                    ),
                    phase=attrs.converters.pipe(float, lambda phase: phase * 0.125 * 100),
                ),
                CommandValidator(
                    pattern=r".*(error).*",
                    signal=lambda error: False,
                    frequency=lambda error: 0,
                    urms=lambda error: 0,
                    irms=lambda error: 0,
                    phase=lambda error: 0,
                ),
            ),
            serial_communication=serial
        )

        self.signal_on: Command = Command(
            message="!ON",
            validators=(
                CommandValidator(
                    pattern=r"signal.*(on)", 
                    signal=lambda b: b.lower() == "on"
                ),
                CommandValidator(
                    pattern=r"\d+#(.+)",
                    signal=lambda b: b.lower() == "on"
                )
            ),
            serial_communication=serial
        )

        self.signal_off: Command = Command(
            message="!OFF",
            estimated_response_time=0.4,
            validators=(
                CommandValidator(
                    pattern=r"signal.*(off)", 
                    signal=lambda b: not b.lower() == "off"
                ),
                CommandValidator(
                    pattern=r"\d+#(.+)",
                    signal=lambda b: not b.lower() == "off"
                )
            ),
            serial_communication=serial
        )

        self.signal_auto: Command = Command(
            message="!AUTO",
            estimated_response_time=0.5,
            validators=CommandValidator(pattern=r".*(auto).*", protocol=str),
            serial_communication=serial
        )

        self.set_serial_mode: Command = Command(
            message="!SERIAL",
            validators=CommandValidator(
                pattern=r".*mode.*(serial).*", communication_mode=str
            ),
            serial_communication=serial
        )

        self.set_analog_mode: Command = Command(
            message="!ANALOG",
            validators=CommandValidator(
                pattern=r".*mode.*(analog).*", communication_mode=str
            ),
            serial_communication=serial
        )

        self.set_khz_mode: Command = Command(
            message="!KHZ",
            validators=CommandValidator(pattern=r".*(khz).*", relay_mode=str),
            serial_communication=serial
        )

        self.set_mhz_mode: Command = Command(
            message="!MHZ",
            validators=CommandValidator(pattern=r".*(mhz).*", relay_mode=str),
            serial_communication=serial
        )

        self.set_atf1: Command = Command(
            message="!atf1=",
            validators=CommandValidator(
                pattern=r".*freq[quency]*.*1.*=.*([\d]+)", atf1=int
            ),
            serial_communication=serial
        )

        self.get_atf1: Command = Command(
            message="?atf1",
            expects_long_answer=True,
            validators=CommandValidator(
                pattern=r"([\d]+)\n([-]?[\d]+[\.]?[\d]*)", atf1=int, atk1=float
            ),
            serial_communication=serial
        )

        self.set_atk1: Command = Command(
            message="!atk1=",
            validators=CommandValidator(pattern=r"([-]?[\d]*[\.]?[\d]*)", atk1=float),
            serial_communication=serial
        )

        self.set_atf2: Command = Command(
            message="!atf2=",
            validators=CommandValidator(
                pattern=r".*freq[quency]*.*2.*=.*([\d]+)", atf2=int
            ),
            serial_communication=serial
        )

        self.get_atf2: Command = Command(
            message="?atf2",
            expects_long_answer=True,
            validators=CommandValidator(
                pattern=r"([\d]+)\n([-]?[\d]+[\.]?[\d]*)", atf2=int, atk2=float
            ),
            serial_communication=serial
        )

        self.set_atk2: Command = Command(
            message="!atk2=",
            validators=CommandValidator(pattern=r"([-]?[\d]*[\.]?[\d]*)", atk2=float),
            serial_communication=serial
        )

        self.set_atf3: Command = Command(
            message="!atf3=",
            validators=CommandValidator(
                pattern=r".*freq[quency]*.*3.*=.*([\d]+)", atf3=int
            ),
            serial_communication=serial
        )

        self.get_atf3: Command = Command(
            message="?atf3",
            expects_long_answer=True,
            validators=CommandValidator(
                pattern=r"([\d]+)\n([-]?[\d]+[\.]?[\d]*)", atf3=int, atk3=float
            ),
            serial_communication=serial
        )

        self.set_atk3: Command = Command(
            message="!atk3=",
            validators=CommandValidator(pattern=r"([-]?[\d]*[\.]?[\d]*)", atk3=float),
            serial_communication=serial
        )

        self.set_att1: Command = Command(
            message="!att1=",
            validators=CommandValidator(pattern=r"([-]?[\d]*[\.]?[\d]*)", att1=float),
            serial_communication=serial
        )

        self.get_att1: Command = Command(
            message="?att1",
            validators=CommandValidator(pattern=r"([-]?[\d]*[\.]?[\d]*)", att1=float),
            serial_communication=serial
        )
