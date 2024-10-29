from __future__ import annotations
import asyncio
import copy
from asyncio import Queue
from typing import (
    Optional,
    Callable,
    List,
    Dict,
    Literal,
    Union,
    Iterable,
    Any,
    Tuple,
    TypedDict,
)
import logging
import serial_asyncio as aserial
import serial
import sys
import attrs

import platform
import datetime
import time
import re

logger = logging.getLogger(__name__)

ENCODING: str = "windows-1252" if platform.system() == "Windows" else "utf-8"


class CommandValidationDict(TypedDict):
    pattern: str
    return_type: type


@attrs.define
class Command:
    value: Any = attrs.field(default=None)
    message: str = attrs.field(default="")
    arguments: str = attrs.field(default="", converter=str)
    response_time: float = attrs.field(default=0.3)
    expects_long_answer: bool = attrs.field(default=False, repr=False)
    answer_received: asyncio.Event = attrs.field(factory=asyncio.Event)
    regex_match_groups: Tuple[str] = attrs.field(factory=tuple, repr=True)

    _validation_pattern: Optional[CommandValidationDict] = attrs.field(
        default=None, repr=False
    )
    _answer_string: str = attrs.field(default="")
    _answer_lines: List[str] = attrs.field(factory=list)
    _answer_received_timestamp: float = attrs.field(factory=time.time)
    _creation_timestamp: float = attrs.field(factory=time.time)
    _measured_response_timestamp: float = attrs.field(default=time.time)

    def __init__(
        self,
        value: Any = None,
        message: str = "",
        arguments: str = "",
        response_time: float = 0.3,
        *args,
        **kwargs,
    ) -> None:
        self.__attrs_init__(
            message=message,
            arguments=arguments,
            response_time=response_time,
            *args,
            **kwargs,
        )

    def __attrs_post_init__(self) -> None:
        self.arguments = str(self.value) if self.value is not None else ""

    @property
    def answer_string(self) -> str:
        return self._answer_string

    @property
    def answer_lines(self) -> List[str]:
        return self._answer_lines

    @property
    def validation_pattern(self) -> Optional[CommandValidationDict]:
        return self._validation_pattern

    @property
    def byte_message(self) -> bytes:
        return f"{self.message}{self.arguments}\n".encode(ENCODING)

    def receive_answer(self, answer: Union[List[str], str]) -> None:
        if isinstance(answer, list):
            self._answer_lines = answer
            self._answer_string = "\n".join(answer)
        elif isinstance(answer, str):
            self._answer_lines = answer.splitlines()
            self._answer_string = answer
        else:
            raise ValueError(f"{answer = } is not of type {str, list}")
        self._answer_received_timestamp = time.time()
        self._measured_response_timestamp = (
            self._answer_received_timestamp - self._creation_timestamp
        )


class Commands:
    @attrs.define
    class SetFrequency(Command):
        message: str = attrs.field(default="!f=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"freq[uency]*\s*=?\s*([\d]+)",
            "return_type": int,
        }

    @attrs.define
    class SetSwitchingFrequency(Command):
        message: str = attrs.field(default="!swf=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"freq[uency]*\s*=?\s*([\d]+)",
            "return_type": int,
        }

    @attrs.define
    class GetOverview(Command):
        message: str = attrs.field(default="?")
        response_time: float = 0.5
        expects_long_answer: bool = True

    @attrs.define
    class GetInfo(Command):
        message: str = attrs.field(default="?")
        response_time: float = 0.5
        expects_long_answer: bool = True
        _validation_pattern: CommandValidationDict = {
            "pattern": r".*ver.*([\d]+[.][\d]+).*",
            "return_type": str,
        }

    @attrs.define
    class GetStatus(Command):
        message: str = attrs.field(default="-")
        response_time = 0.15
        _validation_pattern: CommandValidationDict = {
            "pattern": r"(.+)(?:[-#])+(.+)",
            "return_type": str,
        }

    @attrs.define
    class GetSens(Command):
        message: str = attrs.field(default="?sens")
        response_time = 0.4
        _validation_pattern: CommandValidationDict = {
            "pattern": r"([\d]+)(?:[\s])+([\d]+)",
            "return_type": str,
        }

    @attrs.define
    class SetAnalogMode(Command):
        message: str = attrs.field(default="!ANALOG")
        _validation_pattern: CommandValidationDict = {
            "pattern": r".*mode.*analog.*",
            "return_type": str,
        }

    @attrs.define
    class SetSerialMode(Command):
        message: str = attrs.field(default="!SERIAL")
        _validation_pattern: CommandValidationDict = {
            "pattern": r".*mode.*serial.*",
            "return_type": str,
        }

    @attrs.define
    class SetGain(Command):
        message: str = attrs.field(default="!g=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"gain\s*=?\s*([\d]+)",
            "return_type": int,
        }

    @attrs.define
    class SetKhzMode(Command):
        message: str = attrs.field(default="!KHZ")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"(khz)",
            "return_type": str,
        }

    @attrs.define
    class SetMhzMode(Command):
        message: str = attrs.field(default="!MHZ")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"(mhz)",
            "return_type": str,
        }

    @attrs.define
    class SetWipe(Command):
        message: str = attrs.field(default="!WIPE")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"\s*([\d]+)",
            "return_type": int,
        }

    @attrs.define
    class SetSignalOn(Command):
        message: str = attrs.field(default="!ON")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"(Signal\s+is\s+?ON|signal\s+on)",
            "return_type": str,
        }

    @attrs.define
    class SetSignalOff(Command):
        message: str = attrs.field(default="!OFF")
        response_time: float = 0.4
        expects_long_answer: bool = True
        _validation_pattern: CommandValidationDict = {
            "pattern": r"(Signal\s+is\s+?OFF|signal\s+off)",
            "return_type": str,
        }

    @attrs.define
    class SetSignalAuto(Command):
        message: str = attrs.field(default="!AUTO")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"(auto\s*mode\s*on|auto\s*mode|auto)",
            "return_type": str,
        }

    @attrs.define
    class SetATF1(Command):
        message: str = attrs.field(default="!atf1=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r".*freq[quency]*.*1.*=.*([\d]+)",
            "return_type": int,
        }

    @attrs.define
    class GetATF1(Command):
        message: str = attrs.field(default="?atf1")
        expects_long_answer: bool = True
        response_time: float = 0.5
        _validation_pattern: CommandValidationDict = {
            "pattern": r"([\d]+).*\n.*([-]?[\d]*[\.]?[\d]*)",
            "return_type": str,
        }

    @attrs.define
    class SetATK1(Command):
        message: str = attrs.field(default="!atk1=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"([-]?[\d]*[\.]?[\d]*)",
            "return_type": float,
        }

    @attrs.define
    class SetATF2(Command):
        message: str = attrs.field(default="!atf2=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r".*freq[quency]*.*2.*=.*([\d]+)",
            "return_type": int,
        }

    @attrs.define
    class GetATF2(Command):
        message: str = attrs.field(default="?atf2")
        expects_long_answer: bool = True
        response_time: float = 0.5
        _validation_pattern: CommandValidationDict = {
            "pattern": r"([\d]+).*\n.*([-]?[\d]*[\.]?[\d]*)",
            "return_type": str,
        }

    @attrs.define
    class SetATK2(Command):
        message: str = attrs.field(default="!atk2=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"([-]?[\d]*[\.]?[\d]*)",
            "return_type": float,
        }

    @attrs.define
    class SetATF3(Command):
        message: str = attrs.field(default="!atf3=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r".*freq[quency]*.*3.*=.*([\d]+)",
            "return_type": int,
        }

    @attrs.define
    class GetATF3(Command):
        message: str = attrs.field(default="?atf3")
        expects_long_answer: bool = True
        response_time: float = 0.5
        _validation_pattern: CommandValidationDict = {
            "pattern": r"([\d]+).*\n.*([-]?[\d]*[\.]?[\d]*)",
            "return_type": str,
        }

    @attrs.define
    class SetATK3(Command):
        message: str = attrs.field(default="!atk3=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"([-]?[\d]*[\.]?[\d]*)",
            "return_type": float,
        }

    @attrs.define
    class SetATT1(Command):
        message: str = attrs.field(default="!att1=")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"([-]?[\d]*[\.]?[\d]*)",
            "return_type": float,
        }

    @attrs.define
    class GetATT1(Command):
        message: str = attrs.field(default="?att1")
        _validation_pattern: CommandValidationDict = {
            "pattern": r"([-]?[\d]*[\.]?[\d]*)",
            "return_type": float,
        }


