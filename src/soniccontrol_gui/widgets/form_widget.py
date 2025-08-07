import abc
from enum import Enum
import inspect
from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, Tuple, Type, TypeVar, Union, get_args, get_origin

import copy
import attrs
import cattrs
from pathlib import Path
from soniccontrol.procedures.holder import convert_to_holder_args
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TkinterView, View
from soniccontrol_gui.constants import ui_labels, sizes
from soniccontrol_gui.widgets.file_browse_button import FileBrowseButtonView

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from soniccontrol.procedures.holder import HoldTuple, HolderArgs



def _create_converter():
    # We do not want to convert enums and holder args and pathlib.Path

    def enum_structure_hook(value: Any, t: type) -> Enum:
        if not isinstance(value, Enum):
            raise ValueError("Not a HolderArgs")
        return value

    def enum_unstructure_hook(value: Enum) -> Enum:
        return value
    
    def is_enum(cls: Any) -> bool:
        # here is instance is used to check if cls is a type (Needed because of generic types that are instantiated as objects)
        return isinstance(cls, type) and issubclass(cls, Enum)

    def holder_args_structure_hook(value: Any, t: type) -> HolderArgs:
        return convert_to_holder_args(value)

    def holder_args_unstructure_hook(value: HolderArgs) -> HolderArgs:
        return value
    
    def path_structure_hook(value: Any, t: type) -> Path:
        return value

    def path_unstructure_hook(value: Path) -> Path:
        return value
    
    converter = cattrs.Converter()
    converter.register_structure_hook_func(is_enum, enum_structure_hook)
    converter.register_unstructure_hook_func(is_enum, enum_unstructure_hook)
    converter.register_structure_hook(HolderArgs, holder_args_structure_hook)
    converter.register_unstructure_hook(HolderArgs, holder_args_unstructure_hook)
    converter.register_structure_hook(Path, path_structure_hook)
    converter.register_unstructure_hook(Path, path_unstructure_hook)

    return converter


class EntryStyle(Enum):
    PRIMARY = "primary.TEntry"
    SUCCESS = "success.TEntry"
    DANGER = "danger.TEntry"


T = TypeVar("T")
class FieldViewBase(abc.ABC, Generic[T], View):
    def __init__(self, master: TkinterView, *args, **kwargs):
        View.__init__(self, master, *args, **kwargs)

    @property
    @abc.abstractmethod
    def field_name(self) -> str: ...


    @property
    @abc.abstractmethod
    def default(self) -> T: ...

    @property
    @abc.abstractmethod
    def value(self) -> T: ...

    @value.setter
    @abc.abstractmethod
    def value(self, v: T) -> None: ...

    @abc.abstractmethod
    def bind_value_change(self, command: Callable[[T], None]) -> None: ...


PrimitiveT = TypeVar("PrimitiveT", str, float, int)
class BasicTypeFieldView(FieldViewBase[PrimitiveT]):
    def __init__(self, master: TkinterView, factory: Callable[..., PrimitiveT], 
                field_name: str, *args, default_value: PrimitiveT | None = None, **kwargs):
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

        WidgetRegistry.register_widget(self._str_value, "entry_str", self._widget_name)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")

        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.W)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def default(self) -> PrimitiveT: 
        return self._default_value

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


class BooleanFieldView(FieldViewBase[bool]):
    def __init__(self, master: TkinterView, field_name: str, *args, default_value: bool = False, **kwargs):
        self._field_name = field_name
        self._default_value = default_value
        self._var = ttk.BooleanVar(value=self._default_value)
        self._callback: Callable[[bool], None] = lambda _: None

        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name

        super().__init__(master, *args, **kwargs)
        self._var.trace_add("write", self._on_change)

    def _initialize_children(self) -> None:
        self._checkbutton = ttk.Checkbutton(
            self,
            text=self._field_name,
            variable=self._var
        )
        WidgetRegistry.register_widget(self._checkbutton, "checkbutton", self._widget_name)

    def _initialize_publish(self) -> None:
        self._checkbutton.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def default(self) -> bool:
        return self._default_value

    @property
    def value(self) -> bool:
        return self._var.get()

    @value.setter
    def value(self, v: bool) -> None:
        self._var.set(v)

    def _on_change(self, *_):
        self._callback(self._var.get())

    def bind_value_change(self, command: Callable[[bool], None]) -> None:
        self._callback = command


