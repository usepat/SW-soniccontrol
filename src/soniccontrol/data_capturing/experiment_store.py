import abc
import datetime
from pathlib import Path
from typing import Any, Dict, List, cast

import attrs
import numpy as np
import tables as tb
import pandas as pd

from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import Version
from soniccontrol.data_capturing.converter import create_cattrs_converter_for_basic_serialization
from soniccontrol.data_capturing.experiment import Experiment, ExperimentMetaData
from soniccontrol.device_data import FirmwareInfo


class ExperimentWriter(abc.ABC):
    @abc.abstractmethod
    def write_metadata(self, experiment: Experiment) -> None: ...

    @abc.abstractmethod
    def add_row(self, data: Dict[str, Any]) -> None: ...

    @abc.abstractmethod
    def close(self) -> None: ...

class ExperimentReader(abc.ABC):
    @abc.abstractmethod
    def read_metadata(self) -> Experiment: ...

    @abc.abstractmethod
    def read_data(self) -> pd.DataFrame: ...


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
    def deserialize_attribute_tree(group: tb.Group) -> Dict[str, Any]:
        result = {}
        for sub_group in group._v_groups.values():
            result[sub_group._v_name] = HDF5SerializationHelper.deserialize_attribute_tree(sub_group)
        
        for attr in group._v_attrs._f_list("user"):
            val = group._v_attrs[attr]

            # convert numpy scalars to python primitives
            if isinstance(val, np.generic):
                val = val.item()

            result[attr] = val

        return result

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
        self._data_table = self._file.create_table("/", "data", cast(tb.Description, DataTable))
        

    def write_metadata(self, experiment: Experiment) -> None:
        converter = create_cattrs_converter_for_basic_serialization()
        data = converter.unstructure(experiment, Experiment)
        
        # Unnest metadata, so that the metadata for the form lays also inside the same level as the other meta data
        data.update(data["metadata"])
        del data["metadata"]
        # pytables cannot store as an attribute a list of variable length strings.
        # So we need to convert authors to a string. This is already implemented as a hook

        group = self._file.create_group("/", "metadata")
        HDF5SerializationHelper.serialize_attribute_tree(self._file, group, data)
        self._file.flush()
        
        
    def add_row(self, data: Dict[str, Any]) -> None:
        data = data.copy() # make a copy, so that we do not transform the original data
        timestamp_col = EFieldName.TIMESTAMP.name.lower()
        data[timestamp_col] = data[timestamp_col].isoformat()  # convert the time to a string for direct readability in storage
        # filter data, so that it only contains the columns of the table
        filtered_data = { k.lower(): v for k, v in data.items() if k.lower() in self._data_table.colnames }
        HDF5SerializationHelper.add_rows_to_table(self._file, self._data_table, [filtered_data])
        
    def close(self) -> None: 
        if self._file.isopen:
            self._file.close()


class HDF5ExperimentReader(ExperimentReader):
    def __init__(self, file_path: Path):
        self._file_path = file_path


    def read_metadata(self) -> Experiment:
        data = None
        with tb.open_file(self._file_path.as_posix(), "r") as file_:
            metadata_node = cast(tb.Group, file_.get_node('/metadata', classname='Group'))
            data = HDF5SerializationHelper.deserialize_attribute_tree(metadata_node)
        assert data

        # nest metadata
        metadata_dict = {}
        for attr_name in attrs.fields_dict(ExperimentMetaData):
            if attr_name in data:
                metadata_dict[attr_name] = data.pop(attr_name)
        data["metadata"] = metadata_dict

        converter = create_cattrs_converter_for_basic_serialization()
        experiment =  converter.structure(data, Experiment)
            
        return experiment
    

    def read_data(self) -> pd.DataFrame:
        records = None
        with tb.open_file(self._file_path.as_posix(), "r") as file_:
            table_node = cast(tb.Table, file_.get_node('/data', classname='Table'))
            records = table_node.read()
        assert records is not None
    
        df = pd.DataFrame.from_records(records)
        return df



if __name__ == "__main__":
    filepath = Path("./output/testfile.h5")

    experiment = Experiment(
        metadata=ExperimentMetaData(
            experiment_name="Write and Read test",
            authors=["DW"],
            transducer_id="SOME_TRANSDUCER_ID",
            add_on_id="SOME_ADD_ON",
            connector_type="CABLE",
            medium="SILICON"
        ), 
        firmware_info=FirmwareInfo(), 
        sonic_control_version=Version(0, 0, 0),
        operating_system="Linux"
    )
    example_row = {
        EFieldName.TIMESTAMP.name.lower(): datetime.datetime.now(),
        EFieldName.FREQUENCY.name.lower(): 200000,
        EFieldName.GAIN.name.lower(): 100,
        EFieldName.URMS.name.lower(): 200,
        EFieldName.IRMS.name.lower(): 500, 
        EFieldName.PHASE.name.lower(): 20, 
        EFieldName.TEMPERATURE.name.lower(): 270000
    }

    writer = HDF5ExperimentWriter(filepath)
    writer.write_metadata(experiment)
    writer.add_row(example_row)
    writer.close()

    reader = HDF5ExperimentReader(filepath)
    metadata = reader.read_metadata()
    print(metadata)
    data = reader.read_data()
    print(data)

