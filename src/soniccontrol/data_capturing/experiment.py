from typing import Any, Dict, List, Optional

import attrs
import datetime

from sonic_protocol.schema import SIPrefix, SIUnit, Version
from soniccontrol.data_capturing.capture_target import CaptureTargets
from soniccontrol.device_data import FirmwareInfo
from sonic_protocol.si_unit import MeterSIVar, MilliMeterSIVar, SIVar, SIVarMeta, TemperatureSIVar


def convert_authors(x: Any) -> List[str]:
    if isinstance(x, list):
        if any(map(lambda item: not isinstance(item, str), x)):
            raise ValueError("Expected the list to only contain items of type str")
        return x
    elif isinstance(x, str):
        return list(map(str.strip, x.split(",")))
    raise ValueError("Expected type List[str] or str")


@attrs.define(auto_attribs=True)
class ExperimentMetaData:
    experiment_name: str
    authors: List[str] = attrs.field(converter=convert_authors)

    transducer_id: str
    add_on_id: str
    connector_type: str
    medium: str

    location: Optional[str] = None
    description: str = ""

    medium_temperature: Optional[TemperatureSIVar] = None
    gap: Optional[MilliMeterSIVar] = None
    reflector: Optional[str] = None
    cable_length: Optional[MeterSIVar] = None
    cable_type: Optional[str] = None

    additional_metadata: Dict = attrs.field(factory=dict,
                                                                    #Either specify all major SIVars or allow abstract SIVar
        metadata={"field_view_kwargs": {"types": [int, float, str, SIVar]}}
    )


@attrs.define(auto_attribs=True)
class Experiment:
    metadata: ExperimentMetaData
    firmware_info: FirmwareInfo
    sonic_control_version: Version
    operating_system: str

    capture_target: CaptureTargets = attrs.field(default=CaptureTargets.FREE)
    target_parameters: Dict = attrs.field(factory=dict)

    date_time: datetime.datetime = attrs.field(factory=datetime.datetime.now) 
