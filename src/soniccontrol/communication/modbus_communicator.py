import asyncio
import logging
import struct
from datetime import datetime
from enum import Enum
import time
from typing import Any, Optional

import attrs
import numpy as np
from pymodbus.client import AsyncModbusSerialClient

from sonic_protocol.protocol import protocol_list
from sonic_protocol.command_codes import BaseCommandCode, CommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocols.protocol_v3_0_0.types.types import Parity
from sonic_protocol.python_parser.answer import Answer
from sonic_protocol.python_parser.commands import Command, GetSwf, GetUpdateDescale, SetOff, SetOn, SetSwf
from sonic_protocol.schema import BuildType, CommandContract, CommandParamDef, DeviceType, FieldType, ProtocolType, Timestamp, Version
from soniccontrol.communication.communicator import Communicator
from soniccontrol.fw_device.connection import Connection, ModbusConnection


@attrs.define()
class ModbusCommunicator(Communicator):
    MAILBOX_COMMAND_ADDRESS = 1024
    MAILBOX_RESPONSE_ADDRESS = 0
    MODBUS_MAX_STR_LENGTH = 62
    DEFAULT_DEVICE_ID = 1
    DEFAULT_TRANSCEIVER_ID = 1
    RESPONSE_HEADER_REGISTERS = 2
    RESPONSE_POLL_INTERVAL_S = 0.05
    RESPONSE_TIMEOUT_S = 2.0
    TRANSACTION_TIMEOUT_S = 3.0
    MAX_RETRIES = 3
    GENERIC_DEVICE_ERROR = "Device returned an error"
    FIRMWARE_ENUM_MEMBER_ORDER = {
        DeviceType: (
            DeviceType.UNKNOWN,
            DeviceType.CONFIGURATOR,
            DeviceType.MVP_WORKER,
            DeviceType.DESCALE,
            DeviceType.POSTMAN,
            DeviceType.CRYSTAL,
            DeviceType.SIMULATION,
            DeviceType.DIAGNOSTICS_TOOL,
        ),
        BuildType: (
            BuildType.RELEASE,
            BuildType.DEBUG,
        ),
    }

    _connection_opened: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)
    _modbus_client: Optional[AsyncModbusSerialClient] = attrs.field(
        init=False, default=None, repr=False
    )
    _lock: asyncio.Lock = attrs.field(factory=asyncio.Lock)
    _logger: logging.Logger = attrs.field(factory=logging.getLogger)
    _messages: asyncio.Queue[str] = attrs.field(
        init=False, factory=lambda: asyncio.Queue(maxsize=100), repr=False
    )

    def __attrs_post_init__(self) -> None:
        self._logger = logging.getLogger(
            self._logger.name + "." + ModbusCommunicator.__name__
        )
        super().__init__()


    @property
    def connection_opened(self) -> asyncio.Event:
        return self._connection_opened

    async def open_communication(self, connection: Connection) -> None:
        self._connection = connection
        self._modbus_client = await connection.open_modbus_connection()
        await self._modbus_client.connect()
        response = await self._read_input_registers(
            self.MAILBOX_RESPONSE_ADDRESS,
            count=1,
            device_id=self.DEFAULT_DEVICE_ID,
        )
        if response.isError():
            raise ConnectionError()
        self._connection_opened.set()

    async def close_communication(self, restart: bool = False) -> None:
        if not self._connection_opened.is_set() and self._modbus_client is None:
            return

        self._connection_opened.clear()

        try:
            if self._modbus_client is not None:
                self._modbus_client.close()
        finally:
            if self._connection is not None:
                await self._connection.close_connection()

    async def send_and_wait_for_response(self, request: str, **kwargs) -> str:
        raise NotImplementedError(
            "String based communication does not exist in the modbus world"
        )

    async def read_message(self) -> str:
        return await self._messages.get()

    def _queue_message(self, message: str) -> None:
        if self._messages.full():
            self._messages.get_nowait()
        self._messages.put_nowait(message)

    async def _read_input_registers(self, address: int, count: int, device_id: int):
        assert self._modbus_client is not None
        return await asyncio.wait_for(
            self._modbus_client.read_input_registers(
                address,
                count=count,
                device_id=device_id,
            ),
            timeout=self.TRANSACTION_TIMEOUT_S,
        )

    async def _write_registers(self, address: int, values: list[int], device_id: int):
        assert self._modbus_client is not None
        return await asyncio.wait_for(
            self._modbus_client.write_registers(
                address,
                values,
                device_id=device_id,
            ),
            timeout=self.TRANSACTION_TIMEOUT_S,
        )

    def _pack_command_registers(
        self, command_contract: CommandContract, command: Command
    ) -> list[int]:
        registers = [1, self.DEFAULT_TRANSCEIVER_ID, int(command.code)]
        registers.extend(self.args_to_registers(command_contract, command))
        return registers

    def args_to_registers(
        self, command_contract: CommandContract, command: Command
    ) -> list[int]:
        assert command_contract.command_def is not None
        cmd_def = command_contract.command_def
        registers: list[int] = []
        args = command.args

        if cmd_def.index_param is not None and "index" in args:
            registers.extend(self.value_to_registers(args["index"], cmd_def.index_param))

        if cmd_def.setter_param is not None and "value" in args:
            registers.extend(self.value_to_registers(args["value"], cmd_def.setter_param))

        return registers

    @staticmethod
    def _has_unsupported_string_index(
        command_contract: CommandContract, command: Command
    ) -> bool:
        command_def = command_contract.command_def
        if command_def is None or command_def.index_param is None:
            return False
        return (
            "index" in command.args
            and command_def.index_param.param_type.field_type is str
        )

    def value_to_registers(self, value: Any, param_def: CommandParamDef) -> list[int]:
        return self.field_value_to_registers(value, param_def.param_type)

    def field_value_to_registers(self, value: Any, field_type: FieldType) -> list[int]:
        typ = field_type.field_type

        if typ is bool:
            return [1 if value else 0]
        if typ is np.uint8:
            return [int(value) & 0xFF]
        if typ is np.uint16:
            return [int(value) & 0xFFFF]
        if typ is np.uint32:
            return self.bytes_to_registers(struct.pack(">I", int(value) & 0xFFFFFFFF))
        if typ is int:
            return self.bytes_to_registers(struct.pack(">I", int(value) & 0xFFFFFFFF))
        if typ is float:
            return self.bytes_to_registers(struct.pack(">f", float(value)))
        if typ is str:
            return self.string_to_registers(str(value))
        if typ is Timestamp:
            return self.bytes_to_registers(
                struct.pack(">q", self.timestamp_to_posix(value))
            )
        if typ is Version:
            version = Version.to_version(value)
            return [version.major & 0xFF, version.minor & 0xFF, version.patch & 0xFF]
        if isinstance(typ, type) and issubclass(typ, Enum):
            return [self.enum_member_to_firmware_value(typ, value) & 0xFFFF]

        raise NotImplementedError(f"Modbus payload not implemented for {typ}")

    @staticmethod
    def enum_member_to_firmware_value(enum_type: type[Enum], value: Any) -> int:
        firmware_member_order = ModbusCommunicator.FIRMWARE_ENUM_MEMBER_ORDER.get(enum_type)

        if isinstance(value, enum_type):
            member = value
        else:
            try:
                member = enum_type(value)
            except (TypeError, ValueError):
                if isinstance(value, str):
                    member = enum_type[value]
                else:
                    members = firmware_member_order if firmware_member_order is not None else tuple(enum_type)
                    if 0 <= int(value) < len(members):
                        return int(value)
                    raise ValueError(f"{value} is not a valid {enum_type.__name__}")

        if isinstance(member.value, int):
            return int(member.value)

        members = firmware_member_order if firmware_member_order is not None else tuple(enum_type)
        return members.index(member)

    @staticmethod
    def firmware_value_to_enum_member(enum_type: type[Enum], raw_value: int) -> Enum:
        members = ModbusCommunicator.FIRMWARE_ENUM_MEMBER_ORDER.get(enum_type, tuple(enum_type))
        if not members:
            raise ValueError(f"Enum {enum_type.__name__} has no members")

        first_value = members[0].value
        if isinstance(first_value, int):
            return enum_type(raw_value)

        return members[raw_value]

    @staticmethod
    def bytes_to_registers(payload: bytes) -> list[int]:
        if len(payload) % 2 != 0:
            raise ValueError("Payload length must be divisible by 2")

        return [
            int.from_bytes(payload[index:index + 2], byteorder="big", signed=False)
            for index in range(0, len(payload), 2)
        ]

    @staticmethod
    def registers_to_bytes(registers: list[int]) -> bytes:
        return b"".join(
            int(register).to_bytes(2, byteorder="big", signed=False)
            for register in registers
        )

    def string_to_registers(self, value: str) -> list[int]:
        encoded = value.encode("utf-8")[: self.MODBUS_MAX_STR_LENGTH]
        payload = len(encoded).to_bytes(2, byteorder="big", signed=False)
        payload += encoded.ljust(self.MODBUS_MAX_STR_LENGTH, b"\x00")
        return self.bytes_to_registers(payload)

    @staticmethod
    def timestamp_to_posix(value: Any) -> int:
        if isinstance(value, Timestamp):
            dt = datetime(
                value.year,
                value.month,
                value.day,
                value.hour,
                value.minute,
                value.second,
            )
            return int(dt.timestamp())

        return int(value)

    async def _read_response_header(self) -> list[int] | None:
        try:
            response = await self._read_input_registers(
                self.MAILBOX_RESPONSE_ADDRESS,
                count=self.RESPONSE_HEADER_REGISTERS,
                device_id=self.DEFAULT_DEVICE_ID,
            )
        except asyncio.TimeoutError:
            return None
        if response.isError():
            return None
        return list(response.registers)

    async def _wait_for_response_ready(self) -> tuple[int, str | None]:
        deadline = asyncio.get_running_loop().time() + self.RESPONSE_TIMEOUT_S
        while True:
            header = await self._read_response_header()
            if header is None:
                return 0, "Error reading modbus response header"

            execution_flag, response_len = header
            if execution_flag == 0:
                return response_len, None
            if execution_flag != 1:
                return 0, f"Execution flag invalid: {execution_flag}"
            if asyncio.get_running_loop().time() >= deadline:
                return 0, "Timeout while waiting for modbus response"
            await asyncio.sleep(self.RESPONSE_POLL_INTERVAL_S)

    async def send_command_and_validate(
        self, command_contract: CommandContract, command: Command
    ) -> Answer:
        """
        Implements the mailbox system described in the firmware Modbus API.
        """
        assert self._modbus_client is not None
        assert self._modbus_client.connected

        if self._has_unsupported_string_index(command_contract, command):
            return Answer(
                "Modbus does not support commands with string index parameters",
                False,
                False,
                command.code,
            )
        while self._lock.locked():
            await asyncio.sleep(0.5)
        async with self._lock:
            last_error: Answer | None = None
            for attempt in range(1, self.MAX_RETRIES + 1):
                start = time.perf_counter()
                answer, should_retry = await self._send_command_once(command_contract, command)
                end = time.perf_counter()
                time_passed = end - start
                answer.field_value_dict[EFieldName.TIMING] = time_passed

                if not should_retry:
                    return answer

                last_error = answer
                self._logger.warning(
                    "Modbus command attempt %d/%d failed for %s: %s",
                    attempt,
                    self.MAX_RETRIES,
                    command,
                    answer.message,
                )

            assert last_error is not None
            return last_error

    async def _send_command_once(
        self, command_contract: CommandContract, command: Command
    ) -> tuple[Answer, bool]:
        payload = self._pack_command_registers(command_contract, command)
        try:
            write_result = await self._write_registers(
                self.MAILBOX_COMMAND_ADDRESS,
                payload,
                device_id=self.DEFAULT_DEVICE_ID,
            )
        except asyncio.TimeoutError:
            return Answer("Timeout writing modbus command", False, True, command.code), True
        if write_result.isError():
            return Answer("Error sending modbus command", False, True, command.code), True

        response_len, error_message = await self._wait_for_response_ready()
        if error_message is not None:
            return Answer(error_message, False, True, command.code), True
        if response_len <= 0:
            return Answer("Empty modbus response", False, True, command.code), True

        try:
            response = await self._read_input_registers(
                self.MAILBOX_RESPONSE_ADDRESS + self.RESPONSE_HEADER_REGISTERS,
                count=response_len,
                device_id=self.DEFAULT_DEVICE_ID,
            )
        except asyncio.TimeoutError:
            return Answer("Timeout reading modbus response", False, True, command.code), True
        if response.isError():
            return Answer("Error reading modbus response", False, True, command.code), True

        payload_registers = list(response.registers)
        response_code = payload_registers[0]
        response_fields = payload_registers[1:]
        response_code_enum = self.resolve_command_code(command, response_code)

        if response_code != int(command.code):
            error_text = self.parse_error_message(response_fields)
            answer = Answer(
                error_text,
                False,
                True,
                response_code_enum,
                field_value_dict={EFieldName.ERROR_MESSAGE: error_text},
            )
            self._queue_message(answer.message)
            return answer, False

        answer_dict = self.registers_to_dict(response_fields, command_contract)
        message = self.answer_message_from_fields(answer_dict)
        answer = Answer(
            message,
            True,
            True,
            response_code_enum,
            field_value_dict=answer_dict,
        )
        self._queue_message(answer.message)
        return answer, False

    def parse_error_message(self, registers: list[int]) -> str:
        if not registers:
            return self.GENERIC_DEVICE_ERROR

        try:
            value, _ = self.parse_param(FieldType(str), registers, 0)
        except Exception:
            return self.GENERIC_DEVICE_ERROR

        return value if isinstance(value, str) and value else self.GENERIC_DEVICE_ERROR

    @staticmethod
    def answer_message_from_fields(answer_dict: dict[Any, Any]) -> str:
        if len(answer_dict) == 1:
            return str(next(iter(answer_dict.values())))
        return str(answer_dict)

    @staticmethod
    def resolve_command_code(command: Command, raw_code: int) -> Any:
        try:
            return command.code.__class__(raw_code)
        except ValueError:
            try:
                return BaseCommandCode(raw_code)
            except ValueError:
                return command.code

    def registers_to_dict(
        self, registers: list[int], command_contract: CommandContract
    ) -> dict[Any, Any]:
        answer_dict: dict[Any, Any] = {}
        field_defs = command_contract.answer_def.field_defs()
        current_index = 0
        for field_def in field_defs:
            value, current_index = self.parse_param(
                field_def.field_type, registers, current_index
            )
            answer_dict[field_def.name] = value
        return answer_dict

    def parse_param(
        self, field_type: FieldType, registers: list[int], current_index: int
    ) -> tuple[Any, int]:
        payload = self.registers_to_bytes(registers[current_index:])
        typ = field_type.field_type

        if typ is bool:
            return bool(payload[1]), current_index + 1
        if typ is np.uint8:
            return np.uint8(payload[1]), current_index + 1
        if typ is np.uint16:
            return np.uint16(int.from_bytes(payload[:2], byteorder="big")), current_index + 1
        if typ is np.uint32:
            return np.uint32(int.from_bytes(payload[:4], byteorder="big")), current_index + 2
        if typ is int:
            return int.from_bytes(payload[:4], byteorder="big"), current_index + 2
        if typ is float:
            return struct.unpack(">f", payload[:4])[0], current_index + 2
        if typ is str:
            str_length = min(
                int.from_bytes(payload[:2], byteorder="big"),
                self.MODBUS_MAX_STR_LENGTH,
            )
            decoded = payload[2:2 + str_length].decode("utf-8", errors="ignore")
            return decoded, current_index + 32
        if typ is Timestamp:
            posix_time = int.from_bytes(payload[:8], byteorder="big", signed=True)
            dt = datetime.fromtimestamp(posix_time)
            return (
                Timestamp(
                    hour=dt.hour,
                    minute=dt.minute,
                    second=dt.second,
                    day=dt.day,
                    month=dt.month,
                    year=dt.year,
                ),
                current_index + 4,
            )
        if typ is Version:
            return (
                Version(
                    major=payload[1],
                    minor=payload[3],
                    patch=payload[5],
                ),
                current_index + 3,
            )
        if isinstance(typ, type) and issubclass(typ, Enum):
            raw_value = int.from_bytes(payload[:2], byteorder="big")
            try:
                return self.firmware_value_to_enum_member(typ, raw_value), current_index + 1
            except (IndexError, ValueError):
                return raw_value, current_index + 1

        raise NotImplementedError(f"Modbus parsing not implemented for {typ}")



