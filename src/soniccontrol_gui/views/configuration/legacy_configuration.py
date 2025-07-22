
import asyncio
import logging
from pathlib import Path
from tkinter import filedialog
from typing import Callable, List, Iterable, Optional
import attrs
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
import json
from sonic_protocol.python_parser import commands
from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.scripting.new_scripting import NewScriptingFacade
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
from soniccontrol.scripting.scripting_facade import ScriptingFacade
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.utils.animator import Animator, DotAnimationSequence
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol.events import PropertyChangeEvent
from soniccontrol_gui.views.core.app_state import ExecutionState
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.widgets.file_browse_button import FileBrowseButtonView
from soniccontrol_gui.constants import files
from async_tkinter_loop import async_handler
import marshmallow as marsh
from marshmallow_annotations.ext.attrs import AttrsSchema


from soniccontrol_gui.widgets.message_box import MessageBox

@attrs.define(auto_attribs=True)
class ATConfig:
    atk: int = attrs.field(default=0)
    atf: int = attrs.field(default=0)

@attrs.define(auto_attribs=True)
class TransducerConfig():
    atconfigs: List[ATConfig] = attrs.field()
    att: int = attrs.field(default=0)
    init_script_path: Optional[Path] = attrs.field(default=None)
    # We only use this for creating the dropdown menu in the UI
    # the name should not be stored inside the json file, but should be retrieved from the file name
    name: str = attrs.field(default="template", metadata={"exclude": True})



# schemas used for serialization deserialization
class ATConfigSchema(AttrsSchema):
    class Meta:
        target = ATConfig
        register_as_scheme = True

class TransducerConfigSchema(AttrsSchema):
    class Meta:
        target = TransducerConfig
        register_as_scheme = True
        exclude = ("name",)

    init_script_path = marsh.fields.Method(
        serialize="serialize_path", deserialize="deserialize_path", allow_none=True
    )

    def serialize_path(self, obj) -> str | None:
        return obj.init_script_path.as_posix() if obj.init_script_path else None

    def deserialize_path(self, value):
        return Path(value) if value else None
    
    

class ATConfigFrame(UIComponent):
    def __init__(self, parent: UIComponent, view_parent: View | ttk.Frame, index: int, **kwargs):
        self._index = index
        self._view = ATConfigFrameView(view_parent, index, **kwargs)
        super().__init__(parent, self._view)

    @property
    def value(self) -> ATConfig:
        return ATConfig(
            atk = int(self._view.atk),
            atf = int(self._view.atf),
        )
    
    @value.setter
    def value(self, config: ATConfig) -> None:
        self._view.atf = config.atf
        self._view.atk = config.atk


class ATConfigFrameView(View):
    def __init__(self, master: ttk.Frame, index: int, *args, **kwargs):
        parent_widget_name = kwargs.pop("parent_widget_name", "")
        self._widget_name = parent_widget_name + ".at_config." + str(index)
        self._index = index
        super().__init__(master, *args, **kwargs)

    def _initialize_children(self) -> None:
        self._atf_var = ttk.IntVar()
        self._atk_var = ttk.IntVar()
    
        self._atf_label = ttk.Label(self, text=f"ATF {self._index}")
        self._atk_label = ttk.Label(self, text=f"ATK {self._index}")

        self._atf_spinbox = ttk.Spinbox(self, textvariable=self._atf_var)
        self._atk_spinbox = ttk.Spinbox(self, textvariable=self._atk_var)

        WidgetRegistry.register_widget(self._atf_spinbox, "atf_entry", self._widget_name)
        WidgetRegistry.register_widget(self._atk_spinbox, "atk_entry", self._widget_name)

    def _initialize_publish(self) -> None:
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self._atf_label.grid(row=0, column=0, padx=10, pady=10, sticky=ttk.E)
        self._atf_spinbox.grid(row=0, column=1, padx=10, pady=10, sticky=ttk.W)

        self._atk_label.grid(row=1, column=0, padx=10, pady=10, sticky=ttk.E)
        self._atk_spinbox.grid(row=1, column=1, padx=10, pady=10, sticky=ttk.W)


    # Properties for atf
    @property
    def atf(self):
        return self._atf_var.get()

    @atf.setter
    def atf(self, value):
        self._atf_var.set(value)

    # Properties for atk
    @property
    def atk(self):
        return self._atk_var.get()

    @atk.setter
    def atk(self, value):
        self._atk_var.set(value)



