import asyncio
import logging
from typing import Final, Optional

import attrs
from soniccontrol.communication.connection import Connection, SerialConnection
from soniccontrol.communication.message_fetcher import MessageFetcher
from soniccontrol.communication.communicator import Communicator
from soniccontrol.communication.message_protocol import CommunicationProtocol, SonicMessageProtocol
from soniccontrol.app_config import ENCODING
from soniccontrol.events import Event
from soniccontrol.app_config import PLATFORM, System

@attrs.define()
class SerialCommunicator(Communicator):
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

    _restart: bool = attrs.field(default=False, init=False)
    _message_counter: int = attrs.field(default=0, init=False)

    def __attrs_post_init__(self) -> None:
        self._logger = logging.getLogger(self._logger.name + "." + SerialCommunicator.__name__)
        #self._logger.setLevel("INFO") # FIXME is there a better way to set the log level?
        self._protocol: CommunicationProtocol = SonicMessageProtocol()
        super().__init__()

    @property
    def connection_opened(self) -> asyncio.Event:
        return self._connection_opened
    
    def set_device_log_handler(self, handler: logging.Handler) -> None:
        self._message_fetcher._device_logger.addHandler(handler)

    async def open_communication(
        self, connection: Connection,
        baudrate = 9600
    ) -> None:
        self._connection = connection
        self._logger.debug("try open communication")
        if isinstance(connection, SerialConnection):
            connection.baudrate = baudrate

        self._restart = False 
        self._reader, self._writer = await self._connection.open_connection()
        #self._writer.transport.set_write_buffer_limits(0) #Quick fix
        self._message_fetcher = MessageFetcher(self._reader, self._logger)
        await self._writer.drain()
        self._message_fetcher.run()
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

    async def _send_and_get(self, request_str: str, **kwargs) -> str:
        assert self._writer is not None
        assert self._message_fetcher.is_running

        async with self._lock:
            if request_str != "-":
                self._logger.info("Send command: %s", request_str)

            self._message_counter = (self._message_counter + 1) % self.MESSAGE_ID_MAX_CLIENT
            message_counter = self._message_counter

            message = self._protocol.parse_request(
                request_str, message_counter, **kwargs
            )

            if request_str != "-":
                self._logger.info("Write package: %s", message)
            encoded_message = message.encode(ENCODING)

            
            if PLATFORM == System.WINDOWS:
                # FIXME: Quick fix. We have a weird error that the buffer does not get flushed somehow
                await self._send_chunks(encoded_message)    
            else:
                self._writer.write(encoded_message)
                await self._writer.drain()

            # FIXME: to move the awaiting of the response inside the lock is only a quickfix, because the code on
            # the device of the uart needs to be refactored, so that it can handle messaging bursts.
            response =  await self._message_fetcher.get_answer_of_request(
                message_counter
            )
            if request_str != "-":
                self._logger.info("Receive Answer: %s", response)

            return response

    async def send_and_wait_for_response(self, request: str, **kwargs) -> str:
        if not self._connection_opened.is_set():
            raise ConnectionError("Communicator is not connected")

        timeout = 5 # in seconds
        MAX_RETRIES = 3 
        for i in range(MAX_RETRIES):
            try:
                return await asyncio.wait_for(self._send_and_get(request, **kwargs), timeout)
            except asyncio.TimeoutError:
                self._logger.warn("%d th attempt of %d. Device did not respond in the given timeout of %f s when sending %s", i, MAX_RETRIES, timeout, request)
            
            # The message fetcher runs as a task and its exceptions are not propagated
            # so we have to check here (or somewhere else) if it raised an error
            if self._message_fetcher.exception:
                raise self._message_fetcher.exception

        if self._connection_opened.is_set():
            await self.close_communication()
            raise ConnectionError("Device is not responding")
        else:
            raise ConnectionError("The connection was closed")
    
    async def read_message(self) -> str:
        return await self._message_fetcher.pop_message()

    async def close_communication(self, restart : bool = False) -> None:
        self._restart = restart
        await self._message_fetcher.stop()
        self._connection_opened.clear()
        await self._connection.close_connection()
        self._reader = None
        self._writer = None
        self._logger.info("Disconnected from device")
        if not(self._restart):
            self.emit(Event(Communicator.DISCONNECTED_EVENT))


