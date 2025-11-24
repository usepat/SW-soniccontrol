import logging
import pandas as pd
from sonic_protocol.field_names import EFieldName
from soniccontrol.events import EventManager, PropertyChangeEvent
from collections import deque


class DataProvider(EventManager):
    def __init__(self):
        super().__init__()
        self._max_size = 100
        self._data = pd.DataFrame()
        self._dataqueue = deque([], maxlen=100)
        self._logger = logging.getLogger(__name__)


    @property
    def data(self) -> pd.DataFrame:
        return self._data
    
    def change_dataqueue_max_size(self, size: int) -> None:
        old_data = list(self._dataqueue)
        self._dataqueue = deque(old_data, maxlen=size)
    

    def add_row(self, row: dict):
        self._dataqueue.append(row)      
        self._data = pd.DataFrame(list(self._dataqueue), columns=row.keys())
        self._data[EFieldName.TIMESTAMP.name] = pd.to_datetime(self._data[EFieldName.TIMESTAMP.name], format="%Y-%m-%d %H:%M:%S")
        if self._data[EFieldName.TIMESTAMP.name].dtype == "object":
            self._logger.error("Timestamp column is of type object instead of type datetime64[ns]")
            raise TypeError("Timestamp column is of type object instead of type datetime64[ns]")
        # The column timestamp is in datetime64[ns] format and the timeplot needs it that way, however
        # the csv_table needs it in string format and does this by formatting it in place.
        # I fixed it by creating a copy in the on_update_data method of CsvTable.
        # We could instead do this:
        # self.emit(PropertyChangeEvent("data", None, self._data.copy(deep=True)))
        # This way, nobody can change the timestamp column in the original data.
        self.emit(PropertyChangeEvent("data", None, self._data))


    def clear_data(self):
        self._data = pd.DataFrame()
        self._dataqueue.clear()