class EnumFieldView(FieldViewBase[Enum]):
    def __init__(self, master: TkinterView, field_name: str, enum_class: type[Enum], *args, default_value: Enum | None = None, **kwargs):
        self._enum_class = enum_class
        self._field_name = field_name
        self._default_value = default_value or list(enum_class)[0]
        self._value = self._default_value
        self._selected_enum_member = ttk.StringVar(value=self._value.name)
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name

        super().__init__(master, *args, **kwargs)

        self._callback: Callable[[Enum], None] = lambda _: None
        self._selected_enum_member.trace_add("write", self._combo_box_selection_changed)


    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)

        self._config_entry = ttk.Combobox(
            self,
            textvariable=self._selected_enum_member,
            values=[e.name for e in self._enum_class],
            state="readonly"
        )

        WidgetRegistry.register_widget(self._selected_enum_member, "entry_enum", self._widget_name)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")

        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self._config_entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.W) 

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def default(self) -> Enum: 
        return self._default_value

    @property
    def value(self) -> Enum:
        return self._value 
    
    @value.setter
    def value(self, v: Enum) -> None:
        self._value = v
        self._selected_enum_member.set(v.name)

    def _combo_box_selection_changed(self, *_):
        selected_name = self._selected_enum_member.get()
        self._value = self._enum_class[selected_name]
        self._callback(self._value)

    def bind_value_change(self, command: Callable[[Enum], None]) -> None: 
        self._callback = command


class NullableTypeFieldView(FieldViewBase[Optional[PrimitiveT]]):
    def __init__(self, master: TkinterView, factory: Callable[..., Optional[PrimitiveT]], 
                field_name: str, *args, default_value: Optional[PrimitiveT] = None, **kwargs):

        self._factory = factory
        self._field_name = field_name
        self._default_value: Optional[PrimitiveT] = default_value 
        self._str_value: ttk.StringVar = ttk.StringVar(value=str("" if default_value is None else default_value))
        self._value: Optional[PrimitiveT] = default_value
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name

        super().__init__(master, *args, **kwargs)

        self._callback: Callable[[Optional[PrimitiveT]], None] = lambda _: None
        self._str_value.trace_add("write", self._parse_str_value)


    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)
        self.entry = ttk.Entry(self, textvariable=self._str_value)

        WidgetRegistry.register_widget(self._str_value, "entry_str", self._widget_name)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")

        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.W)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def default(self) -> Optional[PrimitiveT]: 
        return self._default_value

    @property
    def value(self) -> Optional[PrimitiveT]:
        return self._value
    
    @value.setter
    def value(self, v: Optional[PrimitiveT]) -> None:
        self._value = v
        self._str_value.set("" if v is None else str(v))
 
    def _parse_str_value(self, *_args):
        try:
            text = self._str_value.get()
            self.value = None if text == "" else self._factory(text) 
            self.entry.configure(style=EntryStyle.PRIMARY.value)
        except Exception as _:
            self.value = self._default_value 
            self.entry.configure(style=EntryStyle.DANGER.value)
        self._callback(self.value)

    def bind_value_change(self, command: Callable[[Optional[PrimitiveT]], None]):
        self._callback = command


class OptionalPathFieldView(FieldViewBase[Optional[Path]]):
    """
    Adapter for FileBrowseButton to use it inside a FormWidget
    """
    def __init__(self, master: TkinterView, field_name: str, *args, 
                default_value: Path | None = None, field_view_kwargs: Dict[str, Any] = {}, **kwargs):
        self._field_name = field_name
        self._default_value: Path | None = default_value 
        
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name

        super().__init__(master, *args, **kwargs)
        self._browse_button = FileBrowseButtonView(self, self._widget_name, text=self._field_name, **field_view_kwargs)
        self._browse_button.pack(fill=ttk.X, expand=True, pady=sizes.SMALL_PADDING, padx=sizes.SMALL_PADDING)

    def _initialize_children(self) -> None: ...

    def _initialize_publish(self) -> None: ...

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def default(self) -> Path | None: 
        return self._default_value

    @property
    def value(self) -> Path | None:
        return self._browse_button.path
    
    @value.setter
    def value(self, v: Path | None) -> None:
        self._browse_button.path = v
 
    def bind_value_change(self, command: Callable[[Path | None], None]):
        self._browse_button.set_path_changed_callback(command)


