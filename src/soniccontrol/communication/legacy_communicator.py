import asyncio
import logging
from pathlib import Path
from typing import Final, List, Optional

import attrs
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
    _lock: asyncio.Lock = attrs.field(default=asyncio.Lock())
    _logger: logging.Logger = attrs.field(default=logging.getLogger())
    _protocol: Protocol = attrs.field(default=None)


    _restart: bool = attrs.field(default=False, init=False)
    _message_counter: int = attrs.field(default=0, init=False)

    def __attrs_post_init__(self) -> None:
        self._logger = logging.getLogger(self._logger.name + "." + LegacyCommunicator.__name__)
        #self._logger.setLevel("INFO") # FIXME is there a better way to set the log level?
        self._messages = asyncio.Queue(maxsize=100)


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
        self._logger.debug("try open communication")
        if isinstance(connection, SerialConnection):
            connection.baudrate = baudrate

        self._restart = False 
        self._reader, self._writer = await self._connection.open_connection()
        #self._writer.write(b"!SERIAL\n")
        await self._writer.drain()
        await asyncio.sleep(10) # The sonic crystal takes very long until it is ready.
        while True:
            try:
                answer = await asyncio.wait_for(self._reader.readline(), timeout=0.2)
                self._logger.debug("Received: %s", answer)
                #self._answer_lines.append(answer.strip())
            except asyncio.TimeoutError:
                self._logger.debug("Timeout while waiting for connection")
                break
        self._connection_opened.set()

    async def _send_chunks(self, message: bytes) -> None:
        assert self._writer

        total_length = len(message)  # TODO Quick fix for sending messages in small chunks
        offset = 0
        chunk_size=30 # Messages longer than 30 characters could not be sent
        delay = 1

        
        while offset < total_length:
            # Extract a chunk of data
            chunk = message[offset:offset + chunk_size]
            
            # Write the chunk to the writer
            self._writer.write(chunk)
            
            # Drain the writer to ensure it's flushed to the transport
            await self._writer.drain()

            # Move to the next chunk
            offset += chunk_size
            
            # Sleep for the given delay between chunks skip the last pause
            if offset < total_length:
                # Debugging output
                #self._logger.debug(f"Wrote chunk: {chunk}. Waiting for {delay} seconds before sending the next chunk.")
                await asyncio.sleep(delay)
            else:
                pass
                    #self._logger.debug(f"Wrote last chunk: {chunk}.")
        #self._logger.debug("Finished sending all chunks.")

    async def _send_and_get(self, request_str: str) -> str:
        assert self._writer is not None
        assert self._reader is not None

        async with self._lock:
            if request_str != "-":
                self._logger.info("Send command: %s", request_str)
            code = self.deduce_command_code(request_str)
            request_str = request_str + '\n'
            if PLATFORM == System.WINDOWS:
                # FIXME: Quick fix. We have a weird error that the buffer does not get flushed somehow
                await self._send_chunks(request_str.encode("utf-8"))    
            else:
                self._writer.write(request_str.encode("utf-8"))
                await self._writer.drain()
            
            
            #self._logger.info("Found command code: %s", code)
            answer = str(code) + "#"
            while True:
                try:
                    answer_byte = await asyncio.wait_for(self._reader.readline(), timeout=0.5)
                    answer += answer_byte.decode().strip()
                except asyncio.TimeoutError:
                    self._logger.debug("Timeout while waiting for connection")
                    break
            self._logger.debug("Received: %s", answer)
            self._messages.put_nowait(answer)
            if request_str != "-":
                self._logger.info("Receive Answer: %s", answer)
            return answer

    async def send_and_wait_for_response(self, request: str, **kwargs) -> str:
        if not self._connection_opened.is_set():
            raise ConnectionError("Communicator is not connected")

        timeout = 5 # in seconds
        MAX_RETRIES = 3 
        for i in range(MAX_RETRIES):
            try:
                return await asyncio.wait_for(self._send_and_get(request), timeout)
            except asyncio.TimeoutError:
                self._logger.warn("%d th attempt of %d. Device did not respond in the given timeout of %f s when sending %s", i, MAX_RETRIES, timeout, request)
            
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