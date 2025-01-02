import asyncio
import logging
import time
from typing import Final, Optional, List

import attrs
from soniccontrol.communication.connection_factory import ConnectionFactory, SerialConnectionFactory
from soniccontrol.communication.message_fetcher import MessageFetcher
from soniccontrol.command import LegacyCommand
from soniccontrol.communication.communicator import Communicator
from soniccontrol.communication.message_protocol import CommunicationProtocol, LegacyProtocol, SonicMessageProtocol
from soniccontrol.events import Event
from soniccontrol.system import PLATFORM

@attrs.define
class SerialCommunicator(Communicator):
    BAUDRATE: Final[int] = 9600
    MESSAGE_ID_MAX_CLIENT: Final[int] = 2 ** 16 - 1 # 65535 is the max for uint16. so we cannot go higher than that.

    _connection_opened: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)
    _answer_queue: asyncio.Queue[LegacyCommand] = attrs.field(
        init=False, factory=asyncio.Queue, repr=False
    )
    _reader: Optional[asyncio.StreamReader] = attrs.field(
        init=False, default=None, repr=False
    )
    _writer: Optional[asyncio.StreamWriter] = attrs.field(
        init=False, default=None, repr=False
    )
    _lock: asyncio.Lock = attrs.field(default=asyncio.Lock())
    _logger: logging.Logger = attrs.field(default=logging.getLogger())

    _restart: bool = attrs.field(default=False, init=False)
    _message_counter: int = attrs.field(default=0, init=False)

    def __attrs_post_init__(self) -> None:
        self._logger = logging.getLogger(self._logger.name + "." + SerialCommunicator.__name__)
        #self._logger.setLevel("INFO") # FIXME is there a better way to set the log level?
        self._protocol: CommunicationProtocol = SonicMessageProtocol(self._logger)

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
    
    @property
    def handshake_result(self) -> str:
        # Todo: define with Thomas how we make a handshake
        return ""

    async def open_communication(
        self, connection_factory: ConnectionFactory,
        baudrate = BAUDRATE
    ) -> None:
        self._connection_factory = connection_factory
        self._logger.debug("try open communication")
        if isinstance(connection_factory, SerialConnectionFactory):
            connection_factory.baudrate = baudrate

        self._restart = False 
        self._reader, self._writer = await connection_factory.open_connection()
        #self._writer.transport.set_write_buffer_limits(0) #Quick fix
        self._protocol = SonicMessageProtocol(self._logger)
        self._package_fetcher = MessageFetcher(self._reader, self._protocol, self._logger)
        self._connection_opened.set()
        self._writer.write(b'\n')
        await self._writer.drain()
        self._package_fetcher.run()

    async def _send_chunks(self, message: bytes) -> None:
        assert self._writer

        total_length = len(message)  # TODO Quick fix for sending messages in small chunks
        offset = 0
        chunk_size=30 # Messages longer than 30 characters could not be sent
        delay = 1

        async with self._lock:
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
        assert self._package_fetcher.is_running

        if request_str != "-":
            self._logger.info("Send command: %s", request_str)

        self._message_counter = (self._message_counter + 1) % self.MESSAGE_ID_MAX_CLIENT
        message_counter = self._message_counter

        message = self._protocol.parse_request(
            request_str, message_counter
        )

        if request_str != "-":
            self._logger.info("Write package: %s", message)
        encoded_message = message.encode(PLATFORM.encoding)

        # FIXME: Quick fix. We have a weird error that the buffer does not get flushed somehow
        await self._send_chunks(encoded_message)

        response =  await self._package_fetcher.get_answer_of_request(
            message_counter
        )
        if request_str != "-":
            self._logger.info("Receive Answer: %s", response)

        return response

    async def send_and_wait_for_response(self, request: str, **kwargs) -> str:
        if not self._connection_opened.is_set():
            raise ConnectionError("Communicator is not connected")

        timeout = 3 # in seconds
        MAX_RETRIES = 3 
        for i in range(MAX_RETRIES):
            try:
                return await asyncio.wait_for(self._send_and_get(request), timeout)
            except asyncio.TimeoutError:
                self._logger.warn("%d th attempt of %d. Device did not respond in the given timeout of %f s when sending %s", i, MAX_RETRIES, timeout, request)
        
        if self._connection_opened.is_set():
            await self.close_communication()
            raise ConnectionError("Device is not responding")
        else:
            raise ConnectionError("The connection was closed")
    
    async def read_message(self) -> str:
        return await self._package_fetcher.pop_message()

    async def close_communication(self, restart : bool = False) -> None:
        self._restart = restart
        await self._package_fetcher.stop()
        self._connection_opened.clear()
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
        self._reader = None
        self._writer = None
        self._logger.info("Disconnected from device")
        if not(self._restart):
            self.emit(Event(Communicator.DISCONNECTED_EVENT))

    async def change_baudrate(self, baudrate: int) -> None:
        await self.close_communication(restart=True)
        await self.open_communication(self._connection_factory, baudrate)