class TimeFieldView(FieldViewBase[HoldTuple]):
    def __init__(self, master: TkinterView, field_name: str, *args, default_value: HoldTuple | HolderArgs = (100, "ms"), **kwargs):
        self._field_name = field_name
        self._default_value = default_value if isinstance(default_value, tuple) else (default_value.duration, default_value.unit)
        self._time_value = self._default_value[0] 
        self._time_value_str: ttk.StringVar = ttk.StringVar(value=str(self._time_value))
        self._unit_value_str: ttk.StringVar = ttk.StringVar(value=self._default_value[1])
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)

        self._callback: Callable[[HoldTuple], None] = lambda _: None
        self._time_value_str.trace_add("write", self._parse_str_value)
        self._unit_value_str.trace_add("write", self._parse_str_value)


    def _initialize_children(self) -> None:
        self._label = ttk.Label(self, text=self._field_name)
        self._entry_frame = ttk.Frame(self)
        self._entry_time = ttk.Entry(self._entry_frame, textvariable=self._time_value_str)
        self._unit_button = ttk.Button(self._entry_frame, text=self._unit_value_str.get(), command=self._toggle_unit)

        WidgetRegistry.register_widget(self._time_value_str, "time_str", self._widget_name)
        WidgetRegistry.register_widget(self._unit_value_str, "unit_str", self._widget_name)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")

        self._label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self._entry_frame.grid(row=0, column=1, sticky=ttk.W)
        self._entry_time.pack(padx=5, pady=5, side=ttk.LEFT)
        self._unit_button.pack(padx=5, pady=5, side=ttk.RIGHT)

    def _toggle_unit(self) -> None:
        unit = self._unit_value_str.get()
        unit = "ms" if unit == "s" else "s"
        self._unit_value_str.set(unit)
        self._unit_button.configure(text=unit)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def default(self) -> HoldTuple: 
        return self._default_value

    @property
    def value(self) -> HoldTuple:
        return self._time_value, self._unit_value_str.get() # type: ignore
    
    @value.setter
    def value(self, v: HoldTuple | HolderArgs) -> None:
        if isinstance(v, HolderArgs):
            self._time_value = v.duration
            self._time_value_str.set(str(v.duration))
            self._unit_value_str.set(v.unit)
            self._unit_button.configure(text=v.unit)
        else:
            self._time_value = v[0]
            self._time_value_str.set(str(v[0]))
            self._unit_value_str.set(v[1])
            self._unit_button.configure(text=v[1])
 
    def _parse_str_value(self, *_args):
        try:
            self._time_value = float(self._time_value_str.get())
            self._entry_time.configure(style=EntryStyle.PRIMARY.value)
        except Exception as _:
            self._time_value = self._default_value[0] 
            self._entry_time.configure(style=EntryStyle.DANGER.value)
        self._callback((self._time_value, self._unit_value_str.get())) # type: ignore

    def bind_value_change(self, command: Callable[[HoldTuple], None]):
        self._callback = command


class DictFieldView(FieldViewBase):
    def __init__(self, master: TkinterView, field_name: str, *args, default_value: Dict[str, str] | None = None, **kwargs):
        self._entries: Dict[int, Tuple[ttk.StringVar, ttk.StringVar]] = {}
        self._field_name = field_name
        self._callback: Callable[[Dict[str, str]], None] = lambda _: None
        self._default_value = {} if default_value is None else default_value.copy()

        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)

        self.value = self._default_value


    def _initialize_children(self) -> None:
        self._label = ttk.Label(self, text=self._field_name)
        self._add_entry_button = ttk.Button(self, text=ui_labels.FORM_ADD_ENTRY, command=self._add_entry)
        self._entries_frame = ttk.Frame(self)

    def _initialize_publish(self) -> None:
        self._label.pack(fill=ttk.X, side=ttk.TOP)
        self._add_entry_button.pack(fill=ttk.X)
        self._entries_frame.pack(fill=ttk.BOTH, side=ttk.BOTTOM)

    def _generate_entry_id(self) -> int:
        self._id = 0 if not hasattr(self, "_id") else (self._id + 1)
        return self._id
    
    def _add_entry(self, key: str = "", value: str = "") -> None:
        entry_id = self._generate_entry_id()
    
        row_frame = ttk.Frame(self._entries_frame)
    
        entry_key_var = ttk.StringVar(row_frame, key)
        entry_value_var = ttk.StringVar(row_frame, value)
        self._entries[entry_id] = (entry_key_var, entry_value_var)

        entry_key = ttk.Entry(row_frame, textvariable=entry_key_var)
        entry_value = ttk.Entry(row_frame, textvariable=entry_value_var)
        delete_button = ttk.Button(row_frame, text="-")

        row_frame.pack(fill=ttk.X, side=ttk.BOTTOM, pady=3)
        row_frame.columnconfigure(0, weight=2)
        row_frame.columnconfigure(1, weight=2)
        row_frame.columnconfigure(2, weight=1)
        entry_key.grid(column=0, row=0)
        entry_value.grid(column=1, row=0)
        delete_button.grid(column=2, row=0)

        def delete_entry():
            del self._entries[entry_id]
            row_frame.destroy()

        delete_button.configure(command=delete_entry)
        entry_key_var.trace_add("write", self._on_value_change)
        entry_value_var.trace_add("write", self._on_value_change)


    @property
    def field_name(self) -> str: 
        return self._field_name

    @property
    def default(self) -> Dict[str, str]:
        return self._default_value

    @property
    def value(self) -> Dict[str, str]: 
        return { key_var.get(): value_var.get() for key_var, value_var in self._entries.values() }

    @value.setter
    def value(self, v: Dict[str, str]) -> None: 
        for child in self._entries_frame.children.values():
            child.destroy()
        self._entries.clear()

        for key, value in v.items():
            self._add_entry(key, value)

    def _on_value_change(self, *_args):
        self._callback(self.value)

    def bind_value_change(self, command: Callable[[Dict[str, str]], None]) -> None: 
        self._callback = command


