from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any

import datetime

from soniccontrol.sonicamp.sonicagent import SerialAgent
from soniccontrol.sonicamp.status import StatusAdapter, BasicStatusAdapter
from soniccontrol.sonicamp.amp_factory import AmpFactory
from soniccontrol.sonicamp.controllers import (
    FrequencyController,
    GainController,
    ModeController,
)


class SonicAmp:
    @dataclass
    class Data:
        type_: str = field(default="")
        version: float = field(default=0.0)
        firmware_msg: str = field(default="")
        modules: Optional[SonicAmp.Modules] = field(default=None)
        status: Optional[SonicAmp.Status] = field(default=None)

    @dataclass(frozen=True)
    class Modules:
        buffer: bool = field(default=False)
        display: bool = field(default=False)
        eeprom: bool = field(default=False)
        fram: bool = field(default=False)
        i_current: bool = field(default=False)
        current1: bool = field(default=False)
        current2: bool = field(default=False)
        io_serial: bool = field(default=False)
        thermo_ext: bool = field(default=False)
        thermo_int: bool = field(default=False)
        khz: bool = field(default=False)
        mhz: bool = field(default=False)
        portexpander: bool = field(default=False)
        protocol: bool = field(default=False)
        protocol_fix: bool = field(default=False)
        relais: bool = field(default=False)
        scanning: bool = field(default=False)
        sonsens: bool = field(default=False)
        tuning: bool = field(default=False)
        switch: bool = field(default=False)
        switch2: bool = field(default=False)

    @dataclass
    class Status:
        error: int = field(default=0, repr=False)
        frequency: int = field(default=0)
        gain: int = field(default=0)
        current_protocol: int = field(default=0, repr=False)
        wipe_mode: bool = field(default=False, repr=False)
        temperature: float = field(default=0)
        signal: bool = field(default=False)
        urms: Union[float, int] = field(default=0)
        irms: Union[float, int] = field(default=0)
        phase: Union[float, int] = field(default=0)
        timestamp: datetime.datetime = field(
            default_factory=datetime.datetime.now, compare=False
        )

        default_adapter: StatusAdapter = field(
            default=BasicStatusAdapter, repr=False, compare=False, hash=False
        )

        @classmethod
        def from_data(
            cls, data: str, adapter: Optional[StatusAdapter] = None
        ) -> SonicAmp.Status:
            return cls(
                adapter.convert_data(data)
                if adapter
                else cls.default_adapter.convert_data(data)
            )

        @classmethod
        def from_updated_data(
            cls,
            old_status: SonicAmp.Status,
            data: str,
            adapter: Optional[StatusAdapter] = None,
        ) -> SonicAmp.Status:
            return cls(
                adapter.update_data(old_status, data)
                if adapter
                else cls.default_adapter.update_data(old_status, data)
            )

        def dump(self) -> Dict[str, Any]:
            return self.__dict__

    def __init__(
        self,
        serial_agent: SerialAgent,
        data: SonicAmp.Data,
        update_strategy: StatusAdapter,
        frequency_controller: FrequencyController,
        gain_controller: GainController,
        mode_controller: ModeController,
        ramp_strategy: RampStrategy,
    ) -> None:
        self._serial_agent: SerialAgent = serial_agent
        self._frequency_controller: FrequencyController = frequency_controller
        self._gain_controller: GainController = gain_controller
        self._mode_controller: ModeController = mode_controller
        self._update_strategy: StatusAdapter = update_strategy

        self._ramp_strategy: RampStrategy = ramp_strategy
        self._ramp_strategy.set_freq_controller(self._frequency_controller)
        self._ramp_strategy.set_gain_controller(self._gain_controller)
        self._ramp_strategy.set_update_strategy(self._update_strategy)

        self._data: SonicAmp.Data = data

    @property
    def serial_agent(self) -> SerialAgent:
        return self._serial_agent

    @classmethod
    def build_amp(self, data: SonicAmp.Data) -> SonicAmp:
        return AmpFactory.build_amp(data)

    def update(self) -> None:
        self._update_strategy.update(self._data.status)

    def get_status(self) -> Status:
        ...

    def get_sens(self) -> Dict[str, Union[float, int]]:
        ...

    def get_modules(self) -> SonicAmp.Modules:
        ...

    def set_frequency(self, frequency: int) -> str:
        self._update_strategy.operation(
            self._frequency_controller.operation(frequency), self._data.status
        )

    def set_gain(self, gain: int) -> None:
        self._update_strategy.operation(
            self._gain_controller.operation(gain), self._data.status
        )

    def set_signal_on(self) -> None:
        self._update_strategy.operation(
            self._mode_controller.signal_on(), self._data.status
        )

    def set_signal_off(self) -> None:
        self._update_strategy.operation(
            self._mode_controller.signal_off(), self._data.status
        )

    def set_signal_auto(self) -> None:
        self._update_strategy.operation(
            self._mode_controller.signal_auto(), self._data.status
        )

    def hold(self) -> None:
        pass

    def ramp_freq(self) -> None:
        pass

    def ramp_gain(self) -> None:
        pass

    def chirp_ramp_freq(self) -> None:
        pass

    def chirp_ramp_gain(self) -> None:
        pass
