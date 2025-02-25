import abc
from pathlib import Path
from typing import Any

class ExperimentRepositoryBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def load_meta_data_from_template(self, template: dict):
        ...

    @abc.abstractmethod
    def get_meta_data(self, attr_name: str) -> Any:
        ...

    @abc.abstractmethod
    def update_meta_data(self, attr_name: str, value: Any):
        ...

    @abc.abstractmethod
    def add_datapoint(self, datapoint: dict) -> None:
        ...

    @abc.abstractmethod
    def save(self, dir_path: Path) -> Path:
        ...



class ExperimentRepository(ExperimentRepositoryBase):
    def __init__(self, meta_data: dict):
        ...

    def load_meta_data_from_template(self, template: dict):
        ...

    def get_meta_data(self, attr_name: str) -> Any:
        ...

    def update_meta_data(self, attr_name: str, value: Any):
        ...

    def add_datapoint(self, datapoint: dict) -> None:
        ...

    def save(self, dir_path: Path) -> Path:
        ...