from typing import Any, Dict
import attrs
from sonic_protocol.command_codes import CommandCode, ICommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocols.protocol_v3_0_0.types.types import Parity, UartInterface
from sonic_protocol.schema import Loglevel


class Command:
    def __init__(self, code: ICommandCode):
        self._code = code

    @property
    def code(self) -> ICommandCode:
        return self._code

    @property
    def args(self) -> Dict[str, Any]:
        return attrs.asdict(self, recurse=False)


# Commands used for the operator

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
class GetUpdateWorker(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_UPDATE_WORKER_V3_0_0)

@attrs.define()
class GetUpdateDescale(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_UPDATE_DESCALE_V3_0_0)

@attrs.define()
class GetUiptRaw(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_UIPT_RAW)
        

@attrs.define()
class RestartDevice(Command):
    """
    This command should only be used by sonic_device internally.

    If you want to restart the device, use the restart function of SonicDevice or RemoteController instead.
    """
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.RESTART_DEVICE)

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
class GetSignal(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_SIGNAL)


@attrs.define()
class GetAtf(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_ATF)

    index: int = attrs.field()

@attrs.define()
class GetAtk(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_ATK)

    index: int = attrs.field()

@attrs.define()
class GetAtt(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_ATT)

    index: int = attrs.field()

@attrs.define()
class SetFrequency(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_FREQ)

    value: int = attrs.field(alias=EFieldName.FREQUENCY.name)   

@attrs.define()
class SetSwf(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_SWF)

    value: int = attrs.field(alias=EFieldName.SWF.name)

@attrs.define()
class SetGain(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_GAIN)

    value: int = attrs.field(alias=EFieldName.GAIN.name)

@attrs.define()
class SetDac(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_DAC)

    value: int = attrs.field(alias=EFieldName.VOLTAGE.name)

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
    value: int = attrs.field(alias=EFieldName.ATF.name)

@attrs.define()
class SetAtk(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_ATK)

    index: int = attrs.field()
    value: float = attrs.field(alias=EFieldName.ATK.name)

@attrs.define()
class SetAtt(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_ATT)

    index: int = attrs.field()
    value: float = attrs.field(alias=EFieldName.ATT.name)


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
class SetScanFRange(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_SCAN_F_RANGE)
    value: int = attrs.field(alias=EFieldName.SCAN_F_RANGE.name)

@attrs.define()
class SetScanFShift(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_SCAN_F_SHIFT)
    value: int = attrs.field(alias=EFieldName.SCAN_F_SHIFT.name)

@attrs.define()
class SetScanFStep(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_SCAN_F_STEP)
    value: int = attrs.field(alias=EFieldName.SCAN_F_STEP.name)

@attrs.define()
class SetScanGain(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_SCAN_GAIN)
    value: int = attrs.field(alias=EFieldName.SCAN_GAIN.name)

@attrs.define()
class SetScanTStep(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_SCAN_T_STEP)
    value: int = attrs.field(alias=EFieldName.SCAN_T_STEP.name)

@attrs.define()
class SetTuneFShift(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_TUNE_F_SHIFT)
    value: int = attrs.field(alias=EFieldName.TUNE_F_SHIFT.name)

@attrs.define()
class SetTuneFStep(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_TUNE_F_STEP)
    value: int = attrs.field(alias=EFieldName.TUNE_F_STEP.name)

@attrs.define()
class SetTuneGain(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_TUNE_GAIN)
    value: int = attrs.field(alias=EFieldName.TUNE_GAIN.name)

@attrs.define()
class SetTuneNSteps(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_TUNE_N_STEPS)
    value: int = attrs.field(alias=EFieldName.TUNE_N_STEPS.name)

@attrs.define()
class SetTuneTStep(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_TUNE_T_STEP)
    value: int = attrs.field(alias=EFieldName.TUNE_T_STEP.name)

@attrs.define()
class SetTuneTTime(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_TUNE_T_TIME)
    value: int = attrs.field(alias=EFieldName.TUNE_T_TIME.name)

@attrs.define()
class SetWipeFRange(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_WIPE_F_RANGE)
    value: int = attrs.field(alias=EFieldName.WIPE_F_RANGE.name)

@attrs.define()
class SetWipeFStep(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_WIPE_F_STEP)
    value: int = attrs.field(alias=EFieldName.WIPE_F_STEP.name)

@attrs.define()
class SetWipeTOff(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_WIPE_T_OFF)
    value: int = attrs.field(alias=EFieldName.WIPE_T_OFF.name)

@attrs.define()
class SetWipeTOn(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_WIPE_T_ON)
    value: int = attrs.field(alias=EFieldName.WIPE_T_ON.name)

@attrs.define()
class SetWipeTPause(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_WIPE_T_PAUSE)
    value: int = attrs.field(alias=EFieldName.WIPE_T_PAUSE.name)

