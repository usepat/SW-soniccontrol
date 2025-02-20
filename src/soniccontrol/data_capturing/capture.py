import asyncio
import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Sequence

from async_tkinter_loop import async_handler

from sonic_protocol.field_names import EFieldName
from soniccontrol.data_capturing.capture_target import CaptureFree, CaptureTarget
from soniccontrol.data_capturing.csv_writer import CsvWriter
from soniccontrol.data_capturing.data_provider import DataProvider
from soniccontrol.events import Event, EventManager


class Capture(EventManager):
    START_CAPTURE_EVENT = "START_CAPTURE_EVENT"
    END_CAPTURE_EVENT = "END_CAPTURE_EVENT"

    def __init__(self, data_fields: Sequence[EFieldName], output_dir: Path, logger: logging.Logger = logging.getLogger()):
        super().__init__()
        self._logger = logging.getLogger(logger.name + "." + Capture.__name__)
        self._completed_capturing: asyncio.Event = asyncio.Event()
        self._data_attrs = data_fields
        self._has_no_timestamp = EFieldName.TIMESTAMP not in self._data_attrs
        self._output_dir = output_dir
        self._capture_file_format = "sonicmeasure-{}.csv"
        self._data_provider = DataProvider()
        self._csv_data_collector = CsvWriter()
        self._target: CaptureTarget | None = None
        self._completed_capturing.set()

    @property 
    def is_capturing(self) -> bool:
        return not self._completed_capturing.is_set()
    
    async def wait_for_capture_to_complete(self):
        await self._completed_capturing.wait()
    
    @property
    def data_provider(self) -> DataProvider:
        return self._data_provider
    
    async def start_capture(self, capture_target: CaptureTarget = CaptureFree()):
        assert self._completed_capturing.is_set()

        self._target = capture_target
        self._target.subscribe(CaptureTarget.COMPLETED_EVENT, self.capture_target_completed_callback)
        await self._target.before_start_capture()
        self._data_provider.clear_data()

        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        capture_filename = self._output_dir / self._capture_file_format.format(timestamp)
        header = [ data_attr.value for data_attr in self._data_attrs ]
        if self._has_no_timestamp:
            header.insert(0, EFieldName.TIMESTAMP.value)
        self._csv_data_collector.open_file(capture_filename, header)
        self._completed_capturing.clear()
        self.emit(Event(Capture.START_CAPTURE_EVENT))
        self._logger.info("Start Capture")

        self._target.run_to_capturing_task()

    @async_handler
    async def capture_target_completed_callback(self, _e):
        """!
            @brief Helper Method so end_capture can be called over a callback

            @note This runs in its own asyncio loop. So errors will not propagate upwards
        """
        await self.end_capture()

    async def end_capture(self):
        assert not self._completed_capturing.is_set()
        assert self._target

        self._csv_data_collector.close_file()
        self._completed_capturing.set()
        
        self.emit(Event(Capture.END_CAPTURE_EVENT))
        self._logger.info("End Capture")

        await self._target.after_end_capture()
        self._target.unsubscribe(CaptureTarget.COMPLETED_EVENT, self.capture_target_completed_callback)


    def on_update(self, status: Dict[EFieldName, Any]):
        if not self._completed_capturing.is_set():
            attrs: Dict[str, Any] = {}
            if self._has_no_timestamp:
                attrs[EFieldName.TIMESTAMP.value] = datetime.datetime.now()
            for attr_name in self._data_attrs:
                attrs[attr_name.value] = status[attr_name]

            self._data_provider.add_row(attrs)
            self._csv_data_collector.write_entry(attrs)



    