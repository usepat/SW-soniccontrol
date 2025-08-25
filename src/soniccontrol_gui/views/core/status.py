import copy
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple
import ttkbootstrap as ttk
from sonic_protocol.schema import AnswerFieldDef, IEFieldName, Signal
from sonic_protocol.python_parser.answer_field_converter import AnswerFieldToStringConverter
from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocols.protocol_v1_0_0.transducer_commands.transducer_fields import field_temperature_celsius
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import View
from soniccontrol_gui.constants import (color, events, fonts, sizes,
                                                     style, ui_labels)
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.widgets.xyscrolled_frame import XYScrolledFrame
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.views.core.custom_meter import CustomMeter

class StatusBar(UIComponent):
    def __init__(self, parent: UIComponent, parent_slot: View, answer_field_defs: List[AnswerFieldDef]):
        self._logger = logging.getLogger(parent.logger.name + "." + StatusBar.__name__)
        
        self._field_converters = {
            answer_field.field_name : AnswerFieldToStringConverter(answer_field)
            for answer_field in answer_field_defs
        }
        if EFieldName.TEMPERATURE in self._field_converters:
            # Convert mK to °C
            self._field_converters[EFieldName.TEMPERATURE] = AnswerFieldToStringConverter(field_temperature_celsius)

        self._logger.debug("Create Statusbar")
        self._view = StatusBarView(parent_slot, self._field_converters.keys())
        self._status_panel = StatusPanel(self, self._view.panel_frame, answer_field_defs)
        self._status_panel_expanded = False
        super().__init__(parent, self._view, self._logger)
        self._view.set_status_clicked_command(self.on_expand_status_panel)
        self._view.expand_panel_frame(self._status_panel_expanded)

    def on_expand_status_panel(self) -> None:
        self._logger.debug("Expand status panel")
        self._status_panel_expanded = not self._status_panel_expanded
        self._view.expand_panel_frame(self._status_panel_expanded)

    def on_update_status(self, status: Dict[IEFieldName, Any]):
        status = copy.copy(status)
        if EFieldName.TEMPERATURE in status and (status[EFieldName.TEMPERATURE] == 404 or status[EFieldName.TEMPERATURE] == 0):
            status[EFieldName.TEMPERATURE] = float("nan")
        elif EFieldName.TEMPERATURE in status:
            # Convert mK to °C
            temp_mC = status[EFieldName.TEMPERATURE] - 273150.0
            status[EFieldName.TEMPERATURE] = temp_mC / 1000
        field_labels: Dict[IEFieldName, str] = {
            EFieldName.FREQUENCY: "Frequency",
            EFieldName.SWF: "Switching Freq",
            EFieldName.GAIN: "Gain",
            EFieldName.IRMS: "Irms",
            EFieldName.URMS: "Urms",
            EFieldName.PHASE: "Phase",
            EFieldName.TEMPERATURE: "Temperature",
            EFieldName.TS_FLAG: "Transducer Shorted",
            EFieldName.SIGNAL: "Signal",
            EFieldName.PROCEDURE: "Procedure",
            EFieldName.ERROR_CODE: "Error Code",
            EFieldName.UNDEFINED: "Undefined",
            EFieldName.ANOMALY_DETECTION: "Anomaly",
        }
        status_field_text_representations = {
            field: field_labels[field] + ": " + converter.convert(status[field])
            for field, converter in  self._field_converters.items()
        }

        self._view.update_labels(status_field_text_representations)
        if self._status_panel_expanded:
            self._status_panel.on_update_status(status)


class StatusPanel(UIComponent):
    def __init__(self, parent: UIComponent, parent_slot: View, answer_field_defs: List[AnswerFieldDef]): 
        self._answer_field_defs = answer_field_defs  
        self._field_converters = {
            answer_field.field_name : AnswerFieldToStringConverter(answer_field)
            for answer_field in answer_field_defs
        }
        if EFieldName.TEMPERATURE in self._field_converters:
            # Convert mK to °C
            self._field_converters[EFieldName.TEMPERATURE] = AnswerFieldToStringConverter(field_temperature_celsius)
        self._field_names = self._field_converters.keys()

        self._view = StatusPanelView(parent_slot)
        super().__init__(parent, self._view)

    def on_update_status(self, status: Dict[IEFieldName, Any]):
        status_field_text_representations = {
            field: converter.convert(status[field])
            for field, converter in  self._field_converters.items()
        }

        if EFieldName.FREQUENCY in self._field_names:
            freq = status[EFieldName.FREQUENCY] / 1000
        elif EFieldName.SWF in self._field_names:
            freq = status[EFieldName.SWF] / 1000
        else:
            freq = 0

        temp = status[EFieldName.TEMPERATURE] if EFieldName.TEMPERATURE in self._field_names else 0
        is_signal_on = status[EFieldName.SIGNAL] == Signal.ON

        self._view.update_stats(
            freq=freq,
            gain=status[EFieldName.GAIN],
            temp=temp,
            urms=status_field_text_representations[EFieldName.URMS],
            irms=status_field_text_representations[EFieldName.IRMS],
            phase=status_field_text_representations[EFieldName.PHASE],
            signal=ui_labels.SIGNAL_ON if is_signal_on else ui_labels.SIGNAL_OFF
        )

        self._view.set_signal_image(
            images.LED_ICON_GREEN if is_signal_on else images.LED_ICON_RED, 
            sizes.LARGE_BUTTON_ICON_SIZE
        )

