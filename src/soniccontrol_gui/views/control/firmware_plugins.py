from typing import Callable, Iterable, cast
import attrs
import ttkbootstrap as ttk
from async_tkinter_loop import async_handler

from soniccontrol.firmware_plugin_api.discovery import discover_firmware_plugins
from soniccontrol.firmware_plugin_api.plugin_endpoints import FirmwarePluginEndpoints, VarDef, VarType
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.view import TabView, View
from soniccontrol_gui.widgets.form_widget import FormWidget
from soniccontrol_gui.resources import images


class ActionList(UIComponent):
    def __init__(self, parent: UIComponent, slot: View, plugin_endpoints: FirmwarePluginEndpoints):
        self._plugin_endpoints = plugin_endpoints
        self._view = ActionListView(slot)
        super().__init__(parent, self._view)
        self._add_actions()

    def _add_actions(self):
        for action_name in self._plugin_endpoints.action_defs:
            async def do_action(action_name=action_name):
                await self._plugin_endpoints.do_action(action_name)

            self._view.add_action(action_name, async_handler(do_action))


class ActionListView(View):
    def __init__(self, master: ttk.Window | View, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._scroll_frame = ttk.ScrolledFrame(self)

    def _initialize_publish(self) -> None:
        self.pack(fill=ttk.BOTH)
        self._scroll_frame.pack(fill=ttk.BOTH)

    def add_action(self, text: str, command: Callable[[], None]) -> None:
        ttk.Button(self._scroll_frame, text=text, command=command).pack(
            side=ttk.BOTTOM, fill=ttk.X, pady=sizes.MEDIUM_PADDING)


def get_attrs_class_for_plugin(plugin_name: str, var_defs: dict[str, VarDef]) -> type:
    def create_attr_field(var_type: type[VarType], is_writable: bool):
        metadata = {"field_view_kwargs": {"editable": is_writable}}
        if var_type == bool:
            return attrs.field(type=bool, default=False, metadata=metadata)
        elif var_type == int:
            return attrs.field(type=int, default=0, metadata=metadata)
        elif var_type == float:
            return attrs.field(type=float, default=0.0, metadata=metadata)
        elif var_type == str:
            return attrs.field(type=str, factory=str, metadata=metadata)
        else:
            raise NotImplementedError()

    return attrs.make_class(plugin_name, {
        var_name: create_attr_field(var_def.var_type, var_def.is_writable) 
        for var_name, var_def in var_defs.items()
    })


class FirmwarePluginsTab(UIComponent):
    @attrs.define()
    class PluginControls:
        endpoints: FirmwarePluginEndpoints
        vars_form: FormWidget
        action_list: ActionList

    def __init__(self, parent: UIComponent, device: SonicDevice):
        self._view = FirmwarePluginsTabView(parent.view) 
        self._device = device
        self._plugin_controls: dict[str, FirmwarePluginsTab.PluginControls] = {}
        super().__init__(parent, self._view)
        self._view.set_plugin_selected_command(async_handler(self._display_selected_plugin))
        self._view.set_read_vars_command(async_handler(self._fetch_vars))
        self._view.set_write_vars_command(async_handler(self._assign_vars))
        self.top_level_window.pass_loading_task(self._discover_plugins())

    async def _discover_plugins(self):
        plugin_endpoints = await discover_firmware_plugins(self._device)

        for name, endpoints in plugin_endpoints.items():
            vars_form = FormWidget(
                self, 
                self._view.vars_frame, 
                "vars", 
                get_attrs_class_for_plugin(name, endpoints.var_defs), 
                "plugin_vars_form"
            )
            vars_form.view.hide()

            action_list = ActionList(self, self._view.actions_frame, endpoints) # type: ignore

            self._plugin_controls[name] = FirmwarePluginsTab.PluginControls(
                endpoints,
                vars_form,
                action_list
            )

        self._view.set_plugin_combobox_items(self._plugin_controls.keys())

    async def _display_selected_plugin(self):
        for controls in self._plugin_controls.values():
            controls.vars_form.view.hide()
            controls.action_list.view.hide()

        plugin_name = self._view.selected_plugin
        self._plugin_controls[plugin_name].vars_form.view.show()
        self._plugin_controls[plugin_name].action_list.view.show()
        await self._fetch_vars()

    async def _fetch_vars(self):
        plugin_name = self._view.selected_plugin
        vars_form =self._plugin_controls[plugin_name].vars_form
        endpoints = self._plugin_controls[plugin_name].endpoints
        vars_form.form_data = await endpoints.fetch_vars()

    async def _assign_vars(self):
        plugin_name = self._view.selected_plugin
        vars_form =self._plugin_controls[plugin_name].vars_form
        endpoints = self._plugin_controls[plugin_name].endpoints
        await endpoints.assign_vars(vars_form.form_data)


class FirmwarePluginsTabView(TabView):
    def __init__(self, master: ttk.Window | View, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.SCRIPT_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.FIRMWARE_PLUGINS_LABEL

    def _initialize_children(self) -> None:
        self._selected_plugin_var = ttk.StringVar()

        self._control_frame = ttk.Frame(self)
        self._plugin_cbx = ttk.Combobox(self._control_frame, textvariable=self._selected_plugin_var)
        self._fetch_vars_button = ttk.Button(self._control_frame, text=ui_labels.FETCH_LABEL)
        self._assign_vars_button = ttk.Button(self._control_frame, text=ui_labels.WRITE_LABEL)

        self._plugin_controls_frame = ttk.Frame(self)
        self._var_form_slot = ttk.LabelFrame(self._plugin_controls_frame , text=ui_labels.VARIABLES)
        self._action_slot = ttk.LabelFrame(self._plugin_controls_frame , text=ui_labels.ACTIONS)

    def _initialize_publish(self) -> None:
        self._control_frame.pack(side=ttk.TOP, fill=ttk.X, pady=sizes.MEDIUM_PADDING)
        self._assign_vars_button.pack(side=ttk.RIGHT)
        self._fetch_vars_button.pack(side=ttk.RIGHT, padx=sizes.MEDIUM_PADDING)
        self._plugin_cbx.pack(side=ttk.LEFT)

        self._plugin_controls_frame.pack(fill=ttk.BOTH, pady=sizes.MEDIUM_PADDING, padx=sizes.MEDIUM_PADDING)
        self._plugin_controls_frame.grid_rowconfigure(index=0, weight=2, pad=sizes.SMALL_PADDING)
        self._plugin_controls_frame.grid_rowconfigure(index=1, weight=1, pad=sizes.SMALL_PADDING)
        self._var_form_slot.grid(row=0, column=0)
        self._action_slot.grid(row=1, column=0)

    @property
    def selected_plugin(self) -> str:
        return self._selected_plugin_var.get()

    @selected_plugin.setter
    def selected_plugin(self, value: str) -> None:
        self._selected_plugin_var.set(value)

    def set_plugin_combobox_items(self, items: Iterable[str]) -> None:
        self._plugin_cbx["values"] = list(items)

    def set_plugin_selected_command(self, command: Callable[[], None]) -> None:
        self._plugin_cbx.bind("<<ComboboxSelected>>", lambda _: command())

    @property
    def vars_frame(self) -> ttk.Frame:
        return cast(ttk.Frame, self._var_form_slot)

    @property
    def actions_frame(self) -> ttk.Frame:
        return cast(ttk.Frame, self._action_slot)
        
    def set_write_vars_command(self, command: Callable[[], None]) -> None:
        self._assign_vars_button.config(command=command)

    def set_read_vars_command(self, command: Callable[[], None]) -> None:
        self._fetch_vars_button.config(command=command)
