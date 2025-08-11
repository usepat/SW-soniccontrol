import abc
from pathlib import Path
from typing import Any, Dict, List

import tables as tb

from sonic_protocol.field_names import EFieldName
from soniccontrol.data_capturing.converter import create_cattrs_converter_for_basic_serialization
from soniccontrol.data_capturing.experiment import Experiment


class ExperimentWriter(abc.ABC):
    @abc.abstractmethod
    def write_metadata(self, experiment: Experiment) -> None: ...

    @abc.abstractmethod
    def add_row(self, data: Dict[str, Any]) -> None: ...

    @abc.abstractmethod
    def close(self) -> None: ...

class ExperimentReader(abc.ABC):
    @abc.abstractmethod
    def read_experiment(self) -> Experiment: ...


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

    @staticmethod
    def add_rows_to_table(file: tb.File, table: tb.Table, rows: List[Dict[str, Any]]):
        new_row = table.row
        for row in rows:
            for k, v in row.items():
                new_row[k] = v
            new_row.append()
        table.flush()


  # Timestamp gets stored as string, because for a user it is more readable
_cols = {
    EFieldName.TIMESTAMP.name.lower(): tb.StringCol(32), #type: ignore
    EFieldName.FREQUENCY.name.lower(): tb.UInt32Col(), #type: ignore
    EFieldName.GAIN.name.lower(): tb.UInt8Col(), #type: ignore
    EFieldName.URMS.name.lower(): tb.UInt32Col(), #type: ignore
    EFieldName.IRMS.name.lower(): tb.UInt32Col(), #type: ignore
    EFieldName.PHASE.name.lower(): tb.UInt32Col(), #type: ignore
    EFieldName.TEMPERATURE.name.lower(): tb.UInt32Col() #type: ignore
}
DataTable = type("DataTable", (tb.IsDescription, ), _cols)


class HDF5ExperimentWriter(ExperimentWriter):
    def __init__(self, file_path: Path):
        file_extension = ".h5"
        self._file_path_posix = str(file_path) 
        if not self._file_path_posix.endswith(file_extension):
            self._file_path_posix += ".h5" # add extension
        self._file = tb.open_file(self._file_path_posix, "w")
        self._data_table = self._file.create_table("/", "data", DataTable)
        

    def write_metadata(self, experiment: Experiment) -> None:
        converter = create_cattrs_converter_for_basic_serialization()
        data = converter.unstructure(experiment, Experiment)
        
        # Unnest metadata, so that the metadata for the form lays also inside the same level as the other meta data
        data.update(data["metadata"])
        del data["metadata"]
        data["authors"] = ", ".join(data["authors"]) 
        # convert authors into a string for easier storage
        # pytables cannot store as an attribute a list of variable length strings.

        group = self._file.create_group("/", "metadata")
        HDF5SerializationHelper.serialize_attribute_tree(self._file, group, data)
        self._file.flush()
        
        
    def add_row(self, data: Dict[str, Any]) -> None:
        data = data.copy() # make a copy, so that we do not transform the original data
        timestamp_col = EFieldName.TIMESTAMP.name
        data[timestamp_col] = data[timestamp_col].isoformat()  # convert the time to a string for direct readability in storage
        # filter data, so that it only contains the columns of the table
        filtered_data = { k.lower(): v for k, v in data.items() if k.lower() in self._data_table.colnames }
        HDF5SerializationHelper.add_rows_to_table(self._file, self._data_table, [filtered_data])
        
    def close(self) -> None: 
        if self._file.isopen:
            self._file.close()