class StatusBarView(View):
    def __init__(
        self,
        master: ttk.Frame,
        status_fields: Iterable[IEFieldName],
        *args,
        **kwargs
    ) -> None:
        self._status_field_names = status_fields
        self._status_field_labels: Dict[IEFieldName, ttk.Label] = {}
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        tab_name = "status_bar"

        self._panel_frame: ttk.Frame = ttk.Frame(self)
        self._status_bar_frame: ttk.Frame = ttk.Frame(self)

        self._scrolled_info: XYScrolledFrame = XYScrolledFrame(
            self._status_bar_frame, bootstyle=ttk.SECONDARY, autohide=False, mousewheel_scroll_orientation=ttk.HORIZONTAL
        )
        self._scrolled_info.hide_scrollbars()

        for status_field in self._status_field_names:
            if status_field == EFieldName.SIGNAL:
                continue # Skip signal, because that will have an own special label

            label = ttk.Label(
                self._scrolled_info,
                bootstyle=style.INVERSE_SECONDARY
            )
            label.pack(side=ttk.LEFT, padx=5)
            self._status_field_labels[status_field] = label
            WidgetRegistry.register_widget(label, status_field.name.lower() + "_label", tab_name)

        self._signal_frame: ttk.Frame = ttk.Frame(self._status_bar_frame)
        ICON_LABEL_PADDING: tuple[int, int, int, int] = (8, 0, 0, 0)
        signal_label: ttk.Label = ttk.Label(
            self._signal_frame,
            bootstyle=style.INVERSE_SECONDARY, # I just read bootystyle instead of bootstyle. lol
            padding=ICON_LABEL_PADDING,
            image=ImageLoader.load_image_resource(
                images.LIGHTNING_ICON_WHITE, sizes.BUTTON_ICON_SIZE
            ),
            compound=ttk.LEFT,
        )
        signal_label.pack(side=ttk.RIGHT, ipadx=3)
        self._status_field_labels[EFieldName.SIGNAL] = signal_label
        WidgetRegistry.register_widget(signal_label, "signal_label", tab_name)

        self.configure(bootstyle=ttk.SECONDARY)


    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH, padx=3, pady=3)
        self._panel_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True)
        self._status_bar_frame.pack(side=ttk.BOTTOM, fill=ttk.X)
        self._signal_frame.pack(side=ttk.RIGHT)
        self._scrolled_info.pack(expand=True, fill=ttk.BOTH, side=ttk.RIGHT)

    @property 
    def panel_frame(self) -> ttk.Frame:
        return self._panel_frame
    
    def expand_panel_frame(self, expand: bool) -> None:
        if expand:
            self._panel_frame.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True)
        else:
            self._panel_frame.pack_forget()

    def set_status_clicked_command(self, command: Callable[[], None]) -> None:
        for label in self._status_field_labels.values():
            label.bind(events.CLICKED_EVENT, lambda _e: command())

    def update_labels(self, field_texts: Dict[IEFieldName, str]):
        for status_field, text in field_texts.items():
            label = self._status_field_labels[status_field]
            label.configure(text=text)
        self.update()