#####

class LegacyConfiguration(UIComponent):
    NAME_CONFIGURATION_TASK = "configuring"

    def __init__(self, parent: UIComponent, device: SonicDevice, procedure_controller: ProcedureController):
        self._logger = logging.getLogger(parent.logger.name + "." + LegacyConfiguration.__name__)
        
        self._logger.debug("Create Configuration Component")
        self._count_atk_atf = 3
        self._configs: List[TransducerConfig] = []
        self._config_schema = TransducerConfigSchema()
        self._view = ConfigurationView(parent.view, self, self._count_atk_atf)
        self._current_transducer_config: Optional[int] = None
        self._device = device
        self._procedure_controller = procedure_controller
        super().__init__(parent, self._view, self._logger)
        self._view.set_save_config_command(self._save_config)
        self._view.set_transducer_config_selected_command(self._on_transducer_config_selected)
        self._view.set_add_transducer_config_command(self._add_transducer_config_template)
        self._view.set_import_transducer_config_command(self._import_transducer_config)
        self._view.set_submit_transducer_config_command(self._submit_transducer_config)
        self._view.set_delete_transducer_config_command(self._delete_transducer_config)
        self._load_config()

    @property
    def current_transducer_config(self) -> Optional[int]:
        return self._current_transducer_config

    @current_transducer_config.setter
    def current_transducer_config(self, value: Optional[int]) -> None:
        if value != self._current_transducer_config:
            self._current_transducer_config = value
            self._change_transducer_config()

    def _create_default_config_file(self):
        self._logger.info("Create empty configuration file at %s", files.LEGACY_TRANSDUCER_CONFIG_JSON)
        with open(files.LEGACY_TRANSDUCER_CONFIG_JSON, "w") as file:
            # Create 4 ATConfig objects with default values
            data_dict = self._config_schema.dump(TransducerConfig(atconfigs=[ATConfig() for _ in range(self._count_atk_atf)], att = 0)).data
            json.dump(data_dict, file)

    def _load_config(self):
        if files.LEGACY_TRANSDUCER_CONFIG_FOLDER.exists() is False:
            self._logger.info("Create transducer config folder %s", files.LEGACY_TRANSDUCER_CONFIG_FOLDER)
            files.LEGACY_TRANSDUCER_CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
            self._create_default_config_file()

        if not any(files.LEGACY_TRANSDUCER_CONFIG_FOLDER.glob("*.json")):
            self._logger.info("No JSON files found in the transducer config folder")
            self._create_default_config_file()   

        self._logger.info("Load configuration from %s", files.LEGACY_TRANSDUCER_CONFIG_FOLDER)
        for json_file in files.LEGACY_TRANSDUCER_CONFIG_FOLDER.glob("*.json"):
            with open(json_file, "r") as file:
                try:
                    data_dict = json.load(file)
                    config = self._config_schema.load(data_dict).data
                    config.name = json_file.stem
                    self._configs.append(config)
                except Exception as e:
                    self._logger.error("Failed to load config from %s: %s", json_file, e)

        self._view.set_transducer_config_menu_items(map(lambda config: config.name, self._configs))
        self.current_transducer_config = 0 if len(self._configs) > 0 else None

    def _import_transducer_config(self):
        kwargs = {"defaultextension": ".json", "filetypes": [("JSON files", "*.json")]} 
        filename: str = filedialog.askopenfilename(**kwargs)
        if filename == "." or filename == "" or isinstance(filename, (tuple)):
            return
        path = Path(filename)
        if path.exists() is False:
            self._logger.warn("There exists no file with the specified path")
            MessageBox.show_error(self._view.root, "There exists no file with the specified path")
            return
        with open(path, "r") as file:
            try:
                data_dict = json.load(file)
                config = self._config_schema.load(data_dict).data
                config.name = path.stem
                self._configs.append(config)
                self._view.set_transducer_config_menu_items(map(lambda config: config.name, self._configs))
            except Exception as e:
                self._logger.error("Failed to load config from %s: %s", path, e)

    def _save_config(self):
        transducer_config = TransducerConfig(
            name=self._view.transducer_config_name, 
            atconfigs=self._view.atconfigs, 
            att=self._view.att,
            init_script_path= self._view.init_script_path
        )
        if not self._validate_transducer_config_data(transducer_config):
            return

        if self.current_transducer_config is None:
            self._configs.append(transducer_config)
            self._view.set_transducer_config_menu_items(map(lambda config: config.name, self._configs))
            self.current_transducer_config = len(self._configs) - 1
        else:
            self._configs[self.current_transducer_config] = transducer_config
            self._view.set_transducer_config_menu_items(map(lambda config: config.name, self._configs))
            if transducer_config.name != self._view._selected_config.get():
                path = files.LEGACY_TRANSDUCER_CONFIG_FOLDER / f"{self._view._selected_config.get()}.json"
                if path.exists():
                    path.rename(files.LEGACY_TRANSDUCER_CONFIG_FOLDER / f"{transducer_config.name}.json")
                self._view._selected_config.set(transducer_config.name)
        path = files.LEGACY_TRANSDUCER_CONFIG_FOLDER / f"{transducer_config.name}.json"
        self._logger.info("Save configuration to %s", path)
        with open(path, "w") as file:
            data_dict = self._config_schema.dump(transducer_config).data
            json.dump(data_dict, file)

    def _validate_transducer_config_data(self, transducer_config: TransducerConfig) -> bool:            
        if self.current_transducer_config is None and any(map(lambda tconfig: tconfig.name == transducer_config.name, self._configs)):
            self.logger.warn("config with the same name already exists")
            MessageBox.show_error(self._view.root, "config with the same name already exists")
            return False
        if transducer_config.init_script_path is not None and not transducer_config.init_script_path.exists():
            self.logger.warn("there exists no init script with the specified path")
            MessageBox.show_error(self._view.root, "there exists no init script with the specified path")
            return False
        return True

    def _change_transducer_config(self):
        if self.current_transducer_config is None:
            self._view.selected_transducer_config = "none selected"
            self._add_transducer_config_template()
        else:
            current_config = self._configs[self.current_transducer_config]
            self._view.selected_transducer_config = current_config.name
            self._view.transducer_config_name = current_config.name
            self._view.atconfigs = current_config.atconfigs
            self._view.att = current_config.att
            self._view.init_script_path = current_config.init_script_path

    def _on_transducer_config_selected(self):
         for i, transducer_config in enumerate(self._configs):
            if transducer_config.name == self._view.selected_transducer_config:
                self.current_transducer_config = i
                break

    def _add_transducer_config_template(self):
        self._view.atconfigs = [ATConfig()] * self._count_atk_atf
        self._view.att = 0
        self._view.transducer_config_name = "no name"
        self._view.init_script_path = None
        self._view._selected_config.set("no name")
        self.current_transducer_config = None

    def _delete_transducer_config(self):
        if self.current_transducer_config is None:
            return

        config = self._configs.pop(self.current_transducer_config)
        self._logger.info("Delete transducer config %s", config.name)
        path = files.LEGACY_TRANSDUCER_CONFIG_FOLDER / f"{config.name}.json"
        if path.exists():
            path.unlink()
        self._view.set_transducer_config_menu_items(map(lambda config: config.name, self._configs))
        self._add_transducer_config_template()

    @async_handler
    async def _submit_transducer_config(self):
        self._logger.info("Submit Transducer Config")
        
        # Start animation
        animation = Animator(
            DotAnimationSequence(ui_labels.SEND_LABEL), 
            self._view.set_submit_config_button_label, 
            2,
            done_callback=lambda: self._view.set_submit_config_button_label(ui_labels.SEND_LABEL)
        )
        animation.run(num_repeats=-1)
        
        # Send data
        for i, atconfig in enumerate(self._view.atconfigs, start=1):
            await self._device.execute_command(commands.SetAtf(i, atconfig.atf))
            await self._device.execute_command(commands.SetAtk(i, atconfig.atk))

        await self._device.execute_command(commands.SetAtt(1, self._view.att))

        task = asyncio.create_task(self._interpreter_engine())

        # add stop animation callback
        @async_handler
        async def stop_animation(_task):
            await animation.stop()
        task.add_done_callback(stop_animation)

    async def _interpreter_engine(self):
        assert(self._current_transducer_config is not None)

        script_file_path = self._configs[self._current_transducer_config].init_script_path
        if script_file_path is None:
            return

        with script_file_path.open(mode="r") as f:
            script = f.read()

        self._logger.info("Execute init file")
        self._logger.debug("Init file:\n%s", script)
        scripting: ScriptingFacade = NewScriptingFacade()
        interpreter = scripting.parse_script(script)

        assert False, "need to implement stuff"


    def on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        execution_state: ExecutionState = e.new_value.execution_state
        executing_task: str | None = e.new_value.executing_task
        is_executing_configuration_task = execution_state == ExecutionState.BUSY and executing_task == LegacyConfiguration.NAME_CONFIGURATION_TASK 
        enabled = execution_state == ExecutionState.IDLE or is_executing_configuration_task
        self._view.set_submit_config_button_enabled(enabled)



