import asyncio
import time
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
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=LogStorage._MAX_SIZE_LOGS)
        self._worker_handle = asyncio.create_task(self._worker())

    def create_log_handler(self) -> LogStorageHandler:
        return LogStorage.LogStorageHandler(self)

    async def _worker(self):
        burst_count = 0
        while True:
            start = time.perf_counter()

            item = await self._queue.get()

            #  we use the burst counter here to avoid spamming the logging tab with log messages 
            #  that leads to resource exhaustion and a crash of the application
            elapsed = time.perf_counter() - start
            was_instant_read = elapsed < 0.1
            if was_instant_read and burst_count < 10:
                burst_count += 1
            elif not was_instant_read:
                burst_count = 0
            else:
                continue
   
            self._logs.append(item)
            print(len(self._logs))
            if len(self._logs) > LogStorage._MAX_SIZE_LOGS:
                 self._logs.remove_at(0)
    
    @property
    def logs(self) -> ObservableList:
        return self._logs
    
    def __del__(self):
        self._worker_handle.cancel()