class StatusPanelView(View):
    def __init__(self, master: ttk.Window | ttk.tk.Widget, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        tab_name = "status_panel"

        self._main_frame: ttk.Frame = ttk.Frame(self)
        self._meter_frame: ttk.Frame = ttk.Frame(self._main_frame)
        self._sonicmeasure_values_frame: ttk.Frame = ttk.Frame(
            self._main_frame
        )
        self._signal_frame: ttk.Label = ttk.Label(
            self._main_frame, background=color.STATUS_MEDIUM_GREY
        )

        self._freq_meter: CustomMeter = CustomMeter(
            self._meter_frame,
            bootstyle=ttk.DARK,
            textright=ui_labels.KHZ,
            subtext=ui_labels.FREQUENCY,
            metersize=sizes.METERSIZE,
            #Use DeviceParamConstants in kHz
            amountmin=100,
            amountmax=10000,

        )
        WidgetRegistry.register_widget(self._freq_meter, "freq_meter", tab_name)

        self._gain_meter: CustomMeter = CustomMeter(
            self._meter_frame,
            bootstyle=ttk.SUCCESS,
            textright=ui_labels.PERCENT,
            subtext=ui_labels.GAIN,
            metersize=sizes.METERSIZE,
            amountmax=150
        )
        WidgetRegistry.register_widget(self._gain_meter, "gain_meter", tab_name)

        self._temp_meter: CustomMeter = CustomMeter(
            self._meter_frame,
            bootstyle=ttk.WARNING,
            bootstyleneg=ttk.PRIMARY,
            textright=ui_labels.DEGREE_CELSIUS,
            subtext=ui_labels.TEMPERATURE,
            metersize=sizes.METERSIZE,
            amountmin=-20,
            amountmax=80,
        )
        WidgetRegistry.register_widget(self._temp_meter, "temp_meter", tab_name)

        # # --- TEST BUTTONS FOR TEMP METER STEP ---
        # self._temp_step_down_btn = ttk.Button(
        #     self._meter_frame,
        #     text="Temp -",
        #     command=lambda: self._temp_meter.step(-1)
        # )
        # self._temp_step_up_btn = ttk.Button(
        #     self._meter_frame,
        #     text="Temp +",
        #     command=lambda: self._temp_meter.step(1)
        # )

        self._urms_label: ttk.Label = ttk.Label(
            self._sonicmeasure_values_frame,
            anchor=ttk.CENTER,
            style=ttk.PRIMARY,
            background=color.STATUS_LIGHT_GREY,
            font=(fonts.QTYPE_OT, fonts.TEXT_SIZE),
        )
        WidgetRegistry.register_widget(self._urms_label, "urms_label", tab_name)

        self._irms_label: ttk.Label = ttk.Label(
            self._sonicmeasure_values_frame,
            anchor=ttk.CENTER,
            style=ttk.DANGER,
            background=color.STATUS_LIGHT_GREY,
            font=(fonts.QTYPE_OT, fonts.TEXT_SIZE),
        )
        WidgetRegistry.register_widget(self._irms_label, "irms_label", tab_name)

        self._phase_label: ttk.Label = ttk.Label(
            self._sonicmeasure_values_frame,
            anchor=ttk.CENTER,
            style=ttk.INFO,
            foreground=color.DARK_GREEN,
            background=color.STATUS_LIGHT_GREY,
            font=(fonts.QTYPE_OT, fonts.TEXT_SIZE),
        )
        WidgetRegistry.register_widget(self._phase_label, "phase_label", tab_name)

        self._signal_label: ttk.Label = ttk.Label(
            self._signal_frame,
            anchor=ttk.CENTER,
            justify=ttk.CENTER,
            compound=ttk.LEFT,
            font=(fonts.QTYPE_OT, fonts.SMALL_HEADING_SIZE),
            foreground=color.STATUS_LIGHT_GREY,
            background=color.STATUS_MEDIUM_GREY,
            style=style.INVERSE_SECONDARY,
        )
        WidgetRegistry.register_widget(self._signal_label, "signal_label", tab_name)


    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.X, padx=3, pady=3)
        self._main_frame.pack(expand=True, fill=ttk.BOTH)
        self._main_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._main_frame.rowconfigure(2, weight=sizes.EXPAND)
        self._meter_frame.grid(row=0, column=0)
        self._sonicmeasure_values_frame.grid(row=1, column=0, sticky=ttk.EW)
        self._signal_frame.grid(row=2, column=0, sticky=ttk.EW)

        self._meter_frame.rowconfigure(0, weight=sizes.EXPAND)
        self._freq_meter.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._gain_meter.grid(
            row=0,
            column=1,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._temp_meter.grid(
            row=0,
            column=2,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )

        # Place test buttons below the temp meter
        # self._temp_step_down_btn.grid(
        #     row=1, column=2, padx=sizes.SMALL_PADDING, pady=(0, sizes.SMALL_PADDING), sticky=ttk.EW
        # )
        # self._temp_step_up_btn.grid(
        #     row=2, column=2, padx=sizes.SMALL_PADDING, pady=(0, sizes.SMALL_PADDING), sticky=ttk.EW
        # )

        self._sonicmeasure_values_frame.rowconfigure(0, weight=sizes.EXPAND)
        self._sonicmeasure_values_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._sonicmeasure_values_frame.columnconfigure(1, weight=sizes.EXPAND)
        self._sonicmeasure_values_frame.columnconfigure(2, weight=sizes.EXPAND)
        self._urms_label.grid(
            row=0,
            column=0,
            padx=sizes.SMALL_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._irms_label.grid(
            row=0,
            column=1,
            padx=sizes.SMALL_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._phase_label.grid(
            row=0,
            column=2,
            padx=sizes.SMALL_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )

        self._signal_frame.rowconfigure(0, weight=sizes.EXPAND)
        self._signal_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._signal_frame.columnconfigure(1, weight=sizes.EXPAND)
        self._signal_label.grid(
            row=1,
            column=1,
            padx=sizes.SIDE_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.W,
        )

    def set_signal_image(self, image_path: Path | str, sizing: Tuple[int, int]) -> None:
        self._signal_label.configure(
            image=ImageLoader.load_image_resource(str(image_path), sizing)
        )

    def update_stats(self, freq: float, gain: float, temp: float, urms: str, irms: str, phase: str, signal: str):
        self._freq_meter.configure(amountused=round(freq, 1))
        self._gain_meter.configure(amountused=gain)
        if temp != temp:  # Check for NaN
            self._temp_meter.configure(amountused=temp)  # Use a string placeholder
        else:
            self._temp_meter.configure(amountused=round(temp, 1))
        self._urms_label.configure(text=urms)
        self._irms_label.configure(text=irms)
        self._phase_label.configure(text=phase)
        self._signal_label.configure(text=signal)
        self.update()