@attrs.define()
class SetWipeGain(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_WIPE_GAIN)
    value: int = attrs.field(alias=EFieldName.WIPE_GAIN.name)

@attrs.define()
class SetRampFStart(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_RAMP_F_START)
    value: int = attrs.field(alias=EFieldName.RAMP_F_START.name)

@attrs.define()
class SetRampFStep(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_RAMP_F_STEP)
    value: int = attrs.field(alias=EFieldName.RAMP_F_STEP.name)

@attrs.define()
class SetRampFStop(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_RAMP_F_STOP)
    value: int = attrs.field(alias=EFieldName.RAMP_F_STOP.name)

@attrs.define()
class SetRampTOff(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_RAMP_T_OFF)
    value: int = attrs.field(alias=EFieldName.RAMP_T_OFF.name)

@attrs.define()
class SetRampTOn(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_RAMP_T_ON)
    value: int = attrs.field(alias=EFieldName.RAMP_T_ON.name)

@attrs.define()
class SetRampGain(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_RAMP_GAIN)
    value: int = attrs.field(alias=EFieldName.RAMP_GAIN.name)

@attrs.define()
class SetDutyCycleTOn(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_DUTY_CYCLE_T_ON)
    value: int = attrs.field(alias=EFieldName.DUTY_CYCLE_T_ON.name)

@attrs.define()
class SetDutyCycleTOff(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_DUTY_CYCLE_T_OFF)
    value: int = attrs.field(alias=EFieldName.DUTY_CYCLE_T_OFF.name)

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


@attrs.define()
class GetConnectionStatus(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_CONNECTION_STATUS)

@attrs.define()
class GetNumTests(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_NUM_TESTS)

@attrs.define()
class GetTestInfo(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_TEST_INFO)

    index: int = attrs.field()

@attrs.define()
class RunTest(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.RUN_TEST)

    index: int = attrs.field()

@attrs.define()
class AbortTest(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.ABORT_TEST)

@attrs.define()
class GetTestValidationArg(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_TEST_VALIDATION_ARG)

    index: int = attrs.field()

@attrs.define()
class SetLogLevel(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_LOG_LEVEL)

    index: str = attrs.field(alias=EFieldName.LOGGER_NAME.name)
    value: Loglevel = attrs.field(alias=EFieldName.LOG_LEVEL.name)

@attrs.define()
class GetNumLoggers(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_LOGGER_LIST_SIZE)

@attrs.define()
class GetLogger(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_LOGGER_LIST_ITEM)

    index: int = attrs.field(alias=EFieldName.INDEX.name)

@attrs.define()
class GetModbusSettings(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.GET_MODBUS_SETTINGS)

@attrs.define()
class SetModbusServerAddress(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_MODBUS_SLAVE_ADDRESS)

    value: int = attrs.field(alias=EFieldName.MODBUS_SERVER_ID.name)

@attrs.define()
class SetModbusParity(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_MODBUS_PARITY)

    value: Parity = attrs.field(alias=EFieldName.PARITY.name)

@attrs.define()
class SetModbusBaudrate(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_MODBUS_BAUDRATE)

    value: int = attrs.field(alias=EFieldName.BAUDRATE.name)

@attrs.define()
class SetModbusInterface(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.SET_MODBUS_INTERFACE)

    value: UartInterface = attrs.field(alias=EFieldName.UART_INTERFACE.name)

@attrs.define()
class StartConfigurator(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.START_CONFIGURATOR)

    value: str = attrs.field(alias=EFieldName.PASSWORD_HASHED.name)

@attrs.define()
class StartOperator(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.START_OPERATOR)


# Legacy specific commands

# We need a different auto and wipe command so that procedure instantiator  knows which proc to create
@attrs.define()
class SetAutoLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_AUTO)

@attrs.define()
class SetWipeLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_WIPE)

@attrs.define()
class SetStepLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_STEP)
    value: int = attrs.field(alias=EFieldName.LEGACY_STEP.name)

@attrs.define()
class SetSingLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_SING)
    value: int = attrs.field(alias=EFieldName.LEGACY_SING.name)

@attrs.define()
class SetPausLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_PAUS)
    value: int = attrs.field(alias=EFieldName.LEGACY_PAUS.name)

@attrs.define()
class SetRangLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_RANG)
    value: int = attrs.field(alias=EFieldName.LEGACY_RANG.name)

@attrs.define()
class SetTustLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_TUST)
    value: int = attrs.field(alias=EFieldName.LEGACY_TUST.name)

@attrs.define()
class SetTutmLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_TUTM)
    value: int = attrs.field(alias=EFieldName.LEGACY_TUTM.name)

@attrs.define()
class SetScstLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_SCST)
    value: int = attrs.field(alias=EFieldName.LEGACY_SCST.name)

@attrs.define()
class GetPvalLegacy(Command):
    def __attrs_post_init__(self):
        super().__init__(code=CommandCode.LEGACY_PVAL)