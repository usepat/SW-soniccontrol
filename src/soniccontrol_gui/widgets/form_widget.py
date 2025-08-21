import abc
from enum import Enum
import inspect
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union, get_args, get_origin

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
    def valid(self) -> bool: ...

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
        self._is_valid: bool = True  # Start with valid default value
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
        self.entry = ttk.Entry(self, textvariable=self._str_value, width=12)
        if self._si_unit is not None:
            self._si_unit_label = ttk.Label(self, text=self._si_unit, state="readonly")
        WidgetRegistry.register_widget(self._str_value, "entry_str", self._widget_name)
        # Subscribe entry focus to scroll bar if available
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame is not None:
            self.subscribe_focus_to_scroll(self.entry, self._top_scroll_frame)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=0, minsize=80)      # Label: fixed width
        self.grid_columnconfigure(1, weight=1, minsize=120)     # Entry: expandable
        self.grid_rowconfigure(0, weight=1)                     # Allow vertical expansion

        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.EW)
        if self._si_unit_label:
            self._si_unit_label.grid(row=0, column=2, padx=5, pady=5, sticky=ttk.W)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def valid(self) -> bool:
        return self._is_valid

    @property
    def default(self) -> PrimitiveT: 
        return self._default_value

    @property
    def value(self) -> PrimitiveT:
        return self._value
    
    @value.setter
    def value(self, v: PrimitiveT) -> None:
        self._value = v
        self._is_valid = True
        self._str_value.set(str(v))

    def set_value_without_setting_str(self, v: PrimitiveT) -> None:
        self._value = v
 
    def _parse_str_value(self, *_args):
        text = self._str_value.get()
        if text == "":
            # Empty text is invalid for basic types
            self._is_valid = False
            self.entry.configure(style=EntryStyle.DANGER.value)
            return
        try:
            self._value = self._factory(self._str_value.get()) 
            self._is_valid = True
            self.entry.configure(style=EntryStyle.PRIMARY.value)
        except Exception as _:
            # Parse failed - mark as invalid but don't change the value
            # This preserves the last valid value while indicating error state
            self._is_valid = False
            self.entry.configure(style=EntryStyle.DANGER.value)
        self._callback(self._value)


    def bind_value_change(self, command: Callable[[PrimitiveT], None]):
        self._callback = command


