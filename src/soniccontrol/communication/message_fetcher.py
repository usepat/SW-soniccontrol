import asyncio
import logging
from typing import Dict
from asyncio import StreamReader

from soniccontrol.communication.message_protocol import SonicMessageProtocol
from soniccontrol.system import PLATFORM


class MessageFetcher:
    def __init__(self, reader: StreamReader, protocol: SonicMessageProtocol, logger: logging.Logger = logging.getLogger()) -> None:
        self._reader = reader
        self._answers: Dict[int, str] = {}
        self._answer_received: Dict[int, asyncio.Event] = {}
        self._messages = asyncio.Queue(maxsize=100)
        self._task = None
        self._protocol: SonicMessageProtocol = protocol
        self._logger: logging.Logger = logging.getLogger(logger.name + "." + MessageFetcher.__name__)

    async def get_answer_of_request(self, request_id: int) -> str:
        if request_id not in self._answer_received:
            self._answer_received[request_id] = asyncio.Event()

        flag = self._answer_received[request_id]
        await flag.wait()
        flag.clear()
        self._answer_received.pop(request_id)

        answer: str = self._answers.pop(request_id)
        return answer

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    def run(self) -> None:
        self._logger.debug("Start package fetcher")
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        self._logger.debug("Stop package fetcher")
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _worker(self) -> None:
        COMMAND_CODE_DASH = "20"

        while True:
            try:
                response = await self._read_response()
                self._queue_message(response)
                answer_id, answer = self._protocol.parse_response(response)
            except asyncio.CancelledError:
                self._logger.info("Package fetcher was stopped")
                return
            except Exception as e:
                self._logger.error("Exception occured while reading the package:\n%s", e)
                return

            if answer:
                if answer.startswith(COMMAND_CODE_DASH):
                    self._logger.info("Read package: %s", response)
            
                self._answers[answer_id] = answer

                if answer_id not in self._answer_received:
                    self._answer_received[answer_id] = asyncio.Event()
                self._answer_received[answer_id].set()
                

    async def _read_response(self) -> str:
        if self._reader is None:
            raise RuntimeError("reader was not initialized")

        message_terminator = self._protocol.separator
        data = await self._reader.readuntil(
            message_terminator.encode(PLATFORM.encoding)
        ) 
        message = data.decode(PLATFORM.encoding)
        message = message[:-1] # remove separator at the end
        return message
    
    def _queue_message(self, message: str) -> None:
        try:
            self._messages.put_nowait(message)
        except asyncio.QueueFull:
            self._messages.get_nowait()
            self._messages.put_nowait(message)

    async def pop_message(self) -> str:
        return await self._messages.get()