async def main():
    connection = ModbusConnection("Test", None, url="/dev/ttyUSB0", baudrate=9600, parity=Parity.EVEN)
    communicator = ModbusCommunicator()
    await communicator.open_communication(connection)#
    protocol = protocol_list.build_protocol_for(ProtocolType(
        Version(3, 0, 0),
        DeviceType.DESCALE
    ))
    command_contract = protocol.command_contracts.get(CommandCode.SET_ON)
    assert command_contract
    answer = await communicator.send_command_and_validate(command_contract, SetOn())
    print(answer)
    command_contract = protocol.command_contracts.get(CommandCode.GET_UPDATE_DESCALE_V3_0_0)
    assert command_contract
    answer = await communicator.send_command_and_validate(command_contract, GetUpdateDescale())
    print(answer)
    command_contract = protocol.command_contracts.get(CommandCode.GET_UPDATE_DESCALE_V3_0_0)
    assert command_contract
    answer = await communicator.send_command_and_validate(command_contract, GetUpdateDescale())
    print(answer)
    command_contract = protocol.command_contracts.get(CommandCode.GET_UPDATE_DESCALE_V3_0_0)
    assert command_contract
    answer = await communicator.send_command_and_validate(command_contract, GetUpdateDescale())
    print(answer)
    command_contract = protocol.command_contracts.get(CommandCode.SET_OFF)
    assert command_contract
    answer = await communicator.send_command_and_validate(command_contract, SetOff())
    print(answer)
    command_contract = protocol.command_contracts.get(CommandCode.SET_SWF)
    assert command_contract
    answer = await communicator.send_command_and_validate(command_contract, SetSwf(5))
    print(answer)
    command_contract = protocol.command_contracts.get(CommandCode.GET_SWF)
    assert command_contract
    answer = await communicator.send_command_and_validate(command_contract, GetSwf())
    print(answer)

if __name__ == "__main__":
    asyncio.run(main())