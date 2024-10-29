from typing import Any, Optional, Tuple
import asyncio
import functools
import logging
import pathlib
import csv
import datetime
import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledFrame
from async_tkinter_loop import async_handler
from PIL.ImageTk import PhotoImage
import pandas as pd
import matplotlib

matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
from soniccontrol.core.interfaces import RootChild, Connectable, Root
from soniccontrol.core.components.horzontal_scrolled import HorizontalScrolledFrame

logger = logging.getLogger(__name__)


class SonicMeasureFrame(RootChild, Connectable):
    def __init__(
        self,
        master: Root,
        tab_title: str = "Sonic Measure",
        image: Optional[PhotoImage] = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(master, tab_title, image=image, *args, **kwargs)

        self.running: asyncio.Event = asyncio.Event()

        self.last_read_line = 0
        self.urms_visible: ttk.BooleanVar = ttk.BooleanVar(value=True)
        self.irms_visible: ttk.BooleanVar = ttk.BooleanVar(value=True)
        self.phase_visible: ttk.BooleanVar = ttk.BooleanVar(value=True)
        self.frequency_visible: ttk.BooleanVar = ttk.BooleanVar(value=True)

        self.main_frame: ScrolledFrame = ScrolledFrame(self, autohide=True)
        self.button_frame: ttk.Frame = ttk.Frame(self)
        self.start_stop_button: ttk.Button = ttk.Button(
            self.button_frame,
            text="Start",
            style=ttk.SUCCESS,
            image=self.root.start_image,
            compound=ttk.RIGHT,
            command=self.start_liveplot,
        )
        self.spectrum_button: ttk.Button = ttk.Button(
            self.button_frame,
            text="Open SonicMeasure Graph",
            style=ttk.DARK,
            command=self.open_spectrum_measure,
        )

        self.toggle_button_frame: ttk.Frame = ttk.Frame(self.main_frame)
        self.toggle_urms_button = ttk.Checkbutton(
            self.toggle_button_frame,
            text="Urms",
            style="dark-square-toggle",
            variable=self.urms_visible,
            command=self.toggle_urms,
        )
        self.toggle_frequency_button = ttk.Checkbutton(
            self.toggle_button_frame,
            text="Frequency",
            style="dark-square-toggle",
            variable=self.frequency_visible,
            command=self.toggle_frequency,
        )
        self.toggle_irms_button = ttk.Checkbutton(
            self.toggle_button_frame,
            text="Irms",
            style="dark-square-toggle",
            variable=self.irms_visible,
            command=self.toggle_irms,
        )
        self.toggle_phase_button = ttk.Checkbutton(
            self.toggle_button_frame,
            text="Phase",
            style="dark-square-toggle",
            variable=self.phase_visible,
            command=self.toggle_phase,
        )

        self.plot_frame: ttk.Frame = ttk.Frame(self.main_frame)
        self.figure: Figure = Figure(dpi=100)
        self.figure_canvas: FigureCanvasTkAgg = FigureCanvasTkAgg(
            self.figure, self.plot_frame
        )
        self.figure_canvas.draw()
        self.toolbar = NavigationToolbar2Tk(self.figure_canvas, self.plot_frame)
        self.toolbar.update()
        self.drawing_task = None
        self.bind_events()

    def on_connect(self, event: Any = None) -> None:
        return self.publish()

    def open_spectrum_measure(self) -> None:
        self.window = SonicMeasure(self.root, self)
        self.spectrum_button.configure(state=ttk.DISABLED)

    @async_handler
    async def start_liveplot(self) -> None:
        self.running.set()
        self.start_stop_button.configure(
            text="Stop",
            bootstyle=ttk.DANGER,
            image=self.root.pause_image,
            compound=ttk.RIGHT,
            command=self.stop_liveplot,
        )
        self.live_plot_engine()

    @async_handler
    async def live_plot_engine(self) -> None:
        self.initialize_graph()
        while self.running.is_set():
            await self.root.sonicamp.status_changed.wait()
            self.update_graph()
            await asyncio.sleep(0.2)

    def stop_liveplot(self) -> None:
        self.running.clear()
        self.start_stop_button.configure(
            bootstyle=ttk.SUCCESS,
            text="Start",
            image=self.root.start_image,
            command=self.start_liveplot,
        )
        self.figure.clear(keep_observers=False)

    def initialize_graph(self) -> None:
        self.figure.clear()
        self.figure_canvas.get_tk_widget().destroy()
        self.figure_canvas = FigureCanvasTkAgg(
            self.figure, master=self.plot_frame
        )  # Adjust master if needed
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().pack(fill=ttk.BOTH, expand=True)

        self.ax1_frequency = self.figure.add_subplot(1, 1, 1)  # Main axis for frequency
        self.ax1_frequency.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        self.ax1_frequency.tick_params(axis="x", rotation=45)

        self.ax2_urms = self.ax1_frequency.twinx()  # Secondary axis for urms
        self.ax3_irms = self.ax1_frequency.twinx()  # Tertiary axis for irms
        self.ax3_irms.spines["right"].set_position(
            ("outward", 60)
        )  # Move tertiary axis to the right
        self.ax4_phase = self.ax1_frequency.twinx()
        self.figure.subplots_adjust(right=0.8)

        (self.line_frequency,) = self.ax1_frequency.plot(
            [],
            [],
            lw=2,
            marker="o",
            markersize=4,
            linestyle="-",
            label="Frequency",
            color="black",
        )
        (self.line_urms,) = self.ax2_urms.plot(
            [],
            [],
            lw=2,
            marker="o",
            markersize=4,
            linestyle="-",
            label="Urms",
            color="blue",
        )
        (self.line_irms,) = self.ax3_irms.plot(
            [],
            [],
            lw=2,
            marker="o",
            markersize=4,
            linestyle="-",
            label="Irms",
            color="red",
        )
        (self.line_phase,) = self.ax4_phase.plot(
            [],
            [],
            lw=2,
            marker="o",
            markersize=4,
            linestyle="-",
            label="Phase",
            color="green",
        )

        self.ax1_frequency.set_xlabel("Time")
        self.ax1_frequency.set_ylabel("Frequency / Hz")
        self.ax2_urms.set_ylabel("U$_{RMS}$ / mV")
        self.ax3_irms.set_ylabel("I$_{RMS}$ / mA")
        self.ax4_phase.set_ylabel("Phase / °")

        self.time_data = []
        self.frequency_data = []
        self.phase_data = []
        self.urms_data = []
        self.irms_data = []

        self.figure.canvas.mpl_connect("draw_event", self.sync_axes)
        self.ax1_frequency.legend(
            loc="upper left",
            handles=[
                self.line_frequency,
                self.line_irms,
                self.line_urms,
                self.line_phase,
            ],
        )
        self.figure_canvas.draw()

    def sync_axes(self, event) -> None:
        self.ax2_urms.set_yticks(self.ax1_frequency.get_yticks())
        self.ax3_irms.set_yticks(self.ax1_frequency.get_yticks())
        self.ax4_phase.set_yticks(self.ax4_phase.get_yticks())

    def update_graph(self) -> None:
        data = pd.read_csv(
            self.root.status_log_filepath, skiprows=range(1, self.last_read_line)
        )
        self.last_read_line += len(data)
        data["timestamp"] = pd.to_datetime(data["timestamp"])

        self.time_data += data["timestamp"].tolist()
        self.frequency_data += data["frequency"].tolist()
        self.phase_data += data["phase"].tolist()
        self.urms_data += data["urms"].tolist()
        self.irms_data += data["irms"].tolist()

        self.line_frequency.set_data(
            self.time_data[-50:], self.frequency_data[-50:]
        )  # only plot last 100 points
        self.line_urms.set_data(self.time_data[-50:], self.urms_data[-50:])
        self.line_irms.set_data(self.time_data[-50:], self.irms_data[-50:])
        self.line_phase.set_data(self.time_data[-50:], self.phase_data[-50:])

        self.figure_canvas.draw()

        self.ax1_frequency.relim()
        self.ax1_frequency.autoscale_view()
        self.ax2_urms.relim()
        self.ax2_urms.autoscale_view()
        self.ax3_irms.relim()
        self.ax3_irms.autoscale_view()
        self.ax4_phase.relim()
        self.ax4_phase.autoscale_view()

        self.figure_canvas.flush_events()
        self.root.update()

    def toggle_frequency(self) -> None:
        self.toggle_data(
            self.frequency_visible, self.line_frequency, self.ax1_frequency
        )

    def toggle_urms(self) -> None:
        self.toggle_data(self.urms_visible, self.line_urms, self.ax2_urms)

    def toggle_irms(self) -> None:
        self.toggle_data(self.irms_visible, self.line_irms, self.ax3_irms)

    def toggle_phase(self) -> None:
        self.toggle_data(self.phase_visible, self.line_phase, self.ax4_phase)

    def toggle_data(self, tk_var: ttk.Variable, line, axis) -> None:
        is_visible = tk_var.get()
        line.set_visible(is_visible)

    def publish(self) -> None:
        self.button_frame.pack(fill=ttk.X, padx=3, pady=3)
        self.start_stop_button.pack(side=ttk.LEFT, padx=3, pady=3)
        # self.restart_button.pack(side=ttk.LEFT, padx=3, pady=3)
        self.spectrum_button.pack(side=ttk.LEFT, padx=3, pady=3)

        self.main_frame.pack(expand=True, fill=ttk.BOTH, padx=3, pady=3)

        self.toggle_button_frame.pack(fill=ttk.X, padx=3, pady=3)
        self.toggle_frequency_button.pack(side=ttk.LEFT, padx=3, pady=3)
        self.toggle_urms_button.pack(side=ttk.LEFT, padx=3, pady=3)
        self.toggle_irms_button.pack(side=ttk.LEFT, padx=3, pady=3)
        self.toggle_phase_button.pack(side=ttk.LEFT, padx=3, pady=3)

        self.plot_frame.pack(padx=3, pady=3)
        self.figure_canvas.get_tk_widget().pack(fill=ttk.BOTH, expand=True)


class SonicMeasure(ttk.Toplevel):
    def __init__(self, root: Root, parent: SonicMeasureFrame, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.root = root
        self.parent = parent
        self._last_read_line = 0
        self.time_units = ("ms", "s")

        # Ramp variables
        self.ramp_mode: ttk.StringVar = ttk.StringVar(value="ramp_freq")
        self.start_var: ttk.IntVar = ttk.IntVar(value=1000000)
        self.stop_var: ttk.IntVar = ttk.IntVar(value=2000000)
        self.step_var: ttk.IntVar = ttk.IntVar(value=10000)
        self.hold_on_time_var: ttk.DoubleVar = ttk.DoubleVar(value=100)
        self.hold_on_time_unit_var: ttk.StringVar = ttk.StringVar(value="ms")
        self.hold_off_time_var: ttk.DoubleVar = ttk.DoubleVar(value=0)
        self.hold_off_time_unit_var: ttk.StringVar = ttk.StringVar(value="ms")
        self.times_to_repeat_var: ttk.IntVar = ttk.IntVar(value=0)

        self.body_frame: ScrolledFrame = ScrolledFrame(self, autohide=True)
        self.main_frame: ttk.Frame = ttk.Frame(self.body_frame)
        self.button_frame: ttk.Frame = ttk.Frame(self.main_frame)
        self.start_stop_button: ttk.Button = ttk.Button(
            self.button_frame,
            style=ttk.SUCCESS,
            text="Start",
            image=self.root.start_image,
            compound=ttk.RIGHT,
            command=self.start_sonicmeasure,
        )

        self.plot_frame: ttk.Frame = ttk.Frame(self.main_frame)
        self.figure_canvas: MeasureCanvas = MeasureCanvas(self.plot_frame)

        self.configuration_frame: ttk.Frame = ttk.Frame(self.body_frame)
        self.navigation_bar: ttk.Frame = ttk.Frame(self.configuration_frame)
        self.back_button: ttk.Button = ttk.Button(
            self.navigation_bar,
            text="Back",
            style=ttk.DARK,
            state=ttk.DISABLED,
            image=self.root.back_image,
            compound=ttk.LEFT,
            command=self.show_mainframe,
        )
        self.submit_button: ttk.Button = ttk.Button(
            self.navigation_bar,
            text="Start Sonicmeasure",
            style=ttk.SUCCESS,
            image=self.root.forward_image,
            compound=ttk.RIGHT,
            command=self.start_sonicmeasure_process,
        )

        self.ramp_program_frame: HorizontalScrolledFrame = HorizontalScrolledFrame(
            self.configuration_frame, autohide=True, height=80
        )
        # ramp mode frame setter
        self.ramp_modes: Tuple[str] = (
            "ramp_freq",
        )  # "ramp_gain", "chirp_ramp_freq", "chirp_ramp_gain")
        self.ramp_mode_frame: ttk.LabelFrame = ttk.Labelframe(
            self.ramp_program_frame, text="Ramp Mode"
        )
        self.ramp_mode_entry: ttk.Combobox = ttk.Combobox(
            self.ramp_mode_frame,
            textvariable=self.ramp_mode,
            values=self.ramp_modes,
            width=8,
        )

        # start var frame setter
        self.start_var_frame: ttk.LabelFrame = ttk.Labelframe(
            self.ramp_program_frame, text="Start [Hz]"
        )
        self.start_var_entry: ttk.Spinbox = ttk.Spinbox(
            self.start_var_frame,
            width=8,
            textvariable=self.start_var,
            from_=0,
            to=10_000_000,
        )

        # stop_var frame setter
        self.stop_var_frame: ttk.LabelFrame = ttk.Labelframe(
            self.ramp_program_frame, text="Stop [Hz]"
        )
        self.stop_var_entry: ttk.Spinbox = ttk.Spinbox(
            self.stop_var_frame,
            width=8,
            textvariable=self.stop_var,
            from_=0,
            to=10_000_000,
        )

        # step var frame setter
        self.step_var_frame: ttk.LabelFrame = ttk.Labelframe(
            self.ramp_program_frame, text="Step [Hz]"
        )
        self.step_var_entry: ttk.Spinbox = ttk.Spinbox(
            self.step_var_frame,
            width=8,
            textvariable=self.step_var,
            from_=0,
            to=1_000_000,
        )

        # hold on frame setter
        self.hold_on_time_var_frame: ttk.LabelFrame = ttk.Labelframe(
            self.ramp_program_frame, text="Hold on time"
        )
        self.hold_on_time_var_entry: ttk.Spinbox = ttk.Spinbox(
            self.hold_on_time_var_frame,
            textvariable=self.hold_on_time_var,
            from_=0,
            width=5,
            to=10_000_000,
        )

        # hold on unit frame setter
        self.hold_on_time_unit_var_frame: ttk.LabelFrame = ttk.Labelframe(
            self.ramp_program_frame, text="Hold on time unit"
        )
        self.hold_on_time_unit_var_entry: ttk.Combobox = ttk.Combobox(
            self.hold_on_time_unit_var_frame,
            textvariable=self.hold_on_time_unit_var,
            width=3,
            values=self.time_units,
        )

        # hold off frame setter
        self.hold_off_time_var_frame: ttk.LabelFrame = ttk.Labelframe(
            self.ramp_program_frame, text="Hold off time"
        )
        self.hold_off_time_var_entry: ttk.Spinbox = ttk.Spinbox(
            self.hold_off_time_var_frame,
            textvariable=self.hold_off_time_var,
            width=5,
            from_=0,
            to=10_000_000,
        )

        # hold off unit frame setter
        self.hold_off_time_unit_var_frame: ttk.LabelFrame = ttk.Labelframe(
            self.ramp_program_frame, text="Hold off time unit"
        )
        self.hold_off_time_unit_var_entry: ttk.Combobox = ttk.Combobox(
            self.hold_off_time_unit_var_frame,
            width=3,
            textvariable=self.hold_off_time_unit_var,
            values=self.time_units,
        )

        self.static_values_frame: ttk.Labelframe = ttk.Labelframe(
            self.configuration_frame,
            text="Set up values, that are set before the ramp algorithm",
        )
        self.gain_frame: ttk.Labelframe = ttk.Labelframe(
            self.static_values_frame, text="Gain"
        )
        self.gain_entry: ttk.Spinbox = ttk.Spinbox(
            self.gain_frame,
            width=8,
            textvariable=self.root.set_gain_var,
            from_=0,
            to=150,
        )

        self.freq_frame: ttk.Labelframe = ttk.Labelframe(
            self.static_values_frame, text="Frequency"
        )
        self.freq_entry: ttk.Spinbox = ttk.Spinbox(
            self.freq_frame,
            width=8,
            textvariable=self.root.set_frequency_var,
            from_=0,
            to=10_000_000,
        )

        self.logfile_specifier_frame: ttk.Labelframe = ttk.Labelframe(
            self.configuration_frame, text="Specify the filepath for the data storage"
        )
        self.logfile_entry: ttk.Entry = ttk.Entry(
            self.logfile_specifier_frame, textvariable=self.root.sonicmeasure_log_var
        )
        self.browse_files_button: ttk.Button = ttk.Button(
            self.logfile_specifier_frame,
            text="Browse files...",
            style=ttk.SECONDARY,
            command=self.open_log_file,
        )
        self.comment_frame: ttk.Labelframe = ttk.Labelframe(
            self.configuration_frame, text="Make a comment on your data"
        )
        self.comment_entry: ttk.ScrolledText = ttk.ScrolledText(self.comment_frame)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.publish()
        self.start_sonicmeasure()

    def open_log_file(self, event=None) -> None:
        self.log_file_path_var.set(
            ttk.filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=self._filetypes
            )
        )
        logger.debug(f"The new logfile path is: {self.logfile}")

    def on_closing(self) -> None:
        self.root.sonicmeasure_running.clear()
        self.parent.spectrum_button.configure(state=ttk.NORMAL)
        self.destroy()

    def start_sonicmeasure(self) -> None:
        self.main_frame.pack_forget()
        self.configuration_frame.pack(padx=15, fill=ttk.BOTH, expand=True)
        self.root.sonicmeasure_log_var.set(
            f"logs//sonicmeasure_{str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')}.csv"
        )
        self.root.sonicmeasure_logfile = pathlib.Path(
            self.root.sonicmeasure_log_var.get()
        )

    @async_handler
    async def start_sonicmeasure_process(self) -> None:
        self.back_button.configure(state=ttk.NORMAL)
        self.start_stop_button.configure(
            text="Stop",
            bootstyle=ttk.DANGER,
            image=self.root.pause_image,
            compound=ttk.RIGHT,
            command=self.stop_sonicmeasure,
        )
        self.root.sonicmeasure_running.set()
        self.show_mainframe()

        self.plot_frame.destroy()
        self.plot_frame = ttk.Frame(self.main_frame)
        del self.figure_canvas
        self.figure_canvas = MeasureCanvas(
            self.plot_frame, self.start_var.get(), self.stop_var.get()
        )
        self.plot_frame.pack(padx=3, pady=3)
        await asyncio.sleep(0.2)

        await self.sonicmeasure_setup()

    async def sonicmeasure_setup(self) -> None:
        with self.root.sonicmeasure_logfile.open("a", newline="") as file:
            writer = csv.DictWriter(
                file, fieldnames=self.root.fieldnames, extrasaction="ignore"
            )
            writer.writeheader()

        try:
            # await self.root.sonicamp.set_relay_mode_mhz() 
            try:
                logger.debug(f"Frequency is: {self.root.set_frequency_var.get()}")
                await self.root.sonicamp.set_frequency(self.root.set_frequency_var.get())
            except Exception as e:
                logger.warning(e)
            try:
                logger.debug(f"Gain is: {self.root.set_gain_var.get()}")
                await self.root.sonicamp.set_gain(self.root.set_gain_var.get())
            except Exception as e:
                logger.warning(e)     
        except Exception as e:
            logger.warning(e)

        self.ramp_task = asyncio.create_task(
            self.root.sonicamp.ramp_freq(
                self.start_var.get(),
                self.stop_var.get(),
                self.step_var.get(),
                self.hold_on_time_var.get(),
                self.hold_on_time_unit_var.get(),
                self.hold_off_time_var.get(),
                self.hold_off_time_unit_var.get(),
                event=self.root.sonicmeasure_running,
            )
        )
        self.worker = asyncio.create_task(self.ramp_worker())
        await asyncio.gather(self.ramp_task, self.worker)

    async def ramp_worker(self) -> None:
        await self.root.sonicamp.ramper.running.wait()
        while (
            self.root.sonicmeasure_running.is_set()
            and self.root.sonicamp.ramper.running.is_set()
        ):
            await self.root.sonicamp.status_changed.wait()
            self.root.serialize_data(
                self.root.sonicamp.status, self.root.sonicmeasure_logfile
            )
            self.figure_canvas.update(self.root.sonicmeasure_logfile)
            await asyncio.sleep(0.1)
        self.stop_sonicmeasure()

    def stop_sonicmeasure(self) -> None:
        self.root.sonicmeasure_running.clear()
        self.start_stop_button.configure(
            bootstyle=ttk.SUCCESS,
            text="Start",
            image=self.root.start_image,
            command=self.start_sonicmeasure,
        )

    def show_mainframe(self) -> None:
        self.configuration_frame.pack_forget()
        self.main_frame.pack(fill=ttk.BOTH, expand=True, padx=3, pady=3)

    def publish(self) -> None:
        self.body_frame.pack(fill=ttk.BOTH, expand=True)
        self.main_frame.pack(expand=True, fill=ttk.BOTH, padx=3, pady=3)

        self.button_frame.pack(fill=ttk.X, padx=3, pady=3)
        self.start_stop_button.pack(side=ttk.LEFT, padx=3, pady=3)
        # self.pause_resume_button.pack(side=ttk.LEFT, padx=3, pady=3)

        self.plot_frame.pack(padx=3, pady=3)
        self.figure_canvas.get_tk_widget().pack(fill=ttk.BOTH, expand=True)

        self.navigation_bar.pack(pady=5, fill=ttk.X)
        self.back_button.pack(pady=5, side=ttk.LEFT)
        self.submit_button.pack(pady=5, side=ttk.RIGHT)

        self.static_values_frame.pack(padx=3, pady=3, fill=ttk.X, expand=True)
        self.gain_frame.pack(side=ttk.LEFT, expand=True, padx=3, pady=3)
        self.gain_entry.pack(fill=ttk.BOTH, padx=2, pady=2)
        self.freq_frame.pack(side=ttk.LEFT, expand=True, padx=3, pady=3)
        self.freq_entry.pack(fill=ttk.BOTH, padx=2, pady=2)

        self.ramp_program_frame.pack(padx=3, pady=3, fill=ttk.X, expand=True)
        self.ramp_mode_frame.pack(
            side=ttk.LEFT, fill=ttk.X, expand=True, padx=3, pady=3
        )
        self.start_var_frame.pack(
            side=ttk.LEFT, fill=ttk.X, expand=True, padx=3, pady=3
        )
        self.stop_var_frame.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=3, pady=3)
        self.step_var_frame.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=3, pady=3)
        self.hold_on_time_var_frame.pack(
            side=ttk.LEFT, fill=ttk.X, expand=True, padx=3, pady=3
        )
        self.hold_on_time_unit_var_frame.pack(
            side=ttk.LEFT, fill=ttk.X, expand=True, padx=3, pady=3
        )
        self.hold_off_time_var_frame.pack(
            side=ttk.LEFT, fill=ttk.X, expand=True, padx=3, pady=3
        )
        self.hold_off_time_unit_var_frame.pack(
            side=ttk.LEFT, fill=ttk.X, padx=3, pady=3
        )

        self.ramp_mode_entry.pack(fill=ttk.BOTH, expand=True, padx=2, pady=2)
        self.start_var_entry.pack(fill=ttk.BOTH, expand=True, padx=2, pady=2)
        self.stop_var_entry.pack(fill=ttk.BOTH, expand=True, padx=2, pady=2)
        self.step_var_entry.pack(fill=ttk.BOTH, expand=True, padx=2, pady=2)
        self.hold_on_time_var_entry.pack(fill=ttk.BOTH, expand=True, padx=2, pady=2)
        self.hold_on_time_unit_var_entry.pack(
            fill=ttk.BOTH, expand=True, padx=2, pady=2
        )
        self.hold_off_time_var_entry.pack(fill=ttk.BOTH, expand=True, padx=2, pady=2)
        self.hold_off_time_unit_var_entry.pack(
            fill=ttk.BOTH, expand=True, padx=2, pady=2
        )

        self.logfile_specifier_frame.pack(pady=10, fill=ttk.X)
        self.logfile_entry.pack(side=ttk.LEFT, fill=ttk.X, padx=5, pady=5, expand=True)
        self.browse_files_button.pack(side=ttk.RIGHT, fill=ttk.X, padx=5, pady=5)

        # self.comment_frame.pack(pady=5)
        self.comment_entry.pack(padx=5, pady=5)


