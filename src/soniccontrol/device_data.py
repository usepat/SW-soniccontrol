from __future__ import annotations

import asyncio
import datetime
from enum import Enum
from typing import Any, Callable, Dict, Literal

import attrs
from icecream import ic

from sonic_protocol.defs import Version
from sonic_protocol.field_names import EFieldName#
import numpy as np


def default_if_none(default: Any, type_: type = int) -> Callable[[Any], Any]:
    none_converter = attrs.converters.default_if_none(default)

    def converter(value) -> None:
        value = none_converter(value)
        try:
            value = type_(none_converter(value))
        except Exception as e:
            ic(f"VALUE ERROR {e}, {value} is not {type_}")
        return value

    return converter


# We could maybe make this to a meta class. Or build it with a meta class
@attrs.define()
class Status:
    time_stamp: datetime.datetime = attrs.field(
        factory=datetime.datetime.now,
        eq=False,
        converter=lambda b: (
            datetime.datetime.fromtimestamp(b) if isinstance(b, float) else b
        ),
    )
    procedure: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )

    def __attrs_post_init__(self):
        self._changed: asyncio.Event = asyncio.Event()
        self._changed_data: Dict[EFieldName, Any] = {}
        self._remote_proc_finished_running: asyncio.Event = asyncio.Event()
        
    def __getitem__(self, key: EFieldName) -> Any:
        return getattr(self, key.value)
        
    def __setitem__(self, key: EFieldName, value: Any):
        setattr(self, key.value, value)


    def has_attr(self, key: EFieldName) -> bool:
        return hasattr(self, key.value)

    @property 
    def remote_proc_finished_running(self) -> asyncio.Event:
        return self._remote_proc_finished_running

    async def update(self, fields: Dict[EFieldName, Any]) -> Status:
        self._changed.clear()
        self._changed_data.clear()
        timestamp_key: EFieldName = EFieldName.TIME_STAMP
        fields[timestamp_key] = (
            datetime.datetime.now()
            if timestamp_key not in fields
            else datetime.datetime.fromtimestamp(fields[timestamp_key])
        )
        procedure = self.procedure
        changed: bool = False
        for field_path, value in fields.items():
            if self.has_attr(field_path) and self[field_path] != value:
                try:
                    self[field_path] = value
                    self._changed_data[field_path] = value
                    changed = field_path != timestamp_key or changed
                except AttributeError:
                    continue
        if changed:
            #  check if the procedure was changed or finished
            if procedure != 0 and self.procedure != procedure:
                self._remote_proc_finished_running.set()
                await asyncio.sleep(0.1)
                self._remote_proc_finished_running.clear()
            
            self._changed.set()
            await asyncio.sleep(0.1)
            self._changed.clear()
        return self


class StatusBuilder:
    counter: int = 0

    def create_status(self, field_dict: Dict[EFieldName, type[Any]]) -> Status:
        name = "status" + str(StatusBuilder.counter)
        StatusBuilder.counter += 1
        attrs_dict =  { k.value: self._create_attr_field(v) for k, v in field_dict.items() }
        status_class = attrs.make_class(name, attrs_dict, (Status,))
        return status_class()

    def _create_attr_field(self, field_type: type[Any]) :
        if field_type is float:
            return attrs.field(
                default=0.0,
                converter=default_if_none(0.0, float),
                validator=attrs.validators.instance_of(float),
            )
        if field_type is int or np.issubdtype(field_type, np.integer):
            return attrs.field(
                default=0, 
                converter=default_if_none(0, field_type),
                validator=attrs.validators.instance_of(field_type)
            )
        if field_type is bool:  
            return attrs.field(
                default=False,
                converter=default_if_none(False, bool),
                validator=attrs.validators.instance_of(bool),
            )
        if field_type is str:
            return attrs.field(
                default="",
                validator=attrs.validators.instance_of(str),
            )
        if field_type is Version:
            return attrs.field(
                default=Version(0, 0, 0),
                validator=attrs.validators.instance_of(Version),
            )
        if issubclass(field_type, Enum):
            assert len(list(field_type)) > 0,  "The enum provided has no members"
            first_enum_member = next(iter(field_type))
            return attrs.field(
                default=first_enum_member,
                converter=default_if_none(first_enum_member, field_type),
                validator=attrs.validators.instance_of(field_type),
            )
        assert False, "An unsupported type was added to the status field"


@attrs.define
class Modules:
    buffer: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    display: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    eeprom: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    fram: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    i_current: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    current1: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    current2: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    io_serial: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    thermo_ext: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    thermo_int: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    khz: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    mhz: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    portexpander: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    protocol: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    protocol_fix: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    relais: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    scanning: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    sonsens: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    tuning: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    switch: bool = attrs.field(default=False, converter=attrs.converters.to_bool)
    switch2: bool = attrs.field(default=False, converter=attrs.converters.to_bool)



@attrs.define
class Info:
    # TODO refactor this
    device_type: Literal["catch", "wipe", "descale"] = attrs.field(default="descale")
    firmware_info: str = attrs.field(default="") # TODO does not match with validators of info command
    firmware_version: Version = attrs.field(default=Version(0, 0, 0), converter=Version.to_version) 
    protocol_version: Version = attrs.field(default=Version(0, 0, 0), converter=Version.to_version)