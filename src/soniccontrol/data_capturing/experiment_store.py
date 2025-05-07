import abc
from pathlib import Path
from typing import Any, Dict, List

import tables as tb

from sonic_protocol.field_names import EFieldName
from soniccontrol.data_capturing.experiment import Experiment
from soniccontrol.data_capturing.experiment_schema import ExperimentSchema


class ExperimentStore(abc.ABC):
    @abc.abstractmethod
    def write_metadata(self, experiment: Experiment) -> None: ...

    @abc.abstractmethod
    def add_row(self, data: Dict[str, Any]) -> None: ...

    @abc.abstractmethod
    def close(self) -> None: ...


class HDF5SerializationHelper:
    @staticmethod
    def serialize_attribute_tree(file_: tb.File, group: tb.Group, obj: Dict[str, Any]):
        for name, value in obj.items():
            assert isinstance(name, str), "attribute tree has to have strings as attribute names"
            
            if value is None:
                continue
            if isinstance(value, dict):
                sub_group = file_.create_group(group, name)
                HDF5SerializationHelper.serialize_attribute_tree(file_, sub_group, value)
            else:
                group._v_attrs[name] = value
        file_.flush()

    @staticmethod
    def add_rows_to_table(file: tb.File, table: tb.Table, rows: List[Dict[str, Any]]):
        new_row = table.row
        for row in rows:
            for k, v in row.items():
                new_row[k] = v
            new_row.append()
        table.flush()

# TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class HDF5ExperimentStore(ExperimentStore):
    def __init__(self, file_path: Path):
        file_extension = ".h5"
        self._file_path_posix = str(file_path) 
        if not self._file_path_posix.endswith(file_extension):
            self._file_path_posix += ".h5" # add extension
        self._file = tb.open_file(self._file_path_posix, "w")
        self._create_data_table()

    def _create_data_table(self):
        # Timestamp gets stored as string, because for a user it is more readable
        cols = {
            EFieldName.TIMESTAMP.value: tb.StringCol(32), #type: ignore
            EFieldName.FREQUENCY.value: tb.UInt32Col(), #type: ignore
            EFieldName.GAIN.value: tb.UInt8Col(), #type: ignore
            EFieldName.URMS.value: tb.UInt32Col(), #type: ignore
            EFieldName.IRMS.value: tb.UInt32Col(), #type: ignore
            EFieldName.PHASE.value: tb.UInt32Col(), #type: ignore
            EFieldName.TEMPERATURE.value: tb.UInt32Col() #type: ignore
        }
        DataTable = type("DataTable", (tb.IsDescription, ), cols)
        self._data_table = self._file.create_table("/", "data", DataTable)


    def write_metadata(self, experiment: Experiment) -> None:
        schema = ExperimentSchema()
        data = schema.dump(experiment).data
        
        # Unnest metadata, so that the metadata for the form lays also inside the same level as the other meta data
        data.update(data["metadata"])
        del data["metadata"]

        group = self._file.create_group("/", "metadata")
        HDF5SerializationHelper.serialize_attribute_tree(self._file, group, data)
        
    def add_row(self, data: Dict[str, Any]) -> None:
        data = data.copy() # make a copy, so that we do not transform the original data
        timestamp_col = EFieldName.TIMESTAMP.value
        data[timestamp_col] = data[timestamp_col].isoformat() #.strftime(TIME_FORMAT) # convert the time to a string
        # filter data, so that it only contains the columns of the table
        filtered_data = { k: v for k, v in data.items() if k in self._data_table.colnames }
        HDF5SerializationHelper.add_rows_to_table(self._file, self._data_table, [filtered_data])
        
    def close(self) -> None: 
        if self._file.isopen:
            self._file.close()
