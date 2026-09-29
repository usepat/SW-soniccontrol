import asyncio
import datetime
import logging
from pathlib import Path
from typing import Any, Dict

from async_tkinter_loop import async_handler

from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import DeviceType
from soniccontrol.data_capturing.capture_target import CaptureFree, CaptureTarget
from soniccontrol.data_capturing.data_provider import DataProvider
from soniccontrol.data_capturing.experiment import Experiment
from soniccontrol.data_capturing.experiment_store import DataTableDescale, DataTableWorker, ExperimentWriter, HDF5ExperimentWriter
from soniccontrol.updater import Updater
from soniccontrol.utils.events import Event, EventManager



class Capture(EventManager):
    START_CAPTURE_EVENT = "START_CAPTURE_EVENT"
    END_CAPTURE_EVENT = "END_CAPTURE_EVENT"

    def __init__(self, output_dir: Path, updater: Updater, logger: logging.Logger = logging.getLogger()):
        super().__init__()
        self._updater = updater
        self._logger = logging.getLogger(logger.name + "." + Capture.__name__)
        self._completed_capturing: asyncio.Event = asyncio.Event()
        self._output_dir = output_dir
        self._data_provider = DataProvider()
        self._target: CaptureTarget | None = None
        self._experiment: Experiment | None = None
        self._experiment_writer: ExperimentWriter | None = None
        self._metadata_written = False
        self._completed_capturing.set()

        self._update_listener = lambda e: self.on_update(e.data["status"])

    async def __aenter__(self):
        await self.start_capture()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.end_capture()

    @property 
    def is_capturing(self) -> bool:
        return not self._completed_capturing.is_set()
    
    async def wait_for_capture_to_complete(self):
        await self._completed_capturing.wait()
    
    @property
    def data_provider(self) -> DataProvider:
        return self._data_provider

    def setup(self, experiment: Experiment, capture_target: CaptureTarget = CaptureFree()):
        self._experiment = experiment
        self._target = capture_target
    
    async def start_capture(self):
        assert self._completed_capturing.is_set()
        assert self._target is not None and self._experiment is not None, "You have to call setup before starting a capture"
        
        self._experiment.target_parameters = self._target.args

        timestamp_str = self._experiment.date_time.strftime("%Y%m%d_%H%M%S")
        file_name = self._output_dir / f"sonic_measure_{timestamp_str}"
        is_descale = self._experiment.firmware_info.device_type == DeviceType.DESCALE
        data_table_type = DataTableDescale if is_descale else DataTableWorker
        self._experiment_writer = HDF5ExperimentWriter(file_name, data_table_type)
        self._experiment_writer.write_metadata(self._experiment)

        self._target.subscribe(CaptureTarget.COMPLETED_EVENT, self.capture_target_completed_callback)
        self._updater.subscribe(Updater.UPDATE_EVENT, self._update_listener)
        await self._target.before_start_capture()
        self._data_provider.clear_data()
        
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
        if self._completed_capturing.is_set():
            return
        assert self._target

        target = self._target

        self._completed_capturing.set()   
        self._updater.unsubscribe(Updater.UPDATE_EVENT, self._update_listener)     
        target.unsubscribe(CaptureTarget.COMPLETED_EVENT, self.capture_target_completed_callback)

        if self._experiment_writer:
            self._experiment_writer.close()
            self._experiment_writer = None

        await target.after_end_capture()
        self.emit(Event(Capture.END_CAPTURE_EVENT))
        self._logger.info("End Capture")


    def on_update(self, status: Dict[EFieldName, Any]):
        if not self._completed_capturing.is_set():
            assert self._experiment_writer

            attrs: Dict[str, Any] = { k.name: v for k, v in status.items() }
            
            timestamp_col = EFieldName.TIMESTAMP.name
            if EFieldName.TIMESTAMP not in status.keys():
                attrs[timestamp_col] = datetime.datetime.now()
            
            self._data_provider.add_row(attrs)
            self._experiment_writer.add_row(attrs)
