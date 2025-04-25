import asyncio
import logging
from pathlib import Path
from typing import Final, List, Optional

import attrs
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.defs import CommandContract, Protocol
from soniccontrol.communication.connection import Connection, SerialConnection
from soniccontrol.communication.communicator import Communicator
from soniccontrol.communication.message_protocol import CommunicationProtocol, SonicMessageProtocol
from soniccontrol.app_config import ENCODING
from soniccontrol.events import Event
from soniccontrol.app_config import PLATFORM, System

@attrs.define()
class LegacyCommunicator(Communicator):
    MESSAGE_ID_MAX_CLIENT: Final[int] = 2 ** 16 - 1 # 65535 is the max for uint16. so we cannot go higher than that.

    _connection_opened: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)
    _reader: Optional[asyncio.StreamReader] = attrs.field(
        init=False, default=None, repr=False
    )
    _writer: Optional[asyncio.StreamWriter] = attrs.field(
        init=False, default=None, repr=False
    )
    _logger: logging.Logger = attrs.field(default=logging.getLogger())
    _protocol: Protocol = attrs.field(default=None)

    _command_queue: asyncio.Queue = attrs.field(default=asyncio.Queue(), init=False)
    _restart: bool = attrs.field(default=False, init=False)
    _message_counter: int = attrs.field(default=0, init=False)

    def __attrs_post_init__(self) -> None:
        self._logger = logging.getLogger(self._logger.name + "." + LegacyCommunicator.__name__)
        self._device_logger: logging.Logger = logging.getLogger(self._logger.name + ".device")
        self._logger.setLevel("DEBUG") # FIXME is there a better way to set the log level?

        #self._logger.setLevel("INFO") # FIXME is there a better way to set the log level?
        self._messages = asyncio.Queue(maxsize=100)
        self._send_lock = asyncio.Lock()



        super().__init__()

    @property 
    def writer(self) -> asyncio.StreamWriter: 
        assert self._writer
        return self._writer

    @property 
    def reader(self) -> asyncio.StreamReader: 
        assert self._reader
        return self._reader

    @property
    def protocol(self) -> CommunicationProtocol: 
        return self._protocol

    @property
    def connection_opened(self) -> asyncio.Event:
        return self._connection_opened
    
    async def open_communication(
        self, connection: Connection,
        baudrate = 115200
    ) -> None:
        self._connection = connection
        self._logger.info("try open communication")
        if isinstance(connection, SerialConnection):
            connection.baudrate = baudrate

        self._restart = False 
        self._reader, self._writer = await self._connection.open_connection()
        #self._writer.write(b"!SERIAL\n")
        #await self._writer.drain()
        timeout = 10  # Crystal devices takes a long time to respond after connecting
        while True:
            try:
                answer = await asyncio.wait_for(self._reader.readline(), timeout=timeout)
                timeout = 0.2 # Change timeout back so we dont have to wait for 10 after the last line
                self._logger.info("Received: %s", answer)
                #self._answer_lines.append(answer.strip())
            except asyncio.TimeoutError:
                self._logger.info("Timeout while waiting for connection")
                break
        

        self._serial_master_task = asyncio.create_task(self._serial_master())
        self._connection_opened.set()

    async def _serial_master(self) -> None:
        assert self._reader is not None
        assert self._writer is not None
        while True:
            try:
                command, code, future = self._command_queue.get_nowait()
            except asyncio.QueueEmpty:
                command, code, future = None, None, None
            if command is not None and code is not None:
                await self._check_for_unexpected_message() # Before sending command, check if there is an unexpected message
                self._writer.write(command.encode(ENCODING))
                await self._writer.drain()
                try:
                    message = await self._wait_for_response(command, code)
                    try:
                        self._messages.put_nowait(message)
                    except asyncio.QueueFull:
                        self._messages.get_nowait()  # Remove the oldest
                        self._messages.put_nowait(message)
                    self._device_logger.info("Expected: %s", message.strip())
                    if future is not None and not future.done():
                        future.set_result(message)
                        self._logger.info("Set result for future")
                except asyncio.TimeoutError:
                    # send_and_wait_for_response is responsbile for handling the timeout and termination the connection
                    if future is not None and not future.done():
                        future.set_exception(asyncio.TimeoutError("Timeout while waiting for response"))
                    else:
                        assert False, "Future should not be None if we are waiting for a response"
            else:
                await self._check_for_unexpected_message()

    async def _check_for_unexpected_message(self) -> None:
        assert self._reader is not None
        try:
            answer = await asyncio.wait_for(self._reader.readline(), timeout=0.3)
            message = answer.decode(ENCODING)
            try:
                self._messages.put_nowait(message)
            except asyncio.QueueFull:
                self._messages.get_nowait()  # Remove the oldest
                self._messages.put_nowait(message)
            self._device_logger.info("Unexpected: %s", message.strip())
            self._handle_unexpected_message(message)
        except asyncio.TimeoutError:
            pass

    def _handle_unexpected_message(self, message: str) -> None:
        # TODO
        # if(message.startswith("f="")):
        #     send_freq_event()
        #
        return

    async def _wait_for_response(self, command: str, code: int) -> str:
        assert self._reader is not None
        timeout = 0.5 if command.strip() != "-" else 1
        message = str(code) + "#"
        for _ in range(self._get_number_of_lines(code)):
            try:
                answer = await asyncio.wait_for(self._reader.readline(), timeout=timeout)
                message += answer.decode(ENCODING)
            except asyncio.TimeoutError:
                raise asyncio.TimeoutError("Timeout while waiting for response")
        if command.strip() != "-":
            self._logger.info("Received: %s", message)
        return message

    def _get_number_of_lines(self, code: int) -> int:
        if code == CommandCode.GET_INFO:
            return 3
        elif code == CommandCode.GET_PVAL:
            return 4
        return 1

    async def _send_and_get(self, request_str: str) -> str:
        try:
            if request_str != "-":
                self._logger.info("Send command: %s", request_str)
            request_str = request_str + '\n'
            future = asyncio.get_event_loop().create_future()
            code = self.deduce_command_code(request_str)
            if code != 3:
                self._logger.info("Got command code: %s", code)
            await self._command_queue.put((request_str, code, future))
            if request_str.strip() != "-":
                self._logger.info("Sending: %s", request_str)
            answer = await future
            if request_str.strip() != "-":
                self._logger.info("Received: %s", answer)
        except asyncio.TimeoutError:
            # send_and_wait_for_response is responsbile for handling the timeout and termination the connection
            raise asyncio.TimeoutError("Timeout while waiting for response")
        return answer

    async def send_and_wait_for_response(self, request: str, **kwargs) -> str:
        if not self._connection_opened.is_set():
            raise ConnectionError("Communicator is not connected")
        async with self._send_lock:
            MAX_RETRIES = 3 
            for i in range(1, MAX_RETRIES + 1):
                try:
                    return await self._send_and_get(request)
                except asyncio.TimeoutError:
                    self._logger.warn("%d th attempt of %d. Device did not respond when sending %s", i, MAX_RETRIES, request)
                
                # The message fetcher runs as a task and its exceptions are not propagated
                # so we have to check here (or somewhere else) if it raised an error

            if self._connection_opened.is_set():
                await self.close_communication()
                raise ConnectionError("Device is not responding")
            else:
                raise ConnectionError("The connection was closed")
    
    async def read_message(self) -> str:
        return await self._messages.get()

    async def close_communication(self, restart : bool = False) -> None:
        self._serial_master_task.cancel()
        try:
            await self._serial_master_task
        except asyncio.CancelledError:
            self._logger.info("Serial master task cancelled")
        self._restart = restart
        self._connection_opened.clear()
        await self._connection.close_connection()
        self._reader = None
        self._writer = None
        self._logger.info("Disconnected from device")
        if not(self._restart):
            self.emit(Event(Communicator.DISCONNECTED_EVENT))

    async def change_baudrate(self, baudrate: int) -> None:
        await self.close_communication(restart=True)
        await self.open_communication(self._connection, baudrate)

    def deduce_command_code(self, request_str: str) -> int:
        code = 0
        for export in self._protocol.commands:
                commands: List[CommandContract] = export.exports if isinstance(export.exports, list) else [export.exports]
                for command in commands:
                    if command.command_defs is not None and not isinstance(command.command_defs, list):
                        if isinstance(command.command_defs.sonic_text_attrs, list):
                            for attr in command.command_defs.sonic_text_attrs:
                                if hasattr(attr, "string_identifier") and getattr(attr, "string_identifier") is not None:
                                    string_identifier = getattr(attr, "string_identifier")
                                    if string_identifier in request_str:
                                        code = command.code
                        elif command.command_defs.sonic_text_attrs.string_identifier is not None and (
                            (isinstance(command.command_defs.sonic_text_attrs.string_identifier, str) and command.command_defs.sonic_text_attrs.string_identifier in request_str) or
                            (isinstance(command.command_defs.sonic_text_attrs.string_identifier, list) and any(req in request_str for req in command.command_defs.sonic_text_attrs.string_identifier))
                        ):
                            code = command.code
                    elif command.command_defs is not None and isinstance(command.command_defs, list): 
                        for def_entry in command.command_defs:
                            if def_entry is not None and not isinstance(def_entry.exports, list):
                                if isinstance(def_entry.exports.sonic_text_attrs, list):
                                    for attr in def_entry.exports.sonic_text_attrs:
                                        if hasattr(attr, "string_identifier") and getattr(attr, "string_identifier") is not None:
                                            string_identifier = getattr(attr, "string_identifier")
                                            if request_str in string_identifier:
                                                code = command.code
                            elif def_entry is not None and isinstance(def_entry.exports, list):
                                for export in def_entry.exports:
                                    if isinstance(export.sonic_text_attrs, list):
                                        for attr in export.sonic_text_attrs:
                                            if hasattr(attr, "string_identifier") and getattr(attr, "string_identifier") is not None:
                                                string_identifier = getattr(attr, "string_identifier")
                                                if request_str in string_identifier:
                                                    code = command.code
                                    elif export.sonic_text_attrs.string_identifier is not None and request_str in export.sonic_text_attrs.string_identifier:
                                        code = command.code
        return code


async def main():
    # Example usage
    url = "COM19"
    connection = SerialConnection(url=url, baudrate=115200, connection_name=Path(url).name)
    communicator = LegacyCommunicator()
    await communicator.open_communication(connection)
    response = await communicator.send_and_wait_for_response("?info\n")
    print("Response:", response)
    message = ""
    while message != "No message":
        message = await communicator.read_message()
        print("Message:", message)
    await communicator.close_communication()
    # Example of sending a message
    # Add your connection setup and usage here

if __name__ == "__main__":
    asyncio.run(main())