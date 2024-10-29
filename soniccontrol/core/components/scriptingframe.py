from typing import Optional, Any, Tuple, Dict, Callable
import asyncio
import sys
import logging
import copy
import csv
import pathlib
import datetime
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame, ScrolledText
from ttkbootstrap.dialogs import Messagebox
from async_tkinter_loop import async_handler
from PIL.ImageTk import PhotoImage

from soniccontrol.core.interfaces import RootChild, Connectable, Scriptable, Root

logger = logging.getLogger(__name__)


class ScriptingFrame(RootChild, Connectable, Scriptable):
    def __init__(
        self,
        master: Root,
        tab_title: str = "Scripting",
        image: Optional[PhotoImage] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(master, tab_title, image=image, *args, **kwargs)
        self.logfile: Optional[pathlib.Path] = None
        self.sequence_task: Optional[asyncio.Task] = None
        self.current_task_var: ttk.StringVar = ttk.StringVar(value="Idle")
        self.navigation_button_frame: ttk.Frame = ttk.Frame(self)
        self.top_frame: ScrolledFrame = ScrolledFrame(self, autohide=True)

        self.start_script_btn = ttk.Button(
            self.navigation_button_frame,
            text="Run",
            style=ttk.SUCCESS,
            image=self.root.start_image,
            compound=ttk.LEFT,
            command=self.start_script,
        )
        self.script_guide_btn = ttk.Button(
            self.navigation_button_frame,
            text="Function Helper",
            style=ttk.INFO,
            image=self.root.info_image_small_white,
            compound=ttk.LEFT,
            command=self.open_help,
        )

        self.menue: ttk.Menu = ttk.Menu(self.navigation_button_frame)
        self.menue_button: ttk.Menubutton = ttk.Menubutton(
            self.navigation_button_frame,
            image=self.root.menue_image,
            menu=self.menue,
            bootstyle="dark",
        )
        self.menue.add_command(label="Save Script", command=self.save_file)
        self.menue.add_command(label="Load Script", command=self.load_file)
        self.menue.add_command(label="Specify Log file path", command=self.open_logfile)

        self.scripting_frame: ttk.Labelframe = ttk.Labelframe(
            self.top_frame,
            text="Script Editor",
            padding=(5, 5, 5, 5),
        )
        self.scripttext: ttk.Text = ScrolledText(
            self.scripting_frame,
            autohide=True,
            height=30,
            width=50,
            font=("QType Square Light", 12),
        )
        self.script_status_frame: ttk.Frame = ttk.Frame(self)
        self.current_task_label: ttk.Label = ttk.Label(
            self.script_status_frame,
            justify=ttk.CENTER,
            anchor=ttk.CENTER,
            bootstyle=ttk.DARK,
            textvariable=self.current_task_var,
        )
        self.sequence_status: ttk.Progressbar = ttk.Progressbar(
            self.script_status_frame,
            length=160,
            mode="indeterminate",
            orient=ttk.HORIZONTAL,
            bootstyle=ttk.DARK,
        )
        self.bind_events()

    def on_connect(self, event=None) -> None:
        return self.publish()

    def on_script_start(self, event=None) -> None:
        pass

    def on_script_stop(self, event=None) -> None:
        pass

    @async_handler
    async def start_script(self) -> None:
        self.start_script_btn.configure(
            text="Stop",
            bootstyle=ttk.DANGER,
            image=self.root.pause_image,
            command=self.stop_script,
        )
        self.menue_button.configure(state=ttk.DISABLED)
        self.sequence_status.start()

        self.sequence_task = asyncio.create_task(
            self.root.sonicamp.sequence(self.scripttext.get(1.0, ttk.END)),
        )

        await asyncio.sleep(0.1)
        if self.sequence_task.done() and self.sequence_task.exception() is not None:
            logger.warning(f"{self.sequence_task.exception()}")
            Messagebox.show_warning(f"{self.sequence_task.exception()}")
            return self.stop_script()

        if self.logfile is None:
            self.logfile = pathlib.Path(
                f"logs//scripting_log_{str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')}.csv"
            )
        with self.logfile.open("w") as file:
            writer = csv.DictWriter(
                file, fieldnames=self.root.fieldnames, extrasaction="ignore"
            )
            writer.writeheader()
        self.root.on_script_start()
        self.script_engine()

    @async_handler
    async def script_engine(self) -> None:
        await self.root.sonicamp.sequencer.running.wait()
        while (
            self.sequence_task is not None
            and not self.sequence_task.done()
            and self.root.sonicamp.sequencer.running.is_set()
        ):
            self.root.serialize_data(self.root.sonicamp.status, self.logfile)
            self.highlight_line(self.root.sonicamp.sequencer.current_line)
            try:
                if self.root.sonicamp.ramper.running.is_set():
                    self.current_task_var.set(f"{self.root.sonicamp.ramper}")
                elif self.root.sonicamp.holder.holding.is_set():
                    self.current_task_var.set(f"{self.root.sonicamp.holder}")
                else:
                    self.current_task_var.set(f"{self.root.sonicamp.sequencer}")
            except Exception as e:
                logger.debug(sys.exc_info())
                self.current_task_var.set("")
            await asyncio.sleep(0.05)

        if self.sequence_task._exception is not None:
            logger.warning(f"{self.sequence_task.exception()}")
            Messagebox.show_warning(f"{self.sequence_task.exception()}")

        await asyncio.Condition().wait_for(
            lambda: not self.root.sonicamp.sequencer.running.is_set()
        )
        self.stop_script()

    @async_handler
    async def stop_script(self) -> None:
        self.root.sonicamp.sequencer.running.clear()
        self.start_script_btn.configure(
            text="Run",
            style="success.TButton",
            image=self.root.start_image,
            command=self.start_script,
        )
        self.current_task_var.set("Idle")
        self.menue_button.configure(state=ttk.NORMAL)
        self.sequence_status.stop()
        self.scripttext.tag_remove("currentLine", 1.0, "end")
        self.root.on_script_stop()

    def highlight_line(self, line: int) -> None:
        line += 1
        self.scripttext.tag_remove("currentLine", 1.0, "end")
        self.scripttext.tag_add("currentLine", f"{line}.0", f"{line}.end")
        self.scripttext.tag_configure(
            "currentLine", background="#3e3f3a", foreground="#dfd7ca"
        )

    def on_feedback(self, text: str) -> None:
        pass

    def load_file(self) -> None:
        script_filepath: str = ttk.filedialog.askopenfilename(
            defaultextension=".txt", filetypes=self._filetypes
        )

        with open(script_filepath, "r") as f:
            self.scripttext.delete(1.0, ttk.END)
            self.scripttext.insert(ttk.INSERT, f.read())

    def save_file(self) -> None:
        self.save_filename = ttk.filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=self._filetypes
        )

        with open(self.save_filename, "w") as f:
            f.write(self.scripttext.get(1.0, ttk.END))

    def open_logfile(self) -> None:
        self.logfile = pathlib.Path(
            ttk.filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=self._filetypes
            )
        )

    def open_help(self) -> None:
        ScriptGuide(self, self.scripttext)
        self.script_guide_btn.configure(state=ttk.DISABLED)

    def set_horizontal_button_layout(self) -> None:
        for child in self.navigation_button_frame.children.values():
            child.pack_forget()
        self.start_script_btn.pack(side=ttk.LEFT, padx=5, pady=3)
        self.script_guide_btn.pack(side=ttk.LEFT, padx=5, pady=3)
        self.menue_button.pack(side=ttk.RIGHT, padx=5, pady=3)

    def publish(self):
        self.navigation_button_frame.pack(anchor=ttk.N, padx=15, pady=5, fill=ttk.X)
        self.top_frame.pack(expand=True, fill=ttk.BOTH)
        self.set_horizontal_button_layout()

        self.scripting_frame.pack(padx=20, pady=5, fill=ttk.BOTH, expand=True)
        self.scripttext.pack(fill=ttk.BOTH, expand=True)

        self.script_status_frame.pack(side=ttk.BOTTOM, fill=ttk.X)
        self.current_task_label.pack(fill=ttk.X, padx=5, pady=3, side=ttk.LEFT)
        self.sequence_status.pack(fill=ttk.X, padx=5, pady=3, side=ttk.RIGHT)


