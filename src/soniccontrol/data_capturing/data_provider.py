import datetime
import pandas as pd
import numpy as np
from sonic_protocol.field_names import EFieldName
from soniccontrol.events import EventManager, PropertyChangeEvent
from collections import deque
import inspect


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
        print(f"📤 emitted DataFrame id: {id(self._data)}")
        print(f"Type: {row["timestamp"]}: {type(row["timestamp"])}")
        self._dataqueue.append(row)      
        self._data = pd.DataFrame(list(self._dataqueue), columns=row.keys())
        self._data["timestamp"] = pd.to_datetime(self._data["timestamp"], format="%Y-%m-%d %H:%M:%S")
        print(f"🔍 Final dtype of timestamp column: {self._data['timestamp'].dtype}")
        if self._data["timestamp"].dtype == "object":
            type_counts = self._data["timestamp"].apply(type).value_counts()
            print(f"⚠️ Mixed types in timestamp column: {type_counts.to_dict()}")
        else:
            print("✅ timestamp column is datetime64[ns]")
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