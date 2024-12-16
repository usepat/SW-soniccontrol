from typing import Any, Callable, Dict, List, Optional, Type, Union

import attrs
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import View

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from soniccontrol.procedures.holder import HoldTuple, HolderArgs

class IntFieldView(View):
    def __init__(self, master: ttk.Frame | View, field_name: str, *args, default_value: int = 0, **kwargs):
        self._field_name = field_name
        self._default_value = default_value
        self._value: ttk.StringVar = ttk.StringVar(value=str(default_value))
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)
        self.entry = ttk.Entry(self, textvariable=self._value)

        WidgetRegistry.register_widget(self.entry, "entry", self._widget_name)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        self.label.grid(row=0, column=0, padx=5, pady=5)
        self.entry.grid(row=0, column=1, padx=5, pady=5)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def value(self) -> int:
        try:
            return int(self._value.get())
        except Exception as _:
            # TODO: display error
            return self._default_value 
    
    @value.setter
    def value(self, v: int) -> None:
        self._value.set(str(v))
 
    def bind_value_change(self, command: Callable[[int], None]):
        self._value.trace_add("write", lambda *args: command(self.value))


class FloatFieldView(View):
    def __init__(self, master: ttk.Frame | View, field_name: str, *args, default_value: float = 0., **kwargs):
        self._field_name = field_name
        self._default_value = default_value
        self._value: ttk.StringVar = ttk.StringVar(value=str(default_value))
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)
        self.entry = ttk.Entry(self, textvariable=self._value)

        WidgetRegistry.register_widget(self.entry, "entry", self._widget_name)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        self.label.grid(row=0, column=0, padx=5, pady=5)
        self.entry.grid(row=0, column=1, padx=5, pady=5)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def value(self) -> float:
        try:
            return float(self._value.get())
        except Exception as _:
            # TODO: display error
            return self._default_value 
    
    @value.setter
    def value(self, v: float) -> None:
        self._value.set(str(v))

    def bind_value_change(self, command: Callable[[float], None]):
        self._value.trace_add("write", lambda *args: command(self.value))

class TimeFieldView(View):
    def __init__(self, master: ttk.Frame | View, field_name: str, *args, default_time: float | int = 0., unit = "ms", **kwargs):
        self._field_name = field_name
        self._default_time = default_time
        self._time_value: ttk.StringVar = ttk.StringVar(value=str(default_time))
        self._unit_value: ttk.StringVar = ttk.StringVar(value=unit)
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._label = ttk.Label(self, text=self._field_name)
        self._entry_time = ttk.Entry(self, textvariable=self._time_value)
        self._unit_button = ttk.Button(self, text=self._unit_value.get(), command=self._toggle_unit)

        WidgetRegistry.register_widget(self._entry_time, "time_entry", self._widget_name)
        WidgetRegistry.register_widget(self._unit_button, "unit_button", self._widget_name)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        self._label.grid(row=0, column=0, padx=5, pady=5)
        self._entry_time.grid(row=0, column=1, padx=5, pady=5)
        self._unit_button.grid(row=0, column=2, padx=5, pady=5)

    def _toggle_unit(self) -> None:
        unit = self._unit_value.get()
        unit = "ms" if unit == "s" else "s"
        self._unit_value.set(unit)
        self._unit_button.configure(text=unit)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def value(self) -> HoldTuple:
        try:
            time_value = int(self._time_value.get())
        except Exception as _:
            # TODO: display error
            time_value = int(self._default_time) 
        return (time_value, self._unit_value.get())
    
    @value.setter
    def value(self, v: HoldTuple) -> None:
        self._time_value.set(str(v[0]))
        self._unit_value.set(v[1])
        self._unit_button.configure(text=v[1])

    def bind_value_change(self, command: Callable[[HoldTuple], None]):
        self._time_value.trace_add("write", lambda *args: command(self.value))
        self._unit_value.trace_add("write", lambda *args: command(self.value))

"""
This class holds only information about the procedure args.
It cannot start or stop procedures. This is done by the ProcedureController class
"""
class ProcedureWidget(UIComponent):
    def __init__(self, parent: UIComponent, parent_view: View, procedure_name: str, proc_args_class: Type, proc_args_dict: dict):
        self._proc_args_class = proc_args_class
        self._fields: List[Union[TimeFieldView, FloatFieldView, IntFieldView]] = []
        self._procedure_name = procedure_name
        self._view = ProcedureWidgetView(parent_view)
        self._view.set_procedure_name(self._procedure_name)
        self._proc_args_dict = proc_args_dict
        super().__init__(self, self._view)
        self._add_fields_to_widget()

    def _add_fields_to_widget(self):
        for field_name, field in attrs.fields_dict(self._proc_args_class).items():
            if field.type is int:
                field_view = IntFieldView(self._view.field_slot, field_name, parent_widget_name=self._procedure_name)
                self._proc_args_dict[field_name] = field_view.value
                self._fields.append(field_view)
            elif field.type is float:
                field_view = FloatFieldView(self._view.field_slot, field_name, parent_widget_name=self._procedure_name)
                self._fields.append(field_view)
            elif field.type is HolderArgs:
                field_view = TimeFieldView(self._view.field_slot, field_name, parent_widget_name=self._procedure_name)
                self._proc_args_dict[field_name] = field_view.value
                self._fields.append(field_view)
            else:
                raise TypeError(f"The field with name {field_name} has the type {field.type}, which is not supported")
        
            # I use here a decorator so that the field_name gets captured by the function and not gets overwritten in 
            # subsequent runs
            def set_dict_value(key):
                def _set_dict_value(val):
                    self._proc_args_dict[key] = val
                return _set_dict_value
            field_view.bind_value_change(set_dict_value(field_name))
            self._proc_args_dict[field_name] = field_view.value

        self._view._initialize_publish()

    # TODO: refactor this method. Validation should occur in the fields and each one should display
    # its own error message
    # Also constructing the final class should be done by ProcControlling directly
    def get_args(self) -> Optional[Any]:
        dict_args: Dict[str, Any] = {}
        for field in self._fields:
            dict_args[field.field_name] = field.value
        try:
            args = self._proc_args_class(**dict_args)
        except ValueError as e:
            self._view.set_error_message(str(e))
            return None
        else:
            self._view.set_error_message(None)
            return args
        
        
        
class ProcedureWidgetView(View):
    def __init__(self, master: ttk.Frame | View, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._title_frame = ttk.Frame(self)
        self._procedure_title = ttk.StringVar()
        self._procedure_label = ttk.Label(self._title_frame, textvariable=self._procedure_title, font=("Arial", 16))
        self._scrolled_frame = ScrolledFrame(self)
        self._error_label = ttk.Label(self)

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH)
        self._title_frame.pack(fill=ttk.X, pady=10)
        self._procedure_label.pack()
        self._scrolled_frame.pack(fill=ttk.BOTH, pady=10, expand=True)

        for i, child in enumerate(self._scrolled_frame.children.values()):
            child.grid(row=i, column=0, padx=5, pady=5, sticky=ttk.EW)

    @property
    def field_slot(self) -> ttk.Frame:
        return self._scrolled_frame

    def set_procedure_name(self, procedure_name: str) -> None:
        self._procedure_title.set(procedure_name)

    def set_error_message(self, error_msg: Optional[str] = None) -> None:
        if error_msg:
            self._error_label.pack(fill=ttk.X, pady=10)
            self._error_label.configure(text=error_msg)
        else:
            self._error_label.pack_forget()

    def show(self) -> None:
        self.pack(expand=True, fill=ttk.BOTH)

    def hide(self) -> None:
        self.pack_forget()

