from typing import Any, Type

import attrs
from attrs import validators

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser import commands
from soniccontrol.procedures.holder import HolderArgs, convert_to_holder_args
from soniccontrol.procedures.procedure import Procedure, ProcedureArgs
from soniccontrol.sonic_device import SonicDevice


@attrs.define(auto_attribs=True, init=False)
class AutoLegacyArgs(ProcedureArgs):
    @classmethod
    def get_description(cls) -> str:
        return """The AUTO procedure starts by executing the SCAN procedure, and when finished, immediately starts the TUNE procedure.
    - The SCAN procedure measures the electric response of the connected add-on over
        a wide frequency range at low gain and determines the optimal driving frequency.
    - The TUNE procedure is designed to tune the driving frequency to create the optimal field for the intended application.
        It is helpful when certain parameters are expected to change significantly, e.g. temperature, liquid composition etc.
"""

    # TODO set correct limits and defaults
    f_center: int = attrs.field(
        default=1000000,
        metadata={"enum": EFieldName.LEGACY_F_CENTER},
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ]
    )

    tust: int = attrs.field(
        default=500,
        metadata={"enum": EFieldName.LEGACY_TUST},
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ]
    )
    tutm: HolderArgs = attrs.field(
        default=HolderArgs(10000, "ms"),
        metadata={"enum": EFieldName.LEGACY_TUTM},
        converter=convert_to_holder_args
    )
    scst: int = attrs.field(
        default=1000, 
        metadata={"enum": EFieldName.LEGACY_SCST},
        validator=[
            validators.instance_of(int),
            validators.ge(0),
            validators.le(5000000)
        ]
    )

class AutoLegacyProc(Procedure):    
    @classmethod
    def get_args_class(cls) -> Type: 
        return AutoLegacyArgs

    @property
    def is_remote(self) -> bool:
        return True

    async def execute(self, device: SonicDevice, args: AutoLegacyArgs) -> None:
        await device.execute_command(commands.SetTustLegacy(args.tust))
        await device.execute_command(commands.SetScstLegacy(args.scst))
        tutm_duration = int(args.tutm.duration_in_ms) if isinstance(args.tutm, HolderArgs) else int(args.tutm[0])
        await device.execute_command(commands.SetTutmLegacy(tutm_duration))
        await device.execute_command(commands.SetFrequency(args.f_center))

        await device.execute_command(commands.SetAutoLegacy())

    async def fetch_args(self, device: SonicDevice) -> dict[str, Any]:
        # answer = await device.execute_command(commands.GetPvalLegacy())
        # if answer.was_validated and answer.valid:
        #     return AutoLegacyArgs.to_dict_with_holder_args(answer)
        return {}