from typing import Any, Dict, List, Optional

import pandas as pd
import attrs
import datetime

from sonic_protocol.defs import Version
from sonic_protocol.field_names import EFieldName
from soniccontrol.app_config import SOFTWARE_VERSION
from soniccontrol.data_capturing.capture_target import CaptureTargets
from soniccontrol.app_config import PLATFORM
from soniccontrol.device_data import FirmwareInfo


def convert_authors(x: Any) -> List[str]:
    if isinstance(x, list):
        if any(map(lambda item: not isinstance(item, str), x)):
            raise ValueError("Expected the list to only contain items of type str")
        return x
    elif isinstance(x, str):
        return list(map(str.strip, x.split(",")))
    raise ValueError("Expected type List[str] or str")


@attrs.define(auto_attribs=True)
class Experiment:
    experiment_name: str
    authors: List[str] = attrs.field(converter=convert_authors)

    transducer_id: str
    add_on_id: str
    connector_type: str
    medium: str

    firmware_info: FirmwareInfo

    date_time: datetime.datetime = attrs.field(factory=datetime.datetime.now) # deducible
    location: Optional[str] = None
    description: str = ""

    medium_temperature: Optional[float] = None
    gap: Optional[float] = None
    reflector: Optional[str] = None
    cable_length: Optional[float] = None
    cable_type: Optional[str] = None

    additional_metadata: Dict = attrs.Factory(dict)

    data: pd.DataFrame = attrs.Factory(lambda: pd.DataFrame(columns=[
        EFieldName.TIMESTAMP.value, 
        EFieldName.FREQUENCY.value, EFieldName.GAIN.value, 
        EFieldName.URMS.value, EFieldName.IRMS.value, EFieldName.PHASE.value, 
        EFieldName.TEMPERATURE.value
    ]))
    
    # deducible
    sonic_control_version: Version = attrs.field(default=SOFTWARE_VERSION)
    operating_system: str = attrs.field(default=PLATFORM.value)

    capture_target: CaptureTargets = attrs.field(default=CaptureTargets.FREE)
    target_parameters: Dict = attrs.field(factory=dict)

