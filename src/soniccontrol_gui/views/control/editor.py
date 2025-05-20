import logging
import pathlib
from tkinter import filedialog
from typing import Callable, Final, List, Optional, Tuple

import attrs
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText
from async_tkinter_loop import async_handler

from soniccontrol.data_capturing.capture_target import CaptureScriptArgs
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView
from soniccontrol.scripting.interpreter_engine import CurrentTarget, InterpreterEngine, InterpreterState
from soniccontrol.scripting.scripting_facade import ScriptException, ScriptingFacade
from soniccontrol_gui.constants import (sizes, scripting_cards_data,
                                                     ui_labels)
from soniccontrol.events import PropertyChangeEvent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.core.app_state import AppState, ExecutionState
from soniccontrol_gui.widgets.message_box import DialogOptions, MessageBox
from soniccontrol_gui.widgets.pushbutton import PushButtonView
from soniccontrol_gui.views.control.scriptingguide import ScriptingGuide
from soniccontrol_gui.resources import images
from soniccontrol_gui.constants import files


@attrs.define
class Script():
    name: str
    content: str

@attrs.define
class ScriptFile(CaptureScriptArgs):
    filepath: str = attrs.field(default="./script.sonic")
    text: str = attrs.field(default="")
    filetypes: List[Tuple[str, str]] = attrs.field(default=[("Text Files", "*.txt"), ("Sonic Script", "*.sonic")])
    default_extension: str = attrs.field(default=".sonic")
    logger: logging.Logger = attrs.field(default=logging.getLogger("ScriptFile"))

    def load_script(self, filepath: Optional[str] = None):
        if filepath is not None:
            self.filepath = filepath
        with pathlib.Path(self.filepath).open("r") as f:
            self.logger.info("Load script from %s", self.filepath)
            self.text = f.read()

    def save_script(self, filepath: Optional[str] = None):
        if filepath is not None:
            self.filepath = filepath
        with pathlib.Path(self.filepath).open("w") as f:
            self.logger.info("Save script to %s", self.filepath)
            f.write(self.text)

    @property
    def script_text(self) -> str:
        return self.text


