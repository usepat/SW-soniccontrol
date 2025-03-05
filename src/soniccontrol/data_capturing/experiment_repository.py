import abc
from pathlib import Path
from typing import Any

class ExperimentRepositoryBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def load(self, filename: Path):
        ...

    @abc.abstractmethod
    def save(self, dir_path: Path) -> Path:
        ...

    @abc.abstractmethod
    def set_metadata_attr(self, attr_name: str, value: Any):
        ...

    @abc.abstractmethod
    def add_datapoint(self, datapoint: dict) -> None:
        ...



class ExperimentRepository(ExperimentRepositoryBase):
    def __init__(self, meta_data: dict):
        ...

    def load(self, filename: Path):
        ...

    def save(self, dir_path: Path) -> Path:
        ...

    def set_metadata_attr(self, attr_name: str, value: Any):
        ...

    def add_datapoint(self, datapoint: dict) -> None:
        ...