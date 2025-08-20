import abc
from enum import Enum
import inspect
import math
from typing import Any, Callable, Dict, Generic, List, Optional, Protocol, Tuple, Type, TypeVar, Union, get_args, get_origin

import copy
import attrs
import cattrs
from pathlib import Path
from sonic_protocol.schema import SIPrefix
from soniccontrol.data_capturing.converter import create_cattrs_converter_for_forms
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.si_unit import SIVar
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TkinterView, View
from soniccontrol_gui.constants import ui_labels, sizes
from soniccontrol_gui.widgets.file_browse_button import FileBrowseButtonView

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame

from soniccontrol.procedures.holder import HoldTuple, HolderArgs



class EntryStyle(Enum):
    PRIMARY = "primary.TEntry"
    SUCCESS = "success.TEntry"
    DANGER = "danger.TEntry"


T = TypeVar("T")
class FieldViewBase(abc.ABC, Generic[T], View):
    def subscribe_focus_to_scroll(self, widget, top_scroll_frame):
        """
        Binds the <FocusIn> event of the widget to scroll it into view in the top_scroll_frame.
        """
        if top_scroll_frame is None:
            return
        def _on_focus_in(event):
            try:
                widget.update_idletasks()
                top_scroll_frame.update_idletasks()

                # the content frame is this object (its visible container is `.container`).
                if hasattr(top_scroll_frame, 'yview_moveto'):
                    # content height (inner) and container (visible) are available via
                    # top_scroll_frame.winfo_height() and top_scroll_frame.container.winfo_height()
                    content_height = top_scroll_frame.winfo_height()
                    container_height = getattr(top_scroll_frame, 'container', top_scroll_frame).winfo_height()
                    # nothing to do if sizes are not positive
                    if content_height <= 0 or container_height <= 0:
                        return

                    # widget position relative to visible container (to check lower-third)
                    # Walk up the widget.master chain and sum winfo_y() to get a reliable
                    # position inside the scrolled content (more robust than rooty diffs
                    # when the content is placed/moved).
                    def _relative_y_in_ancestor(wdg, ancestor):
                        y = 0
                        w = wdg
                        while w is not None and w != ancestor:
                            try:
                                y += w.winfo_y()
                            except Exception:
                                # if a widget isn't mapped or raises, fall back
                                return None
                            w = getattr(w, 'master', None)
                        return y

                    # precompute root positions as fallbacks
                    widget_root = None
                    container_top = None
                    content_top = None
                    try:
                        widget_root = widget.winfo_rooty()
                    except Exception:
                        widget_root = None
                    try:
                        container_top = top_scroll_frame.container.winfo_rooty()
                    except Exception:
                        container_top = None
                    try:
                        content_top = top_scroll_frame.winfo_rooty()
                    except Exception:
                        content_top = None

                    pos_in_container = _relative_y_in_ancestor(widget, top_scroll_frame.container)
                    # fallback to rooty difference if parent-walk failed and we have values
                    if pos_in_container is None:
                        if widget_root is None or container_top is None:
                            return
                        pos_in_container = widget_root - container_top

                    # If the widget is visible and in the higher (top) third of the visible area, skip scrolling.
                    # If pos_in_container < 0 the widget is above the visible area and we should scroll.
                    if pos_in_container >= 0 and pos_in_container <= (1.0 / 3.0) * container_height:
                        return

                    # Otherwise compute fraction within the full content and scroll so the widget
                    # appears at the top of the visible area. Use animation to avoid jumps.
                    if widget_root is not None and content_top is not None:
                        offset_in_content = widget_root - content_top
                    else:
                        # fallback: use position inside container as approximation
                        offset_in_content = pos_in_container
                    desired_fraction = offset_in_content / float(content_height)
                    desired_fraction = max(0.0, min(1.0, desired_fraction))

                    # current fraction (try via scrollbar); fallback to 0.0
                    try:
                        current_fraction = top_scroll_frame.vscroll.get()[0]
                    except Exception:
                        current_fraction = 0.0

                    # if already close to desired, don't animate
                    if abs(current_fraction - desired_fraction) < 0.01:
                        return

                    # cancel any running animation
                    try:
                        existing = getattr(top_scroll_frame, '_scroll_anim_id', None)
                        if existing:
                            top_scroll_frame.after_cancel(existing)
                    except Exception:
                        pass

                    # animate in a few steps
                    steps = 8
                    duration_ms = 160
                    step_time = max(1, int(duration_ms / steps))
                    delta = (desired_fraction - current_fraction) / float(steps)

                    i = 0
                    def _animate():
                        nonlocal i, current_fraction
                        i += 1
                        current_fraction = current_fraction + delta
                        # clamp
                        frac = max(0.0, min(1.0, current_fraction))
                        try:
                            top_scroll_frame.yview_moveto(frac)
                        except Exception:
                            return
                        if i < steps:
                            top_scroll_frame._scroll_anim_id = top_scroll_frame.after(step_time, _animate)
                        else:
                            top_scroll_frame._scroll_anim_id = None

                    _animate()
            except Exception as e:
                print(f"Error in scroll handler: {e}")

        widget.bind('<FocusIn>', _on_focus_in, '+')
            
    def __init__(self, master: TkinterView, *args, top_scroll_frame: Optional["ScrolledFrame"] = None, **kwargs):
        self._top_scroll_frame: Optional["ScrolledFrame"] = top_scroll_frame
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
        field_view_kwargs = kwargs.pop("field_view_kwargs", {}) # Others also rely on it so dont pop
        self._si_unit_label = None
        self._si_unit = field_view_kwargs.get("SI_unit", None)
        self._value: PrimitiveT = _default_value
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)
        # We pop earlier so that the super__init__ does not fail,
        # but we need restore because other the same Object might be used for other views(ATConfig)
        kwargs['field_view_kwargs'] = field_view_kwargs
        self._callback: Callable[[PrimitiveT], None] = lambda _: None
        self._str_value.trace_add("write", self._parse_str_value)


    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)
        self.entry = ttk.Entry(self, textvariable=self._str_value)
        if self._si_unit is not None:
            self._si_unit_label = ttk.Label(self, text=self._si_unit, state="readonly")
        WidgetRegistry.register_widget(self._str_value, "entry_str", self._widget_name)
        # Subscribe entry focus to scroll bar if available
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame is not None:
            self.subscribe_focus_to_scroll(self.entry, self._top_scroll_frame)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")

        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.W)
        if self._si_unit_label:
            self._si_unit_label.grid(row=0, column=2, padx=5, pady=5, sticky=ttk.W)

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

    @value.setter
    def set_value_without_setting_str(self, v: PrimitiveT) -> None:
        self._value = v
 
    def _parse_str_value(self, *_args):
        text = self._str_value.get()
        if text == "":
            # Don't set value or revert to default, just wait for valid input
            self.entry.configure(style=EntryStyle.DANGER.value)
            return
        try:
            self.set_value_without_setting_str = self._factory(self._str_value.get()) 
            self.entry.configure(style=EntryStyle.PRIMARY.value)
        except Exception as _:
            # I think it would be better to set to some value that signal a missing/broken value
            # Right now when the input failed then default value gets set, which causes the str_value to be set
            # which makes selecting every digit replacing it impossible, also the inputs for float is whack

            # But when we use set_value_without_setting_str then the default_value is being used,
            # even tho the input should be invalid

            # I think we should change this somehow so the user experience is better and it also does not fail silently or using wrong values
            self.set_value_without_setting_str = self._default_value 
            self.entry.configure(style=EntryStyle.DANGER.value)
        self._callback(self.value)


    def bind_value_change(self, command: Callable[[PrimitiveT], None]):
        self._callback = command


