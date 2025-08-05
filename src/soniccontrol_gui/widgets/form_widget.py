import abc
from enum import Enum
import inspect
from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, Tuple, Type, TypeVar, Union, get_args

import copy
import attrs
from soniccontrol.procedures.procedure import ProcedureArgs
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TkinterView, View
from soniccontrol_gui.constants import ui_labels

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from soniccontrol.procedures.holder import HoldTuple, HolderArgs

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


class FieldViewFactoryType(Protocol):
    def __call__(self, view: TkinterView, title: str, *args, **kwargs) -> FieldViewBase:
        ...

FormFieldAttributes = Dict[
    str, 
    Union["attrs.Attribute[Any]", FieldViewFactoryType, "FormFieldAttributes"]
]


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


class BoolFieldView(FieldViewBase[bool]):
    pass

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


def _create_field_view_for_type(field_name, field_type: type, slot: TkinterView, parent_widget_name: str, **kwargs) -> FieldViewBase:
    # is compares for addresses. If variables point to the same underlying object
    # is compares for types. (needed for windows) 
    # == compares for equality. (needed for linux) 
    # == needed for Optional and other compound types, because they are created and not singletons like builtin types
    if field_type is int:
        field_view = BasicTypeFieldView[int](slot, int, field_name, parent_widget_name=parent_widget_name, **kwargs)
    elif field_type is float:
        field_view = BasicTypeFieldView[float](slot, float, field_name, parent_widget_name=parent_widget_name, **kwargs)
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
    elif inspect.isclass(field_type) and issubclass(field_type, Enum): 
        # for enums we have to check if they are subclasses of the Enum base class
        field_view = EnumFieldView(slot, field_name, field_type, parent_widget_name=parent_widget_name, **kwargs)
    elif field_type is Tuple or field_type is tuple:
        field_view = TupleFieldView(slot, field_name, field_type, parent_widget_name=parent_widget_name, **kwargs)
    elif field_type and attrs.has(field_type):
        # for the case that the type is a nested attrs class.
        attributes: FormFieldAttributes = attrs.fields_dict(field_type) #type: ignore
        field_view = ObjectFieldView(slot, field_name, attributes, parent_widget_name=parent_widget_name, **kwargs)
    else:
        raise TypeError(f"The field with name {field_name} has the type {field_type}, which is not supported")

    return field_view


def _create_field_view_for_attr(field_name: str, field: attrs.Attribute, slot: TkinterView, parent_widget_name: str) -> FieldViewBase:
    assert field.type is not None, "There is no type annotation for this field present"

    kwargs = {}
    if field.default is not None and field.default != attrs.NOTHING:
        kwargs["default_value"] = field.default.factory() if hasattr(field.default, "factory") else field.default

    return _create_field_view_for_type(field_name, field.type, slot, parent_widget_name, **kwargs)

_REGISTERED_ATTRS_CLASSES: List[type] = [HolderArgs]


def _is_registered_class(class_type: type) -> bool:
    return any([ class_type is registered_class for registered_class in _REGISTERED_ATTRS_CLASSES ])

class TupleFieldView(FieldViewBase[tuple]):
    def __init__(self,  master: TkinterView, field_name: str, tuple_type: type[tuple], *args, default_value: tuple | None = None, **kwargs):
        self._field_name = field_name
        self._tuple_type = tuple_type
        self._tuple_elements = get_args(tuple_type)
        self._callback: Callable[[tuple], None] = lambda _: None
        if default_value is not None:
            self._value = default_value
        else:
            self._value = tuple(t() for t in self._tuple_elements) 

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
            field_view = _create_field_view_for_type(f"Item {i+1}", class_type, self._frame, self._widget_name)
            self._fields.append(field_view)

            def bind_index(index):
                def _update(val):
                    class_type = self._tuple_elements[index]
                    if isinstance(val, dict) and attrs.has(class_type):
                        # convert value to attribute type, if it is a attrs class    
                        val = class_type(**val)
                    
                    # tuples are immutable, so we have to do it like this
                    lst = list(self._value)
                    lst[i] = val
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
            val_class = v[i].__class__
            if attrs.has(val_class) and not _is_registered_class(val_class):
                # unnest to dict, if it is an attrs class
                field.value = attrs.asdict(v[i]) 
            else:
                field.value = v[i]

    def bind_value_change(self, command: Callable[[tuple], None]) -> None:
        self._callback = command


