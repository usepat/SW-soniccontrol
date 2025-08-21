import tkinter as tk
from typing import Callable, Optional, Type, Any
import ttkbootstrap as ttk
import asyncio

from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import View
from soniccontrol_gui.widgets.form_widget import DynamicFieldViewFactory
from soniccontrol.data_capturing.converter import create_cattrs_converter_for_forms


class DynamicUserSelection(UIComponent):
    """
    A dynamic user selection widget that adapts its UI based on the desired result type.
    
    Uses the form widget factory to automatically create appropriate input fields for any type.
    The UI is fully initialized during __init__ for immediate use.
    
    Usage examples:
    - selection = DynamicUserSelection(parent, "Enter number:", "Input", int)
    - selection = DynamicUserSelection(parent, "Choose frequency:", "Input", AtfSiVar)
    - selection = DynamicUserSelection(parent, "Custom value:", "Input", MyEnum)
    """
    
    def __init__(self, root, message: str, title: str, target_type: Type):
        """
        Initialize the dynamic user selection widget.
        
        Args:
            root: Parent widget
            message: Message to display to user
            title: Window title
            target_type: The type of value to collect from the user
        """
        self._target_type = target_type
        
        self._view = DynamicUserSelectionView(
            root, 
            message, title, target_type
        )
        self._answer = asyncio.Future()
        super().__init__(None, self._view)
        
        # Set up callbacks
        def close_callback():
            if not self._answer.done():
                self._answer.set_result(None)
        self._view.add_close_callback(close_callback)
        
        def ok_callback():
            if not self._answer.done():
                try:
                    result = self._view.get_result()
                    self._answer.set_result(result)
                except Exception as e:
                    # Keep dialog open on validation error
                    self._view.show_error(str(e))
        self._view.add_ok_callback(ok_callback)

    async def wait_for_answer(self) -> Optional[Any]:
        """Wait for the user to provide an answer or cancel the dialog."""
        return await self._answer


class DynamicUserSelectionView(tk.Toplevel, View):  # type: ignore[misc]
    """View that uses form widget factory to create appropriate input fields."""
    WIDGET_NAME = "DynamicUserSelection"

    def __init__(self, root, message: str, title: str, target_type: Type, *args, **kwargs):
        # Initialize Toplevel first, then View
        super().__init__(root, *args, **kwargs)
        self.title(title)
        
        self._message = message
        self._target_type = target_type
        self._close_callback: Callable[[], None] = lambda: None
        self._ok_callback: Callable[[], None] = lambda: None
        
        # The field view that handles the actual input
        self._field_view = None
        self._error_label = None
        
        # Initialize UI immediately
        self._initialize_ui()
        
    def _initialize_ui(self):
        """Initialize the UI using form widget factory."""
        # Configure window
        self.resizable(False, False)
        if hasattr(self.master, 'winfo_toplevel'):
            self.transient(self.master.winfo_toplevel())
        self.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Message label
        ttk.Label(main_frame, text=self._message).pack(fill=tk.X, pady=(0, 10))
        
        # Create field view using form widget factory
        self._create_field_view(main_frame)
        
        # Error label (initially hidden)
        self._error_label = ttk.Label(main_frame, text="", foreground="red")
        self._error_label.pack(fill=tk.X, pady=(5, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT)
        
        # Set initial focus and center window
        self._set_initial_focus()
        self._center_window()
        
        WidgetRegistry.register_widget(self, self.WIDGET_NAME)
    
    def _create_field_view(self, parent):
        """Create the appropriate field view using the form widget factory."""
        try:
            # Create converter and field hooks for the factory
            converter = create_cattrs_converter_for_forms()
            field_hooks = {}
            factory = DynamicFieldViewFactory(converter, field_hooks)
            
            # Use the factory to create the appropriate field view
            self._field_view = factory.from_type(
                field_name=self._target_type.__name__, 
                field_type=self._target_type,
                slot=parent,
                parent_widget_name="user_selection",
            )
            
            # Pack the field view
            self._field_view.pack(fill=tk.X, pady=(0, 10))
            
        except Exception:
            # Fallback to simple text input if field view creation fails
            ttk.Label(parent, text=f"Enter {self._target_type.__name__}:", foreground="orange").pack(anchor=tk.W)
            self._fallback_var = tk.StringVar()
            self._field_view = ttk.Entry(parent, textvariable=self._fallback_var)
            self._field_view.pack(fill=tk.X, pady=(5, 10))
    
    def get_result(self) -> Any:
        """Get the result from the field view."""
        if self._field_view is None:
            raise ValueError("No field view available")
            
        if hasattr(self._field_view, 'value'):
            # Standard field view with value property
            return getattr(self._field_view, 'value')
        elif hasattr(self._field_view, 'get'):
            # Fallback Entry widget
            value_str = getattr(self._field_view, 'get')().strip()
            if not value_str:
                raise ValueError("Empty input")
            
            # Try to convert to the target type
            if self._target_type in (int, float):
                return self._target_type(value_str)
            elif self._target_type is str:
                return value_str
            else:
                # For unknown types, return string
                return value_str
        else:
            raise ValueError("Unable to get value from field view")
    
    def show_error(self, message: str):
        """Show an error message."""
        if self._error_label:
            self._error_label.config(text=message)
    
    def clear_error(self):
        """Clear any error message."""
        if self._error_label:
            self._error_label.config(text="")
    
    def add_close_callback(self, callback: Callable[[], None]):
        """Add a callback for when the dialog is closed."""
        self._close_callback = callback
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def add_ok_callback(self, callback: Callable[[], None]):
        """Add a callback for when OK is clicked."""
        self._ok_callback = callback
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.clear_error()
        self._close_callback()
        self.destroy()
    
    def _on_ok(self):
        """Handle OK button click."""
        self.clear_error()
        self._ok_callback()
        self.destroy()
    
    def _set_initial_focus(self):
        """Set initial focus to the input widget."""
        if self._field_view and hasattr(self._field_view, 'focus_set'):
            self._field_view.focus_set()
    
    def _center_window(self):
        """Center the window relative to the parent window."""
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        
        # Get parent window dimensions and position
        if self.master:
            parent_x = self.master.winfo_rootx()
            parent_y = self.master.winfo_rooty()
            parent_width = self.master.winfo_width()
            parent_height = self.master.winfo_height()
            
            # Calculate position to center relative to parent
            x = parent_x + (parent_width // 2) - (width // 2)
            y = parent_y + (parent_height // 2) - (height // 2)
        else:
            # Fallback to screen center if no parent
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
        
        self.geometry(f"{width}x{height}+{x}+{y}")

