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
class ListAvailableCommands(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LIST_AVAILABLE_COMMANDS)

@attrs.define()
class GetUpdate(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.DASH)

@attrs.define()
class GetGain(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_GAIN)

@attrs.define()
class GetSwf(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_SWF)

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