class Editor(UIComponent):
    def __init__(self, parent: UIComponent, scripting: ScriptingFacade, script_file: ScriptFile, interpreter: InterpreterEngine, app_state: AppState):
        self._logger = logging.getLogger(parent.logger.name + "." + Editor.__name__)

        self._logger.debug("Create Editor")
        self._app_state = app_state
        self._scripting: ScriptingFacade = scripting
        self._script: ScriptFile = script_file
        self._interpreter = interpreter
        self._view = EditorView(parent.view)
        super().__init__(parent, self._view, self._logger)

        self._view.add_menu_command(ui_labels.LOAD_LABEL, self._on_load_script)
        self._view.add_menu_command(ui_labels.LOAD_EXAMPLE_LABEL, self._on_load_example_script)
        self._view.add_menu_command(ui_labels.SAVE_LABEL, self._on_save_script)
        self._view.add_menu_command(ui_labels.SAVE_AS_LABEL, self._on_save_as_script)
        self._view.set_scripting_guide_button_command(self._on_open_scripting_guide)
        def set_text() -> None:
            self._script.text = self._view.editor_text
        self._view.bind_editor_text(set_text)

        self._set_interpreter_state(self._interpreter.interpreter_state)
        # TODO: highlight errors in script
        self._interpreter.subscribe(InterpreterEngine.INTERPRETATION_ERROR, lambda e: self._handle_script_error(e.data["exception"]))
        self._interpreter.subscribe_property_listener(InterpreterEngine.PROPERTY_INTERPRETER_STATE, lambda e: self._set_interpreter_state(e.new_value))
        self._interpreter.subscribe_property_listener(InterpreterEngine.PROPERTY_CURRENT_TARGET, lambda e: self._set_current_target(e.new_value))
        self._app_state.subscribe_property_listener(AppState.EXECUTION_STATE_PROP_NAME, self.on_execution_state_changed)


        self.init_example_scripts()
        

    def init_example_scripts(self) -> None:
        if files.EXAMPLE_SCRIPT_DIR.exists() and any(files.EXAMPLE_SCRIPT_DIR.iterdir()):
            if any(file.suffix == ".sonic" for file in files.EXAMPLE_SCRIPT_DIR.iterdir()):
                self._logger.info("Example script directory exists and contains .sonic files.")
            else:
                self._logger.info("Example script directory exists but does not contain .sonic files.")
                return

        for script in files.EXAMPLE_SCRIPT_DIR.iterdir():
            if script.suffix == ".sonic":
                with script.open() as _script:
                    self._logger.info("Loaded example script: %s", script.name)
                    self.save_example_script(Script(name=script.stem, content=_script.read()))

    def save_example_script(self, script: Script) -> None:
        example_script = files.EXAMPLE_SCRIPT.with_name(files.EXAMPLE_SCRIPT.name  + "-" + script.name + ".sonic")
        if not example_script.parent.exists():
            example_script.parent.mkdir(parents=True, exist_ok=True)

        with open(example_script, "w") as file:
            file.write(script.content)

    def on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        execution_state: ExecutionState = e.new_value
        if execution_state == ExecutionState.BUSY_EXECUTING_SCRIPT:
            return
        elif execution_state == ExecutionState.IDLE:
            self._set_interpreter_state(self._interpreter.interpreter_state)
        else:
            self._view.start_pause_continue_button.configure(enabled=False)
            self._view.single_step_button.configure(enabled=False)
            self._view.stop_button.configure(enabled=False)
            self._view.editor_enabled = False

    def _set_current_target(self, target: CurrentTarget):
        self._view.highlight_line(target.line)
        self._view.current_task = target.task

    def _set_interpreter_state(self, interpreter_state: InterpreterState):
        self._interpreter_state = interpreter_state
        self._logger.info("Interpreterstate: %s", self._interpreter_state.name)
        match interpreter_state:
            case InterpreterState.READY:
                self._view.start_pause_continue_button.configure(
                    label=ui_labels.START_LABEL,
                    image=(images.PLAY_ICON_WHITE, sizes.BUTTON_ICON_SIZE),
                    command=self._on_start_script,
                    enabled=True
                )
                self._view.single_step_button.configure(
                    label=ui_labels.SINGLE_STEP_LABEL,
                    image=(images.FORWARDS_ICON_WHITE, sizes.BUTTON_ICON_SIZE),
                    command=self._on_single_step_script,
                    enabled=True
                )
                self._view.stop_button.configure(
                    label=ui_labels.STOP_LABEL,
                    image=(images.END_ICON_WHITE, sizes.BUTTON_ICON_SIZE),
                    command=self._on_stop_script,
                    enabled=False
                )
                self._view.editor_enabled = True
                self._app_state.execution_state = ExecutionState.IDLE

            case InterpreterState.RUNNING:
                self._view.start_pause_continue_button.configure(
                    label=ui_labels.PAUSE_LABEL,
                    image=(images.PAUSE_ICON_WHITE, sizes.BUTTON_ICON_SIZE),
                    command=self._on_pause_script,
                    enabled=True
                )
                self._view.single_step_button.configure(
                    enabled=False
                )
                self._view.stop_button.configure(
                    enabled=True
                )
                self._view.editor_enabled = False
                self._app_state.execution_state = ExecutionState.BUSY_EXECUTING_SCRIPT

            case InterpreterState.PAUSED:
                self._view.start_pause_continue_button.configure(
                    label=ui_labels.RESUME_LABEL,
                    image=(images.PLAY_ICON_WHITE, sizes.BUTTON_ICON_SIZE),
                    command=self._on_continue_script,
                    enabled=True
                )
                self._view.single_step_button.configure(
                    enabled=True
                )
                self._view.stop_button.configure(
                    enabled=True
                )
                self._view.editor_enabled = False
                self._app_state.execution_state = ExecutionState.IDLE

    def _on_load_script(self):
        filename: str = filedialog.askopenfilename(
            defaultextension=self._script.default_extension, 
            filetypes=self._script.filetypes,
        )
        if filename == "." or filename == "" or isinstance(filename, (tuple)):
            return
        
        self._script.load_script(filename)
        self._view.editor_text = self._script.text

    def _on_load_example_script(self):
        filename: str = filedialog.askopenfilename(
            defaultextension=".sonic",
            filetypes=[("Sonic Script", "*.sonic")],
            initialdir=files.SCRIPT_DIR
        )
        if filename == "." or filename == "" or isinstance(filename, (tuple)):
            return
        
        self._script.load_script(filename)
        self._view.editor_text = self._script.text

    def _on_save_as_script(self):
        filename: str = filedialog.asksaveasfilename(
            defaultextension=self._script.default_extension, 
            filetypes=self._script.filetypes
        )
        if filename == "." or filename == "" or isinstance(filename, (tuple)):
            return
        
        self._script.text = self._view.editor_text
        self._script.save_script(filename)

    def _on_save_script(self):
        if pathlib.Path(self._script.filepath).exists():
            self._script.text = self._view.editor_text
            self._script.save_script()
        else:
            self._on_save_as_script()

    def _on_open_scripting_guide(self):
        ScriptingGuide(self._view, self._view.editor_text_view, scripting_cards_data)


    def _try_parse_script(self) -> bool:
        self._script.text = self._view.editor_text
        try:
            self._interpreter.script =  self._scripting.parse_script(self._script.text)
            return True
        except ScriptException as e:
            self._handle_script_error(e)
            return False

    @async_handler
    async def _on_start_script(self):
        warning_message = MessageBox(self.view.root, "By pressing \"proceed\" you will start the script without **logging**. If you want to keep a log, please use the SonicMeasure tab and start a new experiment. Are you sure you want to proceed without logging?", "Are you sure?", [DialogOptions.CANCEL, DialogOptions.PROCEED])
        answer = await warning_message.wait_for_answer()
        if answer == DialogOptions.CANCEL:
            return
        elif answer == DialogOptions.PROCEED:
            pass
        else:
            assert False
        if not self._try_parse_script():
            return
            
        self._interpreter.start()

    @async_handler
    async def _on_single_step_script(self):
        if self._interpreter.interpreter_state == InterpreterState.READY:
            if not self._try_parse_script():
                return

        self._interpreter.single_step()

    @async_handler
    async def _on_stop_script(self):
        await self._interpreter.stop()

    def _on_continue_script(self):
        self._interpreter.start() 

    @async_handler
    async def _on_pause_script(self):
        await self._interpreter.pause()

    def _handle_script_error(self, e: ScriptException):
        self._view.highlight_line(e.line_begin, color_background="#ff2c2c")
        MessageBox.show_error(self._view.root, f"{e.__class__.__name__}: {str(e)}")
        