"""
An FieldHook takes as input the type of the attr class, the attrs.Attribute for the field  and the slot, where to put the field.
Finally we also provide a dict with kwargs.

We register the hook for a field of a class.
"""
FieldHook = Callable[[type, "attrs.Attribute[Any]", TkinterView, Dict[str, Any]], FieldViewBase]

FieldHookRegistry =  Dict[Tuple[type, str], FieldHook]

class DynamicFieldViewFactory:
    def __init__(self, converter: cattrs.Converter, field_hooks: FieldHookRegistry):
        self._converter = converter
        self._field_hooks = field_hooks

    def from_type(self, field_name, field_type: type, slot: TkinterView, parent_widget_name: str, **kwargs) -> FieldViewBase:
        # is compares for addresses. If variables point to the same underlying object
        # is compares for types. (needed for windows) 
        # == compares for equality. (needed for linux) 
        # == needed for Optional and other compound types, because they are created and not singletons like builtin types
        if field_type is int:
            field_view = BasicTypeFieldView[int](slot, int, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type is float:
            field_view = BasicTypeFieldView[float](slot, float, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type is bool:
            field_view = BooleanFieldView(slot, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type is str:
            field_view = BasicTypeFieldView[str](slot, str, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type == Optional[int] or field_type is Optional[int]:
            field_view = NullableTypeFieldView[int](slot, int, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type == Optional[float] or field_type is Optional[float]:
            field_view = NullableTypeFieldView[float](slot, float, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type == Optional[str] or field_type is Optional[str]:
            field_view = NullableTypeFieldView[str](slot, str, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type is Dict or field_type is dict:
            field_view = DictFieldView(slot, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type is HolderArgs:
            field_view = TimeFieldView(slot, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type == Optional[Path] or field_type is Optional[Path]:
            field_view = OptionalPathFieldView(slot, field_name, parent_widget_name=parent_widget_name, **kwargs)
        elif inspect.isclass(field_type) and issubclass(field_type, Enum): 
            # for enums we have to check if they are subclasses of the Enum base class
            field_view = EnumFieldView(slot, field_name, field_type, parent_widget_name=parent_widget_name, **kwargs)
        elif get_origin(field_type) is tuple or field_type is tuple:
            field_view = TupleFieldView(slot, field_name, field_type, self, parent_widget_name=parent_widget_name, **kwargs)
        elif field_type and attrs.has(field_type):
            # for the case that the type is a nested attrs class.
            kwargs.pop("default_value", None) # We do not use default values here. We deduce them later through attrs.Attribute
            field_view = ObjectFieldView(slot, field_name, field_type, self, parent_widget_name=parent_widget_name, **kwargs)
        else:
            raise TypeError(f"The field with name {field_name} has the type {field_type}, which is not supported")

        return field_view


    def from_attribute(self, field_name: str, field: attrs.Attribute, obj_class: type, slot: TkinterView, parent_widget_name: str) -> FieldViewBase:
        assert field.type is not None, "There is no type annotation for this field present"

        # Apply Attribute Hook
        hook_key = (obj_class, field_name)
        if hook_key in self._field_hooks:
            hook = self._field_hooks[hook_key]
            field_view = hook(obj_class, field, slot, {"parent_widget_name": parent_widget_name})
            return field_view

        # Deduce kwargs for field from attrs.Attribute
        kwargs = {}
        if field.default is not None and field.default != attrs.NOTHING:
            kwargs["default_value"] = field.default.factory() if hasattr(field.default, "factory") else field.default

        field_view_kwargs_name = "field_view_kwargs"
        if field_view_kwargs_name in field.metadata:
            kwargs[field_view_kwargs_name] = field.metadata.get(field_view_kwargs_name) 

        return self.from_type(field_name, field.type, slot, parent_widget_name, **kwargs)
    
    def unstructure_value(self, val: Any, obj_class: type) -> Any:
        """
        This function is needed, because we need to unstructure the default values.
        """
        return self._converter.unstructure(val, obj_class)


class TupleFieldView(FieldViewBase[tuple]):
    def __init__(self,  master: TkinterView, field_name: str, tuple_type: type[tuple], field_view_factory: DynamicFieldViewFactory, *args, default_value: tuple | None = None, **kwargs):
        self._field_name = field_name
        self._tuple_type = tuple_type
        self._tuple_elements = get_args(tuple_type)

        self._field_view_factory = field_view_factory

        self._callback: Callable[[tuple], None] = lambda _: None
        if default_value is not None:
            default_value = tuple(t() for t in self._tuple_elements) 

        # We need to unstructure the tuple sub types. Else we get problems if we want to structure it back.
        self._value = self._field_view_factory.unstructure_value(default_value, self._tuple_type)

        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        self._fields: List[FieldViewBase] = []
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._frame = ttk.LabelFrame(self, text=self._field_name)
        self._add_fields_to_widget()

    def _initialize_publish(self) -> None:
        self._frame.grid(sticky=ttk.NSEW, padx=5, pady=5)

        for i, field_view in enumerate(self._fields):
            field_view.grid(row=i, column=0, padx=5, pady=5, sticky=ttk.W)

    def _add_fields_to_widget(self):
        for i, class_type in enumerate(self._tuple_elements):
            field_view = self._field_view_factory.from_type(f"Item {i+1}", class_type, self._frame, self._widget_name)
            self._fields.append(field_view)

            def bind_index(index):
                def _update(val):  
                    # tuples are immutable, so we have to do it like this
                    lst = list(self._value)
                    lst[index] = val
                    self._value = tuple(lst)

                    self._callback(self._value) 
                return _update
            # This is to ensure that values attributes are always up to date with the actual values of the field_views            
            field_view.bind_value_change(bind_index(i))            

    @property
    def field_name(self) -> str: 
        return self._field_name

    @property
    def default(self) -> tuple:
        return tuple(field_view.default for field_view in self._fields)
    
    @property
    def value(self) -> tuple:
        return self._value
    
    @value.setter
    def value(self, v: tuple) -> None:
        if len(v) != len(self._fields):
            raise ValueError("Tuple length mismatch.")
        
        for i, field in enumerate(self._fields):
            field.value = v[i]

    def bind_value_change(self, command: Callable[[tuple], None]) -> None:
        self._callback = command


class ObjectFieldView(FieldViewBase[dict]):
    def __init__(self, master: TkinterView, field_name: str, obj_class: type, field_view_factory: DynamicFieldViewFactory, *args, **kwargs):
        self._field_name = field_name
        self._obj_class = obj_class
        self._callback: Callable[[dict], None] = lambda _: None
        self._value: dict = {}

        # TODO: handle default values
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._field_view_factory = field_view_factory
        self._widget_name = parent_widget_name + "." + self._field_name
        self._fields: Dict[str, FieldViewBase] = {}
        super().__init__(master, *args, **kwargs)
            

    def _initialize_children(self) -> None:
        self._frame = ttk.LabelFrame(self, text=self._field_name)
        self._add_fields_to_widget()

    def _initialize_publish(self) -> None:
        self._frame.grid(sticky=ttk.NSEW, padx=5, pady=5)

        for i, field_view in enumerate(self._fields.values()):
            field_view.grid(row=i, column=0, padx=5, pady=5, sticky=ttk.W)

    def _add_fields_to_widget(self):
        fields = attrs.fields_dict(self._obj_class)
        for field_name, field in fields.items():
            field_view = self._field_view_factory.from_attribute(field_name, field, self._obj_class, self._frame, self._widget_name)

            self._fields[field_name] = field_view
            self._value[field_name] = field_view.value

            # I use here a decorator so that the field_name gets captured by the function and not gets overwritten in 
            # subsequent runs
            def set_dict_value(key):
                def _set_dict_value(val):
                    self._value[key] = val
                    self._callback({ key: val }) # we only return the attributes to update. More performant
                return _set_dict_value
            # This is to ensure that values attributes are always up to date with the actual values of the field_views            
            field_view.bind_value_change(set_dict_value(field_name))

    @property
    def field_name(self) -> str: 
        return self._field_name

    @property
    def default(self) -> dict:
        default_fields =  {}
        for field_name, field in self._fields.items():
            default_fields[field_name] = field.default
        return default_fields

    @property
    def value(self) -> dict: 
        return self._value

    @value.setter
    def value(self, v: dict) -> None: 
        for field_name, value in v.items():
            # This updates also automatically the self._value of this class
            self._fields[field_name].value = value
        self._callback(copy.deepcopy(self._value)) # We use deepcopy to avoid reference issues


    def bind_value_change(self, command: Callable[[dict], None]) -> None: 
        self._callback = command

class FormWidget(UIComponent):
    def __init__(self, parent: UIComponent, parent_view: View | ttk.Frame, 
                 title: str, form_class: type, model_dict: dict | None = None, field_hooks: FieldHookRegistry = {}):
        """
            args:
                model_dict: Is a dictionary that is one way bound target to source. So if the form gets updated, it updates the dictionary too, but not vice versa.
        """
        assert attrs.has(form_class), "the form class provided has to be an attrs class"
        self._attrs_class: type = form_class
        self._converter = _create_converter()
        self._field_view_factory = DynamicFieldViewFactory(self._converter, field_hooks)

        self._title = title
        self._view = FormWidgetView(parent_view)
        self._view.set_title(self._title)
        super().__init__(parent, self._view)

        self._attr_view = ObjectFieldView(self._view.field_slot, self._title, self._attrs_class, self._field_view_factory)
        self._view._initialize_publish()

        # bind the model dict to the view
        self._model_dict = {} if model_dict is None else model_dict
        self._model_dict.update(**self._attr_view.value)
        self._attr_view.bind_value_change(lambda value: self._model_dict.update(**value))

    @property
    def converter(self) -> cattrs.Converter:
        return self._converter

    @property
    def attrs_object(self) -> Any:
        """
        With this getter you can get the form data as a finished attr object.
        But for that you have to initialize FormWidget with an attrs class for form_attrs
        """
        try:
            return self._converter.structure(self._attr_view.value, self._attrs_class)
        except cattrs.ClassValidationError as e:
            raise e
    
    @attrs_object.setter
    def attrs_object(self, value: Any):
        """
        With this setter you can set the form data by an attr object.
        But for that you have to initialize FormWidget with an attrs class for form_attrs
        """
        assert isinstance(value, self._attrs_class), f"The value provided is of class {value.__class__} but expected {self._attrs_class}"
        data = self._converter.unstructure(value, self._attrs_class)
        self._attr_view.value = data
        pass

    @property
    def form_data(self) -> Dict[str, Any]:
        """
        Gets the form data. Consists of nested dicts
        """
        return self._model_dict

    @form_data.setter
    def form_data(self, value: Dict[str, Any]):
        self._attr_view.value = value

    def set_to_default(self) -> None:
        self._attr_view.value = self._attr_view.default

        
class FormWidgetView(View):
    def __init__(self, master: ttk.Frame | View, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._title_frame = ttk.Frame(self)
        self._title = ttk.StringVar()
        self._title_label = ttk.Label(self._title_frame, textvariable=self._title, font=("Arial", 16))
        self._scrolled_frame = ScrolledFrame(self)
        

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH, expand=True)
        self._title_frame.pack(fill=ttk.X, pady=10)
        self._title_label.pack()
        self._scrolled_frame.pack(fill=ttk.BOTH, pady=10, expand=True)

        # TODO: refactor this, because we have now only one child inside the scroll frame
        for i, child in enumerate(self._scrolled_frame.children.values()):
            child.pack(fill=ttk.X, padx=5, pady=5)
        

    @property
    def field_slot(self) -> ttk.Frame:
        return self._scrolled_frame

    def set_title(self, title: str) -> None:
        self._title.set(title)

    def show(self) -> None:
        self.pack(expand=True, fill=ttk.BOTH)

    def hide(self) -> None:
        self.pack_forget()

