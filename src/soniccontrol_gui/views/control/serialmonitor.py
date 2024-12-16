import logging
from typing import Callable, List
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from async_tkinter_loop import async_handler

from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.view import TabView, View
from soniccontrol.command import LegacyCommand
from soniccontrol.communication.communicator import Communicator
from soniccontrol_gui.state_fetching.message_fetcher import MessageFetcher
from soniccontrol_gui.utils.animator import Animator, DotAnimationSequence, load_animation
from soniccontrol_gui.constants import sizes, style, ui_labels
from soniccontrol.events import PropertyChangeEvent
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.views.core.app_state import ExecutionState
from soniccontrol_gui.resources import images
from soniccontrol_gui.resources import resources

class SerialMonitor(UIComponent):
    def __init__(self, parent: UIComponent, communicator: Communicator):
        self._logger = logging.getLogger(parent.logger.name + "." + SerialMonitor.__name__)
        self._view = SerialMonitorView(parent.view)
        super().__init__(parent, self._view, self._logger)

        # decorate send and receive with loading animation
        self._animation = Animator(
            DotAnimationSequence("Wait for answer", num_dots=5), 
            self._view.set_loading_text, 
            5,
            done_callback=lambda: self._view.set_loading_text("")
        )
        animation_decorator = load_animation(
            self._animation, 
            num_repeats=-1
        )
        self._send_and_receive = animation_decorator(self._send_and_receive) 


        self._logger.debug("Create SerialMonitor")
        self._communicator = communicator
        self._message_fetcher = MessageFetcher(self._communicator)
        self._command_history: List[str] = []
        self._command_history_index: int = 0
        self._view.set_send_command_button_command(self._send_command)
        self._view.set_read_button_command(self._on_read_button_pressed)
        self._view.bind_command_line_input_on_return_pressed(self._send_command)
        self._view.bind_command_line_input_on_down_pressed(lambda: self._scroll_command_history(False))
        self._view.bind_command_line_input_on_up_pressed(lambda: self._scroll_command_history(True))
        self._message_fetcher.subscribe(MessageFetcher.MESSAGE_RECEIVED_EVENT, lambda e: self._view.add_text_line(e.data["message"]))

    @async_handler
    async def _send_command(self): 
        command_str = self._view.command_line_input.strip()
        self._logger.debug("Command: %s", command_str)
        self._view.command_line_input = ""
        self._view.add_text_line(">>> " + command_str)
        if len(self._command_history) == 0 or command_str != self._command_history[self._command_history_index]:
            self._command_history.append(command_str)
            self._command_history_index = 0
        
        if self._is_internal_command(command_str):
            await self._handle_internal_command(command_str) 
        else:
            answer_str = await self._send_and_receive(command_str)
            self._print_answer(answer_str)

    async def _send_and_receive(self, command_str: str) -> str:
        try:
            answer, _ = await LegacyCommand(message=command_str).execute(connection=self._communicator)
            return answer.string
        except Exception as e:
            self._logger.error(str(e))
            return str(e)        

    def _print_answer(self, answer_str: str):
        self._logger.debug("Answer: %s", answer_str)
        self._view.add_text_line(answer_str)


    def _print_log(self, log_msg: str):
        self._view.add_text_line(log_msg)


    def _is_internal_command(self, command_str: str):
        return command_str in ["clear", "help"]


    async def _handle_internal_command(self, command_str: str) -> None:
        self._logger.debug("Execute internal command")
        if command_str == "clear":
            self._view.clear()
        elif command_str == "help":
            help_text = ""
            if self._communicator.protocol.major_version == 1:
                with open(resources.HELPTEXT_SONIC_V1, "r") as file:
                    help_text = file.read()
            else:
                help_text = await self._send_and_receive("?help")
            
            help_text += "\n"
            with open(resources.HELPTEXT_INTERNAL_COMMANDS, "r") as file:
                help_text += file.read()
            self._view.add_text_line(help_text)
            

    def _scroll_command_history(self, is_scrolling_up: bool):
        if len(self._command_history) == 0:
            return
        
        self._command_history_index += -1 if is_scrolling_up else +1
        self._command_history_index %= len(self._command_history) 
        self._view.command_line_input = self._command_history[self._command_history_index]

    @async_handler
    async def _on_read_button_pressed(self):
        if self._message_fetcher.is_running:
            await self._message_fetcher.stop()
        else:
            self._message_fetcher.run()

    def on_execution_state_changed(self, e: PropertyChangeEvent) -> None:
        execution_state: ExecutionState = e.new_value
        enabled = execution_state not in [ExecutionState.NOT_RESPONSIVE, ExecutionState.BUSY_FLASHING]
        self._view.set_send_command_button_enabled(enabled)
        self._view.set_command_line_input_enabled(enabled)



