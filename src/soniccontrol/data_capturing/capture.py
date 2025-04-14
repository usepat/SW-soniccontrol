import asyncio
import datetime
import logging
from pathlib import Path
from typing import Any, Dict

from async_tkinter_loop import async_handler
import pandas as pd
import json
import attrs

from sonic_protocol.field_names import EFieldName
from soniccontrol.data_capturing.capture_target import CaptureFree, CaptureTarget
from soniccontrol.data_capturing.data_provider import DataProvider
from soniccontrol.data_capturing.experiment import Experiment
from soniccontrol.data_capturing.experiment_schema import ExperimentSchema
from soniccontrol.events import Event, EventManager
from soniccontrol.procedures.holder import HolderArgs


class HolderArgsJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, HolderArgs):
            return attrs.asdict(o)
        return super().encode(o)
    

class Capture(EventManager):
    START_CAPTURE_EVENT = "START_CAPTURE_EVENT"
    END_CAPTURE_EVENT = "END_CAPTURE_EVENT"

    def __init__(self, output_dir: Path, logger: logging.Logger = logging.getLogger()):
        super().__init__()
        self._logger = logging.getLogger(logger.name + "." + Capture.__name__)
        self._completed_capturing: asyncio.Event = asyncio.Event()
        self._output_dir = output_dir
        self._data_provider = DataProvider()
        self._target: CaptureTarget | None = None
        self._experiment: Experiment | None = None
        self._completed_capturing.set()

    @property 
    def is_capturing(self) -> bool:
        return not self._completed_capturing.is_set()
    
    async def wait_for_capture_to_complete(self):
        await self._completed_capturing.wait()
    
    @property
    def data_provider(self) -> DataProvider:
        return self._data_provider
    
    async def start_capture(self, experiment: Experiment, capture_target: CaptureTarget = CaptureFree()):
        assert self._completed_capturing.is_set()

        self._experiment = experiment
        self._experiment.target_parameters = capture_target.args

        self._target = capture_target
        self._target.subscribe(CaptureTarget.COMPLETED_EVENT, self.capture_target_completed_callback)
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
        assert not self._completed_capturing.is_set()
        assert self._target

        self._completed_capturing.set()        
        self._write_experiment_data()

        self.emit(Event(Capture.END_CAPTURE_EVENT))
        self._logger.info("End Capture")

        await self._target.after_end_capture()
        self._target.unsubscribe(CaptureTarget.COMPLETED_EVENT, self.capture_target_completed_callback)

    def _write_experiment_data(self):
        assert self._experiment

        timestamp = self._experiment.date_time.strftime('%Y%m%d_%H%M%S')
        capture_filename = self._output_dir / "sonic_measure_{}.json".format(timestamp)
        schema = ExperimentSchema()
        data = schema.dump(self._experiment).data
        with open(capture_filename, "w") as file:
            json.dump(data, file, cls=HolderArgsJsonEncoder)


    def on_update(self, status: Dict[EFieldName, Any]):
        if not self._completed_capturing.is_set():
            assert self._experiment

            attrs: Dict[str, Any] = { k.value: v for k, v in status.items() }
            
            if EFieldName.TIMESTAMP not in status.keys():
                attrs[EFieldName.TIMESTAMP.value] = datetime.datetime.now()

            self._data_provider.add_row(attrs)

            attrs_dataframe = pd.DataFrame([attrs])
            # ensure attrs has all the columns of experiment.data
            attrs_dataframe = attrs_dataframe.reindex(columns=self._experiment.data.columns, fill_value=None)
            self._experiment.data = pd.concat([self._experiment.data, attrs_dataframe], ignore_index=True)            



    