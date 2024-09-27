import datetime
import logging

from async_tkinter_loop import async_handler

from soniccontrol_gui.constants import files
from soniccontrol_gui.state_fetching.capture_target import CaptureFree, CaptureTarget
from soniccontrol.device_data import Status
from soniccontrol_gui.state_fetching.csv_writer import CsvWriter
from soniccontrol_gui.state_fetching.data_provider import DataProvider
from soniccontrol.events import Event, EventManager


class Capture(EventManager):
    START_CAPTURE_EVENT = "START_CAPTURE_EVENT"
    END_CAPTURE_EVENT = "END_CAPTURE_EVENT"

    def __init__(self, logger: logging.Logger = logging.getLogger()):
        super().__init__()
        self._logger = logging.getLogger(logger.name + "." + Capture.__name__)
        self._is_capturing = False
        self._data_attrs = ["timestamp", "signal", "frequency", "gain", "urms", "irms", "phase", "temperature"]
        self._capture_file_format = "sonicmeasure-{}.csv"
        self._data_provider = DataProvider()
        self._csv_data_collector = CsvWriter()

    @property 
    def is_capturing(self) -> bool:
        return self._is_capturing
    
    @property
    def data_provider(self) -> DataProvider:
        return self._data_provider
    
    async def start_capture(self, capture_target: CaptureTarget = CaptureFree()):
        assert not self._is_capturing

        self._target = capture_target
        await self._target.before_start_capture()

        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        capture_filename = files.LOG_DIR / self._capture_file_format.format(timestamp)
        self._csv_data_collector.open_file(capture_filename, self._data_attrs)
        self._is_capturing = True
        self.emit(Event(Capture.START_CAPTURE_EVENT))
        self._logger.info("Start Capture")

        self._target.run_to_capturing_task()

    @async_handler
    async def capture_target_completed_callback(self):
        """!
            @brief Helper Method so end_capture can be called over a callback

            @note This runs in its own asyncio loop. So errors will not propagate upwards
        """
        await self.end_capture()

    async def end_capture(self):
        assert self._is_capturing

        self._csv_data_collector.close_file()
        self._is_capturing = False
        self.emit(Event(Capture.END_CAPTURE_EVENT))
        self._logger.info("End Capture")

        await self._target.after_end_capture()


    def on_update(self, status: Status):
        if self._is_capturing:
            attrs = {}
            for attr_name in self._data_attrs:
                attrs[attr_name] = getattr(status, attr_name)

            self._data_provider.add_row(attrs)
            self._csv_data_collector.write_entry(attrs)



    