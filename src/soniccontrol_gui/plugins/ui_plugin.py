from typing import List, Set, Optional, Callable
from pathlib import Path

import attrs
import abc
import tkinter as tk
import ttkbootstrap as ttk

# --- your existing imports (kept as-is even if unused in this snippet) ---
from sonic_protocol.protocol_list import ProtocolList
from sonic_protocol.protocol import LatestProtocol
from sonic_protocol.schema import DeviceType
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.view import TabView, TkinterView, View
from soniccontrol_gui.views.core.device_window import DeviceWindow, KnownDeviceWindow
from importlib.metadata import entry_points
# ------------------------------------------------------------------------

# TODO add UIPluginSlotComponent and PluginSlotRegistry


# FACTORY now takes master + parent_component so views are born with the correct master
class UIComponentFactory(abc.ABC):
    @abc.abstractmethod
    def __call__(self, master, parent: UIComponent, *args, **kwargs) -> UIComponent:
        ...


class UIPluginSlotView(View):
    """
    A container that either shows plugin components as tabs, or stacked with a scroll.
    It *creates* plugin components so their views are constructed with the correct master.
    """
    def __init__(self, master, plugin_factories: list[UIComponentFactory], parent_component: UIComponent, *args, **kwargs):
        self._plugin_factories = plugin_factories
        self._parent_component = parent_component
        self._tabs = kwargs.pop("tabs", False)
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._plugin_components: list[UIComponent] = []

        if self._tabs:
            self._notebook = ttk.Notebook(self)
            self._notebook.pack(fill=tk.BOTH, expand=True)

            for factory in self._plugin_factories:
                comp = factory(self._notebook, self._parent_component)
                self._plugin_components.append(comp)

                # make sure the widget is really a Tk widget and has the right master
                widget = comp.view
                if not isinstance(widget, (tk.Widget)):
                    raise TypeError(f"Plugin view {widget!r} is not a Tk widget")
                if widget.master is not self._notebook:
                    raise RuntimeError("Plugin view master must be the Notebook")

                # only pass image if it is a real PhotoImage
                img = getattr(widget, "image", None)
                kwargs = {}
                if isinstance(img, tk.PhotoImage):  # or ttkbootstrap Image if you use that wrapper
                    kwargs["image"] = img

                title = getattr(comp, "tab_title", getattr(widget, "tab_title", "Plugin"))
                self._notebook.add(widget, text=title, **kwargs)

        else:
            canvas = tk.Canvas(self)  # tk.Canvas (not ttk)
            scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
            self._scrollable_frame = ttk.Frame(canvas)

            self._scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window((0, 0), window=self._scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            for factory in self._plugin_factories:
                comp = factory(self._scrollable_frame, self._parent_component)
                self._plugin_components.append(comp)
                comp.view.pack(fill=tk.X, expand=True, pady=4)

    def _initialize_publish(self) -> None:
        pass


@attrs.define(hash=True)
class UIPlugin:
    slot_name: str
    component_factory: UIComponentFactory


class UIPluginSlotComponent(UIComponent):
    """
    UIComponent wrapper for the slot view. It does NOT auto-pack; caller decides placement.
    """
    def __init__(self, parent: UIComponent, ui_plugins: list[UIPlugin], *, master=None, **kwargs):
        master = master or parent.view  # default to parent.view if not provided
        factories = [p.component_factory for p in ui_plugins]
        self._view = UIPluginSlotView(master, factories, parent, **kwargs)
        super().__init__(parent, self._view)


# Optional global registry (as you had)
class UIPluginRegistry:
    _registered_plugins: Set[UIPlugin] = set()

    @staticmethod
    def register_ui_plugin(plugin: UIPlugin):
        UIPluginRegistry._registered_plugins.add(plugin)

    @staticmethod
    def get_ui_plugins() -> List[UIPlugin]:
        return list(UIPluginRegistry._registered_plugins)


# --- TEST PLUGIN VIEWS ---
class TestPluginView1(View):
    def _initialize_children(self) -> None:
        label = ttk.Label(self, text="Test Plugin 1")
        label.pack(padx=10, pady=10)

    def _initialize_publish(self) -> None:
        pass

    @property
    def tab_title(self):
        return "Plugin 1"


class TestPluginView2(View):
    def _initialize_children(self) -> None:
        label = ttk.Label(self, text="Test Plugin 2")
        label.pack(padx=10, pady=10)

    def _initialize_publish(self) -> None:
        pass

    @property
    def tab_title(self):
        return "Plugin 2"


class TestPluginView3(View):
    def _initialize_children(self) -> None:
        label = ttk.Label(self, text="Test Plugin 3")
        label.pack(padx=10, pady=10)

    def _initialize_publish(self) -> None:
        pass

    @property
    def tab_title(self):
        return "Plugin 3"


# --- TEST PLUGIN COMPONENTS (accept master, parent_component) ---
class TestPluginComponent1(UIComponent):
    def __init__(self, master, parent_component: UIComponent):
        self._view = TestPluginView1(master)
        super().__init__(parent_component, self._view)

    @property
    def tab_title(self):
        return self._view.tab_title


class TestPluginComponent2(UIComponent):
    def __init__(self, master, parent_component: UIComponent):
        self._view = TestPluginView2(master)
        super().__init__(parent_component, self._view)

    @property
    def tab_title(self):
        return self._view.tab_title


class TestPluginComponent3(UIComponent):
    def __init__(self, master, parent_component: UIComponent):
        self._view = TestPluginView3(master)
        super().__init__(parent_component, self._view)

    @property
    def tab_title(self):
        return self._view.tab_title


class TestPluginComponent1Factory(UIComponentFactory):
    def __call__(self, master, parent: UIComponent, *args, **kwargs) -> UIComponent:
        return TestPluginComponent1(master, parent)


class TestPluginComponent2Factory(UIComponentFactory):
    def __call__(self, master, parent: UIComponent, *args, **kwargs) -> UIComponent:
        return TestPluginComponent2(master, parent)


class TestPluginComponent3Factory(UIComponentFactory):
    def __call__(self, master, parent: UIComponent, *args, **kwargs) -> UIComponent:
        return TestPluginComponent3(master, parent)


# # Register test plugins in the "ConnectionWindow" slot
# UIPluginRegistry.register_ui_plugin(
#     UIPlugin("ConnectionWindow", TestPluginComponent1Factory())
# )
# UIPluginRegistry.register_ui_plugin(
#     UIPlugin("ConnectionWindow", TestPluginComponent2Factory())
# )
# UIPluginRegistry.register_ui_plugin(
#     UIPlugin("ConnectionWindow", TestPluginComponent3Factory())
# )


def register_ui_plugins():
    eps = entry_points()
    for ep in eps.select(group="soniccontrol_gui.ui_plugins"):
        ui_plugin = ep.load()
        UIPluginRegistry.register_ui_plugin(ui_plugin)