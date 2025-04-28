from typing import Any, Dict
import attrs
from sonic_protocol.defs import CommandCode
from sonic_protocol.field_names import EFieldName


class Command:
    def __init__(self, code: CommandCode):
        self._code = code

    @property
    def code(self) -> CommandCode:
        return self._code

    @property
    def args(self) -> Dict[str, Any]:
        return attrs.asdict(self)


@attrs.define()
class GetProtocol(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_PROTOCOL)

@attrs.define()
class GetInfo(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_INFO)

@attrs.define()
class GetUpdate(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_UPDATE)

@attrs.define()
class GetGain(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_GAIN)

@attrs.define()
class GetSwf(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_SWF)

@attrs.define()
class GetFreq(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_FREQ)

@attrs.define()
class SetFrequency(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_FREQ)

    value: int = attrs.field(alias=EFieldName.FREQUENCY.value)   

@attrs.define()
class SetSwf(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_SWF)

    value: int = attrs.field(alias=EFieldName.SWF.value)

@attrs.define()
class SetGain(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_GAIN)

    value: int = attrs.field(alias=EFieldName.GAIN.value)

@attrs.define()
class SetOn(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_ON)

@attrs.define()
class SetOff(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_OFF)

@attrs.define()
class SetAtf(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_ATF)

    index: int = attrs.field()
    value: int = attrs.field(alias=EFieldName.ATF.value)

@attrs.define()
class SetAtk(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_ATK)

    index: int = attrs.field()
    value: int = attrs.field(alias=EFieldName.ATK.value)

@attrs.define()
class SetAtt(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_ATT)

    index: int = attrs.field()
    value: int = attrs.field(alias=EFieldName.ATT.value)


@attrs.define()
class SetRamp(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_RAMP)

@attrs.define()
class SetTune(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_TUNE)

@attrs.define()
class SetAuto(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_AUTO)

@attrs.define()
class SetWipe(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_WIPE)

@attrs.define()
class SetScan(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_SCAN)

@attrs.define()
class SetScanArg(Command):
    def __attrs_post_init__(self):
        alias_map = {
            CommandCode.SET_SCAN_F_RANGE: EFieldName.SCAN_F_RANGE.value,
            CommandCode.SET_SCAN_F_SHIFT: EFieldName.SCAN_F_SHIFT.value,
            CommandCode.SET_SCAN_F_STEP: EFieldName.SCAN_F_STEP.value,
            CommandCode.SET_SCAN_GAIN: EFieldName.SCAN_GAIN.value,
            CommandCode.SET_SCAN_T_STEP: EFieldName.SCAN_T_STEP.value,
        }
        if self.argCode not in alias_map:
            raise ValueError(f"Invalid ArgCode: {self.argCode}")
        object.__setattr__(self, 'value_alias', alias_map[self.argCode])
        super().__init__(code=self.argCode)
    argCode: CommandCode = attrs.field()
    value: int = attrs.field()
    value_alias: str = attrs.field(init=False)

@attrs.define()
class SetTuneArg(Command):
    def __attrs_post_init__(self):
        alias_map = {
            CommandCode.SET_TUNE_F_SHIFT: EFieldName.TUNE_F_SHIFT.value,
            CommandCode.SET_TUNE_F_STEP: EFieldName.TUNE_F_STEP.value,
            CommandCode.SET_TUNE_GAIN: EFieldName.TUNE_GAIN.value,
            CommandCode.SET_TUNE_N_STEPS: EFieldName.TUNE_N_STEPS.value,
            CommandCode.SET_TUNE_T_STEP: EFieldName.TUNE_T_STEP.value,
            CommandCode.SET_TUNE_T_TIME: EFieldName.TUNE_T_TIME.value,
        }
        if self.argCode not in alias_map:
            raise ValueError(f"Invalid ArgCode: {self.argCode}")
        object.__setattr__(self, 'value_alias', alias_map[self.argCode])
        super().__init__(code=self.argCode)
    argCode: CommandCode = attrs.field()
    value: int = attrs.field()
    value_alias: str = attrs.field(init=False)

@attrs.define()
class SetWipeArg(Command):
    def __attrs_post_init__(self):
        alias_map = {
            CommandCode.SET_WIPE_F_RANGE: EFieldName.WIPE_F_RANGE.value,
            CommandCode.SET_WIPE_F_STEP: EFieldName.WIPE_F_STEP.value,
            CommandCode.SET_WIPE_T_OFF: EFieldName.WIPE_T_OFF.value,
            CommandCode.SET_WIPE_T_ON: EFieldName.WIPE_T_ON.value,
            CommandCode.SET_WIPE_T_PAUSE: EFieldName.WIPE_T_PAUSE.value,
        }
        if self.argCode not in alias_map:
            raise ValueError(f"Invalid ArgCode: {self.argCode}")
        object.__setattr__(self, 'value_alias', alias_map[self.argCode])
        super().__init__(code=self.argCode)
    argCode: CommandCode = attrs.field()
    value: int = attrs.field()
    value_alias: str = attrs.field(init=False)

@attrs.define()
class SetRampArg(Command):
    def __attrs_post_init__(self):
        alias_map = {
            CommandCode.SET_RAMP_F_START: EFieldName.RAMP_F_START.value,
            CommandCode.SET_RAMP_F_STEP: EFieldName.RAMP_F_STEP.value,
            CommandCode.SET_RAMP_F_STOP: EFieldName.RAMP_F_STOP.value,
            CommandCode.SET_RAMP_T_OFF: EFieldName.RAMP_T_OFF.value,
            CommandCode.SET_RAMP_T_ON: EFieldName.RAMP_T_ON.value,
        }
        if self.argCode not in alias_map:
            raise ValueError(f"Invalid ArgCode: {self.argCode}")
        object.__setattr__(self, 'value_alias', alias_map[self.argCode])
        super().__init__(code=self.argCode)
    argCode: CommandCode = attrs.field()
    value: int = attrs.field()
    value_alias: str = attrs.field(init=False)


@attrs.define()
class SonicForce(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SONIC_FORCE)

@attrs.define()
class SetStop(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_STOP)

@attrs.define()
class GetRamp(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_RAMP)

@attrs.define()
class GetWipe(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_WIPE)

@attrs.define()
class GetTune(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_TUNE)

@attrs.define()
class GetScan(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_SCAN)


@attrs.define()
class GetAuto(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_AUTO)