class ScriptGuide(ttk.Toplevel):
    def __init__(self, parent, scripttext, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.parent: ScriptingFrame = parent
        self.scripttext: ttk.ScrolledText = scripttext

        self.card_data: Tuple[Dict[str, str], ...] = (
            {
                "keyword": "startloop",
                "arguments": "times: optional uint",
                "description": "Starts a loop and loops until an endloop was found. If no argument was passed, then the loop turns to a 'While True loop'",
                "example": "startloop 5",
            },
            {
                "keyword": "endloop",
                "arguments": "None",
                "description": "Ends the last started loop",
                "example": "endloop",
            },
            {
                "keyword": "on",
                "arguments": "None",
                "description": "Sets the signal to ON",
                "example": "on",
            },
            {
                "keyword": "off",
                "arguments": "None",
                "description": "Set the signal to OFF",
                "example": "off",
            },
            {
                "keyword": "auto",
                "arguments": "None",
                "description": "Turns the auto mode on.\nIt is important to hold after that command to stay in auto mode.\nIn the following example the auto mode is turned on for 5 seconds",
                "example": "auto\nhold 5s",
            },
            {
                "keyword": "gain",
                "arguments": "gain: uint",
                "description": "Set the Gain of the device",
                "example": "gain 100",
            },
            {
                "keyword": "hold",
                "arguments": "hold: int,\nunit: 'ms' or 's'",
                "description": "Hold the state of the device\nfor a certain amount of time",
                "example": "hold 10s",
            },
            {
                "keyword": "ramp_freq",
                "arguments": "start: uint,\nstop: uint,\nstep: int,\non_signal_hold: uint,\nunit: 'ms' or 's',\noff_signal_hold: uint,\nunit: 'ms' or 's'",
                "description": "Ramp up the frequency from\none point to another",
                "example": "ramp_freq 1000000 2000000 1000 100ms 100ms",
            },
            # {
            #     "keyword": "ramp_gain",
            #     "arguments": "start: uint,\nstop: uint,\nstep: int,\non_signal_hold: uint,\nunit: 'ms' or 's',\noff_signal_hold: uint,\nunit: 'ms' or 's'",
            #     "description": "Ramp up the gain from\none point to another",
            #     "example": "ramp_gain 10 100 10 100ms 100ms",
            # },
            # {
            #     "keyword": "chirp_freq_series",
            #     "arguments": "start: uint,\ndifference: uint,\nstep: int,\non_signal_hold: uint,\nunit: 'ms' or 's',\noff_signal_hold: uint,\nunit: 'ms' or 's'\ntimes: uint",
            #     "description": "Ramp up the frequency from\nthe start to the upper and lower difference.",
            #     "example": "chirp_freq_series 1000000 2000000 1000 100ms 100ms",
            # },
        )

        self.scrolled_frame: ScrolledFrame = ScrolledFrame(self)
        self.scrolled_frame.pack(expand=True, fill=ttk.BOTH)

        for data in self.card_data:
            insert_command: Callable[[Any], Any] = lambda event, text=data["example"]: (
                self.insert_text(text)
            )
            card: ScriptingGuideCard = ScriptingGuideCard(
                parent=self.scrolled_frame,
                data=data,
                callback=insert_command,
            )
            card.pack(expand=True, fill=ttk.BOTH, padx=20, pady=15)
            card.publish()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self) -> None:
        self.parent.script_guide_btn.configure(state=ttk.NORMAL)
        self.destroy()

    def insert_text(self, text: str) -> None:
        self.scripttext.insert(self.scripttext.index(ttk.INSERT), f"{text}\n")


