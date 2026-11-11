import tkinter as tk

from soniccontrol.app_config import APP_CONFIG
from sonic_protocol.schema import SIUnit, SIPrefix
from sonic_protocol.si_unit import AbsoluteFrequencySIVar, MeterSIVar, SIVarMeta
from soniccontrol_gui.utils.debounce_job import DebounceJob
from soniccontrol_gui.widgets.form_widget import SITypeFieldView


def make_field(default_value=None, *, use_spinbox=False):
    root = tk.Tk()
    root.withdraw()
    field = SITypeFieldView(
        root,
        "value",
        default_value=default_value,
        field_view_kwargs={
            "si_var_class": type(default_value) if default_value is not None else MeterSIVar,
            "use_spinbox": use_spinbox,
        },
    )
    return field, root


def test_float_sivar_scale_uses_prefix_decimals():
    field, root = make_field(MeterSIVar(1.23456, SIPrefix.NONE))
    try:
        assert field._get_display_decimals(SIPrefix.MILLI) == 0
        assert field._get_display_decimals(SIPrefix.CENTI) == 2
        assert field._get_display_decimals(SIPrefix.KILO) == 3
    finally:
        field.destroy()
        root.destroy()


def test_float_sivar_display_uses_active_decimal_policy():
    field, root = make_field(MeterSIVar(1.23456, SIPrefix.NONE))
    try:
        assert field._format_display_value(1.23456, SIPrefix.KILO) == "1.235"

        field._display_decimals = 2
        assert field._format_display_value(1.23456, SIPrefix.KILO) == "1.23"

        field._display_decimals = 3
        assert field._get_display_decimals(SIPrefix.KILO) == 3
    finally:
        field.destroy()
        root.destroy()


def test_float_sivar_trailing_zeroes_are_stripped_without_leaving_a_decimal_point():
    field, root = make_field(MeterSIVar(1.0, SIPrefix.NONE))
    try:
        field._display_decimals = 3
        assert field._format_display_value(1.0, SIPrefix.NONE) == "1"
        assert field._format_display_value(1.23, SIPrefix.NONE) == "1.23"
        assert field._format_display_value(1.2300, SIPrefix.NONE) == "1.23"
    finally:
        field.destroy()
        root.destroy()


def test_float_sivar_prefix_change_resets_to_prefix_cap_policy():
    field, root = make_field(AbsoluteFrequencySIVar(100100.0, SIPrefix.NONE))
    try:
        assert field.si_prefix_combobox is not None
        field._display_decimals = 2
        field.si_prefix_combobox.set("kHz")
        field.si_prefix_combobox.event_generate("<<ComboboxSelected>>")
        root.update()

        assert field._display_decimals == 1
        assert field._str_value.get() == "100.1"
    finally:
        field.destroy()
        root.destroy()


def test_scale_uses_existing_display_decimals_instead_of_resetting_to_zero():
    field, root = make_field(MeterSIVar(100.0, SIPrefix.NONE))
    try:
        field._display_decimals = 2
        field._update_str_value_without_trace("100", preserve_display_decimals=True)
        assert field._display_decimals == 2
        assert field._str_value.get() == "100"
    finally:
        field.destroy()
        root.destroy()


def test_float_sivar_manual_entry_truncates_decimals_instead_of_rounding():
    field, root = make_field(MeterSIVar(1.0, SIPrefix.NONE))
    try:
        field._display_decimals = 3
        field._str_value.set("1.2348")
        field._parse_str_value()
        assert field.value.value == 1.234
        assert field._str_value.get() == "1.234"
    finally:
        field.destroy()
        root.destroy()


def test_real_spinbox_buttonup_keeps_two_decimal_display_count():
    field, root = make_field(AbsoluteFrequencySIVar(123450.0, SIPrefix.NONE), use_spinbox=True)
    try:
        assert field.si_prefix_combobox is not None
        assert field.spinbox is not None
        field.si_prefix_combobox.set("kHz")
        field.si_prefix_combobox.event_generate("<<ComboboxSelected>>")
        root.update()
        assert field._str_value.get() == "123.45"

        # Use the spinbox's native increment event rather than a nonexistent Python
        # method. The native widget broadcasts this through the <<Increment>> Tk event.
        field.spinbox.event_generate("<<Increment>>")
        root.update()

        assert field._display_decimals == 2
        assert field._str_value.get() == "223.45"
    finally:
        field.destroy()
        root.destroy()


