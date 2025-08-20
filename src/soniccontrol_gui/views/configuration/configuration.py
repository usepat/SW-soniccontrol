
import asyncio
import logging
from pathlib import Path
from tkinter import filedialog
from typing import Callable, List, Iterable, Optional, Tuple, Any, cast
import ttkbootstrap as ttk
import json
from sonic_protocol.python_parser import commands
from sonic_protocol.schema import SIPrefix, SIUnit
from soniccontrol.data_capturing.converter import create_cattrs_converter_for_basic_serialization
from soniccontrol.scripting.interpreter_engine import InterpreterEngine
from soniccontrol.scripting.new_scripting import NewScriptingFacade
from soniccontrol.updater import Updater
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.si_unit import SIVar, SIVarMeta
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView
from soniccontrol.scripting.scripting_facade import ScriptException, ScriptingFacade
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.utils.animator import Animator, DotAnimationSequence
from soniccontrol_gui.constants import sizes, ui_labels, file_dialog_opts
from soniccontrol.events import PropertyChangeEvent
from soniccontrol_gui.views.core.app_state import ExecutionState
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.constants import files
from async_tkinter_loop import async_handler

from soniccontrol_gui.widgets.form_widget import FormWidget
from soniccontrol_gui.widgets.message_box import MessageBox
    
import attrs
import cattrs


ATF_META = SIVarMeta(si_unit=SIUnit.HERTZ, si_prefix_min=SIPrefix.NONE, si_prefix_max=SIPrefix.MEGA)
ATT_META = SIVarMeta(si_unit=SIUnit.CELSIUS, si_prefix_min=SIPrefix.MILLI, si_prefix_max=SIPrefix.NONE)# Milli?



@attrs.define(auto_attribs=True)
class ATConfig:
    atf: SIVar[int] = attrs.field(factory=lambda: SIVar(value=0, si_prefix=SIPrefix.NONE, meta=ATF_META))
    atk: float = attrs.field(default=0)
    att: SIVar[float] = attrs.field(factory=lambda: SIVar(value=0.0, si_prefix=SIPrefix.NONE, meta=ATT_META))

@attrs.define(auto_attribs=True)
class TransducerConfig():
    # the name should not be stored inside the json file, but should be retrieved from the file name
    name: str = attrs.field(default="no name")
    init_script_path: Optional[Path] = attrs.field(default=None, metadata={"field_view_kwargs": file_dialog_opts.SONIC_SCRIPT})
    atconfigs: Tuple[ATConfig, ATConfig, ATConfig, ATConfig] = attrs.field(factory=lambda: tuple(ATConfig() for _ in range(4))) #type: ignore


