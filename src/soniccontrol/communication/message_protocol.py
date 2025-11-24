from enum import Enum
import logging
from typing import Any
import abc
import attrs

from sonic_protocol.schema import Version


class ProtocolType(Enum):
    SONIC_MESSAGE_PROTOCOL = "Sonic Message Protocol"

class CommunicationProtocol:
    @property
    def separator(self) -> str:
        return "\0"

    @abc.abstractmethod
    def parse_response(self, response: str) -> Any: ...

    @abc.abstractmethod
    def parse_request(self, request: str, request_id: int) -> Any: ...

    @abc.abstractmethod
    def prot_type(self) -> ProtocolType: ...

    @property
    @abc.abstractmethod
    def version(self) -> Version: ...


class DeviceLogLevel(Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"

@attrs.define()
class Message:
    content: str = attrs.field()

@attrs.define()
class CommandMessage(Message):
    msg_id: int = attrs.field()

@attrs.define()
class AnswerMessage(Message):
    msg_id: int = attrs.field()

@attrs.define()
class NotifyMessage(Message):
    pass

@attrs.define()
class LogMessage(Message):
    log_level: DeviceLogLevel = attrs.field()

class SonicMessageProtocol(CommunicationProtocol):
    LOG_PREFIX = "LOG"
    ANSWER_PREFIX = "ANS"
    COMMAND_PREFIX = "COM"
    NOTIFY_PREFIX = "NOTIFY"

    @property
    def separator(self) -> str:
        return "\r"

    @staticmethod
    def _extract_log_level(log: str) -> DeviceLogLevel:
        log_level_str = log[log.index("=")+1:log.index(":")]
        try:
            return DeviceLogLevel[log_level_str]
        except (KeyError, ValueError):
            raise SyntaxError("Could not parse log level")

    def parse_response(self, response: str) -> Message:
        """
        returns:
        A Tuple with 
        - the package id
        - The answer (if the package contains an answer)
        """
        response = response.strip()
        if response.startswith(SonicMessageProtocol.ANSWER_PREFIX):
            response_id = int(response[response.index("#")+1:response.index("=")])
            content = response[response.index("=")+1:]
            return AnswerMessage(content, response_id)
        elif response.startswith(SonicMessageProtocol.NOTIFY_PREFIX):
            content = response[response.index("=")+1:]
            return NotifyMessage(content)
        elif response.startswith(SonicMessageProtocol.LOG_PREFIX):
            log_level = SonicMessageProtocol._extract_log_level(response)
            log_msg = response[response.index(":")+1:]
            return LogMessage(log_msg, log_level)
        else:
            raise SyntaxError("Could not parse response: " + response)

    def parse_request(self, request: str, request_id: int) -> str:
        # The \n at the end ensures that terminals in canonical mode read in the whole message
        return f"{SonicMessageProtocol.COMMAND_PREFIX}#{request_id}={request}{self.separator}"
    
    @abc.abstractmethod
    def prot_type(self) -> ProtocolType:
        return ProtocolType.SONIC_MESSAGE_PROTOCOL

    @property
    @abc.abstractmethod
    def version(self) -> Version:
        return Version(2, 0, 0)