class SITypeFieldView(FieldViewBase[SIVar]):
    def __init__(self, master: TkinterView, field_name: str, *args, default_value: SIVar, **kwargs):
        
        _default_value = default_value
        self._field_name = field_name
        self._default_value: SIVar = _default_value 
        self._str_value: ttk.StringVar = ttk.StringVar(value=str(_default_value))
        field_view_kwargs = kwargs.pop("field_view_kwargs", {}) # Others also rely on it so dont pop
        self._value: SIVar = _default_value
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)
        # We pop earlier so that the super__init__ does not fail,
        # but we need restore because other the same Object might be used for other views(ATConfig)
        kwargs['field_view_kwargs'] = field_view_kwargs
        self._callback: Callable[[SIVar], None] = lambda _: None
        self._str_value.trace_add("write", self._parse_str_value)


    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)
        self.entry = ttk.Entry(self, textvariable=self._str_value)
        # Build readable labels for prefixes and a mapping back to the enum
        # First collect only the allowed prefixes (allowed_prefix may raise, so be defensive)
        prefixes: List[SIPrefix] = []
        for p in SIPrefix:
            try:
                if self._value.allowed_prefix(p):
                    prefixes.append(p)
            except Exception:
                # ignore prefixes that can't be queried
                continue

        def _prefix_label(p: SIPrefix) -> str:
            # prefer explicit attributes, with safe fallbacks
            sym = getattr(p, "symbol", None) or (p.value if isinstance(getattr(p, "value", None), str) else "")
            si_unit = getattr(self._value.meta, "si_unit", None)
            unit_str = getattr(si_unit, "value", "") if si_unit is not None else ""
            if sym is not None:
                return f"{sym}{unit_str}".strip()
            return f"{p.name} {unit_str}".strip()

        prefix_items = [_prefix_label(p) for p in prefixes]
        # map label -> prefix (zip uses the same filtered prefixes list)
        self._prefix_map = {label: p for label, p in zip(prefix_items, prefixes)}

        # Combobox for selecting prefix (show readable labels)
        self.si_unit_combobox = ttk.Combobox(self, values=prefix_items, state="readonly")
        try:
            current_prefix = getattr(self._value, "si_prefix", None)
            if current_prefix is not None:
                for lbl, p in self._prefix_map.items():
                    if p == current_prefix:
                        self.si_unit_combobox.set(lbl)
                        break
        except Exception:
            pass

        # handler: convert the numeric value to the new prefix so displayed number stays the same unit-wise
        def _on_prefix_change(_=None):
            sel = self.si_unit_combobox.get()
            prefix = self._prefix_map.get(sel)
            if prefix is None:
                return
            try:
                # self._value assumed to be an SIVar instance (model)
                # convert_to_prefix mutates value to represent same quantity in new prefix
                self._value.convert_to_prefix(prefix)
                # update the entry text to reflect converted numeric value
                self._str_value.set(str(self._value.value))
                # notify listeners
                self._callback(self._value)
            except Exception:
                # out-of-range selection or other error: indicate to user
                self.entry.configure(style=EntryStyle.DANGER.value)

        self.si_unit_combobox.bind("<<ComboboxSelected>>", _on_prefix_change)
        WidgetRegistry.register_widget(self.si_unit_combobox, "unit_combobox", self._widget_name)
        WidgetRegistry.register_widget(self._str_value, "entry_str", self._widget_name)
        # Subscribe entry focus to scroll bar if available
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame is not None:
            self.subscribe_focus_to_scroll(self.entry, self._top_scroll_frame)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")

        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.W)
        self.si_unit_combobox.grid(row=0, column=2, padx=5, pady=5, sticky=ttk.W)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def default(self) -> SIVar: 
        return self._default_value

    @property
    def value(self) -> SIVar:
        return self._value
    
    @value.setter
    def value(self, v: SIVar) -> None:
        self._value = v
        self._str_value.set(str(self._value.value))

    @value.setter
    def set_value_without_setting_str(self, v: SIVar) -> None:
        self._value = v
 
    def _parse_str_value(self, *_args):
        text = self._str_value.get()
        if text == "":
            # Don't set value or revert to default, just wait for valid input
            self.entry.configure(style=EntryStyle.DANGER.value)
            return
        try:
            value = type(self.value.value)(self._str_value.get())
            self.set_value_without_setting_str = SIVar(value, self.value.si_prefix, self.value.meta)
            self.entry.configure(style=EntryStyle.PRIMARY.value)
        except Exception as _:
            # I think it would be better to set to some value that signal a missing/broken value
            # Right now when the input failed then default value gets set, which causes the str_value to be set
            # which makes selecting every digit replacing it impossible, also the inputs for float is whack

            # But when we use set_value_without_setting_str then the default_value is being used,
            # even tho the input should be invalid

            # I think we should change this somehow so the user experience is better and it also does not fail silently or using wrong values
            self.set_value_without_setting_str = self._default_value 
            self.entry.configure(style=EntryStyle.DANGER.value)
        self._callback(self.value)


    def bind_value_change(self, command: Callable[[SIVar], None]):
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
        self._checkbutton.bind("<Return>", lambda e: self._var.set(not self._var.get()))
        
        # Subscribe checkbutton to scroll on focus
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame:
            self.subscribe_focus_to_scroll(self._checkbutton, self._top_scroll_frame)

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
        
        # Subscribe combobox to scroll on focus
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame:
            self.subscribe_focus_to_scroll(self._config_entry, self._top_scroll_frame)

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
        
        # Subscribe entry to scroll on focus
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame:
            self.subscribe_focus_to_scroll(self.entry, self._top_scroll_frame)

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
        
        # Subscribe entry to scroll on focus
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame:
            self.subscribe_focus_to_scroll(self._entry_time, self._top_scroll_frame)

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

    def from_type(self, field_name, field_type: type, slot: TkinterView, parent_widget_name: str, top_scroll_frame: Optional[ScrolledFrame] = None, **kwargs) -> FieldViewBase:
        # is compares for addresses. If variables point to the same underlying object
        # is compares for types. (needed for windows) 
        # == compares for equality. (needed for linux) 
        # == needed for Optional and other compound types, because they are created and not singletons like builtin types
        if field_type is int:
            return BasicTypeFieldView[int](slot, int, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type is float:
            return BasicTypeFieldView[float](slot, float, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type is bool:
            return BooleanFieldView(slot, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type is str:
            return BasicTypeFieldView[str](slot, str, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type is SIVar[int] or field_type is SIVar[float]:
            return SITypeFieldView(slot, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type == Optional[int] or field_type is Optional[int]:
            return NullableTypeFieldView[int](slot, int, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type == Optional[float] or field_type is Optional[float]:
            return NullableTypeFieldView[float](slot, float, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type == Optional[str] or field_type is Optional[str]:
            return NullableTypeFieldView[str](slot, str, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type is Dict or field_type is dict:
            return DictFieldView(slot, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type is HolderArgs:
            return TimeFieldView(slot, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type == Optional[Path] or field_type is Optional[Path]:
            return OptionalPathFieldView(slot, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif inspect.isclass(field_type) and issubclass(field_type, Enum): 
            # for enums we have to check if they are subclasses of the Enum base class
            return EnumFieldView(slot, field_name, field_type, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif get_origin(field_type) is tuple or field_type is tuple:
            return TupleFieldView(slot, field_name, field_type, self, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif field_type and attrs.has(field_type):
            # for the case that the type is a nested attrs class.
            kwargs.pop("default_value", None) # We do not use default values here. We deduce them later through attrs.Attribute
            return ObjectFieldView(slot, field_name, field_type, self, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        else:
            raise TypeError(f"The field with name {field_name} has the type {field_type}, which is not supported")

    def from_attribute(self, field_name: str, field: attrs.Attribute, obj_class: type, slot: TkinterView, parent_widget_name: str, top_scroll_frame: Optional[ScrolledFrame] = None) -> FieldViewBase:
        assert field.type is not None, "There is no type annotation for this field present"

        # Apply Attribute Hook
        hook_key = (obj_class, field_name)
        if hook_key in self._field_hooks:
            hook = self._field_hooks[hook_key]
            field_view = hook(obj_class, field, slot, {"parent_widget_name": parent_widget_name, "top_scroll_frame": top_scroll_frame})
            return field_view

        # Deduce kwargs for field from attrs.Attribute
        kwargs = {}
        if field.default is not None and field.default != attrs.NOTHING:
            kwargs["default_value"] = field.default.factory() if hasattr(field.default, "factory") else field.default

        field_view_kwargs_name = "field_view_kwargs"
        if field_view_kwargs_name in field.metadata:
            kwargs[field_view_kwargs_name] = field.metadata.get(field_view_kwargs_name) 

        return self.from_type(field_name, field.type, slot, parent_widget_name, top_scroll_frame, **kwargs)
    
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
            field_view = self._field_view_factory.from_type(f"Item {i+1}", class_type, self._frame, self._widget_name, top_scroll_frame=self._top_scroll_frame)
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
            field_view = self._field_view_factory.from_attribute(field_name, field, self._obj_class, self._frame, self._widget_name, top_scroll_frame=self._top_scroll_frame)
            self._fields[field_name] = field_view
            self._value[field_name] = field_view.value

            def set_dict_value(key):
                def _set_dict_value(val):
                    self._value[key] = val
                    self._callback(self._value) # we only return the attributes to update. More performant
                return _set_dict_value
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
        self._converter = create_cattrs_converter_for_forms()
        self._field_view_factory = DynamicFieldViewFactory(self._converter, field_hooks)

        self._title = title
        self._view = FormWidgetView(parent_view)
        self._view.set_title(self._title)
        super().__init__(parent, self._view)
        # self._view.field_slot is the ScrolledFrameView we need to scroll when
        self._attr_view = ObjectFieldView(self._view.field_slot, self._title, self._attrs_class, self._field_view_factory, top_scroll_frame=self._view._scrolled_frame)
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