@attrs.define
class LegacySerialCommunicator(Communicator):   
    BAUDRATE = 115200

    _init_command: LegacyCommand = attrs.field(init=False)
    _connection_opened: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)
    _connection_closed: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)
    _lock: asyncio.Lock = attrs.field(init=False, factory=asyncio.Lock, repr=False)

    _reader: Optional[asyncio.StreamReader] = attrs.field(
        init=False, default=None, repr=False
    )
    _writer: Optional[asyncio.StreamWriter] = attrs.field(
        init=False, default=None, repr=False
    )
    _logger: logging.Logger = attrs.field(default=logging.getLogger())

    def __attrs_post_init__(self) -> None:
        self._logger = logging.getLogger(self._logger.name + "." + LegacySerialCommunicator.__name__)
        self._protocol: CommunicationProtocol = LegacyProtocol()
        self._restart = False
        self._handshake = ""
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

    @property
    def connection_closed(self) -> asyncio.Event:
        return self._connection_closed

    @property
    def handshake_result(self) -> str:
        return self._handshake

    async def open_communication(
        self, connection_factory: ConnectionFactory, baudrate: int = BAUDRATE
    ) -> None:
        self._connection_factory = connection_factory
        
        if isinstance(connection_factory, SerialConnectionFactory):
            connection_factory.baudrate = baudrate
            self._url = connection_factory.url

        self._restart = False
        self._reader, self._writer = await connection_factory.open_connection()
        self._logger.info("Open communication with handshake")
        self._handshake = await self.read_long_message(reading_time=6)
        self._logger.info(self._handshake)

        self._connection_opened.set()

    async def _send_and_get(self, request: str, response_time: float = 5., expects_long_answer: bool = False) -> str:
        assert (self._writer is not None)
        if request != "-":
            self._logger.info("Write command: %s", request)

        encoded_request = request.encode(PLATFORM.encoding)
        self._writer.write(encoded_request)
        await self._writer.drain()

        if request == "?info":
            reading_time = 1  # FIXME Quick fix, newer device take longer to respond, so only part of the message gets recieved and then the package parser fails
        else:
            reading_time = 0.2
        response = await (
            self.read_long_message(response_time=response_time, reading_time=reading_time)
            if expects_long_answer
            else self._read_message()
        )

        if request != "-":
            self._logger.info("Received Answer: %s", response)
        return response

    async def send_and_wait_for_response(self, request: str, **kwargs) -> str:
        if not self.connection_opened.is_set():
            raise ConnectionError("Communicator is not connected")

        async with self._lock:
            timeout =  10 # in seconds
            try:
                return await asyncio.wait_for(self._send_and_get(request, **kwargs), timeout)
            except asyncio.TimeoutError:
                raise ConnectionError("Device is not responding")

    async def read_message(self) -> str:
        async with self._lock:
            try:
                msg = await asyncio.wait_for(self._read_message(), 1)
                return msg
            except asyncio.TimeoutError:
                return ""

    async def _read_message(self) -> str:
        message: str = ""
        await asyncio.sleep(0.2)
        if self._reader is None:
            return message
        try:
            response = await self._reader.readline()
            message = response.decode(PLATFORM.encoding).strip()
        except Exception as e:
            self._logger.error(str(e))
        return message

    async def read_long_message(
        self, response_time: float = 0.3, reading_time: float = 0.2
    ) -> str:
        if self._reader is None:
            return ""

        target = time.time() + reading_time
        lines: List[str] = []
        while time.time() < target:
            try:
                response = await asyncio.wait_for(
                    self._reader.readline(), timeout=response_time
                )
                line = response.decode(PLATFORM.encoding).strip()
                lines.append(line)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self._logger.error(str(e))
                break

        message = "\n".join(lines)
        return message

    async def close_communication(self, restart : bool = False) -> None:
        self._restart = restart
        self._connection_opened.clear()
        self._connection_closed.set()
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
        self._reader = None
        self._writer = None
        if not(self._restart):
            self.emit(Event(Communicator.DISCONNECTED_EVENT))

    async def change_baudrate(self, baudrate: int) -> None:
        await self.close_communication(restart=True)
        await self.open_communication(self._connection_factory, baudrate)