class MeasureCanvas(FigureCanvasTkAgg):
    def __init__(self, master=..., start: int = 0, stop: int = 6_000_000) -> None:
        self.master: ttk.Frame = master
        self.figure: Figure = Figure(dpi=100)
        self.toolbar = NavigationToolbar2Tk(self, master)
        super().__init__(self.figure, master)

        self._last_read_line: int = 1
        self._lock: asyncio.Lock = asyncio.Lock()
        self.get_tk_widget().pack(fill=ttk.BOTH, expand=True)

        self.ax_urms = self.figure.add_subplot(111)
        self.figure.subplots_adjust(right=0.8)

        self.ax_irms = self.ax_urms.twinx()
        self.ax_phase = self.ax_urms.twinx()
        self.ax_phase.spines["right"].set_position(("axes", 1.15))

        (self.line_urms,) = self.ax_urms.plot(
            [], [], "bo-", label="U$_{RMS}$ / mV", markersize=4, lw=2
        )
        (self.line_irms,) = self.ax_irms.plot(
            [], [], "ro-", label="I$_{RMS}$ / mA", markersize=4, lw=2
        )
        (self.line_phase,) = self.ax_phase.plot(
            [], [], "go-", label="Phase / °", markersize=4, lw=2
        )

        self.ax_urms.set_xlim(start, stop)
        self.ax_urms.set_xlabel("Frequency / Hz")
        self.ax_urms.set_ylabel("U$_{RMS}$ / mV")
        self.ax_irms.set_ylabel("I$_{RMS}$ / mA")
        self.ax_phase.set_ylabel("Phase / °")

        self.ax_urms.yaxis.label.set_color(self.line_urms.get_color())
        self.ax_irms.yaxis.label.set_color(self.line_irms.get_color())
        self.ax_phase.yaxis.label.set_color(self.line_phase.get_color())

        self.ax_urms.legend(handles=[self.line_urms, self.line_irms, self.line_phase])

        self.time_data = []
        self.frequency_data = []
        self.phase_data = []
        self.urms_data = []
        self.irms_data = []

        self.draw()

    @async_handler
    async def update(self, path: pathlib.Path) -> None:
        async with self._lock:
            data = pd.read_csv(path, skiprows=range(1, self._last_read_line))
            self._last_read_line += len(data)

            self.frequency_data += data["frequency"].tolist()
            self.urms_data += data["urms"].tolist()
            self.irms_data += data["irms"].tolist()
            self.phase_data += data["phase"].tolist()

            self.line_urms.set_data(self.frequency_data, self.urms_data)
            self.line_irms.set_data(self.frequency_data, self.irms_data)
            self.line_phase.set_data(self.frequency_data, self.phase_data)

            self.draw()

            self.ax_urms.relim()
            self.ax_urms.autoscale_view()
            self.ax_irms.relim()
            self.ax_irms.autoscale_view()
            self.ax_phase.relim()
            self.ax_phase.autoscale_view()

            self.flush_events()
            self.master.update()