def test_manual_entry_updates_spinbox_decimal_tracking():
    field, root = make_field(MeterSIVar(1.23456, SIPrefix.NONE))

    class FakeSpinbox:
        def __init__(self):
            self._config = {}

        def configure(self, **kwargs):
            self._config.update(kwargs)

        def cget(self, key):
            return self._config.get(key)

    try:
        field._use_spinbox = True
        field.spinbox = FakeSpinbox()
        field._str_value.set("1.")
        field._parse_str_value()
        assert field._display_decimals == 0
        assert field.spinbox.cget("format") == "%.0f"
        assert field._format_display_value(0.0, SIPrefix.NONE) == "0"

        field._str_value.set("1.23")
        field._parse_str_value()
        assert field._display_decimals == 2
        assert field.spinbox.cget("format") == "%.2f"
    finally:
        field.destroy()
        root.destroy()


def test_parse_str_value_reformats_valid_spinbox_input():
    field, root = make_field(AbsoluteFrequencySIVar(123450.0, SIPrefix.NONE), use_spinbox=True)
    try:
        field.si_prefix_combobox.set("kHz")
        field.si_prefix_combobox.event_generate("<<ComboboxSelected>>")
        root.update()

        seen = []
        original_update = field._update_str_value_without_trace

        def recording(new_value, *, preserve_display_decimals=False):
            seen.append((new_value, preserve_display_decimals))
            return original_update(new_value, preserve_display_decimals=preserve_display_decimals)

        field._update_str_value_without_trace = recording
        field._str_value.set("223.45")
        field._parse_str_value()

        assert seen
        assert seen[-1][0] == "223.45"
        assert field._str_value.get() == "223.45"
    finally:
        field.destroy()
        root.destroy()



def test_spinbox_repeat_delay_uses_app_setting():
    field = object.__new__(SITypeFieldView)
    previous = APP_CONFIG.spinbox_repeat_mode
    try:
        APP_CONFIG.spinbox_repeat_mode = "fast"
        assert field._get_spinbox_repeat_delay_ms() == 60

        APP_CONFIG.spinbox_repeat_mode = "slow"
        assert field._get_spinbox_repeat_delay_ms() == 500
    finally:
        APP_CONFIG.spinbox_repeat_mode = previous


def test_debounce_job_preserves_keyword_arguments():
    captured = {}

    class DummyWidget:
        def after(self, delay_ms, callback):
            callback()
            return "job"

        def after_cancel(self, job):
            pass

    def callback(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    job = DebounceJob(callback, DummyWidget(), debounce_time_ms=1)
    job(flush=True)

    assert captured["args"] == ()
    assert captured["kwargs"] == {"flush": True}


def test_si_field_flush_callback_keeps_enter_context():
    recorded = {}
    field = object.__new__(SITypeFieldView)
    field._value = "value"
    field._is_valid = True
    field._callback = lambda *args, **kwargs: recorded.setdefault("seen", (args, kwargs))

    field._flush_value_change()

    assert recorded["seen"][0] == ("value",)
    assert recorded["seen"][1] == {"flush": True}


def test_si_field_enter_flush_clears_selection_and_focus():
    recorded = {}

    class FakeWidget:
        def selection_clear(self):
            recorded["selection_clear"] = True

        def icursor(self, pos):
            recorded["icursor"] = pos

    field = object.__new__(SITypeFieldView)
    field._is_valid = True
    field._parse_str_value = lambda: None
    field._flush_value_change = lambda **kwargs: recorded.setdefault("flush", kwargs)
    field._get_input_widget = lambda: widget
    field.focus_set = lambda: recorded.setdefault("focus_set", True)
    widget = FakeWidget()

    field._handle_enter_keypress()

    assert recorded["selection_clear"] is True
    assert recorded["focus_set"] is True