class SITypeFieldView(FieldViewBase[SIVar]):
    def __init__(self, master: TkinterView, field_name: str, *args, default_value: SIVar, **kwargs):
        
        _default_value = default_value
        self._field_name = field_name
        self._default_value: SIVar = _default_value 
        self._str_value: ttk.StringVar = ttk.StringVar(value=str(_default_value.value))
        field_view_kwargs = kwargs.pop("field_view_kwargs", {}) # Others also rely on it so dont pop
        self._value: SIVar = _default_value
        self._is_valid: bool = True  # Start with valid default value
        
        # Determine value type from the default_value's actual type
        self._value_type = type(default_value.value)
        
        # Extract optional UI elements from kwargs
        self._use_scale = field_view_kwargs.get("use_scale", False)
        self._use_spinbox = field_view_kwargs.get("use_spinbox", False)
        
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)
        # We pop earlier so that the super__init__ does not fail,
        # but we need restore because other the same Object might be used for other views(ATConfig)
        kwargs['field_view_kwargs'] = field_view_kwargs
        self._callback: Callable[[SIVar], None] = lambda _: None
        self._trace_id = self._str_value.trace_add("write", self._parse_str_value)
        
        # Track timer for visual feedback to avoid multiple overlapping timers
        self._style_reset_timer = None
        
        # Flag to prevent recursive scale updates
        self._updating_scale = False

    def _clamp_value_with_feedback(self, value, prefix, update_callback: Optional[Callable[[Any], None]] = None):
        """
        Clamp a value to the valid range and provide visual feedback.
        
        Args:
            value: The value to clamp
            prefix: The SI prefix for range calculation
            update_callback: Optional callback to update the UI with clamped value
            
        Returns:
            tuple: (clamped_value, was_clamped)
        """
        if not (self._value and hasattr(self._value, 'is_value_in_range')):
            return value, False
            
        if self._value.is_value_in_range(value, prefix):
            # Value is in range - reset to normal style
            self._get_input_widget().configure(style=EntryStyle.PRIMARY.value)
            self._is_valid = True
            return value, False
            
        # Value is out of range - clamp it
        was_clamped = False
        if hasattr(self._value, 'get_min_value_in_prefix') and hasattr(self._value, 'get_max_value_in_prefix'):
            min_val = self._value.get_min_value_in_prefix(prefix)
            max_val = self._value.get_max_value_in_prefix(prefix)
            # Clamp the value to the valid range
            clamped_value = max(min_val, min(max_val, value))
            # Convert back to the correct type
            clamped_value = self._value_type(clamped_value)
            was_clamped = True
            
            # Update UI if callback provided
            if update_callback:
                update_callback(clamped_value)
            
            # Show visual feedback for clamping
            self._show_clamp_feedback()
            
            return clamped_value, was_clamped
            
        return value, False
    
    def _show_clamp_feedback(self):
        """Show temporary visual feedback that a value was clamped."""
        # Cancel any existing timer to avoid overlapping
        if self._style_reset_timer:
            self.after_cancel(self._style_reset_timer)
            
        # Show warning style
        self._get_input_widget().configure(style=EntryStyle.DANGER.value)
        self._is_valid = False
        
        # Reset style after delay
        def _reset_style():
            self._style_reset_timer = None
            if hasattr(self, '_get_input_widget'):
                self._get_input_widget().configure(style=EntryStyle.PRIMARY.value)
                self._is_valid = True
                
        self._style_reset_timer = self.after(1500, _reset_style)

    def _update_str_value_without_trace(self, new_value: str):
        """Update the string value without triggering the trace callback to avoid recursion."""
        try:
            self._str_value.trace_remove("write", self._trace_id)
        except ValueError:
            pass  # Trace might not exist
        self._str_value.set(new_value)
        self._trace_id = self._str_value.trace_add("write", self._parse_str_value)

    def destroy(self):
        """Clean up resources when widget is destroyed."""
        # Cancel any pending timer
        if self._style_reset_timer:
            self.after_cancel(self._style_reset_timer)
            self._style_reset_timer = None
        # Call parent destroy
        super().destroy()


    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)
        self.entry = ttk.Entry(self, textvariable=self._str_value, width=12)
        
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

        # Check if there's only one allowed prefix
        if len(prefixes) == 1:
            # Only one prefix allowed - use a label instead of combobox
            current_prefix_label = prefix_items[0]
            self.si_unit_label = ttk.Label(self, text=current_prefix_label, state="readonly")
            self.si_unit_combobox = None  # No combobox needed
        else:
            # Multiple prefixes - use combobox for selection with dynamic width
            max_width = max(len(item) for item in prefix_items) if prefix_items else 5
            combobox_width = min(max(max_width + 2, 5), 8)  # Between 5-8 characters
            self.si_unit_combobox = ttk.Combobox(self, values=prefix_items, state="readonly", width=combobox_width)
            self.si_unit_label = None  # No label needed
            
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
            # Only handle prefix changes if combobox exists (multiple prefixes)
            if self.si_unit_combobox is None:
                return
                
            sel = self.si_unit_combobox.get()
            prefix = self._prefix_map.get(sel)
            if prefix is None:
                return
            try:
                # self._value assumed to be an SIVar instance (model)
                # convert_to_prefix mutates value to represent same quantity in new prefix
                self._value.convert_to_prefix(prefix)
                
                # After prefix conversion, check if the value is still in valid range
                # and clamp it if necessary
                current_value = self._value.value
                if not self._value.is_value_in_range(current_value, prefix):
                    # Value is out of range after prefix conversion - clamp it
                    min_val = self._value.get_min_value_in_prefix(prefix)
                    max_val = self._value.get_max_value_in_prefix(prefix)
                    clamped_value = max(min_val, min(max_val, current_value))
                    # Convert to the appropriate type
                    clamped_value = self._value_type(clamped_value)
                    self._value.value = clamped_value
                    # Show visual feedback for clamping
                    self._show_clamp_feedback()
                
                # update the entry text to reflect converted numeric value
                self._update_str_value_without_trace(str(self._value.value))
                # Update scale range if scale is enabled
                if self._use_scale:
                    self._update_scale_range()
                    # Also update the scale position to the new converted value
                    self._updating_scale = True
                    try:
                        self.scale.set(float(self._value.value))
                    finally:
                        self._updating_scale = False
                # Update spinbox range if spinbox is enabled
                if self._use_spinbox:
                    self._update_spinbox_range()
                # notify listeners
                self._callback(self._value)
            except Exception:
                # out-of-range selection or other error: indicate to user
                self._get_input_widget().configure(style=EntryStyle.DANGER.value)

        # Only bind combobox event if combobox exists
        if self.si_unit_combobox is not None:
            self.si_unit_combobox.bind("<<ComboboxSelected>>", _on_prefix_change)
        
        # Optional Scale widget
        if self._use_scale:
            # Create a frame to hold the scale and its labels
            self.scale_frame = ttk.Frame(self)
            self.scale = ttk.Scale(self.scale_frame, orient='horizontal')
            
            # Create min/max labels for the scale
            self.scale_min_label = ttk.Label(self.scale_frame, text="0")
            self.scale_max_label = ttk.Label(self.scale_frame, text="100")
            
            # Layout the scale frame: min_label | scale | max_label
            self.scale_frame.grid_columnconfigure(1, weight=1)  # Scale takes most space
            self.scale_min_label.grid(row=0, column=0, padx=2)
            self.scale.grid(row=0, column=1, sticky=ttk.EW, padx=5)
            self.scale_max_label.grid(row=0, column=2, padx=2)
            
            self._update_scale_range()
            self.scale.set(float(self._value.value))
            
            def _on_scale_change(value):
                # Prevent recursive calls
                if self._updating_scale:
                    return
                    
                try:
                    # Convert the scale value to the appropriate type
                    scaled_value = self._value_type(float(value))
                    
                    # Clamp value if needed and provide visual feedback
                    def update_scale_position(clamped_val):
                        # Set the flag to prevent recursion
                        self._updating_scale = True
                        try:
                            self.scale.set(float(clamped_val))
                        finally:
                            self._updating_scale = False
                    
                    scaled_value, was_clamped = self._clamp_value_with_feedback(
                        scaled_value, self._value.si_prefix, update_scale_position)
                    
                    self._value.value = scaled_value
                    # Update the string value without triggering trace recursion
                    self._update_str_value_without_trace(str(scaled_value))
                    self._callback(self._value)
                except Exception:
                    self._get_input_widget().configure(style=EntryStyle.DANGER.value)
            
            self.scale.configure(command=_on_scale_change)
            #WidgetRegistry.register_widget(self.scale, "scale", self._widget_name)
        
        # Optional Spinbox widget
        if self._use_spinbox:
            self.spinbox = ttk.Spinbox(self, textvariable=self._str_value, width=12)
            self._update_spinbox_range()
            
            def _on_spinbox_change():
                # Parse the spinbox value and trigger validation
                self._parse_str_value()
            
            self.spinbox.configure(command=_on_spinbox_change)
            WidgetRegistry.register_widget(self.spinbox, "spinbox", self._widget_name)

        # Only register combobox if it exists (multiple prefixes)
        if self.si_unit_combobox is not None:
            WidgetRegistry.register_widget(self.si_unit_combobox, "unit_combobox", self._widget_name)
        # Register label if it exists (single prefix)
        if self.si_unit_label is not None:
            WidgetRegistry.register_widget(self.si_unit_label, "unit_label", self._widget_name)
            
        WidgetRegistry.register_widget(self._str_value, "entry_str", self._widget_name)
        # Subscribe entry focus to scroll bar if available
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame is not None:
            # Subscribe the appropriate input widget based on what's being used
            if self._use_spinbox:
                self.subscribe_focus_to_scroll(self.spinbox, self._top_scroll_frame)
            else:
                self.subscribe_focus_to_scroll(self.entry, self._top_scroll_frame)

    def _update_scale_range(self) -> None:
        """Update the scale widget range based on the current prefix and metadata range."""
        if not self._use_scale or not hasattr(self, 'scale'):
            return
            
        try:
            # Get the min/max values in the current prefix from metadata
            current_prefix = self._value.si_prefix
            range_min = self._value.get_min_value_in_prefix(current_prefix)
            range_max = self._value.get_max_value_in_prefix(current_prefix)
            
            # Configure the scale with proper range
            self.scale.configure(from_=range_min, to=range_max)
            
            # Update the labels if they exist
            if hasattr(self, 'scale_min_label') and hasattr(self, 'scale_max_label'):
                # Format the numbers nicely
                if isinstance(self._value.value, int):
                    min_text = f"{int(range_min)}"
                    max_text = f"{int(range_max)}"
                else:
                    min_text = f"{range_min:.1f}"
                    max_text = f"{range_max:.1f}"
                
                self.scale_min_label.configure(text=min_text)
                self.scale_max_label.configure(text=max_text)
            
        except Exception:
            # Fallback to default range
            self.scale.configure(from_=0, to=100)
            if hasattr(self, 'scale_min_label') and hasattr(self, 'scale_max_label'):
                self.scale_min_label.configure(text="0")
                self.scale_max_label.configure(text="100")

    def _update_spinbox_range(self) -> None:
        """Update the spinbox widget range based on the current prefix and metadata range."""
        if not self._use_spinbox or not hasattr(self, 'spinbox'):
            return
            
        try:
            # Get the min/max values in the current prefix from metadata
            current_prefix = self._value.si_prefix
            range_min = self._value.get_min_value_in_prefix(current_prefix)
            range_max = self._value.get_max_value_in_prefix(current_prefix)
            
            # Calculate smart increment based on the range and prefix
            range_span = range_max - range_min
            
            if isinstance(self._value.value, int):
                # For integers, use sensible step sizes
                if range_span <= 100:
                    increment = 1
                elif range_span <= 1000:
                    increment = 10
                elif range_span <= 10000:
                    increment = 100
                elif range_span <= 100000:
                    increment = 1000
                else:
                    increment = 10000
                    
                self.spinbox.configure(from_=int(range_min), to=int(range_max), increment=increment)
            else:
                # For floats, use decimal increments based on the range
                if range_span <= 1:
                    increment = 0.01
                elif range_span <= 10:
                    increment = 0.1
                elif range_span <= 100:
                    increment = 1.0
                elif range_span <= 1000:
                    increment = 10.0
                else:
                    increment = 100.0
                    
                self.spinbox.configure(from_=range_min, to=range_max, increment=increment)
                
        except Exception:
            # Fallback to default range
            self.spinbox.configure(from_=0, to=100, increment=1)

    def _get_input_widget(self):
        """Get the currently visible input widget (entry or spinbox)."""
        if self._use_spinbox and hasattr(self, 'spinbox'):
            return self.spinbox
        else:
            return self.entry

    def _initialize_publish(self) -> None:
        # Configure columns with better proportions
        self.grid_columnconfigure(0, weight=0, minsize=80)      # Label: fixed width
        self.grid_columnconfigure(1, weight=1, minsize=120)     # Entry/Spinbox: expandable
        self.grid_columnconfigure(2, weight=0, minsize=60)      # Unit: fixed width

        # Place the basic widgets in row 0
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        
        # Use spinbox instead of entry if enabled, otherwise use entry
        if self._use_spinbox:
            self.spinbox.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.EW)
            # Hide the entry widget if spinbox is used
            # Note: We still create the entry for consistency but don't grid it
        else:
            self.entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.EW)
            
        # Place combobox or label based on number of allowed prefixes
        if self.si_unit_combobox is not None:
            self.si_unit_combobox.grid(row=0, column=2, padx=5, pady=5, sticky=ttk.EW)
        elif self.si_unit_label is not None:
            self.si_unit_label.grid(row=0, column=2, padx=5, pady=5, sticky=ttk.W)
        
        # Place scale below all other widgets if enabled
        if self._use_scale:
            # Configure row 1 for the scale - allow it to expand vertically
            self.grid_rowconfigure(1, weight=1)
            # Span the scale frame across all three columns
            self.scale_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=ttk.NSEW)
        else:
            # If no scale, allow the main row to expand
            self.grid_rowconfigure(0, weight=1)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def valid(self) -> bool:
        return self._is_valid

    @property
    def default(self) -> SIVar: 
        return self._default_value

    @property
    def value(self) -> SIVar:
        return self._value
    
    @value.setter
    def value(self, v: SIVar) -> None:
        self._value = v
        # Update the string value without triggering trace recursion
        self._update_str_value_without_trace(str(self._value.value))
        # Update optional widgets when value changes
        if self._use_scale and hasattr(self, 'scale'):
            self._update_scale_range()
            self._updating_scale = True
            try:
                self.scale.set(float(self._value.value))
            finally:
                self._updating_scale = False
        if self._use_spinbox and hasattr(self, 'spinbox'):
            self._update_spinbox_range()

    @value.setter
    def set_value_without_setting_str(self, v: SIVar) -> None:
        self._value = v
        # Update optional widgets when value changes
        if self._use_scale and hasattr(self, 'scale'):
            self._update_scale_range()
            self._updating_scale = True
            try:
                self.scale.set(float(self._value.value))
            finally:
                self._updating_scale = False
        if self._use_spinbox and hasattr(self, 'spinbox'):
            self._update_spinbox_range()
 
    def _parse_str_value(self, *_args):
        text = self._str_value.get()
        if text == "":
            # Empty text is invalid for SIVar
            self._is_valid = False
            self._get_input_widget().configure(style=EntryStyle.DANGER.value)
            return
        try:
            # Get current prefix from combobox if it exists, otherwise use the single prefix
            if self.si_unit_combobox is not None:
                sel = self.si_unit_combobox.get()
                current_prefix = self._prefix_map.get(sel, SIPrefix.NONE)
            else:
                # Single prefix case - get the only prefix from the map
                current_prefix = list(self._prefix_map.values())[0] if self._prefix_map else SIPrefix.NONE
            
            # Use the value_type stored during initialization
            value = self._value_type(text)
            
            self._update_str_value_without_trace(str(value))
            min_val = self._value.get_min_value_in_prefix(current_prefix)
            max_val = self._value.get_max_value_in_prefix(current_prefix)
            if value < min_val or value > max_val:
                self._get_input_widget().configure(style=EntryStyle.DANGER.value)
                self._is_valid = False
            else:
                self._get_input_widget().configure(style=EntryStyle.PRIMARY.value)
                self._is_valid = True
            
            # Create new SIVar with fixed meta
            if self._value:
                self._value.value = value
                self._value.si_prefix = current_prefix
                
            # Update optional widgets when value changes
            if self._use_scale and hasattr(self, 'scale'):
                self._update_scale_range()
                self._updating_scale = True
                try:
                    self.scale.set(float(value))
                finally:
                    self._updating_scale = False
            if self._use_spinbox and hasattr(self, 'spinbox'):
                self._update_spinbox_range()
                
        except Exception as _:
            # Parse failed - mark as invalid but don't change the value
            self._is_valid = False
            self._get_input_widget().configure(style=EntryStyle.DANGER.value)
        self._callback(self.value)


    def bind_value_change(self, command: Callable[[SIVar], None]):
        self._callback = command

