import abc
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Type, TypeVar

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
class FormWidget(UIComponent):
    def __init__(self, parent: UIComponent, parent_view: View, title: str, attrs_class: Type, model_dict: dict = {}):
        """
            args:
                model_dict: Is a dictionary that is one way bound target to source. So if the form gets updated, it updates the dictionary too, but not vice versa.
        """
        self._attrs_class = attrs_class
        self._fields: List[FieldViewBase] = []
        self._procedure_name = title
        self._view = FormWidgetView(parent_view)
        self._view.set_title(self._procedure_name)
        self._model_dict = model_dict
        super().__init__(self, self._view)
        self._add_fields_to_widget()

    def _add_fields_to_widget(self):
        for field_name, field in attrs.fields_dict(self._attrs_class).items():
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

            self._model_dict[field_name] = field_view.value

            # I use here a decorator so that the field_name gets captured by the function and not gets overwritten in 
            # subsequent runs
            def set_dict_value(key):
                def _set_dict_value(val):
                    self._model_dict[key] = val
                return _set_dict_value
            
            field_view.bind_value_change(set_dict_value(field_name))

        self._view._initialize_publish()

    @property
    def form_data(self) -> Dict[str, Any]:
        return self._model_dict.copy() 
        
        
class FormWidgetView(View):
    def __init__(self, master: ttk.Frame | View, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._title_frame = ttk.Frame(self)
        self._title = ttk.StringVar()
        self._title_label = ttk.Label(self._title_frame, textvariable=self._title, font=("Arial", 16))
        self._scrolled_frame = ScrolledFrame(self)

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH)
        self._title_frame.pack(fill=ttk.X, pady=10)
        self._title_label.pack()
        self._scrolled_frame.pack(fill=ttk.BOTH, pady=10, expand=True)

        for i, child in enumerate(self._scrolled_frame.children.values()):
            child.grid(row=i, column=0, padx=5, pady=5, sticky=ttk.EW)

    @property
    def field_slot(self) -> ttk.Frame:
        return self._scrolled_frame

    def set_title(self, title: str) -> None:
        self._title.set(title)

    def show(self) -> None:
        self.pack(expand=True, fill=ttk.BOTH)

    def hide(self) -> None:
        self.pack_forget()

