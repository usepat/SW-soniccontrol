import logging
from typing import List
import abc
from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from sonic_protocol.schema import Loglevel, Version
from soniccontrol.logger.utils import is_sub_logger
from soniccontrol.sonic_device import SonicDevice


class AbstractLogger(abc.ABC):
    @property
    @abc.abstractmethod
    def log_level(self) -> Loglevel: ...

    @abc.abstractmethod
    async def set_log_level(self, log_level: Loglevel): ...

    @property
    @abc.abstractmethod
    def qual_logger_name(self) -> str: ...


class LoggerDiscovery(abc.ABC):
    @abc.abstractmethod
    async def discover_loggers(self) -> List[AbstractLogger]: ...



class PythonLogger(AbstractLogger):
    def __init__(self, logger: logging.Logger):
        self._logger: logging.Logger = logger
        super().__init__()

    @staticmethod
    def convert_to_py_log_level(log_level: Loglevel):
        match log_level:
            case Loglevel.DEBUG:
                return logging.DEBUG
            case Loglevel.INFO:
                return logging.INFO
            case Loglevel.WARN:
                return logging.WARNING
            case Loglevel.ERROR:
                return logging.ERROR
            case Loglevel.DEBUG_EXTENSIVE:
                return logging.DEBUG
            case Loglevel.DISABLED:
                assert False, "py logger does not have a disabled log level. you need to disable the logger manually"

    @staticmethod
    def convert_to_schema_log_level(log_level: int) -> Loglevel:
        match log_level:
            case logging.DEBUG:
                return Loglevel.DEBUG
            case logging.INFO:
                return Loglevel.INFO
            case logging.WARNING:
                return Loglevel.WARN
            case logging.ERROR:
                return Loglevel.ERROR
        assert False, "unreachable"

    @property
    def log_level(self) -> Loglevel: 
        if self._logger.disabled:
            return Loglevel.DISABLED
        
        log_level= self._logger.getEffectiveLevel()
        return PythonLogger.convert_to_schema_log_level(log_level)

    async def set_log_level(self, log_level: Loglevel): 
        is_disabled = log_level == Loglevel.DISABLED
        self._logger.disabled = is_disabled
        if is_disabled:
            return
        
        py_log_level = PythonLogger.convert_to_py_log_level(log_level)
        self._logger.setLevel(py_log_level)

    @property
    def qual_logger_name(self) -> str: 
        return self._logger.name
    

class PythonLoggerDiscovery(LoggerDiscovery):
    def __init__(self, parent_logger: logging.Logger = logging.getLogger()):
        """
            Params
            ======
            parent_logger: is used for filtering out loggers, that are not sub loggers of this one.
        """
        self._parent_logger: logging.Logger = parent_logger
        super().__init__()

    async def discover_loggers(self) -> List[AbstractLogger]:
        return [
            PythonLogger(logger)
            for logger in logging.root.manager.loggerDict.values()
            if isinstance(logger, logging.Logger) and is_sub_logger(logger, self._parent_logger)
        ]



class DeviceLogger(AbstractLogger):
    def __init__(self, device: SonicDevice, logger_name: str, log_level: Loglevel):
        assert device.info.protocol_version >= Version(3, 0, 0), "Logger discovery is only available since protocol v3.0.0"
        
        self._device = device
        self._logger_name = logger_name
        self._log_level = log_level
        super().__init__()

    @property
    def log_level(self) -> Loglevel: 
        return self._log_level

    async def set_log_level(self, log_level: Loglevel): 
        await self._device.execute_command(commands.SetLogLevel(self._logger_name, log_level))
        self._log_level = log_level

    @property
    def qual_logger_name(self) -> str: 
        return self._logger_name
    

class DeviceLoggerDiscovery(LoggerDiscovery):
    def __init__(self, device: SonicDevice):
        self._device = device
        super().__init__()

    async def discover_loggers(self) -> List[AbstractLogger]:
        answer = await self._device.execute_command(commands.GetNumLoggers())
        count = answer[EFieldName.COUNT]

        loggers: List[AbstractLogger] = []
        for i in range(count):
            answer = await self._device.execute_command(commands.GetLogger(i))
            logger_name = answer[EFieldName.LOGGER_NAME]
            log_level = answer[EFieldName.LOG_LEVEL]
            loggers.append(DeviceLogger(self._device, logger_name, log_level))

        return loggers