T = TypeVar("T", int, float)
class OptionalSITypeFieldView(FieldViewBase[Optional[SIVar[T]]]):
    def __init__(self, master: TkinterView, field_name: str, *args, 
                 default_value: Optional[SIVar[T]] = None, **kwargs):
        
        self._field_name = field_name
        self._default_value: Optional[SIVar] = default_value 
        
        # Initialize display value
        if default_value is None:
            display_value = ""
        else:
            display_value = str(default_value.value)
            
        self._str_value: ttk.StringVar = ttk.StringVar(value=display_value)
        field_view_kwargs = kwargs.pop("field_view_kwargs", {})
        
        # Extract optional UI elements from kwargs
        self._use_scale = kwargs.pop("use_scale", False)
        self._use_spinbox = kwargs.pop("use_spinbox", False)
        
        # Store the SIVar subclass factory from field_view_kwargs
        self._si_var_class = field_view_kwargs.get("si_var_class", None)
        
        # Extract metadata from the subclass or default value
        if self._si_var_class and hasattr(self._si_var_class, '_si_meta'):
            self._si_meta = self._si_var_class._si_meta
        elif default_value is not None:
            self._si_meta = default_value.meta
        else:
            # No valid source for metadata - this is an error condition
            raise ValueError(f"OptionalSITypeFieldView for field '{field_name}' requires either a si_var_class in field_view_kwargs or a default_value with metadata")
        
        # Extract the actual type from the default value if available,
        # otherwise determine from the SIVar subclass
        if default_value is not None:
            self._value_type = type(default_value.value)
        else:
            # For new instances without default value, determine type from the SIVar subclass
            # The si_var_class should be a specific subclass like AtfSiVar(SIVar[int]) or TemperatureSIVar(SIVar[float])
            if self._si_var_class:
                # Check if it's AtfSiVar (which uses int) or other types (which use float)
                if hasattr(self._si_var_class, '__orig_bases__'):
                    # Extract the Generic type parameter from SIVar[T]
                    for base in self._si_var_class.__orig_bases__:
                        if hasattr(base, '__origin__') and base.__origin__ is SIVar:
                            if hasattr(base, '__args__') and base.__args__:
                                self._value_type = base.__args__[0]
                                break
                    else:
                        # Couldn't extract type from bases
                        raise RuntimeError(f"Could not determine value type from SIVar subclass {self._si_var_class.__name__} for field '{self._field_name}'")
                else:
                    # If we can't determine from generic parameters
                    raise RuntimeError(f"Could not determine value type from SIVar subclass {self._si_var_class.__name__} for field '{self._field_name}' - no __orig_bases__ available")
            else:
                # No si_var_class available - this should not happen due to earlier validation
                raise RuntimeError(f"No si_var_class available for field '{self._field_name}' - this indicates a programming error")
        
        self._value: Optional[SIVar] = default_value
        self._is_valid: bool = True  # Start with valid state (None is valid for optional)
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)
        kwargs['field_view_kwargs'] = field_view_kwargs
        self._callback: Callable[[Optional[SIVar]], None] = lambda _: None
        self._str_value.trace_add("write", self._parse_str_value)
        
        # Flag to prevent recursive scale updates
        self._updating_scale = False

    def _get_default_prefix_from_constructor(self) -> Optional[SIPrefix]:
        """Extract the default si_prefix value from the SIVar subclass constructor."""
        if not self._si_var_class:
            return None
            
        import inspect
        try:
            # Get the constructor signature
            sig = inspect.signature(self._si_var_class.__init__)
            
            # Look for the si_prefix parameter
            if 'si_prefix' in sig.parameters:
                param = sig.parameters['si_prefix']
                if param.default != inspect.Parameter.empty:
                    return param.default
            
            return None
        except Exception:
            # If anything goes wrong with inspection, return None
            return None

    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)
        self.entry = ttk.Entry(self, textvariable=self._str_value, width=12)
        
        # Build readable labels for prefixes using the fixed meta
        prefixes: List[SIPrefix] = []
        for p in SIPrefix:
            try:
                if self._si_meta.si_prefix_min <= p <= self._si_meta.si_prefix_max:
                    prefixes.append(p)
            except Exception:
                continue

        def _prefix_label(p: SIPrefix) -> str:
            sym = getattr(p, "symbol", None) or ""
            unit_str = getattr(self._si_meta.si_unit, "value", "") if self._si_meta.si_unit is not None else ""
            if sym is not None:
                return f"{sym}{unit_str}".strip()
            return f"{p.name} {unit_str}".strip()

        prefix_items = [_prefix_label(p) for p in prefixes]
        self._prefix_map = {label: p for label, p in zip(prefix_items, prefixes)}

        # Combobox for selecting prefix
        # Calculate dynamic width based on prefix string lengths
        combobox_width = max(len(item) for item in prefix_items) if prefix_items else 5
        combobox_width = min(max(combobox_width, 5), 8)  # Ensure width is between 5 and 8
        self.si_unit_combobox = ttk.Combobox(self, values=prefix_items, state="readonly", width=combobox_width)
        
        # Set current prefix if value exists
        if self._value is not None:
            for lbl, p in self._prefix_map.items():
                if p == self._value.si_prefix:
                    self.si_unit_combobox.set(lbl)
                    break
        else:
            # Get default prefix from the SIVar subclass constructor
            default_prefix = self._get_default_prefix_from_constructor()
            if default_prefix is not None:
                # Set combobox to the default prefix from constructor
                for lbl, p in self._prefix_map.items():
                    if p == default_prefix:
                        self.si_unit_combobox.set(lbl)
                        break
                else:
                    # Programming error: default prefix not in allowed range
                    raise RuntimeError(f"Programming error: Default prefix {default_prefix} from {self._si_var_class.__name__} constructor is not in allowed range {self._si_meta.si_prefix_min} to {self._si_meta.si_prefix_max} for field '{self._field_name}'")
            else:
                # Fallback: couldn't determine default prefix, use first available
                if prefix_items:
                    self.si_unit_combobox.set(prefix_items[0])

        def _on_prefix_change(_=None):
            sel = self.si_unit_combobox.get()
            prefix = self._prefix_map.get(sel)
            if prefix is None:
                return
            try:
                if self._value is not None:
                    # Convert existing value to new prefix
                    self._value.convert_to_prefix(prefix)
                    self._str_value.set(str(self._value.value))
                self._callback(self._value)
            except Exception:
                self.entry.configure(style=EntryStyle.DANGER.value)

        self.si_unit_combobox.bind("<<ComboboxSelected>>", _on_prefix_change)
        WidgetRegistry.register_widget(self.si_unit_combobox, "unit_combobox", self._widget_name)
        WidgetRegistry.register_widget(self._str_value, "entry_str", self._widget_name)
        
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame is not None:
            self.subscribe_focus_to_scroll(self.entry, self._top_scroll_frame)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=0, minsize=80)      # Label: fixed width
        self.grid_columnconfigure(1, weight=1, minsize=120)     # Entry: expandable
        self.grid_columnconfigure(2, weight=0, minsize=60)      # Unit: fixed width

        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.EW)
        self.si_unit_combobox.grid(row=0, column=2, padx=5, pady=5, sticky=ttk.EW)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def valid(self) -> bool:
        return self._is_valid

    @property
    def default(self) -> Optional[SIVar[T]]: 
        return self._default_value

    @property
    def value(self) -> Optional[SIVar[T]]:
        return self._value
    
    @value.setter
    def value(self, v: Optional[SIVar[T]] | None) -> None:
        # Handle both SIVar objects and unstructured dicts
        if v is None:
            self._value = None
            self._str_value.set("")
        else:
            self._value = v
            for lbl, p in self._prefix_map.items():
                if p == self._value.si_prefix:
                    self.si_unit_combobox.set(lbl)
                    self._str_value.set(str(v.value))
                    break
 
    def _parse_str_value(self, *_args):
        text = self._str_value.get().strip()
        if text == "":
            # Empty text means None value - this is valid for Optional
            self._value = None
            self._is_valid = True
            self.entry.configure(style=EntryStyle.PRIMARY.value)
            self._callback(self._value)
            return
            
        try:
            # Get current prefix from combobox
            sel = self.si_unit_combobox.get()
            current_prefix = self._prefix_map.get(sel, SIPrefix.NONE)
            
            # Use the value_type stored during initialization
            value = self._value_type(text)
            # Create new SIVar with fixed meta
            if self._value:
                self._value.value = value
                self._value.si_prefix = current_prefix
            else:
                # Create new instance using the stored subclass factory
                if self._si_var_class:
                    # Use the specific subclass if available
                    self._value = self._si_var_class(value, current_prefix)
                else:
                    # This should never happen since we validate si_var_class in __init__
                    raise RuntimeError(f"No si_var_class available for field '{self._field_name}' - this indicates a programming error")
            self._is_valid = True
            self.entry.configure(style=EntryStyle.PRIMARY.value)
            
        except Exception:
            # On parse error, mark as invalid but keep previous value
            self._is_valid = False
            self.entry.configure(style=EntryStyle.DANGER.value)
            
        self._callback(self._value)

    def bind_value_change(self, command: Callable[[Optional[SIVar[T]]], None]):
        self._callback = command



