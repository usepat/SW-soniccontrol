import asyncio
import logging
from typing import Dict
from asyncio import StreamReader

from soniccontrol.communication.message_protocol import SonicMessageProtocol, Message, AnswerMessage, LogMessage, NotifyMessage, DeviceLogLevel
from soniccontrol.app_config import ENCODING


class MessageFetcher:
    def __init__(self, reader: StreamReader, logger: logging.Logger = logging.getLogger()) -> None:
        self._reader = reader
        self._answers: Dict[int, str] = {}
        self._answer_received: Dict[int, asyncio.Event] = {}
        self._messages = asyncio.Queue(maxsize=100)
        self._task = None
        self._protocol = SonicMessageProtocol()
        self._logger: logging.Logger = logging.getLogger(logger.name + "." + MessageFetcher.__name__)
        self._device_logger: logging.Logger = logging.getLogger(logger.name + ".device")


    @property
    def exception(self) -> BaseException | None:
        if self._task is not None and self._task.done():
            return self._task.exception()
        return None

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
        self._logger.debug("Start message fetcher")
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        self._logger.debug("Stop message fetcher")

        if self._task is not None:
            try:
                self._task.cancel()
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                self._logger.error(str(e))
            self._task = None

    def _convert_log_levels(self, log_level: DeviceLogLevel) -> int:
        match log_level:
            case DeviceLogLevel.INFO:
                return logging.INFO
            case DeviceLogLevel.WARN:
                return logging.WARN
            case DeviceLogLevel.ERROR:
                return logging.ERROR
            case DeviceLogLevel.DEBUG:
                return logging.DEBUG

    async def _worker(self) -> None:
        # TODO: use the command_code_dash from the protocol directly or inject it
        COMMAND_CODE_DASH = "20"

        response = ""
        while True:
            try:
                response = await self._read_response()
                self._queue_message(response)
                message: Message = self._protocol.parse_response(response)
            except asyncio.CancelledError:
                self._logger.info("Message fetcher was stopped")
                return
            except asyncio.IncompleteReadError as e:
                #self._logger.warning("Encountered EOF or reached max length before reading separator:\n%s", e.partial)
                if len(e.partial) > 0:
                    decoded_trash_read = e.partial.decode(ENCODING)
                    self._logger.error(f"Read undefined expected bytes: {decoded_trash_read}")
                    raise e
                # I dont think we can ignore because when the simulation exits how else do we detect that something is wrong?
                continue # ignore eof. happens if empty strings get send
            except SyntaxError as e:
                self._logger.error(e)
                continue
            except Exception as e:
                self._logger.error("Exception occured while reading the package:\n%s", e)
                raise e 

            if isinstance(message, AnswerMessage):
                if message.content.startswith(COMMAND_CODE_DASH):
                    self._logger.info("Read message: %s", response)
            
                self._answers[message.msg_id] = message.content

                if message.msg_id not in self._answer_received:
                    self._answer_received[message.msg_id] = asyncio.Event()
                self._answer_received[message.msg_id].set()
            elif isinstance(message, NotifyMessage):
                pass # TODO: implement producer consumer architecture here for notify events. We need a NotificationFetcher class similar to updater
            elif isinstance(message, LogMessage):
                log_level = self._convert_log_levels(message.log_level)
                self._device_logger.log(log_level, message.content)
            else:
                raise Exception(f"Received unexpected message type: {type(message)}, content is: {message.content}")
                

    async def _read_response(self) -> str:
        if self._reader is None:
            raise RuntimeError("reader was not initialized")

        message_terminator = self._protocol.separator
        data = await self._reader.readuntil(
            message_terminator.encode(ENCODING)
        ) 
        message = data.decode(ENCODING)
        message = message[:-1] # remove separator at the end
        return message
    
    def _queue_message(self, message: str) -> None:
            if self._messages.full():
                self._messages.get_nowait()
            self._messages.put_nowait(message)

    async def pop_message(self) -> str:
        return await self._messages.get()