class SerialMonitorView(TabView):
    def __init__(self, master: ttk.Window | View, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def image(self) -> ttk.ImageTk.PhotoImage:
        return ImageLoader.load_image_resource(images.CONSOLE_ICON_BLACK, sizes.TAB_ICON_SIZE)

    @property
    def tab_title(self) -> str:
        return ui_labels.SERIAL_MONITOR_LABEL

    def _initialize_children(self) -> None:
        tab_name = "serial_monitor"
        self._main_frame: ttk.Frame = ttk.Frame(self)
        self._output_frame: ttk.Labelframe = ttk.Labelframe(
            self._main_frame, text=ui_labels.OUTPUT_LABEL
        )
        self._scrolled_frame: ScrolledFrame = ScrolledFrame(
            self._output_frame, autohide=True
        )
        self._monitor_frame: ttk.Frame = ttk.Frame(
            self._scrolled_frame
        )
        self._loading_label: ttk.Label = ttk.Label(
            self._scrolled_frame,
            text="",
            font=("Consolas", 10)
        )

        INPUT_FRAME_PADDING = (3, 1, 3, 4)
        self._input_frame: ttk.Labelframe = ttk.Labelframe(
            self._main_frame, text=ui_labels.INPUT_LABEL, padding=INPUT_FRAME_PADDING
        )
        self._read_button: ttk.Checkbutton = ttk.Checkbutton(
            self._input_frame,
            text=ui_labels.AUTO_READ_LABEL,
            style=style.DARK_SQUARE_TOGGLE,
        )
        self._command_line_input = ttk.StringVar()
        self.command_line_input_entry: ttk.Entry = ttk.Entry(self._input_frame, textvariable=self._command_line_input, style=ttk.DARK)
        self._send_button: ttk.Button = ttk.Button(
            self._input_frame,
            text=ui_labels.SEND_LABEL,
            style=ttk.SUCCESS,
            image=ImageLoader.load_image_resource(
                images.PLAY_ICON_WHITE, sizes.BUTTON_ICON_SIZE
            ),
            compound=ttk.RIGHT,
        )

        WidgetRegistry.register_widget(self._read_button, "read_button", tab_name)
        WidgetRegistry.register_widget(self.command_line_input_entry, "command_line_input_entry", tab_name)
        WidgetRegistry.register_widget(self._send_button, "send_button", tab_name)

    def _initialize_publish(self) -> None:
        self._main_frame.pack(expand=True, fill=ttk.BOTH)
        self._main_frame.columnconfigure(0, weight=sizes.EXPAND)
        self._main_frame.rowconfigure(0, weight=sizes.EXPAND)
        self._main_frame.rowconfigure(1, weight=sizes.DONT_EXPAND, minsize=40)
        self._output_frame.grid(
            row=0,
            column=0,
            sticky=ttk.NSEW,
            pady=sizes.MEDIUM_PADDING,
            padx=sizes.LARGE_PADDING,
        )
        self._scrolled_frame.pack(
            expand=True,
            fill=ttk.BOTH,
            pady=sizes.MEDIUM_PADDING,
            padx=sizes.MEDIUM_PADDING,
        )
        self._monitor_frame.pack(
            fill=ttk.BOTH,
            expand=True
        )
        self._loading_label.pack(
            side=ttk.BOTTOM,
            anchor=ttk.W,
            fill=ttk.X
        )

        self._input_frame.grid(
            row=1,
            column=0,
            sticky=ttk.EW,
            pady=sizes.MEDIUM_PADDING,
            padx=sizes.LARGE_PADDING,
        )
        self._input_frame.columnconfigure(0, weight=1)
        self._input_frame.columnconfigure(1, weight=10)
        self._input_frame.columnconfigure(2, weight=3)
        self._read_button.grid(
            row=0,
            column=0,
            sticky=ttk.EW,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self.command_line_input_entry.grid(
            row=0,
            column=1,
            sticky=ttk.EW,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )
        self._send_button.grid(
            row=0,
            column=2,
            sticky=ttk.EW,
            padx=sizes.MEDIUM_PADDING,
            pady=sizes.MEDIUM_PADDING,
        )

    def set_send_command_button_command(self, command: Callable[[], None]):
        self._send_button.configure(command=command)

    def set_read_button_command(self, command: Callable[[], None]):
        self._read_button.configure(command=command)

    def set_send_command_button_enabled(self, enabled: bool) -> None:
        self._send_button.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    def set_command_line_input_enabled(self, enabled: bool) -> None:
        self.command_line_input_entry.configure(state=ttk.NORMAL if enabled else ttk.DISABLED)

    @property
    def command_line_input(self) -> str:
        return self._command_line_input.get()

    @command_line_input.setter
    def command_line_input(self, text: str):
        self._command_line_input.set(text)

    def set_loading_text(self, text: str) -> None:
        self._loading_label.configure(text=text)

    def bind_command_line_input_on_down_pressed(self, command: Callable[[], None]):
        self.command_line_input_entry.bind("<Down>", lambda _: command()) 

    def bind_command_line_input_on_up_pressed(self, command: Callable[[], None]):
        self.command_line_input_entry.bind("<Up>", lambda _: command())

    def bind_command_line_input_on_return_pressed(self, command: Callable[[], None]):
        self.command_line_input_entry.bind("<Return>", lambda _: command())

    def add_text_line(self, text: str):
        ttk.Label(self._scrolled_frame, text=text, font=("Consolas", 10)).pack(
            fill=ttk.X, side=ttk.TOP, anchor=ttk.W
        )
        self._scrolled_frame.update()
        self._scrolled_frame.yview_moveto(1)

    def clear(self):
        for child in self._scrolled_frame.winfo_children():
            child.destroy()
