from enum import Enum
import logging
from typing import Any
import abc
from soniccontrol.communication.package_parser import Package, PackageParser


class ProtocolType(Enum):
    PACAKGE_PROTOCOL = "Package Protocol"

class CommunicationProtocol:
    @property
    def start_symbol(self) -> str:
        return PackageParser.start_symbol

    @property
    def end_symbol(self) -> str:
        return PackageParser.end_symbol

    @property
    def max_bytes(self) -> int:
        return PackageParser.max_bytes

    @abc.abstractmethod
    def parse_response(self, response: str) -> Any: ...

    @abc.abstractmethod
    def parse_request(self, request: str, request_id: int) -> Any: ...

    @abc.abstractmethod
    def prot_type(self) -> ProtocolType: ...

    @property
    @abc.abstractmethod
    def major_version(self) -> int: ...


class LegacyProtocol(CommunicationProtocol):
    def __init__(self):
        super().__init__()

    @property
    def start_symbol(self) -> str:
        return ""

    @property
    def end_symbol(self) -> str:
        return "\n"

    @property
    def max_bytes(self) -> int:
        return PackageParser.max_bytes

    def parse_response(self, response: str) -> str:
        return response

    def parse_request(self, request: str, request_id: int) -> Any:
        return request
    
    @abc.abstractmethod
    def prot_type(self) -> ProtocolType:
        return ProtocolType.PACAKGE_PROTOCOL

    @property
    @abc.abstractmethod
    def major_version(self) -> int:
        return 1


class DeviceLogLevel(Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"

class PackageProtocol(CommunicationProtocol):
    LOG_PREFIX = "LOG="

    def __init__(self, logger: logging.Logger = logging.getLogger()):
        self._logger: logging.Logger = logging.getLogger(logger.name + "." + PackageProtocol.__name__)
        self._device_logger: logging.Logger = logging.getLogger(logger.name + ".device")
        super().__init__()

    @property
    def start_symbol(self) -> str:
        return PackageParser.start_symbol

    @property
    def end_symbol(self) -> str:
        return PackageParser.end_symbol

    @property
    def max_bytes(self) -> int:
        return PackageParser.max_bytes

    @staticmethod
    def _extract_log_level(log: str) -> int:
        log_level_str = log[len(PackageProtocol.LOG_PREFIX):log.index(":")]
        match log_level_str:
            case DeviceLogLevel.ERROR:
                return logging.ERROR
            case DeviceLogLevel.WARN:
                return logging.WARN
            case DeviceLogLevel.INFO:
                return logging.INFO
            case DeviceLogLevel.DEBUG:
                return logging.DEBUG
        raise SyntaxError("Could not parse log level")

    def parse_response(self, response: str) -> tuple[int, str]:
        package = PackageParser.parse_package(response)
        lines = package.content.splitlines(keepends=True)
        answer = ""
        for line in lines:
            if line.startswith(PackageProtocol.LOG_PREFIX):
                line = line.strip() # remove newline \n at the end
                log_level = PackageProtocol._extract_log_level(line)
                self._device_logger.log(log_level, line)
            elif line.isspace() or len(line) == 0:
                continue  # ignore whitespace
            else:
                answer += line

        return package.identifier, answer

    def parse_request(self, request: str, request_id: int) -> str:
        package = Package("0", "0", request_id, request)
        message_str = (
            PackageParser.write_package(package) + "\n"
        )  # \n is needed after the package.

        return message_str
    
    @abc.abstractmethod
    def prot_type(self) -> ProtocolType:
        return ProtocolType.PACAKGE_PROTOCOL

    @property
    @abc.abstractmethod
    def major_version(self) -> int:
        return 2

