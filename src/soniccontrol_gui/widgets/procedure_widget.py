import abc
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union, get_type_hints

import attrs
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import View

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from soniccontrol.procedures.holder import HoldTuple, HolderArgs

class EntryStyle(Enum):
    PRIMARY = "primary.TEntry"
    SUCCESS = "success.TEntry"
    DANGER = "danger.TEntry"


T = TypeVar("T")
class FieldViewBase(abc.ABC, Generic[T], View):
    def __init__(self, master: ttk.Frame | View, *args, **kwargs):
        View.__init__(self, master, *args, **kwargs)

    @property
    @abc.abstractmethod
    def field_name(self) -> str: ...

    @property
    @abc.abstractmethod
    def value(self) -> T: ...

    @value.setter
    @abc.abstractmethod
    def value(self, v: T) -> None: ...

    @abc.abstractmethod
    def bind_value_change(self, command: Callable[[T], None]) -> None: ...


PrimitiveT = TypeVar("PrimitiveT", str, float, int, bool)
class BasicTypeFieldView(FieldViewBase[PrimitiveT]):
    def __init__(self, master: ttk.Frame | View, factory: Callable[..., PrimitiveT], field_name: str, *args, default_value: PrimitiveT | None = None, **kwargs):
        if default_value is None:
            _default_value: PrimitiveT = factory() # create default value. Only works for primitives
        else:
            _default_value = default_value

        self._factory = factory
        self._field_name = field_name
        self._default_value: PrimitiveT = _default_value 
        self._str_value: ttk.StringVar = ttk.StringVar(value=str(_default_value))
        self._value: PrimitiveT = _default_value
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name

        super().__init__(master, *args, **kwargs)

        self._callback: Callable[[PrimitiveT], None] = lambda _: None
        self._str_value.trace_add("write", self._parse_str_value)


    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)
        self.entry = ttk.Entry(self, textvariable=self._str_value)

        WidgetRegistry.register_widget(self.entry, "entry", self._widget_name)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        self.label.grid(row=0, column=0, padx=5, pady=5)
        self.entry.grid(row=0, column=1, padx=5, pady=5)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def value(self) -> PrimitiveT:
        return self._value
    
    @value.setter
    def value(self, v: PrimitiveT) -> None:
        self._value = v
        self._str_value.set(str(v))
 
    def _parse_str_value(self, *_args):
        try:
            self.value = self._factory(self._str_value.get()) 
            self.entry.configure(style=EntryStyle.PRIMARY.value)
        except Exception as _:
            self.value = self._default_value 
            self.entry.configure(style=EntryStyle.DANGER.value)
        self._callback(self.value)


    def bind_value_change(self, command: Callable[[PrimitiveT], None]):
        self._callback = command


class TimeFieldView(FieldViewBase[HoldTuple]):
    def __init__(self, master: ttk.Frame | View, field_name: str, *args, default_time: int = 0, unit = "ms", **kwargs):
        self._field_name = field_name
        self._default_time = default_time
        self._time_value = default_time
        self._time_value_str: ttk.StringVar = ttk.StringVar(value=str(default_time))
        self._unit_value_str: ttk.StringVar = ttk.StringVar(value=unit)
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)

        self._callback: Callable[[HoldTuple], None] = lambda _: None
        self._time_value_str.trace_add("write", self._parse_str_value)
        self._unit_value_str.trace_add("write", self._parse_str_value)


    def _initialize_children(self) -> None:
        self._label = ttk.Label(self, text=self._field_name)
        self._entry_time = ttk.Entry(self, textvariable=self._time_value_str)
        self._unit_button = ttk.Button(self, text=self._unit_value_str.get(), command=self._toggle_unit)

        WidgetRegistry.register_widget(self._entry_time, "time_entry", self._widget_name)
        WidgetRegistry.register_widget(self._unit_button, "unit_button", self._widget_name)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        self._label.grid(row=0, column=0, padx=5, pady=5)
        self._entry_time.grid(row=0, column=1, padx=5, pady=5)
        self._unit_button.grid(row=0, column=2, padx=5, pady=5)

    def _toggle_unit(self) -> None:
        unit = self._unit_value_str.get()
        unit = "ms" if unit == "s" else "s"
        self._unit_value_str.set(unit)
        self._unit_button.configure(text=unit)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def value(self) -> HoldTuple:
        return self._time_value, self._unit_value_str.get() # type: ignore
    
    @value.setter
    def value(self, v: HoldTuple) -> None:
        self._time_value = v[0]
        self._time_value_str.set(str(v[0]))
        self._unit_value_str.set(v[1])
        self._unit_button.configure(text=v[1])
 
    def _parse_str_value(self, *_args):
        try:
            self._time_value = float(self._time_value_str.get())
            self._entry_time.configure(style=EntryStyle.PRIMARY.value)
        except Exception as _:
            self._time_value = self._default_time 
            self._entry_time.configure(style=EntryStyle.DANGER.value)
        self._callback((self._time_value, self._unit_value_str.get())) # type: ignore

    def bind_value_change(self, command: Callable[[HoldTuple], None]):
        self._callback = command

"""
This class holds only information about the procedure args.
It cannot start or stop procedures. This is done by the ProcedureController class
"""
class ProcedureWidget(UIComponent):
    def __init__(self, parent: UIComponent, parent_view: View, procedure_name: str, proc_args_class: Type, proc_args_dict: dict):
        self._proc_args_class = proc_args_class
        self._fields: List[FieldViewBase] = []
        self._procedure_name = procedure_name
        self._view = ProcedureWidgetView(parent_view)
        self._view.set_procedure_name(self._procedure_name)
        self._proc_args_dict = proc_args_dict
        super().__init__(self, self._view)
        self._add_fields_to_widget()

    def _add_fields_to_widget(self):
        for field_name, field in attrs.fields_dict(self._proc_args_class).items():
            if field.type is int:
                field_view = BasicTypeFieldView[int](self._view.field_slot, int, field_name, parent_widget_name=self._procedure_name)
            elif field.type is float:
                field_view = BasicTypeFieldView[float](self._view.field_slot, float, field_name, parent_widget_name=self._procedure_name)
            elif field.type is str:
                field_view = BasicTypeFieldView[str](self._view.field_slot, str, field_name, parent_widget_name=self._procedure_name)
            elif field.type is HolderArgs:
                field_view = TimeFieldView(self._view.field_slot, field_name, parent_widget_name=self._procedure_name)
            else:
                raise TypeError(f"The field with name {field_name} has the type {field.type}, which is not supported")
            self._fields.append(field_view)

            self._proc_args_dict[field_name] = field_view.value

            # I use here a decorator so that the field_name gets captured by the function and not gets overwritten in 
            # subsequent runs
            def set_dict_value(key):
                def _set_dict_value(val):
                    self._proc_args_dict[key] = val
                return _set_dict_value
            
            field_view.bind_value_change(set_dict_value(field_name))

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