class CommandValidator:
    def __init__(self, sonicamp: SonicAmp) -> None:
        self.sonicamp: SonicAmp = sonicamp
        self.validation_patterns: Dict[type, re.Pattern] = {
            command_type: re.compile(
                command_type().validation_pattern["pattern"], re.IGNORECASE
            )
            for command_type in self.sonicamp.commands
            if command_type().validation_pattern is not None
        }

    def accepts(self, command: Command) -> bool:
        if command.validation_pattern is None:
            return False

        pattern = self.validation_patterns.get(type(command))
        if pattern is None:
            raise AttributeError(
                f"{Command = } is not part of {self.sonicamp = }'s commands"
            )

        match = pattern.search(command.answer_string)
        if match is None:
            return False
        try:
            command.value = command.validation_pattern["return_type"](match.group(1))
        except Exception as e:
            command.value = match.group(0)
            logger.warning(sys.exc_info())
        finally:
            command.regex_match_groups = match.groups()
        return True

    def find_command(self, answer: str) -> Optional[Command]:
        for command_type in self.sonicamp.commands:
            command: Command = command_type()
            command.receive_answer(answer=answer)
            if self.accepts(command):
                return command


class SerialCommunicator:
    communication_debug_file = "communication_debug_file.txt"
    def __init__(self, port: str) -> None:
        self.port: str = port
        self.connection_closed: asyncio.Event = asyncio.Event()
        self._procedure_condition: asyncio.Condition = asyncio.Condition()
        self._connection_open: asyncio.Event = asyncio.Event()

        self.command_queue: Queue[Command] = Queue()
        self.answer_queue: Queue[Command] = Queue()
        self.lock: asyncio.Lock = asyncio.Lock()
        self.encoding: str = (
            "windows-1252" if platform.system() == "Windows" else "utf-8"
        )
        self.reader = None
        self.writer = None
        self.init_command: Command = Command(response_time=0.5)

        # Open the file for appending logs
        self.file = open(self.communication_debug_file, "w")

    @property
    def connection_open(self) -> asyncio.Event:
        return self._connection_open
    
    def _log_with_timestamp(self, message: str) -> None:
        """Helper method to write a message to the log file with a timestamp."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.file.write(f"[{timestamp}] {message}\n")
            self.file.flush()  # Force the buffer to flush after each write
            logger.debug(f"Wrote to file {self.communication_debug_file}")
        except Exception as e:
            logger.debug(e)

    async def setup(self) -> None:
        try:
            self.reader, self.writer = await aserial.open_serial_connection(
                url=self.port,
                baudrate=115200,
            )
        except Exception as e:
            logger.debug(sys.exc_info())
            self.reader = None
            self.writer = None
        else:
            self.init_command.receive_answer(
                await self.read_long_message(reading_time=6)
            )
            logger.debug(f"Init Command: {self.init_command}")
            self._connection_open.set()
            asyncio.create_task(self.worker())

    async def worker(self) -> None:
        if self.writer is None or self.reader is None:
            logger.debug("No connection available")
            return
        while not self.writer.is_closing():
            command = await self.command_queue.get()
            async with self.lock:
                try:
                    # Write command to the file with timestamp
                    self._log_with_timestamp(f"Sending command: {command.byte_message}")

                    self.writer.write(command.byte_message)
                    await self.writer.drain()

                    response = await (
                        self.read_long_message(response_time=command.response_time)
                        if command.expects_long_answer
                        else self.read_message(response_time=command.response_time)
                    )

                    # Write response to the file with timestamp
                    self._log_with_timestamp(f"Received response: {response}")
                    
                    command.receive_answer(response)
                    command.answer_received.set()
                    await self.answer_queue.put(command)
                except serial.SerialException:
                    self.disconnect()
                except Exception as e:
                    logger.debug(sys.exc_info())
                    break
        self.disconnect()

    async def read_message(self, response_time: float = 0.3) -> str:
        message: str = ""
        await asyncio.sleep(0.2)
        if self.reader is None:
            return message
        try:
            response = await asyncio.wait_for(
                self.reader.readline(), timeout=response_time
            )
            message = response.decode(self.encoding).strip()
        except Exception as e:
            logger.debug(f"Exception while reading {sys.exc_info()}")
        return message

    async def read_long_message(
        self, response_time: float = 0.3, reading_time: float = 0.2
    ) -> List[str]:
        if self.reader is None:
            return []

        target = time.time() + reading_time
        message: List[str] = []
        while time.time() < target:
            try:
                response = await asyncio.wait_for(
                    self.reader.readline(), timeout=response_time
                )
                line = response.decode(self.encoding).strip()
                message.append(line)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Exception while reading {sys.exc_info()}")
                break

        return message

    def disconnect(self) -> None:
        self.writer.close() 
        self.reader = None
        self._connection_open.clear()
        self.connection_closed.set()

    async def await_writer_closed(self) -> None:
        self.writer.close() 
        await self.writer.wait_closed()
        self.reader = None
        self._connection_open.clear()
        self.connection_closed.set()

    def __del__(self):
        # Ensure that the file is closed properly
        self.file.close()


class CalcStrategy:
    @staticmethod
    def execute(*args, **kwargs) -> Any:
        ...


class ParsingStrategy:
    @staticmethod
    def parse(*args, **kwargs) -> Any:
        ...

    @staticmethod
    def try_to_evaluate(value: Any) -> Any:
        ...


class FullscaleCalcStrategy(CalcStrategy):
    @staticmethod
    def execute(
        frequency: int, urms: float, irms: float, phase: float, *args, **kwargs
    ) -> Dict[str, Union[int, float]]:
        urms = urms if urms > 282_300 else 282_300
        urms = (urms * 0.000_400_571 - 1130.669402) * 1000 + 0.5

        irms = irms if irms > 3_038_000 else 303_800
        irms = (irms * 0.000_015_601 - 47.380671) * 1000 + 0.5

        phase = (phase * 0.125) * 100
        return {"frequency": frequency, "urms": urms, "irms": irms, "phase": phase}


class FactorisedCalcStrategy(CalcStrategy):
    @staticmethod
    def execute(
        frequency: int, urms: float, irms: float, phase: float, *args, **kwargs
    ) -> Dict[str, Union[int, float]]:
        urms /= 1000
        irms /= 1000
        phase /= 1_000_000
        return {"frequency": frequency, "urms": urms, "irms": irms, "phase": phase}


class MinusHashParsingStrategy(ParsingStrategy):
    @staticmethod
    def parse(status_string: str, *args, **kwargs) -> Dict[str, Any]:
        return dict(
            zip(
                ("error", "frequency", "gain", "protocol", "wipe_mode", "temperature"),
                re.split(r"(?<!['])[-#]", status_string),
            )
        )


def default_if_none(default: Any, type_: type = int) -> Callable[[Any], Any]:
    none_converter = attrs.converters.default_if_none(default)

    def converter(value) -> None:
        value = none_converter(value)
        try:
            value = type_(none_converter(value))
        except Exception as e:
            logger.debug(f"VALUE ERROR {e}, {value} is not {type_}")
        return value

    return converter


@attrs.define()
class Status:
    error: int = attrs.field(
        default=0,
        repr=False,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    frequency: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    gain: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    protocol: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    wipe_mode: bool = attrs.field(
        default=False,
        converter=default_if_none(False, attrs.converters.to_bool),
        validator=attrs.validators.instance_of(bool),
    )
    temperature: float = attrs.field(
        default=0.0,
        converter=[
            lambda x: (
                default_if_none(0.0, float)(
                    x.strip("'") if isinstance(x, str) and "'" in x else x
                )
            ),
            lambda x: x if -100 < x < 350 else 0.0,
        ],
        validator=attrs.validators.instance_of(float),
    )
    signal: bool = attrs.field(
        default=False,
        converter=default_if_none(False, bool),
        validator=attrs.validators.instance_of(bool),
    )
    urms: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    irms: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    phase: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    atf1: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    atk1: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    atf2: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    atk2: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    atf3: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    atk3: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    att1: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )

    relay_mode: Optional[Literal["kHz", "MHz"]] = attrs.field(
        default=None,
        converter=attrs.converters.optional(str),
        kw_only=True,
    )
    timestamp: datetime.datetime = attrs.field(
        factory=datetime.datetime.now,
        eq=False,
        converter=lambda b: (
            datetime.datetime.fromtimestamp(b) if isinstance(b, float) else b
        ),
    )

    @classmethod
    def from_status_command(
        cls,
        command: Command,
        parsing_strategy: ParsingStrategy = MinusHashParsingStrategy(),
        calculation_strategy: Optional[CalcStrategy] = None,
        old_status: Optional[Status] = None,
    ) -> Status:
        if not command.answer_string or "Error" in command.answer_string:
            return cls(timestamp=command._answer_received_timestamp)
        status: Dict[str, Any] = parsing_strategy.parse(command.answer_string)
        if calculation_strategy is not None:
            status = calculation_strategy.execute(**status)
        return (
            cls(**status) if old_status is None else attrs.evolve(old_status, **status)
        )

    @classmethod
    def from_sens_command(
        cls,
        command: Command,
        calculation_strategy: Optional[CalcStrategy] = None,
        old_status: Optional[Status] = None,
    ) -> Status:
        if not command.answer_string or "Error" in command.answer_string:
            return cls(timestamp=command._answer_received_timestamp)

        convert_sonicmeasure_field = lambda x: float(x) if "." in x else int(x)
        return_dict: Dict[str, Any] = dict(
            zip(
                ("frequency", "urms", "irms", "phase"),
                map(convert_sonicmeasure_field, command.answer_string.split(" ")),
            )
        )

        if calculation_strategy is not None:
            return_dict = calculation_strategy.execute(**return_dict)

        return_dict["timestamp"] = command._answer_received_timestamp
        return (
            cls(**return_dict)
            if old_status is None
            else attrs.evolve(old_status, **return_dict)
        )


@attrs.frozen
class Modules:
    buffer: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    display: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    eeprom: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    fram: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    i_current: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    current1: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    current2: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    io_serial: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    thermo_ext: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    thermo_int: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    khz: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    mhz: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    portexpander: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    protocol: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    protocol_fix: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    relais: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    scanning: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    sonsens: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    tuning: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    switch: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    switch2: bool = attrs.field(default=False, converter=attrs.converters.to_bool)

    @classmethod
    def from_string(cls, module_string: str) -> Modules:
        return cls(*module_string.split("="))


@attrs.frozen
class Info:
    device_type: Literal["soniccatch", "sonicwipe", "sonicdescale"] = attrs.field(
        default="soniccatch"
    )
    firmware_info: str = attrs.field(default="")
    version: float = attrs.field(default=0.2)
    modules: Modules = attrs.field(factory=Modules)

    @classmethod
    def from_firmware(cls, firmware_info: str, *args, **kwargs) -> Info:
        match = re.search(r".*ver.*([\d]+[.][\d]+).*", firmware_info, re.IGNORECASE)
        logger.debug(f"Match: {match.groups()}")
        version: float = float(match.group(1)) if match is not None else 0.2
        return cls(firmware_info=firmware_info, version=version, *args, **kwargs)


@attrs.define
class Hold:
    duration: float = attrs.field(
        default=100.0,
        converter=float,
        validator=attrs.validators.instance_of(float),
    )
    unit: Literal["ms", "s"] = attrs.field(
        default="ms",
        validator=attrs.validators.in_(("ms", "s")),
    )

    external_event: asyncio.Event = attrs.field(kw_only=True, default=None)
    holding: asyncio.Event = attrs.field(factory=asyncio.Event)
    _remaining_time: float = attrs.field(default=0.0)

    def __attrs_post_init__(self) -> None:
        self.duration = self.duration if self.unit == "s" else self.duration / 1000
        if self.external_event is None:
            self.external_event = self.holding

    def __repr__(self) -> str:
        return f"Holding state: {self.remaining_time} seconds remaining"

    @property
    def remaining_time(self) -> Optional[float]:
        return self._remaining_time

    async def execute(self) -> None:
        self.holding.set()
        end_time: float = time.time() + self.duration
        while time.time() < end_time and self.holding.is_set():
            self._remaining_time = round(end_time - time.time(), 2)
            await asyncio.sleep(0.01)

        self._remaining_time = 0
        self.holding.clear()


@attrs.define
class Ramp:
    sonicamp: SonicAmp = attrs.field()
    start_value: int = attrs.field()
    stop_value: int = attrs.field()
    step_value: int = attrs.field(converter=abs)
    hold_on_time: Union[float, int] = attrs.field(
        default=100,
        validator=attrs.validators.instance_of((int, float)),
    )
    hold_on_time_unit: Literal["ms", "s"] = attrs.field(
        default="ms",
        validator=attrs.validators.in_(("ms", "s")),
    )
    hold_off_time: Union[float, int] = attrs.field(
        default=0,
        validator=attrs.validators.instance_of((int, float)),
    )
    hold_off_time_unit: Literal["ms", "s"] = attrs.field(
        default="ms",
        validator=attrs.validators.in_(("ms", "s")),
    )

    external_event: asyncio.Event = attrs.field(default=None, kw_only=True)
    values: Iterable[int] = attrs.field(init=False, factory=tuple)
    running: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)
    _current_value: int = attrs.field(init=False, default=0)
    _lock: asyncio.Lock = attrs.field(init=False, factory=asyncio.Lock)

    def __attrs_post_init__(self):
        self.step_value = (
            self.step_value if self.start_value < self.stop_value else -self.step_value
        )
        self.stop_value = self.stop_value + self.step_value
        self.values = range(self.start_value, self.stop_value, self.step_value)
        if self.external_event is None:
            self.external_event = self.running

    def __repr__(self) -> str:
        if not self.running.is_set():
            return "Ramp at 0 Hz"
        value: str = (
            f"Ramp at {self.current_value if self.current_value is not None else 0} Hz"
        )
        logger.debug(f"Ramp: {value}")
        return value

    @property
    def current_value(self) -> int:
        return self._current_value

    async def update(self, update_strategy: Callable[[Any], Any] = None) -> None:
        await self.running.wait()
        if self.external_event is not None:
            return
        while self.external_event.is_set() and self.running.is_set():
            if update_strategy is None:
                await self.sonicamp.get_status()
            else:
                await update_strategy()

    async def execute(
        self, update_coroutine: Optional[Callable[[Any], Any]] = None
    ) -> None:
        await self.sonicamp.get_overview()
        update_task = asyncio.create_task(self.update(update_coroutine))
        ramping_task = asyncio.create_task(self.ramp())
        await asyncio.gather(ramping_task, update_task)
        await self.sonicamp.set_signal_off()

    async def ramp(self) -> None:
        await self.sonicamp.set_frequency(self.start_value)
        self.running.set()
        await self.sonicamp.set_signal_on()

        i: int = 0
        value: int = 0
        while (
            self.external_event.is_set()
            and self.running.is_set()
            and i < len(self.values)
        ):
            value = self.values[i]
            self._current_value = value

            await self.sonicamp.set_frequency(value)
            if self.hold_off_time:
                await self.sonicamp.set_signal_on()
            await self.sonicamp.hold(self.hold_on_time, self.hold_on_time_unit)

            if self.hold_off_time:
                await self.sonicamp.set_signal_off()
                await self.sonicamp.hold(self.hold_off_time, self.hold_off_time_unit)

            i += 1

        self._current_value = 0
        self.running.clear()


@attrs.define
class SonicParser:
    SUPPORTED_TOKENS: List[str] = [
        "frequency",
        "gain",
        "ramp_freq",
        "ramp_gain",
        "on",
        "off",
        "hold",
        "startloop",
        "endloop",
        "!WIPE",
        "WIPE",
        "wipe",
        # "chirp_ramp_freq",
        # "chirp_ramp_gain",
        "!AUTO",
        "AUTO",
        "auto"
    ]

    def parse_text(self, text: str) -> dict[str, Union[tuple[Any, ...], str]]:
        lines: list[str] = list(filter(None, text.rstrip().splitlines()))
        commands, arguments, comment = self.parse_lines(lines)
        loops: tuple[dict[str, int], ...] = self.parse_for_loops(commands, arguments)

        self.check_syntax_acception(loops, commands, arguments)
        logger.debug(
            {
                "commands": commands,
                "arguments": arguments,
                "loops": loops,
                "comments": comment,
            }
        )
        return {
            "commands": commands,
            "arguments": arguments,
            "loops": loops,
            "comments": comment,
        }

    def values_correctly_converted(
        self, arg: Union[int, tuple[Union[int, str], ...]]
    ) -> bool:
        return (
            not isinstance(arg, int) and arg.isnumeric()
            if not isinstance(arg, tuple)
            else any(self.values_correctly_converted(value) for value in arg)
        )

    def parse_lines(self, lines: list[str]) -> tuple[Any, ...]:
        commands: list[str] = list()
        arguments: list[Union[str, int]] = list()
        comments: str = str()
        for line in lines:
            if "#" in line:
                comments += f"{line}\n"
                continue

            command, argument = self._parse_line(line)
            commands.append(command)
            arguments.append(argument)

        return (tuple(commands), tuple(arguments), comments)

    def parse_for_loops(
        self, commands: list[str], arguments: list[Union[str, int]]
    ) -> tuple[dict[str, int], ...]:
        loops: list[dict[str, int]] = list()
        for i, command in enumerate(commands):
            if command == "startloop":
                quantifier: int = int(
                    arguments[i]
                    if arguments[i] is not None and isinstance(arguments[i], int)
                    else -1
                )
                loops.insert(i, {"begin": i, "quantifier": quantifier})

            elif command == "endloop":
                loops.insert(i, {})
                for loop in reversed(loops):
                    if len(loop) != 2:
                        continue
                    loop.update({"end": i})
                    break

            else:
                loops.insert(i, {})
        return tuple(loops)

    def _parse_line(self, line: str) -> Tuple[Union[str, int, Tuple], ...]:
        if line is None or line == "":
            return ((), ())

        tmp_line_list: List[List[str]] = [i.split(",") for i in line.split(" ")]
        line_list: List[Union[str, int]] = list(
            filter(None, [item for sublist in tmp_line_list for item in sublist])
        )

        for i, part in enumerate(line_list):
            if part[-1:] == "s" and part[-2:] != "ms" and part[:-1].isnumeric():
                line_list.insert(i + 1, part[-1:])
                line_list[i] = int(part[:-1])
            elif part[-2:] == "ms" and part[:-2].isnumeric():
                line_list.insert(i + 1, part[-2:])
                line_list[i] = int(part[:-2])
            elif part.isnumeric():
                line_list[i] = int(part)

        command: str = line_list[0]
        line_list.pop(0)
        return (command, line_list[0] if len(line_list) == 1 else tuple(line_list))

    def check_syntax_acception(self, loops, commands, arguments) -> None:
        if any(
            (len(loop) != 3 and loop is not None and len(loop) != 0) for loop in loops
        ):
            raise ValueError(
                "Syntax of loops is invalid. Maybe you forgot to close a loop?"
            )

        elif any(self.values_correctly_converted(arg) for arg in arguments):
            raise ValueError(
                "Argument(s) could not have been correctly converted to  integers,\nplease call for support or try again"
            )

        elif any(command not in self.SUPPORTED_TOKENS and not command.startswith("!") for command in commands):
            raise ValueError("One or more commands are illegal or written wrong")


@attrs.define
class Sequence:
    _sonicamp: SonicAmp = attrs.field()
    _script_text: str = attrs.field(validator=attrs.validators.instance_of(str))
    _parser: SonicParser = attrs.field(init=False, factory=SonicParser, repr=False)

    _commands: List[Any] = attrs.field(init=False, factory=list)
    _original_commands: List[Any] = attrs.field(init=False, factory=list)
    _current_command: str = attrs.field(init=False, default="")
    _current_line: int = attrs.field(init=False, default=0)

    running: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)

    def __attrs_post_init__(self) -> None:
        parsed_test = self._parser.parse_text(self._script_text)
        parsed_test = zip(
            parsed_test["commands"], parsed_test["arguments"], parsed_test["loops"]
        )
        self._commands = list(
            {"command": command, "argument": argument, "loop": loop}
            for command, argument, loop in parsed_test
        )
        self._original_commands = copy.deepcopy(self._commands)

    def __repr__(self) -> str:
        return self.current_command

    @property
    def current_line(self) -> int:
        return self._current_line

    @property
    def current_command(self) -> str:
        return self._current_command

    async def update(self, update_strategy: Callable[[Any], Any] = None) -> None:
        await self.running.wait()
        while self.running.is_set():
            if update_strategy is None:
                status = await self._sonicamp.get_status()
            else:
                await update_strategy()

    async def execute(self, update_strategy: Callable[[Any], Any] = None) -> None:
        await self._sonicamp.get_overview()
        update_task = asyncio.create_task(self.update(update_strategy))
        ramping_task = asyncio.create_task(self.loop())
        await asyncio.gather(ramping_task, update_task)

    async def loop(self) -> None:
        self.running.set()
        while self.running.is_set() and self._current_line < len(self._commands):
            try:
                if self._commands[self._current_line]["command"] == "startloop":
                    self.startloop_response()
                elif self._commands[self._current_line]["command"] == "endloop":
                    self.endloop_response()
                else:
                    await self.execute_command(self._current_line)
                    self._current_line += 1
            except Exception as e:
                logger.debug(sys.exc_info())
        self.running.clear()

    def startloop_response(self) -> None:
        loop: Dict[str, int] = self._commands[self._current_line]["loop"]
        if (
            loop.get("quantifier")
            and isinstance(loop.get("quantifier"), int)
            and loop.get("quantifier") != -1
        ):
            loop["quantifier"] -= 1
            self._current_line += 1
        elif loop.get("quantifier") == -1:
            self._current_line += 1
        else:
            logger.debug(f"Jumping to {loop['end'] + 1}; quantifier = 0")
            self._current_line = loop["end"] + 1

    def endloop_response(self) -> None:
        logger.debug(f"'endloop' @ {self._current_line}")
        loop_command: dict[str, int] = list(
            filter(
                lambda x: (x["loop"].get("end") == self._current_line), self._commands
            )
        )[0]
        loop: Dict[str, Any] = loop_command["loop"]
        self._commands[loop["begin"] + 1 : loop["end"] - 1] = copy.deepcopy(
            self._original_commands[loop["begin"] + 1 : loop["end"] - 1]
        )
        self._current_line = loop["begin"]

    async def execute_command(self, line: int) -> None:
        command: Dict[str, Any] = self._commands[self._current_line]
        self._current_command = f'Executing {command["command"]} {command["argument"]}'
        logger.debug(f"Executing command: '{command}'")

        match command["command"]:
            case "frequency":
                await self._sonicamp.set_frequency(command["argument"])
            case "gain":
                await self._sonicamp.set_gain(command["argument"])
            case "ramp_freq":
                self._current_command = self._sonicamp.ramper
                await self._sonicamp.ramp_freq(*command["argument"], event=self.running)
            case "ramp_gain":
                self._current_command = self._sonicamp.ramper
                await self._sonicamp.ramp_gain(*command["argument"], event=self.running)
            case "!AUTO" | "AUTO" | "auto":
                await self._sonicamp.set_signal_auto()
            case "WIPE" | "!WIPE" | "wipe":
                await self._sonicamp.set_wipe()
            case "hold":
                self._current_command = self._sonicamp.holder
                await self._sonicamp.hold(*command["argument"], event=self.running)
            case "on":
                await self._sonicamp.set_signal_on()
            case "off":
                await self._sonicamp.set_signal_off()
            case _:
                if command["command"].startswith("!"):
                    await self._sonicamp.send_command(command["command"])
                else:
                    self.running.clear()
                    raise ValueError(f"{command} is not valid.")


class SonicAmpFactory:
    @staticmethod
    async def build_amp(serial: SerialCommunicator) -> SonicAmp:
        device_type: Command = Command(message="?type", response_time=0.5)
        await serial.command_queue.put(device_type)
        await device_type.answer_received.wait()

        firmware: Command = Command(
            message="?info", response_time=0.5, expects_long_answer=True
        )
        await serial.command_queue.put(firmware)
        await firmware.answer_received.wait()

        info: Info = Info.from_firmware(
            firmware_info=firmware.answer_string, device_type=device_type.answer_string
        )
        if info.device_type == "soniccatch" and info.version == 0.4:
            return SonicCatch(serial, info=info)

        if info.device_type == "soniccatch" and info.version == 0.4:
            return SonicCatch(serial, info=info)
        if info.device_type == "soniccatch" and info.version == 0.3:
            return SonicCatchOld(serial, info=info)
        elif info.device_type == "sonicdescale" and info.version == 41:
            return SonicDescale(serial, info=info)
        else:
            raise NotImplementedError(
                "This device seems not to be implemented for sonicpackage!"
            )
            return SonicAmp(serial, info=info)


class SonicAmp:
    def __init__(
        self, serial: SerialCommunicator, status: Status = Status(), info: Info = Info()
    ) -> None:
        self.serial: SerialCommunicator = serial
        self.status: Status = status
        self.status_changed: asyncio.Event = asyncio.Event()
        self.info: Info = info
        self.last_overview_timestamp: float = 0.0
        self.commands: List[type] = [
            Commands.SetSignalOn,
            Commands.SetSignalOff,
            Commands.GetInfo,
            Commands.GetOverview,
        ]

        self.command_validator: CommandValidator = CommandValidator(self)
        self.ramper: Optional[Ramp] = Ramp(self, 0, 0, 10)
        self.holder: Optional[Hold] = Hold(1)
        self.sequencer: Optional[Sequence] = Sequence(self, "")
        self.check_command(self.serial.init_command)

    @staticmethod
    async def build_amp(serial: SerialCommunicator) -> SonicAmp:
        return await SonicAmpFactory.build_amp(serial)

    def add_commands(self, commands: Iterable[type]) -> None:
        self.commands.extend(commands)
        self.command_validator = CommandValidator(self)

    async def send_command(self, message: str = "") -> str:
        command = await self.execute_command(
            Command(message=message, response_time=0.5, expects_long_answer=True)
        )
        return command.answer_string

    async def execute_command(
        self,
        command: Command,
        *args,
        **kwargs,
    ) -> Command:
        await self.serial.command_queue.put(command)
        await command.answer_received.wait()
        self.check_command(command)
        logger.debug(f"Done with command {command}")
        return command

    def disconnect(self) -> None:
        self.serial.disconnect()

    def update_status(self, command, *args, **kwargs) -> None:
        self.status = attrs.evolve(
            self.status, timestamp=command._answer_received_timestamp, *args, **kwargs
        )
        self.status_changed.set()
        self.status_changed.clear()
        logger.debug(f"Status updated from Amp: {self.status}")

    def scan_command(self, command) -> None:
        if isinstance(command, Commands.GetOverview):
            pass
        elif isinstance(command, Commands.GetInfo):
            pass
        elif isinstance(command, Commands.SetSignalOn):
            self.update_status(command, signal=True)
        elif isinstance(command, Commands.SetSignalOff):
            self.update_status(command, signal=False, urms=0.0, irms=0.0, phase=0.0)
            logger.debug(f"Status updated set signal off: {self.status}")

    def get_status(self) -> Status:
        ...

    def check_command(self, command: Command) -> None:
        for answer in command.answer_lines:
            potential_command: Optional[Command] = self.command_validator.find_command(
                answer
            )
            if potential_command:
                potential_command._answer_received_timestamp = (
                    command._answer_received_timestamp
                )
                self.scan_command(potential_command)

    async def set_signal_off(self) -> str:
        command = await self.execute_command(Commands.SetSignalOff())
        return command.answer_string

    async def set_signal_on(self) -> str:
        command = await self.execute_command(Commands.SetSignalOn())
        return command.answer_string

    async def get_info(self) -> str:
        command = await self.execute_command(Commands.GetInfo())
        return command.answer_string

    async def get_overview(self) -> str:
        command = await self.execute_command(Commands.GetOverview())
        return command.answer_string

    async def update_strategy(self) -> Status:
        ...

    async def sequence(self, script: str) -> None:
        self.sequencer = Sequence(self, script)
        await self.sequencer.execute(self.update_strategy)

    async def hold(
        self,
        duration: float = 100,
        unit: Literal["ms", "s"] = "ms",
        event: asyncio.Event = asyncio.Event(),
    ) -> None:
        self.holder = Hold(duration=duration, unit=unit, external_event=event)
        await self.holder.execute()

    async def ramp_freq(
        self,
        start: int,
        stop: int,
        step: int = 100,
        hold_on_time: float = 50,
        hold_on_time_unit: Literal["ms", "s"] = "ms",
        hold_off_time: float = 0,
        hold_off_time_unit: Literal["ms", "s"] = "ms",
        event: asyncio.Event = asyncio.Event(),
    ) -> None:
        self.ramper = Ramp(
            self,
            start,
            stop,
            step,
            hold_on_time,
            hold_on_time_unit,
            hold_off_time,
            hold_off_time_unit,
            external_event=event,
        )
        await self.ramper.execute(self.update_strategy)

    async def ramp_gain(
        self,
        start: int,
        stop: int,
        step: int,
        hold_on_time: float,
        hold_on_time_unit: Literal["ms", "s"],
        hold_off_time: float,
        hold_off_time_unit: Literal["ms", "s"],
        event: asyncio.Event = asyncio.Event(),
    ) -> None:
        self.ramper = Ramp(
            self,
            start,
            stop,
            step,
            hold_on_time,
            hold_on_time_unit,
            hold_off_time,
            hold_off_time_unit,
            external_event=event,
        )
        asyncio.create_task(self.ramper.execute(self.update_strategy))


class SonicCatch(SonicAmp):
    def __init__(
        self, serial: SerialCommunicator, status: Status = Status(), info: Info = Info()
    ) -> None:
        super().__init__(serial, status, info)
        self.add_commands(
            (
                Commands.SetFrequency,
                Commands.SetGain,
                Commands.SetKhzMode,
                Commands.SetMhzMode,
                Commands.SetSignalAuto,
                Commands.GetSens,
                Commands.GetStatus,
                Commands.GetATF1,
                Commands.GetATF2,
                Commands.GetATF3,
                Commands.SetATF1,
                Commands.SetATF2,
                Commands.SetATF3,
                Commands.SetATK1,
                Commands.SetATK2,
                Commands.SetATK3,
                Commands.SetATT1,
                Commands.GetATT1,
                Commands.SetWipe,
            )
        )

    def scan_command(self, command) -> None:
        if isinstance(command, Commands.SetFrequency):
            self.update_status(command, frequency=command.value)
        elif isinstance(command, Commands.SetGain):
            self.update_status(command, gain=command.value)
        elif isinstance(command, Commands.GetStatus):
            self.status = Status.from_status_command(command, old_status=self.status)
            self.update_status(command, signal=True if self.status.frequency else False)
            logger.debug(f"Status updated from GetStatus: {self.status}")
            self.status_changed.set()
            self.status_changed.clear()
        elif isinstance(command, Commands.GetSens):
            self.status = Status.from_sens_command(
                command,
                old_status=self.status,
                calculation_strategy=FactorisedCalcStrategy(),
            )
            logger.debug(f"Status updated from GetSens: {self.status}")
            self.status_changed.set()
            self.status_changed.clear()
        elif isinstance(command, Commands.SetSignalAuto):
            self.update_status(command, protocol=110)
        elif isinstance(command, Commands.SetMhzMode):
            self.update_status(command, relay_mode="mhz")
        elif isinstance(command, Commands.SetKhzMode):
            self.update_status(command, relay_mode="khz")
        elif isinstance(command, Commands.SetATF1):
            self.update_status(command, atf1=command.value)
        elif isinstance(command, Commands.SetATF2):
            self.update_status(command, atf2=command.value)
        elif isinstance(command, Commands.SetATF3):
            self.update_status(command, atf3=command.value)
        else:
            return super().scan_command(command)

    async def update_strategy(self) -> Status:
        if self.status.signal: # and self.status.relay_mode == "mhz"
            status = await self.get_sens()
        elif (time.time() - self.last_overview_timestamp) > 10:
            status = await self.get_overview()
        else:
            status = await self.get_status()
        return status

    async def set_frequency(self, frequency: int) -> str:
        command = await self.execute_command(Commands.SetFrequency(value=frequency))
        return command.answer_string

    async def set_atf(self, number: int, frequency: int, *args, **kwargs) -> int:
        if number not in (1, 2, 3):
            return 0
        atf_dict: Dict[int, Dict[str, Any]] = {
            1: {"command": Commands.SetATF1, "status": self.status.atf1},
            2: {"command": Commands.SetATF2, "status": self.status.atf2},
            3: {"command": Commands.SetATF3, "status": self.status.atf3},
        }
        command = await self.execute_command(
            atf_dict[number]["command"](value=frequency)
        )
        return command.answer_string

    async def get_atf(self, number: int, *args, **kwargs) -> None:
        if number not in (1, 2, 3):
            return 0
        atf_command_dict: Dict[int, Command] = {
            1: Commands.GetATF1,
            2: Commands.GetATF2,
            3: Commands.GetATF3,
        }
        logger.debug(f"Getting ATF{number}: {self.status}")
        command = await self.execute_command(atf_command_dict[number]())
        atf_values_dict = {
            f"atf{number}": int(command.answer_lines[0]),
            f"atk{number}": float(command.answer_lines[1]),
        }
        self.update_status(command, **atf_values_dict)
        logger.debug(f"After getting ATF{number}: {self.status}")
        return self.status

    async def set_atk(self, number: int, coefficient: float, *args, **kwargs) -> None:
        atk_dict: Dict[int, Dict[str, Any]] = {
            1: {"command": Commands.SetATK1, "status": self.status.atk1},
            2: {"command": Commands.SetATK2, "status": self.status.atk2},
            3: {"command": Commands.SetATK3, "status": self.status.atk3},
        }
        command = await self.execute_command(
            atk_dict[number]["command"](value=coefficient)
        )
        if self.command_validator.accepts(command):
            atk_dict[number]["status"] = float(command.answer_string)
        return command.answer_string

    async def set_att1(self, temperature: float, *args, **kwargs) -> None:
        command = await self.execute_command(Commands.SetATT1(value=temperature))
        if self.command_validator.accepts(command):
            self.update_status(command, att1=float(command.answer_string))
        return command.answer_string

    async def get_att1(self, *args, **kwargs) -> None:
        command = await self.execute_command(Commands.GetATT1())
        if self.command_validator.accepts(command):
            self.update_status(command, att1=float(command.answer_string))
        return self.status.att1

    async def set_gain(self, gain: int) -> str:
        command = await self.execute_command(Commands.SetGain(value=gain))
        return command.answer_string

    async def get_status(self) -> Status:
        command = await self.execute_command(Commands.GetStatus())
        return self.status

    async def get_sens(self) -> Status:
        command = await self.execute_command(Commands.GetSens())
        return self.status

    async def set_signal_auto(self) -> str:
        command = await self.execute_command(Commands.SetSignalAuto())
        return command.answer_string

    async def set_relay_mode_khz(self) -> str:
        command = await self.execute_command(Commands.SetKhzMode())
        return command.answer_string

    async def set_relay_mode_mhz(self) -> str:
        command = await self.execute_command(Commands.SetMhzMode())
        return command.answer_string

    async def set_wipe(self) -> str:
        command = await self.execute_command(Commands.SetWipe())
        return command.answer_string


class SonicCatchOld(SonicAmp):
    def __init__(
        self, serial: SerialCommunicator, status: Status = Status(), info: Info = Info()
    ) -> None:
        super().__init__(serial, status, info)
        self.add_commands(
            (
                Commands.SetFrequency,
                Commands.SetGain,
                Commands.SetKhzMode,
                Commands.SetMhzMode,
                Commands.SetSignalAuto,
                Commands.GetSens,
                Commands.GetStatus,
            )
        )

    def scan_command(self, command) -> None:
        if isinstance(command, Commands.SetFrequency):
            self.update_status(command, frequency=command.value)
        elif isinstance(command, Commands.SetGain):
            self.update_status(command, gain=command.value)
        elif isinstance(command, Commands.GetStatus):
            self.status = Status.from_status_command(command, old_status=self.status)
            self.update_status(command, signal=True if self.status.frequency else False)
            logger.debug(f"Status updated: {self.status}")
            self.status_changed.set()
            self.status_changed.clear()
        elif isinstance(command, Commands.GetSens):
            self.status = Status.from_sens_command(
                command,
                old_status=self.status,
                calculation_strategy=FactorisedCalcStrategy(),
            )
            logger.debug(f"Status updated: {self.status}")
            self.status_changed.set()
            self.status_changed.clear()
        elif isinstance(command, Commands.SetSignalAuto):
            self.update_status(command, protocol=110)
        elif isinstance(command, Commands.SetMhzMode):
            self.update_status(command, relay_mode="mhz")
        elif isinstance(command, Commands.SetKhzMode):
            self.update_status(command, relay_mode="khz")
        else:
            return super().scan_command(command)

    async def update_strategy(self) -> Status:
        if self.status.signal and self.status.relay_mode == "mhz":
            status = await self.get_sens()
        elif (time.time() - self.last_overview_timestamp) > 10:
            status = await self.get_overview()
        else:
            status = await self.get_status()
        return status

    async def set_frequency(self, frequency: int) -> str:
        command = await self.execute_command(Commands.SetFrequency(value=frequency))
        return command.answer_string

    async def set_gain(self, gain: int) -> str:
        command = await self.execute_command(Commands.SetGain(value=gain))
        return command.answer_string

    async def get_status(self) -> Status:
        command = await self.execute_command(Commands.GetStatus())
        return self.status

    async def get_sens(self) -> Status:
        command = await self.execute_command(Commands.GetSens())
        return self.status

    async def set_signal_auto(self) -> str:
        command = await self.execute_command(Commands.SetSignalAuto())
        return command.answer_string

    async def set_relay_mode_khz(self) -> str:
        command = await self.execute_command(Commands.SetKhzMode())
        return command.answer_string

    async def set_relay_mode_mhz(self) -> str:
        command = await self.execute_command(Commands.SetMhzMode())
        return command.answer_string


class SonicDescale(SonicAmp):
    def __init__(
        self, serial: SerialCommunicator, status: Status = Status(), info: Info = Info()
    ) -> None:
        super().__init__(serial, status, info)
        self.add_commands(
            (
                Commands.SetSwitchingFrequency,
                Commands.SetGain,
                Commands.SetAnalogMode,
                Commands.SetSerialMode,
            )
        )

    async def scan_command(self, command) -> None:
        if isinstance(command, Commands.SetSwitchingFrequency):
            pass
        elif isinstance(command, Commands.SetAnalogMode):
            pass
        elif isinstance(command, Commands.SetSerialMode):
            pass
        elif isinstance(command, Commands.SetGain):
            pass
        else:
            return super().scan_command(command)

    async def update_strategy(self) -> Status:
        return await self.get_overview()

    async def get_status(self) -> Status:
        return self.get_overview()

    async def set_switching_frequency(self, frequency: int) -> str:
        command = await self.execute_command(
            Commands.SetSwitchingFrequency(value=frequency)
        )
        return command.answer_string

    async def set_gain(self, gain: int) -> str:
        command = await self.execute_command(Commands.SetGain(value=gain))
        return command.answer_string

    async def set_analog_mode(self, frequency: int) -> str:
        command = await self.execute_command(Commands.SetAnalogMode())
        return command.answer_string

    async def set_serial_mode(self, frequency: int) -> str:
        command = await self.execute_command(Commands.SetSerialMode())
        return command.answer_string