class Configuration(UIComponent):
    CONFIGURATION_TASK_NAME = "configuring"

    def __init__(self, parent: UIComponent, device: SonicDevice, updater: Updater):
        self._logger = logging.getLogger(parent.logger.name + "." + Configuration.__name__)


        # Use the shared, lazily-created forms converter so other UI code can
        # reuse the same hooks and behavior (SIPrefix, SIUnit, SIVarMeta, SIVar).

        # Is this bad?
        self._converter = create_cattrs_converter_for_basic_serialization()

        # ensure that the name of the config does not get written into the json file
        omit_name_hook = cattrs.gen.make_dict_unstructure_fn(TransducerConfig, self._converter, name=cattrs.gen.override(omit=True))
        self._converter.register_unstructure_hook(TransducerConfig, omit_name_hook)

        self._logger.debug("Create Configuration Component")
        self._count_atk_atf = 4
        self._configs: List[TransducerConfig] = []
        self._current_transducer_config: Optional[int] = None
        self._device = device
        self._interpreter = InterpreterEngine(device, updater)

        self._view = ConfigurationView(parent.view, self, self._count_atk_atf)
        self._form = FormWidget(self, self._view.form_slot, "Transducer Config", TransducerConfig)
        super().__init__(parent, self._view, self._logger)

        def show_script_error(e):
            error = e.data["exception"]
            MessageBox.show_error(self._view.root, f"{error.__class__.__name__}: {str(error)}")

        self._interpreter.subscribe(InterpreterEngine.INTERPRETATION_ERROR, show_script_error)

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
        self._logger.info("Create empty configuration file at %s", files.TRANSDUCER_CONFIG_JSON)
        with open(files.TRANSDUCER_CONFIG_JSON, "w") as file:
            # Create 4 ATConfig objects with default values
            data_dict = self._converter.unstructure(TransducerConfig())
            json.dump(data_dict, file)

    def apply_migration(self, data_dict: dict):
        try:
            self._converter.structure(dict, TransducerConfig)
        except Exception as e:
            pass
        return

    def _load_config(self):
        if files.TRANSDUCER_CONFIG_FOLDER.exists() is False:
            self._logger.info("Create transducer config folder %s", files.TRANSDUCER_CONFIG_FOLDER)
            files.TRANSDUCER_CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
            self._create_default_config_file()

        if not any(files.TRANSDUCER_CONFIG_FOLDER.glob("*.json")):
            self._logger.info("No JSON files found in the transducer config folder")
            self._create_default_config_file()   

        self._logger.info("Load configuration from %s", files.TRANSDUCER_CONFIG_FOLDER)
        for json_file in files.TRANSDUCER_CONFIG_FOLDER.glob("*.json"):
            with open(json_file, "r") as file:
                try:
                    data_dict = json.load(file)
                    self.apply_migration(data_dict)
                    config = self._converter.structure(data_dict, TransducerConfig)
                    config.name = json_file.stem
                    self._configs.append(config)
                except Exception as e:
                    self._logger.error("Failed to load config from %s: %s", json_file, e)

        self._view.set_transducer_config_menu_items(map(lambda config: config.name, self._configs))
        self.current_transducer_config = 0 if len(self._configs) > 0 else None

    def _import_transducer_config(self):
        filename: str = filedialog.askopenfilename(**file_dialog_opts.JSON)
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
                config = self._converter.structure(data_dict, TransducerConfig)
                config.name = path.stem
                self._configs.append(config)
                self._view.set_transducer_config_menu_items(map(lambda config: config.name, self._configs))
            except Exception as e:
                self._logger.error("Failed to load config from %s: %s", path, e)

    def _save_config(self):
        transducer_config = self._form.attrs_object
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
                path = files.TRANSDUCER_CONFIG_FOLDER / f"{self._view._selected_config.get()}.json"
                if path.exists():
                    path.rename(files.TRANSDUCER_CONFIG_FOLDER / f"{transducer_config.name}.json")
                self._view._selected_config.set(transducer_config.name)
        path = files.TRANSDUCER_CONFIG_FOLDER / f"{transducer_config.name}.json"
        self._logger.info("Save configuration to %s", path)
        with open(path, "w") as file:
            data_dict = self._converter.unstructure(transducer_config)
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
            self._form.attrs_object = current_config

    def _on_transducer_config_selected(self):
         for i, transducer_config in enumerate(self._configs):
            if transducer_config.name == self._view.selected_transducer_config:
                self.current_transducer_config = i
                break

    def _add_transducer_config_template(self):
        self._form.attrs_object = TransducerConfig(name="no name")
        self._view._selected_config.set("no name")
        self.current_transducer_config = None

    def _delete_transducer_config(self):
        if self.current_transducer_config is None:
            return

        config = self._configs.pop(self.current_transducer_config)
        self._logger.info("Delete transducer config %s", config.name)
        path = files.TRANSDUCER_CONFIG_FOLDER / f"{config.name}.json"
        if path.exists():
            path.unlink()
        self._view.set_transducer_config_menu_items(map(lambda config: config.name, self._configs))
        self._add_transducer_config_template()

    @async_handler
    async def _submit_transducer_config(self):
        self._logger.info("Submit Transducer Config")
        
        # Start animation
        animation = Animator(
            DotAnimationSequence(ui_labels.CONFIGURING_LABEL), 
            self._view.set_loading_label, 
            2,
            done_callback=lambda: self._view.set_loading_label("")
        )
        animation.run(num_repeats=-1)
        
        # Send data
        config: TransducerConfig = self._form.attrs_object
        for i, atconfig in enumerate(config.atconfigs):
            # i+1 because atfs start at 1 and not 0.
            # SIVar holds the primitive in .value; device commands expect primitives.
            await self._device.execute_command(commands.SetAtf(i+1, atconfig.atf.to_prefix(SIPrefix.NONE)))
            await self._device.execute_command(commands.SetAtk(i+1, atconfig.atk))
            await self._device.execute_command(commands.SetAtt(i+1, atconfig.att.to_prefix(SIPrefix.NONE)))

        if config.init_script_path is not None:
            await self._execute_init_script(config.init_script_path)
        
        await animation.stop()
    

    async def _execute_init_script(self, script_file_path: Path):
        with script_file_path.open(mode="r") as f:
            script = f.read()

        self._logger.info("Execute init file")
        self._logger.debug("Init file:\n%s", script)
        scripting: ScriptingFacade = NewScriptingFacade()
        try:
            runnable_script = scripting.parse_script(script)
        except ScriptException as error:
            MessageBox.show_error(self._view.root, f"{error.__class__.__name__}: {str(error)}")
            return
        else: 
            self._interpreter.script = runnable_script
            self._interpreter.start()

        timeout = 5 * 60 # 5 minutes
        try:
            await asyncio.wait_for(self._interpreter.wait_for_script_to_halt(), timeout)
        except TimeoutError:
            MessageBox.show_error(self.view.root, f"The initialization script took longer to execute than {timeout} seconds")
        except asyncio.CancelledError:
            self._logger.error("The execution of the init file got interrupted")


    def on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        execution_state: ExecutionState = e.new_value.execution_state
        running_task: str | None = e.new_value.running_task
        is_executing_configuration_task = execution_state == ExecutionState.BUSY and running_task == Configuration.CONFIGURATION_TASK_NAME 
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

        self._loading_label = ttk.Label(
            self._config_frame, text=""
        )

        self._transducer_config_frame: ttk.Frame = ttk.Frame(
            self._config_frame
        )
        

    def _initialize_publish(self) -> None:
        self._config_frame.pack(expand=True, fill=ttk.BOTH)
        self._config_frame.columnconfigure(0, weight=sizes.DONT_EXPAND)
        self._config_frame.columnconfigure(1, weight=sizes.DONT_EXPAND)
        self._config_frame.columnconfigure(2, weight=sizes.EXPAND)
        self._config_frame.columnconfigure(3, weight=sizes.DONT_EXPAND)
        self._config_frame.columnconfigure(4, weight=sizes.DONT_EXPAND)
        self._config_frame.columnconfigure(5, weight=sizes.DONT_EXPAND)
        self._config_frame.rowconfigure(0, weight=sizes.DONT_EXPAND)
        self._config_frame.rowconfigure(1, weight=sizes.DONT_EXPAND)
        self._config_frame.rowconfigure(2, weight=sizes.EXPAND)
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

        self._loading_label.grid(row=1, column=0, columnspan=6,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING
        )

        self._transducer_config_frame.grid(row=2, column=0, columnspan=6, sticky=ttk.NSEW)

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

    def set_loading_label(self, text: str) -> None:
        self._loading_label.configure(text=text)

    @property
    def selected_transducer_config(self) -> str:
        return self._selected_config.get()

    @selected_transducer_config.setter
    def selected_transducer_config(self, value: str) -> None:
        self._selected_config.set(value)

    def set_transducer_config_menu_items(self, items: Iterable[str]) -> None:
        self._config_entry["values"] = list(items)

    @property
    def form_slot(self) -> ttk.Frame:
        return self._transducer_config_frame
    

