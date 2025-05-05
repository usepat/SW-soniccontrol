import abc
from pathlib import Path

import pandas as pd

from sonic_protocol.field_names import EFieldName
from soniccontrol.data_capturing.experiment import Experiment
from soniccontrol.data_capturing.experiment_schema import ExperimentSchema


class ExperimentStore(abc.ABC):
    @abc.abstractmethod
    def write_metadata(self, experiment: Experiment) -> None: ...

    @abc.abstractmethod
    def add_row(self, data: dict) -> None: ...

    @abc.abstractmethod
    def close(self) -> None: ...


class HDF5ExperimentStore(ExperimentStore):
    def __init__(self, file_path: Path):
        file_extension = ".h5"
        self._file_path_posix = str(file_path) 
        if not self._file_path_posix.endswith(file_extension):
            self._file_path_posix += ".h5" # add extension
        self._hdf5_store = pd.HDFStore(self._file_path_posix,
                                        mode="a",
                                        complevel=9,
                                        complib="blosc")
        
    def write_metadata(self, experiment: Experiment) -> None:
        schema = ExperimentSchema()
        data = schema.dump(experiment).data

        df_target_parameters = pd.DataFrame([data["target_parameters"]])
        df_firmware_info = pd.DataFrame([data["firmware_info"]])
        df_additional_metadata = pd.DataFrame([data["metadata"]["additional_metadata"]])

        # remove data that we already extracted and flatten the structure
        del data["target_parameters"]
        del data["firmware_info"]
        del data["metadata"]["additional_metadata"]
        data.update(data["metadata"])
        del data["metadata"]

        df_metadata = pd.DataFrame([data])
        
        min_str_size = 32 # used for setting a larger minimum on string columns
        self._hdf5_store.put("metadata",
                                df_metadata,
                                min_itemsize={"values": min_str_size})
        self._hdf5_store.put("metadata/firmware_info",
                                df_firmware_info,
                                min_itemsize={"values": min_str_size})
        self._hdf5_store.put("metadata/additional_metadata",
                                df_additional_metadata,
                                min_itemsize={"values": min_str_size})
        self._hdf5_store.put("metadata/target_parameters",
                                df_target_parameters,
                                min_itemsize={"values": min_str_size})

    def add_row(self, data: dict) -> None:
        df = pd.DataFrame([data])
        df = df[Experiment.data_columns()]
        timestamp_col = EFieldName.TIMESTAMP.value
        df[timestamp_col] = df[timestamp_col].dt.tz_localize(None)

        self._hdf5_store.append("data",
                                df,
                                format="table",
                                data_columns=True)
        
    def close(self) -> None: 
        if self._hdf5_store.is_open:
            self._hdf5_store.close()