class ObjectFieldView(FieldViewBase[dict]):
    # We need to register HolderArgs, because all attrs classes get unnested and mapped onto ObjectFieldViews per default

    def __init__(self, master: TkinterView, field_name: str, obj_attrs: FormFieldAttributes, *args, **kwargs):
        self._field_name = field_name
        self._obj_attrs = obj_attrs
        self._callback: Callable[[dict], None] = lambda _: None
        self._value: dict = {}

        parent_widget_name = kwargs.pop("parent_widget_name", "")
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
        for field_name, field in self._obj_attrs.items():
            if isinstance(field, dict):
                # field is another FormFieldAttributes object
                field_view = ObjectFieldView(self._frame, field_name, field)
            elif isinstance(field, attrs.Attribute):
                field_view = _create_field_view_for_attr(field_name, field, self._frame, self._widget_name)
            else: 
                # field is FieldViewFactory
                field_view = field(self._frame, field_name, parent_widget_name=self._widget_name)

            self._fields[field_name] = field_view
            self._value[field_name] = field_view.value

            # I use here a decorator so that the field_name gets captured by the function and not gets overwritten in 
            # subsequent runs
            def set_dict_value(key):
                def _set_dict_value(val):
                    attr = self._obj_attrs[key]
                    if isinstance(val, dict) and isinstance(attr, attrs.Attribute) and attr.type is not None and attrs.has(attr.type):
                        # convert value to attribute type, if it is a nested attrs class    
                        val = attr.type(**val)
                    
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
            attr = self._obj_attrs[field_name]
            if isinstance(attr, attrs.Attribute) and attr.type is not None and attrs.has(attr.type) \
                    and not _is_registered_class(attr.type):
                # needed for correct unnesting/nesting
                default_value = attr.type(**field.default)
            else:
                default_value = field.default

            default_fields[field_name] = default_value
        return default_fields

    @property
    def value(self) -> dict: 
        return self._value

    @value.setter
    def value(self, v: dict) -> None: 
        for field_name, value in v.items():
            if attrs.has(value.__class__) and not _is_registered_class(value.__class__):
                # unnest to dict, if it is an attrs class
                value = attrs.asdict(value) 

            # This updates also automatically the self._value of this class
            self._fields[field_name].value = value
        self._callback(copy.deepcopy(self._value)) # We use deepcopy to avoid reference issues


    def bind_value_change(self, command: Callable[[dict], None]) -> None: 
        self._callback = command



class FormWidget(UIComponent):
    def __init__(self, parent: UIComponent, parent_view: View | ttk.Frame, 
                 title: str, form_attrs: Type | FormFieldAttributes | ProcedureArgs, model_dict: dict | None = None):
        """
            args:
                model_dict: Is a dictionary that is one way bound target to source. So if the form gets updated, it updates the dictionary too, but not vice versa.
        """
        if isinstance(form_attrs, type) and issubclass(form_attrs, ProcedureArgs):
            self._form_attrs: FormFieldAttributes = form_attrs.fields_dict_with_alias()
        else:
            self._form_attrs: FormFieldAttributes = form_attrs if isinstance(form_attrs, dict) else attrs.fields_dict(form_attrs) #type: ignore

        self._title = title
        self._view = FormWidgetView(parent_view)
        self._view.set_title(self._title)
        super().__init__(parent, self._view)

        self._attr_view = ObjectFieldView(self._view.field_slot, self._title, self._form_attrs)
        self._view._initialize_publish()

        # bind the model dict to the view
        self._model_dict = {} if model_dict is None else model_dict
        self._model_dict.update(**self._attr_view.value)
        self._attr_view.bind_value_change(lambda value: self._model_dict.update(**value))

    @property
    def form_data(self) -> Dict[str, Any]:
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