class EditorView(TabView):
    def __init__(self, master: ttk.Window, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.SCRIPT_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.SCRIPTING_LABEL

    def _initialize_children(self) -> None:
        tab_name = "editor"
        self._main_frame: ttk.Frame = ttk.Frame(self)

        SCRIPTING_PADDING: Final[tuple[int, int, int, int]] = (6, 1, 6, 7)
        self._scripting_frame: ttk.Labelframe = ttk.Labelframe(
            self._main_frame,
            text=ui_labels.SCRIPT_EDITOR_LABEL,
            padding=SCRIPTING_PADDING,
        )
        self._editor_text: ScrolledText = ScrolledText(
            self._scripting_frame, 
            autohide=True, 
        )
        WidgetRegistry.register_widget(self._editor_text, "text_editor", tab_name)

        self._script_status_frame: ttk.Frame = ttk.Frame(self)
        self._current_task_var = ttk.StringVar(value="")
        self._current_task_label: ttk.Label = ttk.Label(
            self._script_status_frame, textvariable=self._current_task_var, justify=ttk.CENTER, style=ttk.DARK
        )
        WidgetRegistry.register_widget(self._current_task_label, "current_task_label", tab_name)

        self._navigation_button_frame: ttk.Frame = ttk.Frame(self)
        self._start_pause_continue_button = PushButtonView(
            self._navigation_button_frame,
            compound=ttk.LEFT
        )
        self._single_step_button = PushButtonView(
            self._navigation_button_frame,
            compound=ttk.LEFT
        )
        self._stop_button = PushButtonView(
            self._navigation_button_frame,
            compound=ttk.LEFT
        )
        self._scripting_guide_button: ttk.Button = ttk.Button(
            self._navigation_button_frame,
            text=ui_labels.GUIDE_LABEL,
            style=ttk.INFO,
            image=ImageLoader.load_image_resource(images.INFO_ICON_WHITE, (13, 13)),
            compound=ttk.LEFT, 
        )
        WidgetRegistry.register_widget(self.start_pause_continue_button._button, "start_pause_continue_button", tab_name)
        WidgetRegistry.register_widget(self._single_step_button._button, "single_step_button", tab_name)
        WidgetRegistry.register_widget(self._stop_button._button, "stop_button", tab_name)

        self._menue: ttk.Menu = ttk.Menu(self._navigation_button_frame)
        self._menue_button: ttk.Menubutton = ttk.Menubutton(
            self._navigation_button_frame,
            menu=self._menue,
            style=ttk.DARK,
            image=ImageLoader.load_image_resource(images.MENUE_ICON_WHITE, (13, 13)),
            compound=ttk.LEFT,
        )


    def _initialize_publish(self) -> None:
        self.columnconfigure(0, weight=sizes.EXPAND)
        self.rowconfigure(0, weight=sizes.DONT_EXPAND, minsize=20)
        self.rowconfigure(1, weight=sizes.EXPAND)
        self.rowconfigure(2, weight=sizes.DONT_EXPAND, minsize=20)
        self._navigation_button_frame.grid(
            row=0,
            column=0,
            sticky=ttk.EW,
            padx=sizes.LARGE_PADDING,
            pady=sizes.LARGE_PADDING,
        )
        self._start_pause_continue_button._button.grid(
            row=0,
            column=0,
            padx=sizes.MEDIUM_PADDING,
            sticky=ttk.W,
        )
        self._single_step_button._button.grid(
            row=0,
            column=1,
            padx=sizes.MEDIUM_PADDING,
            sticky=ttk.W,
        )
        self._stop_button._button.grid(
            row=0,
            column=2,
            padx=sizes.MEDIUM_PADDING,
            sticky=ttk.W,
        )
        self._scripting_guide_button.grid(
            row=0,
            column=3,
            padx=sizes.MEDIUM_PADDING,
            sticky=ttk.W,
        )
        self._navigation_button_frame.columnconfigure(3, weight=sizes.EXPAND)
        self._menue_button.grid(
            row=0, column=4, sticky=ttk.E, padx=sizes.MEDIUM_PADDING
        )

        self._main_frame.grid(row=1, column=0, sticky=ttk.NSEW)
        self._scripting_frame.pack(
            expand=True,
            fill=ttk.BOTH,
            padx=sizes.SIDE_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._editor_text.pack(expand=True, fill=ttk.BOTH)

        self._script_status_frame.grid(
            row=2,
            column=0,
            sticky=ttk.EW,
            padx=sizes.SIDE_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._script_status_frame.columnconfigure(0, weight=3)
        self._script_status_frame.columnconfigure(1, weight=sizes.EXPAND)
        self._current_task_label.grid(row=0, column=0, columnspan=2, sticky=ttk.EW)

    def add_menu_command(self, label: str, command: Callable[[], None]) -> None:
        self._menue.add_command(label=label, command=command)

    @property 
    def editor_text_view(self) -> ttk.Frame:
        return self._editor_text
    
    def set_scripting_guide_button_command(self, command: Callable[[], None]) -> None:
        self._scripting_guide_button.configure(command=command)

    @property
    def editor_text(self) -> str:
        return self._editor_text.get(1.0, ttk.END) # type: ignore
    
    @editor_text.setter
    def editor_text(self, value: str) -> None:
        self._editor_text.delete(1.0, ttk.END) # type: ignore
        self._editor_text.insert(ttk.INSERT, value) # type: ignore

    def bind_editor_text(self, command: Callable[[], None]) -> None:
        self._editor_text.text.bind('<KeyRelease>', lambda event: command())

    @property
    def current_task(self) -> str:
        return self._current_task_var.get()
    
    @current_task.setter
    def current_task(self, value: str) -> None:
        self._current_task_var.set(value)

    @property
    def editor_enabled(self) -> bool:
        pass

    @editor_enabled.setter 
    def editor_enabled(self, enabled: bool) -> None:
        pass

    @property
    def start_pause_continue_button(self) -> PushButtonView:
        return self._start_pause_continue_button
    
    @property
    def single_step_button(self) -> PushButtonView:
        return self._single_step_button

    @property
    def stop_button(self) -> PushButtonView:
        return self._stop_button

    def highlight_line(self, line_idx: Optional[int], color_background: str = "#3e3f3a", color_foreground: str = "#dfd7ca") -> None:
        current_line_tag = "currentLine"
        self._editor_text.tag_remove(current_line_tag, 1.0, "end") # type: ignore

        if line_idx is not None:
            self._editor_text.tag_add(current_line_tag, f"{line_idx}.0", f"{line_idx}.end") # type: ignore
            self._editor_text.tag_configure( # type: ignore
                current_line_tag, background=color_background, foreground=color_foreground
            )