class ScriptingGuideCard(ttk.Labelframe):
    def __init__(
        self,
        parent,
        data: Dict[str, str],
        callback: Callable[[Any], Any],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(parent, *args, **kwargs)
        self.data: Dict[str, str] = copy.deepcopy(data)
        self.callback: Callable[[Any], Any] = copy.deepcopy(callback)

        self.keyword_frame: ttk.Frame = ttk.Frame(self)
        self.keyword_label: ttk.Label = ttk.Label(
            self.keyword_frame,
            font=("QType CondBook", 20),
            text=self.data["keyword"],
        )

        self.info_frame: ttk.Frame = ttk.Frame(self)
        self.arguments_frame: ttk.Frame = ttk.Frame(self.info_frame)
        self.arguments_title: ttk.Label = ttk.Label(
            self.arguments_frame, text=f"Arguments:", font=("Arial", 13, "bold")
        )
        self.arguments_label: ttk.Label = ttk.Label(
            self.arguments_frame, text=self.data["arguments"]
        )

        self.description_frame: ttk.Frame = ttk.Frame(self.info_frame)
        self.description_title: ttk.Label = ttk.Label(
            self.description_frame, text=f"Description:", font=("Arial", 13, "bold")
        )
        self.description_label: ttk.Label = ttk.Label(
            self.description_frame, text=self.data["description"]
        )

        self.example_frame: ttk.Frame = ttk.Frame(self.info_frame)
        self.example_title: ttk.Label = ttk.Label(
            self.example_frame, text=f"Example:", font=("Arial", 13, "bold")
        )
        self.example_label: ttk.Label = ttk.Label(
            self.example_frame, text=self.data["example"]
        )

        self.bind_deep(self, "<Button-1>", self.callback)
        self.bind_deep(self, "<Enter>", self.mark)
        self.bind_deep(self, "<Leave>", self.unmark)

    @staticmethod
    def bind_deep(widget, event, handler) -> None:
        widget.bind(event, handler)
        for child in widget.winfo_children():
            ScriptingGuideCard.bind_deep(child, event, handler)

    @staticmethod
    def deep_mark(widget, style) -> None:
        if isinstance(widget, (ttk.Label, ttk.LabelFrame)):
            widget.configure(bootstyle=style)
        for child in widget.winfo_children():
            ScriptingGuideCard.deep_mark(child, style)

    def unmark(self, event: Any = None) -> None:
        ScriptingGuideCard.deep_mark(self, ttk.DEFAULT)

    def mark(self, event: Any = None) -> None:
        ScriptingGuideCard.deep_mark(self, ttk.PRIMARY)

    def publish(self) -> None:
        self.keyword_frame.pack(padx=10, pady=5, fill=ttk.X)
        self.keyword_label.pack(expand=True, fill=ttk.X, padx=5, pady=5)

        self.info_frame.pack(padx=5, pady=5, fill=ttk.X)
        self.arguments_frame.pack(fill=ttk.X, padx=5, pady=5)
        self.arguments_title.pack(fill=ttk.X, padx=3, pady=3)
        self.arguments_label.pack(fill=ttk.X, padx=3, pady=3)

        self.description_frame.pack(fill=ttk.X, padx=5, pady=5)
        self.description_title.pack(fill=ttk.X, padx=3, pady=3)
        self.description_label.pack(fill=ttk.X, padx=3, pady=3)

        self.example_frame.pack(fill=ttk.X, padx=5, pady=5)
        self.example_title.pack(fill=ttk.X, padx=3, pady=3)
        self.example_label.pack(fill=ttk.X, padx=3, pady=3)
