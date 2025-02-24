from enum import Enum
import logging
from typing import Any
import abc


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
    def major_version(self) -> int: ...


class DeviceLogLevel(Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"

class SonicMessageProtocol(CommunicationProtocol):
    LOG_PREFIX = "LOG"
    ANSWER_PREFIX = "ANS"
    COMMAND_PREFIX = "COM"

    def __init__(self, logger: logging.Logger = logging.getLogger()):
        self._logger: logging.Logger = logging.getLogger(logger.name + "." + SonicMessageProtocol.__name__)
        self._device_logger: logging.Logger = logging.getLogger(logger.name + ".device")
        super().__init__()

    @property
    def separator(self) -> str:
        return "\r"

    @staticmethod
    def _extract_log_level(log: str) -> int:
        log_level_str = log[log.index("=")+1:log.index(":")]
        match log_level_str:
            case DeviceLogLevel.ERROR.value:
                return logging.ERROR
            case DeviceLogLevel.WARN.value:
                return logging.WARN
            case DeviceLogLevel.INFO.value:
                return logging.INFO
            case DeviceLogLevel.DEBUG.value:
                return logging.DEBUG
        raise SyntaxError("Could not parse log level")

    def parse_response(self, response: str) -> tuple[int, str | None]:
        """
        returns:
        A Tuple with 
        - the package id
        - The answer (if the package contains an answer)
        """
        response = response.strip()
        if response.startswith(SonicMessageProtocol.ANSWER_PREFIX):
            response_id = int(response[response.index("#")+1:response.index("=")])
            answer = response[response.index("=")+1:]
            return response_id, answer
        elif response.startswith(SonicMessageProtocol.LOG_PREFIX):
            log_level = SonicMessageProtocol._extract_log_level(response)
            self._device_logger.log(log_level, response)
            return 0, None # has no id
        else:
            raise SyntaxError("Could not parse response: " + response)

    def parse_request(self, request: str, request_id: int) -> str:
        return f"{SonicMessageProtocol.COMMAND_PREFIX}#{request_id}={request}\n"
    
    @abc.abstractmethod
    def prot_type(self) -> ProtocolType:
        return ProtocolType.SONIC_MESSAGE_PROTOCOL

    @property
    @abc.abstractmethod
    def major_version(self) -> int:
        return 2

