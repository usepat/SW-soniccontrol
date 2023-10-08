from __future__ import annotations
from typing import *
import asyncio
import attrs
import datetime
from icecream import ic
from soniccontrol.sonicpackage.command import Command


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


@attrs.define()
class Status:
    error: int = attrs.field(
        default=0,
        repr=False,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    frequency: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    gain: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    protocol: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    wipe_mode: bool = attrs.field(
        default=False,
        converter=default_if_none(False, attrs.converters.to_bool),
        validator=attrs.validators.instance_of(bool),
    )
    temperature: float = attrs.field(
        default=0.0,
        converter=[
            lambda x: (
                default_if_none(0.0, float)(
                    x.strip("'") if isinstance(x, str) and "'" in x else x
                )
            ),
            lambda x: x if -100 < x < 350 else 0.0,
        ],
        validator=attrs.validators.instance_of(float),
    )
    signal: bool = attrs.field(
        default=False,
        converter=default_if_none(False, bool),
        validator=attrs.validators.instance_of(bool),
    )
    urms: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    irms: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    phase: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    atf1: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    atk1: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    atf2: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    atk2: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    atf3: int = attrs.field(
        default=0,
        converter=default_if_none(0, int),
        validator=attrs.validators.instance_of(int),
    )
    atk3: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    att1: float = attrs.field(
        default=0.0,
        converter=default_if_none(0.0, float),
        validator=attrs.validators.instance_of(float),
    )
    relay_mode: Optional[Literal["KHz", "MHz"]] = attrs.field(
        default=None,
        converter=attrs.converters.optional(str),
        kw_only=True,
    )
    communication_mode: Optional[Literal["Serial", "Manual", "Analog"]] = attrs.field(
        default="Manual"
    )
    timestamp: datetime.datetime = attrs.field(
        factory=datetime.datetime.now,
        eq=False,
        converter=lambda b: (
            datetime.datetime.fromtimestamp(b) if isinstance(b, float) else b
        ),
    )
    _changed: asyncio.Event = attrs.field(init=False, factory=asyncio.Event)

    @property
    def changed(self) -> asyncio.Event:
        return self._changed

    def update(self, **kwargs) -> Status:
        kwargs["timestamp"] = (
            datetime.datetime.now()
            if not kwargs.get("timestamp")
            else datetime.datetime.fromtimestamp(kwargs.get("timestamp"))
        )
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._changed.set()
        return self


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

    @classmethod
    def from_string(cls, module_string: str) -> Modules:
        return cls(*module_string.split("="))


@attrs.define
class Info:
    device_type: Literal["catch", "wipe", "descale"] = attrs.field(default="catch")
    firmware_info: str = attrs.field(default="")
    version: float = attrs.field(default=0.2)
    modules: Modules = attrs.field(factory=Modules)

    def update(self, **kwargs) -> Info:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self