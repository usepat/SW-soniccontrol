import asyncio
import logging
import logging.handlers

from soniccontrol_gui.utils.observable_list import ObservableList


class DeviceLogFilter(logging.Filter):
    def filter(self, record) -> bool:
        return "device" in record.name
    
class NotDeviceLogFilter(logging.Filter):
    def filter(self, record) -> bool:
        return "device" not in record.name

class LogStorage:
    class LogStorageHandler(logging.Handler):
        def __init__(self, logStorage: "LogStorage", log_level: int = logging.INFO):
            super(LogStorage.LogStorageHandler, self).__init__()
            formatter = logging.Formatter("%(asctime)s: %(levelname)s - %(name)s - %(message)s")
            self.setFormatter(formatter)
            self._logStorage = logStorage
            self._log_level = log_level

        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno >= self._log_level:
                try:
                    log = self.format(record)
                    self._logStorage._queue.put_nowait(log)
                except:
                    self.handleError(record)


    _MAX_SIZE_LOGS = 1000

    def __init__(self):
        self._logs: ObservableList = ObservableList()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_handle = asyncio.create_task(self._worker())

    def create_log_handler(self) -> LogStorageHandler:
        return LogStorage.LogStorageHandler(self)

    async def _worker(self):
        while True:
            item = await self._queue.get()
            self._logs.append(item)
            if len(self._logs) > LogStorage._MAX_SIZE_LOGS:
                 self._logs.remove_at(0)
    
    @property
    def logs(self) -> ObservableList:
        return self._logs
    
    def __del__(self):
        self._worker_handle.cancel()
