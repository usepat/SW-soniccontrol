from typing import Optional, Any
import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from async_tkinter_loop import async_handler
from PIL.ImageTk import PhotoImage
from soniccontrol.core.interfaces import RootChild, Connectable, WidthLayout, Root
from soniccontrol.sonicpackage.sonicamp import SonicCatch


class HomeFrame(RootChild, Connectable):
    def __init__(
        self,
        master: Root,
        tab_title: str = "Home",
        image: Optional[PhotoImage] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(master, tab_title, image=image, *args, **kwargs)
        self.set_layouts(
            [
                WidthLayout(min_size=400, command=self.set_large_width_uscontrolframe),
                WidthLayout(min_size=10, command=self.set_small_width_uscontrolframe),
            ]
        )

        self._debounce_time_ms: int = 250
        self._debounce_job: Any = None

        self.main_frame: ScrolledFrame = ScrolledFrame(self, autohide=True)
        self.top_frame: ttk.Frame = ttk.Frame(self.main_frame)
        self.control_frame: ttk.LabelFrame = ttk.LabelFrame(
            self.top_frame, text="Manual Control"
        )

        self.freq_spinbox: ttk.Spinbox = ttk.Spinbox(
            self.control_frame,
            increment=100,
            from_=20_000,
            to=6_000_000,
            textvariable=self.root.set_frequency_var,
            width=16,
            bootstyle=ttk.DARK,
            command=self.set_frequency,
        )
        self.freq_spinbox_placeholder = "Set Frequency..."
        self.freq_spinbox.delete(0, tk.END)
        self.freq_spinbox.insert(0, self.freq_spinbox_placeholder)
        self.freq_spinbox.bind("<FocusIn>", self.on_freq_spinbox_focus_in)
        self.freq_spinbox.bind("<FocusOut>", self.on_freq_spinbox_focus_out)

        self.gain_frame: ttk.Frame = ttk.Frame(self.control_frame)
        self.gain_spinbox: ttk.Spinbox = ttk.Spinbox(
            self.gain_frame,
            increment=10,
            from_=0,
            to=150,
            textvariable=self.root.set_gain_var,
            style=ttk.DARK,
            command=self.set_gain,
        )
        self.gain_scale: ttk.Scale = ttk.Scale(
            self.gain_frame,
            from_=0,
            to=150,
            orient=tk.HORIZONTAL,
            style=ttk.SUCCESS,
            variable=self.root.set_gain_var,
            command=self.set_gain,
        )
        self.gain_spinbox_placeholder = "Set Gain..."
        self.gain_spinbox.delete(0, tk.END)
        self.gain_spinbox.insert(0, self.gain_spinbox_placeholder)
        self.gain_spinbox.bind("<FocusIn>", self.on_gain_spinbox_focus_in)
        self.gain_spinbox.bind("<FocusOut>", self.on_gain_spinbox_focus_out)

        self.mode_frame: ttk.Label = ttk.Label(self.control_frame)
        self.wipemode_button: ttk.Radiobutton = ttk.Radiobutton(
            self.mode_frame,
            text="Wipe mode",
            variable=self.root.mode,
            value="Wipe",
            bootstyle="dark-outline-toolbutton",
            command=self.set_relay_mode_khz,
        )
        self.catchmode_button: ttk.Radiobutton = ttk.Radiobutton(
            self.mode_frame,
            text="Catch mode",
            variable=self.root.mode,
            value="Catch",
            bootstyle="dark-outline-toolbutton",
            command=self.set_relay_mode_mhz,
        )

        self.set_val_btn: ttk.Button = ttk.Button(
            self.control_frame,
            text="Set Signal on",
            bootstyle=ttk.DARK,
            command=self.set_values,
        )

        self.us_control_frame: ttk.Frame = ttk.Frame(self.main_frame)
        self.us_on_button: ttk.Button = ttk.Button(
            self.us_control_frame,
            text="WIPE",
            bootstyle=ttk.SUCCESS,
            width=10,
            command=self.set_signal_wipe,
        )

        self.us_auto_button: ttk.Button = ttk.Button(
            self.us_control_frame,
            text="AUTO",
            bootstyle=ttk.PRIMARY,
            width=10,
            command=self.set_signal_auto,
        )

        self.us_off_button: ttk.Button = ttk.Button(
            self.us_control_frame,
            text="OFF",
            bootstyle=ttk.DANGER,
            width=10,
            command=self.set_signal_off,
        )

        self.botframe: ttk.Frame = ttk.Frame(self.main_frame)
        self.output_frame: ttk.Frame = ttk.LabelFrame(self.botframe, text="Feedback")
        self.feedback_frame: ScrolledFrame = ScrolledFrame(
            self.output_frame,
            height=200,
            width=475,
        )
        self.bind_events()

    def on_gain_spinbox_focus_in(self, event):
        current_value = self.gain_spinbox.get()
        if current_value == self.gain_spinbox_placeholder:
            self.gain_spinbox.delete(0, tk.END)

    def on_gain_spinbox_focus_out(self, event):
        current_value = self.gain_spinbox.get()
        if not current_value:
            self.gain_spinbox.insert(0, self.gain_spinbox_placeholder)

    def on_freq_spinbox_focus_in(self, event):
        current_value = self.freq_spinbox.get()
        if current_value == self.freq_spinbox_placeholder:
            self.freq_spinbox.delete(0, tk.END)

    def on_freq_spinbox_focus_out(self, event):
        current_value = self.freq_spinbox.get()
        if not current_value:
            self.freq_spinbox.insert(0, self.freq_spinbox_placeholder)

    def on_connect(self, connection_data: Connectable.ConnectionData) -> None:
        return self.publish()

    def on_refresh(self, event=None) -> None:
        pass

    def publish(self) -> None:
        self.main_frame.pack(side=tk.TOP, expand=True, fill=ttk.BOTH)
        self.top_frame.pack(side=tk.TOP, padx=10, pady=10)
        self.control_frame.pack(side=tk.TOP, fill=tk.X)
        self.freq_spinbox.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.gain_frame.pack(side=tk.TOP, fill=tk.X)
        self.gain_spinbox.grid(row=0, column=0, padx=10, pady=10)
        self.gain_scale.grid(row=0, column=1, padx=10, pady=10, sticky=tk.EW)

        if not isinstance(self.root.sonicamp, SonicCatch): 
            self.mode_frame.pack(side=tk.TOP, fill=tk.X)
            self.wipemode_button.pack(
                side=ttk.LEFT, expand=True, fill=ttk.X, padx=10, pady=10
            )
            self.catchmode_button.pack(
                side=ttk.LEFT, expand=True, fill=ttk.X, padx=10, pady=10
            )

        self.set_val_btn.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.us_control_frame.pack(side=tk.TOP, padx=10, pady=10)

        self.botframe.pack(side=tk.TOP)
        self.feedback_frame.pack(
            side=tk.LEFT,
        )
        self.output_frame.pack(anchor=tk.N, side=tk.TOP, padx=10, pady=10, fill=tk.BOTH)

    def set_small_width_uscontrolframe(self, *args, **kwargs) -> None:
        for child in self.us_control_frame.children.values():
            child.grid_forget()
        self.us_on_button.pack(side=ttk.TOP, fill=ttk.X, padx=5, pady=5)
        self.us_auto_button.pack(side=ttk.TOP, fill=ttk.X, padx=5, pady=5)
        self.us_off_button.pack(side=ttk.TOP, fill=ttk.X, padx=5, pady=5)

    def set_large_width_uscontrolframe(self, *args, **kwargs) -> None:
        for i, child in enumerate(self.us_control_frame.children.values()):
            child.pack_forget()
        self.us_on_button.grid(row=0, column=0, padx=10, pady=10, sticky=tk.EW)
        self.us_auto_button.grid(row=0, column=1, padx=10, pady=10, sticky=tk.EW)
        self.us_off_button.grid(row=0, column=2, padx=10, pady=10, sticky=tk.EW)

    @async_handler
    async def set_frequency(self, event: Any = None, *args, **kwargs) -> None:
        @async_handler
        async def _set_frequency() -> None:
            answer = await self.root.sonicamp.set_frequency(
                self.root.set_frequency_var.get()
            )
            self.on_feedback(answer)
            self._debounce_job = None

        if self._debounce_job is not None:
            self.after_cancel(self._debounce_job)
        self._debounce_job = self.after(self._debounce_time_ms, _set_frequency)

    @async_handler
    async def set_gain(self, event: Any = None, *args, **kwargs) -> None:
        @async_handler
        async def _set_gain() -> None:
            answer = await self.root.sonicamp.set_gain(self.root.set_gain_var.get())
            self.on_feedback(answer)
            self._debounce_job = None

        if self._debounce_job is not None:
            self.after_cancel(self._debounce_job)
        self._debounce_job = self.after(self._debounce_time_ms, _set_gain)

    @async_handler
    async def set_relay_mode_khz(self) -> None:
        self.on_feedback(await self.root.sonicamp.set_relay_mode_khz())
        for child in self.gain_frame.winfo_children():
            child.configure(state=ttk.DISABLED)

    @async_handler
    async def set_relay_mode_mhz(self) -> None:
        self.on_feedback(await self.root.sonicamp.set_relay_mode_mhz())
        for child in self.gain_frame.winfo_children():
            child.configure(state=ttk.NORMAL)

    @async_handler
    async def set_values(self) -> None:
        try:
            self.on_feedback(
                await self.root.sonicamp.set_frequency(self.root.set_frequency_var.get())
            )
        except Exception as e:
            pass
        try:
            self.on_feedback(
                await self.root.sonicamp.set_gain(self.root.set_gain_var.get())
            )
        except Exception as e:
            pass
        self.on_feedback(
            await self.root.sonicamp.set_signal_on()
        )


    @async_handler
    async def set_signal_on(self) -> None:
        self.on_feedback(await self.root.sonicamp.set_signal_on())

    @async_handler
    async def set_signal_off(self) -> None:
        self.on_feedback(await self.root.sonicamp.set_signal_off())

    @async_handler
    async def set_signal_auto(self) -> None:
        self.on_feedback(await self.root.sonicamp.set_signal_auto())

    @async_handler
    async def set_signal_wipe(self) -> None:
        self.on_feedback(await self.root.sonicamp.set_wipe())

    def on_feedback(self, text: str) -> None:
        ttk.Label(self.feedback_frame, text=text, font=("Consolas", 10)).pack(
            fill=tk.X, side=tk.TOP, anchor=tk.W
        )
        self.feedback_frame.update()
        self.feedback_frame.yview_moveto(1)