class BooleanFieldView(FieldViewBase[bool]):
    def __init__(self, master: TkinterView, field_name: str, *args, default_value: bool = False, **kwargs):
        self._field_name = field_name
        self._default_value = default_value
        self._var = ttk.BooleanVar(value=self._default_value)
        self._callback: Callable[[bool], None] = lambda _: None

        # Extract field_view_kwargs for checkbutton configuration
        field_view_kwargs = kwargs.pop("field_view_kwargs", {})
        self._checkbutton_kwargs = field_view_kwargs  # Store for use in _initialize_children
        
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name

        super().__init__(master, *args, **kwargs)
        # Restore field_view_kwargs for potential reuse
        kwargs['field_view_kwargs'] = field_view_kwargs
        self._var.trace_add("write", self._on_change)

    def _initialize_children(self) -> None:
        # Create checkbutton with additional kwargs from field_view_kwargs
        checkbutton_config = {
            "text": self._field_name,
            "variable": self._var
        }
        # Add any additional configuration from field_view_kwargs
        checkbutton_config.update(self._checkbutton_kwargs)
        
        self._checkbutton = ttk.Checkbutton(self, **checkbutton_config)
        WidgetRegistry.register_widget(self._checkbutton, "checkbutton", self._widget_name)
        self._checkbutton.bind("<Return>", lambda e: self._var.set(not self._var.get()))
        
        # Subscribe checkbutton to scroll on focus
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame:
            self.subscribe_focus_to_scroll(self._checkbutton, self._top_scroll_frame)

    def _initialize_publish(self) -> None:
        self.grid_rowconfigure(0, weight=1)                     # Allow vertical expansion
        self._checkbutton.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def valid(self) -> bool:
        return True  # Boolean fields are always valid

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

        enum_names = [e.name for e in self._enum_class]
        # Calculate dynamic width based on enum name lengths
        combobox_width = max(len(name) for name in enum_names) if enum_names else 5
        combobox_width = min(max(combobox_width, 5), 15)  # Ensure width is between 5 and 15

        self._config_entry = ttk.Combobox(
            self,
            textvariable=self._selected_enum_member,
            values=enum_names,
            state="readonly",
            width=combobox_width
        )

        WidgetRegistry.register_widget(self._selected_enum_member, "entry_enum", self._widget_name)
        
        # Subscribe combobox to scroll on focus
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame:
            self.subscribe_focus_to_scroll(self._config_entry, self._top_scroll_frame)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=1, uniform="col")
        self.grid_columnconfigure(1, weight=1, uniform="col")
        self.grid_rowconfigure(0, weight=1)                     # Allow vertical expansion

        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self._config_entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.EW) 

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def valid(self) -> bool:
        return True  # Enum fields are always valid (combobox ensures valid selection)

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
        self._is_valid: bool = True  # Start with valid state (None is valid for nullable)
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name

        super().__init__(master, *args, **kwargs)

        self._callback: Callable[[Optional[PrimitiveT]], None] = lambda _: None
        self._str_value.trace_add("write", self._parse_str_value)


    def _initialize_children(self) -> None:
        self.label = ttk.Label(self, text=self._field_name)
        self.entry = ttk.Entry(self, textvariable=self._str_value, width=12)

        WidgetRegistry.register_widget(self._str_value, "entry_str", self._widget_name)
        
        # Subscribe entry to scroll on focus
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame:
            self.subscribe_focus_to_scroll(self.entry, self._top_scroll_frame)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=0, minsize=80)      # Label: fixed width
        self.grid_columnconfigure(1, weight=1, minsize=120)     # Entry: expandable
        self.grid_rowconfigure(0, weight=1)                     # Allow vertical expansion

        self.label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky=ttk.EW)

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def valid(self) -> bool:
        return self._is_valid

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
            self._value = None if text == "" else self._factory(text) 
            self._is_valid = True
            self.entry.configure(style=EntryStyle.PRIMARY.value)
        except Exception as _:
            # Parse failed - mark as invalid but don't change the value
            self._is_valid = False
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

    def _initialize_children(self) -> None: 
        pass

    def _initialize_publish(self) -> None: 
        pass

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def valid(self) -> bool:
        return True  # OptionalPathFieldView is always valid (None is valid)

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
        self._is_valid: bool = True  # Start with valid default value
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + "." + self._field_name
        super().__init__(master, *args, **kwargs)

        self._callback: Callable[[HoldTuple], None] = lambda _: None
        self._time_value_str.trace_add("write", self._parse_str_value)
        self._unit_value_str.trace_add("write", self._parse_str_value)


    def _initialize_children(self) -> None:
        self._label = ttk.Label(self, text=self._field_name)
        self._entry_frame = ttk.Frame(self)
        self._entry_time = ttk.Entry(self._entry_frame, textvariable=self._time_value_str, width=12)
        self._unit_button = ttk.Button(self._entry_frame, text=self._unit_value_str.get(), command=self._toggle_unit)

        WidgetRegistry.register_widget(self._time_value_str, "time_str", self._widget_name)
        WidgetRegistry.register_widget(self._unit_value_str, "unit_str", self._widget_name)
        
        # Subscribe entry to scroll on focus
        if hasattr(self, '_top_scroll_frame') and self._top_scroll_frame:
            self.subscribe_focus_to_scroll(self._entry_time, self._top_scroll_frame)

    def _initialize_publish(self) -> None:
        self.grid_columnconfigure(0, weight=0, minsize=80)      # Label: fixed width
        self.grid_columnconfigure(1, weight=1, minsize=120)     # Entry frame: expandable
        self.grid_rowconfigure(0, weight=1)                     # Allow vertical expansion

        self._label.grid(row=0, column=0, padx=5, pady=5, sticky=ttk.W)
        self._entry_frame.grid(row=0, column=1, sticky=ttk.EW)
        self._entry_time.pack(padx=5, pady=5, side=ttk.LEFT, fill=ttk.X, expand=True)
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
    def valid(self) -> bool:
        return self._is_valid

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
            self._is_valid = True
            self._entry_time.configure(style=EntryStyle.PRIMARY.value)
        except Exception as _:
            # Parse failed - mark as invalid but don't change the value
            self._is_valid = False
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

        entry_key = ttk.Entry(row_frame, textvariable=entry_key_var, width=12)
        entry_value = ttk.Entry(row_frame, textvariable=entry_value_var, width=12)
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
    def valid(self) -> bool:
        return True  # DictFieldView is always valid

    @property
    def default(self) -> Dict[str, str]:
        return self._default_value

    @property
    def value(self) -> Dict[str, str]: 
        return { key_var.get(): value_var.get() for key_var, value_var in self._entries.values() }

    @value.setter
    def value(self, v: Dict[str, str]) -> None: 
        # Create a list copy to avoid "dictionary changed size during iteration" error
        children_to_destroy = list(self._entries_frame.children.values())
        for child in children_to_destroy:
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
        elif inspect.isclass(field_type) and issubclass(field_type, SIVar):
            # Handle direct SIVar subclasses like TemperatureSIVar, AtfSiVar
            field_view_kwargs = kwargs.get("field_view_kwargs", {})
            field_view_kwargs["si_var_class"] = field_type
            kwargs["field_view_kwargs"] = field_view_kwargs
            # Create default instance - SIVar subclasses provide default constructors
            default_instance =  kwargs.get('default_value', None)
            if not default_instance:
                # For SIVar subclasses, always use explicit parameters to avoid linter confusion
                # The concrete subclasses like AtfSiVar, AttSiVar have defaults, but we'll be explicit
                if hasattr(field_type, '_si_meta') or (inspect.isclass(field_type) and issubclass(field_type, SIVar)):
                    # It's a concrete SIVar subclass - create with explicit defaults
                    kwargs['default_value'] = field_type(value=0, si_prefix=SIPrefix.NONE)
                else:
                    # Fallback for other types
                    try:
                        kwargs['default_value'] = field_type()
                    except TypeError:
                        kwargs['default_value'] = field_type(value=0, si_prefix=SIPrefix.NONE)
            return SITypeFieldView(slot, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
        elif get_origin(field_type) is Union and len(get_args(field_type)) == 2 and type(None) in get_args(field_type):
            # Handle Optional[SomeType] which is Union[SomeType, None]
            inner_type = get_args(field_type)[0] if get_args(field_type)[1] is type(None) else get_args(field_type)[1]
            
            # Check if it's Optional[SIVar subclass]
            if inspect.isclass(inner_type) and issubclass(inner_type, SIVar):
                # This is Optional[TemperatureSIVar] or similar SIVar subclass
                # Pass the subclass in field_view_kwargs for the factory
                field_view_kwargs = kwargs.get("field_view_kwargs", {})
                field_view_kwargs["si_var_class"] = inner_type
                kwargs["field_view_kwargs"] = field_view_kwargs
                return OptionalSITypeFieldView[float](slot, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
            elif inner_type is int:
                return NullableTypeFieldView[int](slot, int, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
            elif inner_type is float:
                return NullableTypeFieldView[float](slot, float, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
            elif inner_type is str:
                return NullableTypeFieldView[str](slot, str, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
            elif inner_type is Path:
                return OptionalPathFieldView(slot, field_name, parent_widget_name=parent_widget_name, top_scroll_frame=top_scroll_frame, **kwargs)
            else:
                # Fallback for unsupported Optional types
                raise TypeError(f"The field with name {field_name} has type Optional[{inner_type}], which is not supported")
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
    def valid(self) -> bool:
        # TupleFieldView is valid if all its child field views are valid
        return all(field.valid for field in self._fields)

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
        self._frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure the frame to expand its columns
        self._frame.grid_columnconfigure(0, weight=1)

        for i, field_view in enumerate(self._fields.values()):
            field_view.grid(row=i, column=0, padx=5, pady=5, sticky=ttk.NSEW)
            # Configure each row to expand vertically to distribute space evenly
            self._frame.grid_rowconfigure(i, weight=1)

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
    def valid(self) -> bool:
        # ObjectFieldView is valid if all its child field views are valid
        return all(field.valid for field in self._fields.values())

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
                 title: str, form_class: type, model_dict: dict | None = None, field_hooks: FieldHookRegistry = {}, use_scroll: bool = True):
        """
            args:
                model_dict: Is a dictionary that is one way bound target to source. So if the form gets updated, it updates the dictionary too, but not vice versa.
                use_scroll: Whether to use a scrolled frame (default True) or a regular frame (False)
        """
        assert attrs.has(form_class), "the form class provided has to be an attrs class"
        self._attrs_class: type = form_class
        self._converter = create_cattrs_converter_for_forms()
        self._field_view_factory = DynamicFieldViewFactory(self._converter, field_hooks)

        self._title = title
        self._view = FormWidgetView(parent_view, use_scroll=use_scroll)
        self._view.set_title(self._title)
        super().__init__(parent, self._view)
        # self._view.field_slot is the content frame (scrolled or regular) we need to scroll when using ScrolledFrame
        scroll_frame = self._view._content_frame if use_scroll else None
        self._attr_view = ObjectFieldView(self._view.field_slot, self._title, self._attrs_class, self._field_view_factory, top_scroll_frame=scroll_frame)
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
        # Check validity before allowing access to attrs_object
        if not self._attr_view.valid:
            raise ValueError("Cannot access attrs_object: form contains invalid fields")
        
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

    @property
    def is_valid(self) -> bool:
        """
        Check if all form fields are in a valid state
        """
        return self._attr_view.valid

    @form_data.setter
    def form_data(self, value: Dict[str, Any]):
        self._attr_view.value = value

    def set_to_default(self) -> None:
        self._attr_view.value = self._attr_view.default

        
class FormWidgetView(View):
    def __init__(self, master: ttk.Frame | View, use_scroll: bool = True, *args, **kwargs):
        self._use_scroll = use_scroll
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._title_frame = ttk.Frame(self)
        self._title = ttk.StringVar()
        self._title_label = ttk.Label(self._title_frame, textvariable=self._title, font=("Arial", 16))
        
        if self._use_scroll:
            self._content_frame = ScrolledFrame(self)
        else:
            self._content_frame = ttk.Frame(self)

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH, expand=True)
        self._title_frame.pack(fill=ttk.X, pady=10)
        self._title_label.pack()
        self._content_frame.pack(fill=ttk.BOTH, pady=10, expand=True)

        # TODO: refactor this, because we have now only one child inside the scroll frame
        for i, child in enumerate(self._content_frame.children.values()):
            child.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)

    @property
    def field_slot(self) -> ttk.Frame:
        return self._content_frame

    def set_title(self, title: str) -> None:
        self._title.set(title)

    def show(self) -> None:
        self.pack(expand=True, fill=ttk.BOTH)

    def hide(self) -> None:
        self.pack_forget()