class ConfigurationView(TabView):
    def __init__(self, master: ttk.Frame, presenter: UIComponent, count_atk_atf: int, *args, **kwargs):
        self._presenter = presenter
        self._count_atk_atf = count_atk_atf
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.SETTINGS_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.CONFIGURATION_TAB

    def _initialize_children(self) -> None:
        tab_name = "configuration"

        self._config_frame: ttk.Frame = ttk.Frame(self)
        self._add_config_button: ttk.Button = ttk.Button(
            self._config_frame,
            text=ui_labels.NEW_LABEL,
            style=ttk.DARK,
            # image=utils.ImageLoader.load_image(
            #     images.PLUS_ICON_WHITE, sizes.BUTTON_ICON_SIZE
            # ),
        )
        self._import_config_button: ttk.Button = ttk.Button(
            self._config_frame,
            text=ui_labels.IMPORT_LABEL,
            style=ttk.DARK,
        )
        self._selected_config: ttk.StringVar = ttk.StringVar()
        self._config_entry: ttk.Combobox = ttk.Combobox(
            self._config_frame, textvariable=self._selected_config, style=ttk.DARK
        )
        self._config_entry["state"] = "readonly" # prevent typing a value
        self._save_config_button: ttk.Button = ttk.Button(
            self._config_frame, text=ui_labels.SAVE_LABEL, style=ttk.DARK
        )
        self._submit_config_button: ttk.Button = ttk.Button(
            self._config_frame, text=ui_labels.SEND_LABEL, style=ttk.SUCCESS
        )
        self._delete_config_button: ttk.Button = ttk.Button(
            self._config_frame, text=ui_labels.DELETE_LABEL, style=ttk.SUCCESS
        )

        WidgetRegistry.register_widget(self._add_config_button, "add_config_button", tab_name)
        WidgetRegistry.register_widget(self._import_config_button, "import_config_button", tab_name)
        WidgetRegistry.register_widget(self._config_entry, "config_entry", tab_name)
        WidgetRegistry.register_widget(self._save_config_button, "save_config_button", tab_name)
        WidgetRegistry.register_widget(self._submit_config_button, "submit_config_button", tab_name)
        WidgetRegistry.register_widget(self._delete_config_button, "delete_config_button", tab_name)

        self._transducer_config_frame: ttk.Frame = ttk.Frame(
            self._config_frame
        )
        self._config_name: ttk.StringVar = ttk.StringVar()
        self._config_name_textbox: ttk.Entry = ttk.Entry(
            self._transducer_config_frame, textvariable=self._config_name
        )
        self._atconfigs_frame: ScrolledFrame = ScrolledFrame(self._transducer_config_frame)
        self._atconfig_frames: List[ATConfigFrame] = []
        for i in range(0, self._count_atk_atf):
            at_config_frame = ATConfigFrame(self._presenter, self._atconfigs_frame, i, parent_widget_name=tab_name)
            self._atconfig_frames.append(at_config_frame)
        
        self._att_var = ttk.IntVar()
        self._att_label = ttk.Label( self._atconfigs_frame, text="ATT")
        self._att_spinbox = ttk.Spinbox( self._atconfigs_frame, textvariable=self._att_var)
        WidgetRegistry.register_widget(self._att_spinbox, "att_entry", tab_name)

        self._browse_script_init_button: FileBrowseButtonView = FileBrowseButtonView(
            self._transducer_config_frame, 
            tab_name,
            text=ui_labels.SPECIFY_PATH_LABEL, 
            style=ttk.DARK,
        )

    def _initialize_publish(self) -> None:
        self._config_frame.pack(expand=True, fill=ttk.BOTH)
        self._config_frame.columnconfigure(0, weight=sizes.DONT_EXPAND)
        self._config_frame.columnconfigure(1, weight=sizes.EXPAND)
        self._config_frame.columnconfigure(2, weight=sizes.DONT_EXPAND)
        self._config_frame.columnconfigure(3, weight=sizes.DONT_EXPAND)
        self._config_frame.columnconfigure(4, weight=sizes.DONT_EXPAND)
        self._config_frame.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self._config_frame.rowconfigure(1, weight=sizes.EXPAND)
        self._add_config_button.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._import_config_button.grid(
            row=0,
            column=1,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._config_entry.grid(
            row=0,
            column=2,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._save_config_button.grid(
            row=0,
            column=3,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._submit_config_button.grid(
            row=0,
            column=4,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._delete_config_button.grid(
            row=0,
            column=5,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )

        self._transducer_config_frame.grid(row=1, column=0, columnspan=5, sticky=ttk.NSEW)
        self._transducer_config_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._transducer_config_frame.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self._transducer_config_frame.rowconfigure(1, weight=sizes.EXPAND)
        self._transducer_config_frame.rowconfigure(2, weight=sizes.DONT_EXPAND)
        self._config_name_textbox.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )
        self._atconfigs_frame.grid(
            row=1,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.NSEW,
        )
        for i, atconfig_frame in enumerate(self._atconfig_frames):
            atconfig_frame.view.grid(row=i, column=0, padx=sizes.MEDIUM_PADDING, pady=sizes.MEDIUM_PADDING, sticky=ttk.EW)

        next_row = len(self._atconfig_frames)          # first free row under the AT/AF pairs

        self._att_label.grid(
            row=next_row,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW
        )

        self._att_spinbox.grid(
            row=next_row,
            column=1,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW
        )

        self._browse_script_init_button.grid(
            row=2,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
            sticky=ttk.EW,
        )

    def set_save_config_command(self, command: Callable[[], None]) -> None:
        self._save_config_button.configure(command=command)

    def set_transducer_config_selected_command(self, command: Callable[[], None]) -> None:
        self._config_entry.bind("<<ComboboxSelected>>", lambda _: command())

    def set_add_transducer_config_command(self, command: Callable[[], None]) -> None:
        self._add_config_button.configure(command=command)

    def set_import_transducer_config_command(self, command: Callable[[], None]) -> None:
        self._import_config_button.configure(command=command)

    def set_submit_transducer_config_command(self, command: Callable[[], None]) -> None:
        self._submit_config_button.configure(command=command)

    def set_delete_transducer_config_command(self, command: Callable[[], None]) -> None:
        self._delete_config_button.configure(command=command)

    def set_submit_config_button_enabled(self, enabled: bool) -> None:
        self._submit_config_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    def set_submit_config_button_label(self, text: str) -> None:
        self._submit_config_button.configure(text=text)

    @property 
    def atconfigs(self) -> List[ATConfig]:
        return list(map(lambda x: x.value, self._atconfig_frames))
    
    @property
    def att(self) -> int:
        return self._att_var.get()
    
    @att.setter
    def att(self, att: int) -> None:
        self._att_var.set(att)

    @atconfigs.setter
    def atconfigs(self, values: Iterable[ATConfig]) -> None:
        for i, atconfig in enumerate(values):
            self._atconfig_frames[i].value = atconfig

    @property
    def init_script_path(self) -> Optional[Path]:
        return self._browse_script_init_button.path

    @init_script_path.setter
    def init_script_path(self, value: Optional[Path]) -> None:
        self._browse_script_init_button.path = value

    @property
    def selected_transducer_config(self) -> str:
        return self._selected_config.get()

    @selected_transducer_config.setter
    def selected_transducer_config(self, value: str) -> None:
        self._selected_config.set(value)

    def set_transducer_config_menu_items(self, items: Iterable[str]) -> None:
        self._config_entry["values"] = list(items)
    
    @property
    def transducer_config_name(self) -> str:
        return self._config_name.get()

    @transducer_config_name.setter
    def transducer_config_name(self, value: str) -> None:
        self._config_name.set(value)


