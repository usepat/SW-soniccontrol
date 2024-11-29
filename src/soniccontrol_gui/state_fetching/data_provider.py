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


    @property
    def data(self) -> pd.DataFrame:
        return self._data
    

    def add_row(self, row: dict):
        time_stamp_key = EFieldName.TIME_STAMP.value
        if time_stamp_key in row.keys():
            row[time_stamp_key] = pd.to_datetime(row[time_stamp_key], errors='raise', format="%Y-%m-%d %H:%M:%S.%f")
            
        self._dataqueue.append(row)
        self._data = pd.DataFrame(list(self._dataqueue), columns=row.keys())

        self.emit(PropertyChangeEvent("data", None, self._data))