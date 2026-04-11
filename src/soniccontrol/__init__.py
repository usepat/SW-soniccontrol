from __future__ import annotations

import logging
from importlib import import_module
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from sonic_protocol.command_codes import CommandCode
    from sonic_protocol.field_names import EFieldName
    from sonic_protocol.python_parser import commands
    from sonic_protocol.python_parser.answer import Answer
    from sonic_protocol.python_parser.commands import Command
    from sonic_protocol.schema import DeviceParamConstantType, DeviceType, Loglevel, Procedure
    from sonic_protocol.si_unit import (
        AbsoluteFrequencySIVar,
        AtfSiVar,
        AttSiVar,
        GainSIVar,
        MeterSIVar,
        MilliMeterSIVar,
        RelativeFrequencySIVar,
        SIPrefix,
        SIUnit,
        SwfSIVar,
        TemperatureSIVar,
    )
    from soniccontrol.communication.connection import CLIConnection, SerialConnection
    from soniccontrol.data_capturing.experiment import Experiment, ExperimentMetaData
    from soniccontrol.data_capturing.experiment_store import HDF5ExperimentReader, HDF5ExperimentWriter
    from soniccontrol.network.connection import RemoteServerConnection
    from soniccontrol.network.enable_server_on_startup.script import enable_server_on_startup
    from soniccontrol.network.server import start_server
    from soniccontrol.procedures.procs import (
        AutoArgs,
        RamperArgs,
        ScanArgs,
        SpectrumMeasureArgs,
        TuneArgs,
        WipeArgs,
    )
    from soniccontrol.remote_controller import RemoteController

_SONIC_PROTOCOL_SI_UNIT_MODULE = "sonic_protocol.si_unit"
_SONIC_PROTOCOL_SCHEMA_MODULE = "sonic_protocol.schema"
_PROCEDURES_MODULE = "soniccontrol.procedures.procs"

__all__ = [
    "AbsoluteFrequencySIVar",
    "Answer",
    "AtfSiVar",
    "AttSiVar",
    "AutoArgs",
    "CLIConnection",
    "Command",
    "CommandCode",
    "DeviceParamConstantType",
    "DeviceType",
    "EFieldName",
    "Experiment",
    "ExperimentMetaData",
    "GainSIVar",
    "HDF5ExperimentReader",
    "HDF5ExperimentWriter",
    "Loglevel",
    "MeterSIVar",
    "MilliMeterSIVar",
    "Procedure",
    "RamperArgs",
    "RelativeFrequencySIVar",
    "RemoteController",
    "RemoteServerConnection",
    "SIPrefix",
    "SIUnit",
    "ScanArgs",
    "SerialConnection",
    "SpectrumMeasureArgs",
    "SwfSIVar",
    "TemperatureSIVar",
    "TuneArgs",
    "WipeArgs",
    "commands",
    "enable_server_on_startup",
    "logger",
    "start_server",
]

_EXPORTS = {
    "RemoteController": ("soniccontrol.remote_controller", "RemoteController"),
    "commands": ("sonic_protocol.python_parser", "commands"),
    "Command": ("sonic_protocol.python_parser.commands", "Command"),
    "Answer": ("sonic_protocol.python_parser.answer", "Answer"),
    "EFieldName": ("sonic_protocol.field_names", "EFieldName"),
    "CommandCode": ("sonic_protocol.command_codes", "CommandCode"),
    "AtfSiVar": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "AtfSiVar"),
    "AttSiVar": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "AttSiVar"),
    "SwfSIVar": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "SwfSIVar"),
    "GainSIVar": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "GainSIVar"),
    "MeterSIVar": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "MeterSIVar"),
    "MilliMeterSIVar": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "MilliMeterSIVar"),
    "TemperatureSIVar": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "TemperatureSIVar"),
    "AbsoluteFrequencySIVar": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "AbsoluteFrequencySIVar"),
    "RelativeFrequencySIVar": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "RelativeFrequencySIVar"),
    "SIPrefix": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "SIPrefix"),
    "SIUnit": (_SONIC_PROTOCOL_SI_UNIT_MODULE, "SIUnit"),
    "DeviceParamConstantType": (_SONIC_PROTOCOL_SCHEMA_MODULE, "DeviceParamConstantType"),
    "Procedure": (_SONIC_PROTOCOL_SCHEMA_MODULE, "Procedure"),
    "Loglevel": (_SONIC_PROTOCOL_SCHEMA_MODULE, "Loglevel"),
    "DeviceType": (_SONIC_PROTOCOL_SCHEMA_MODULE, "DeviceType"),
    "ScanArgs": (_PROCEDURES_MODULE, "ScanArgs"),
    "AutoArgs": (_PROCEDURES_MODULE, "AutoArgs"),
    "TuneArgs": (_PROCEDURES_MODULE, "TuneArgs"),
    "WipeArgs": (_PROCEDURES_MODULE, "WipeArgs"),
    "RamperArgs": (_PROCEDURES_MODULE, "RamperArgs"),
    "SpectrumMeasureArgs": (_PROCEDURES_MODULE, "SpectrumMeasureArgs"),
    "Experiment": ("soniccontrol.data_capturing.experiment", "Experiment"),
    "ExperimentMetaData": ("soniccontrol.data_capturing.experiment", "ExperimentMetaData"),
    "HDF5ExperimentReader": ("soniccontrol.data_capturing.experiment_store", "HDF5ExperimentReader"),
    "HDF5ExperimentWriter": ("soniccontrol.data_capturing.experiment_store", "HDF5ExperimentWriter"),
    "CLIConnection": ("soniccontrol.communication.connection", "CLIConnection"),
    "SerialConnection": ("soniccontrol.communication.connection", "SerialConnection"),
    "start_server": ("soniccontrol.network.server", "start_server"),
    "enable_server_on_startup": (
        "soniccontrol.network.enable_server_on_startup.script",
        "enable_server_on_startup",
    ),
    "RemoteServerConnection": ("soniccontrol.network.connection", "RemoteServerConnection"),
}


def __getattr__(name: str) -> Any:
    if name == "logger":
        return logger

    export = _EXPORTS.get(name)
    if export is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attribute_name = export

    module = import_module(module_name)
    return getattr(module, attribute_name)


def __dir__() -> list[str]:
    return sorted(__all__)
