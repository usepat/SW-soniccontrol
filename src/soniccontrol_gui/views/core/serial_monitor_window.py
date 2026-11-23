import asyncio
import codecs
import logging
import tkinter as tk

from async_tkinter_loop import async_handler
from serial import SerialException
from serial.tools import list_ports
import ttkbootstrap as ttk

from soniccontrol.fw_device.connection import SerialConnection
from soniccontrol_gui.constants import sizes, ui_labels
from soniccontrol_gui.resources import images
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.view import TabView, View
from soniccontrol_gui.views.core.device_window import DeviceWindow, DeviceWindowView


class SerialMonitorLauncherView(View):
    def _initialize_children(self) -> None:
        self._window: SerialMonitorWindow | None = None
        self.open_button = ttk.Button(self, text="Open Serial Monitor", command=self._open_monitor)

    def _initialize_publish(self) -> None:
        self.open_button.pack(anchor=ttk.W, padx=8, pady=8)

    def _open_monitor(self) -> None:
        if self._window is None or not self._window.view.is_open:
            self._window = SerialMonitorWindow(self.root)
        self._window.view.lift()
        self._window.view.focus_set()


class SerialMonitorWindow(DeviceWindow):
    def __init__(self, root: tk.Tk | tk.Toplevel) -> None:
        self._terminal_window = DeviceWindowView(root, split=False)
        self._terminal_window.title(ui_labels.SERIAL_MONITOR_LABEL)
        super().__init__(logging.getLogger("serial_monitor.ui"), self._terminal_window, window_name="serial_monitor")
        self.monitor = SerialTerminalView(self._terminal_window)
        self._session: asyncio.Task[None] | None = None
        self._stopping = False
        self._writer: asyncio.StreamWriter | None = None
        self.monitor.refresh_button.configure(command=self._refresh_ports)
        self.monitor.open_button.configure(command=self._open_port)
        self.monitor.close_button.configure(command=self._close_port)
        self.monitor.send_button.configure(command=self._send)
        self.monitor.command_entry.bind("<Return>", lambda _: self._send())
        self._refresh_ports()

        self._terminal_window.add_tab_views([self.monitor])

    @property
    def view(self) -> DeviceWindowView:
        return self._terminal_window

    def _refresh_ports(self) -> None:
        try:
            ports = [port.device for port in sorted(list_ports.comports())]
        except OSError as exc:
            self._report_error("Could not list serial ports", exc)
        else:
            self.monitor.port_entry.configure(values=ports)

    def _open_port(self) -> None:
        if self._session is not None or self._is_closing:
            return
        port = self.monitor.port.get().strip()
        if not port:
            self.monitor.status.set("Choose or enter a serial port.")
            return
        try:
            baudrate = int(self.monitor.baudrate.get())
            if baudrate <= 0:
                raise ValueError
        except ValueError:
            self.monitor.status.set("Enter a positive baud rate.")
            return
        self.monitor.status.set(f"Opening {port}...")
        self.monitor.set_port_controls(active=True, connected=False)
        self._stopping = False
        self._session = asyncio.create_task(self._run_session(port, baudrate))

    async def _run_session(self, port: str, baudrate: int) -> None:
        connection = SerialConnection(port, None, url=port, baudrate=baudrate)
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        try:
            reader, self._writer = await connection.open_connection()
            self.monitor.status.set(f"Connected to {port} at {baudrate} baud")
            self.monitor.set_port_controls(active=True, connected=True)
            while data := await reader.read(4096):
                self.monitor.append(decoder.decode(data))
            self.monitor.append(decoder.decode(b"", final=True))
            self.monitor.status.set("Serial port disconnected.")
        except (OSError, SerialException, ValueError) as exc:
            self._report_error("Serial connection failed", exc)
        finally:
            self._stopping = True
            self._writer = None
            self.monitor.set_port_controls(active=True, connected=False)
            try:
                await connection.close_connection()
            finally:
                self._session = None
                if not self._is_closing:
                    self.monitor.set_port_controls(active=False, connected=False)

    @async_handler
    async def _close_port(self) -> None:
        await self._stop_session()
        if not self._is_closing:
            self.monitor.status.set("Disconnected")

    async def _stop_session(self) -> None:
        session = self._session
        if session is None:
            return
        self.monitor.set_port_controls(active=True, connected=False)
        if not self._stopping:
            self._stopping = True
            session.cancel()
        try:
            await asyncio.shield(session)
        except asyncio.CancelledError:
            if not session.cancelled():
                raise
        finally:
            if self._session is session and session.done():
                self._session = None
                if not self._is_closing:
                    self.monitor.set_port_controls(active=False, connected=False)

    async def _shutdown_before_close(self) -> None:
        await self._stop_session()

    def _send(self) -> None:
        writer = self._writer
        if writer is None or writer.is_closing() or self._is_closing:
            return
        line = self.monitor.command.get()
        try:
            writer.write((line + "\r").encode())
        except (OSError, SerialException) as exc:
            self._report_error("Could not send", exc)
        else:
            self.monitor.command.set("")

    def _report_error(self, message: str, error: Exception) -> None:
        self.logger.warning("%s: %s", message, error)
        self.monitor.status.set(f"{message}: {error}")


class SerialTerminalView(TabView):
    @property
    def tab_title(self) -> str:
        return ui_labels.SERIAL_MONITOR_LABEL

    @property
    def image(self):
        return ImageLoader.load_image_resource(images.CONSOLE_ICON_BLACK, sizes.TAB_ICON_SIZE)

    def _initialize_children(self) -> None:
        self.port = tk.StringVar(self)
        self.baudrate = tk.StringVar(self, "115200")
        self.status = tk.StringVar(self, "Disconnected")
        self.command = tk.StringVar(self)

        self.connection_frame = ttk.Frame(self)
        self.port_entry = ttk.Combobox(self.connection_frame, textvariable=self.port)
        self.baudrate_entry = ttk.Combobox(
            self.connection_frame, textvariable=self.baudrate, width=9,
            values=("9600", "19200", "38400", "57600", "115200"),
        )
        self.refresh_button = ttk.Button(self.connection_frame, text="Refresh")
        self.open_button = ttk.Button(self.connection_frame, text="Connect")
        self.close_button = ttk.Button(self.connection_frame, text="Disconnect")
        self.status_label = ttk.Label(self, textvariable=self.status, wraplength=560)

        self.output_frame = ttk.Frame(self)
        self.output = tk.Text(self.output_frame, state=ttk.DISABLED, wrap=ttk.WORD)
        self.scrollbar = ttk.Scrollbar(self.output_frame, orient=ttk.VERTICAL, command=self.output.yview)
        self.output.configure(yscrollcommand=self.scrollbar.set)
        self.input_frame = ttk.Frame(self)
        self.command_entry = ttk.Entry(self.input_frame, textvariable=self.command)
        self.send_button = ttk.Button(self.input_frame, text=ui_labels.SEND_LABEL)
        self.clear_button = ttk.Button(self.input_frame, text="Clear", command=self._clear)
        self.set_port_controls(active=False, connected=False)

    def _initialize_publish(self) -> None:
        self.connection_frame.pack(fill=ttk.X, padx=8, pady=8)
        ttk.Label(self.connection_frame, text="Port").grid(row=0, column=0, padx=4)
        self.port_entry.grid(row=0, column=1, padx=4, sticky=ttk.EW)
        self.refresh_button.grid(row=0, column=2, padx=4)
        ttk.Label(self.connection_frame, text="Baud rate").grid(row=0, column=3, padx=4)
        self.baudrate_entry.grid(row=0, column=4, padx=4)
        self.open_button.grid(row=0, column=5, padx=4)
        self.close_button.grid(row=0, column=6, padx=4)
        self.connection_frame.columnconfigure(1, weight=1)
        self.status_label.pack(fill=ttk.X, padx=12)

        self.output_frame.pack(fill=ttk.BOTH, expand=True, padx=8, pady=8)
        self.scrollbar.pack(side=ttk.RIGHT, fill=ttk.Y)
        self.output.pack(fill=ttk.BOTH, expand=True)
        self.input_frame.pack(fill=ttk.X, padx=8, pady=(0, 8))
        self.command_entry.pack(side=ttk.LEFT, fill=ttk.X, expand=True, padx=(0, 4))
        self.send_button.pack(side=ttk.LEFT, padx=4)
        self.clear_button.pack(side=ttk.LEFT, padx=4)

    def set_port_controls(self, *, active: bool, connected: bool) -> None:
        for widget in (self.port_entry, self.baudrate_entry, self.refresh_button, self.open_button):
            widget.configure(state=ttk.DISABLED if active else ttk.NORMAL)
        for widget in (self.command_entry, self.send_button, self.close_button):
            widget.configure(state=ttk.NORMAL if connected else ttk.DISABLED)

    def append(self, text: str) -> None:
        if not text:
            return
        self.output.configure(state=ttk.NORMAL)
        self.output.insert(ttk.END, text)
        self.output.configure(state=ttk.DISABLED)
        self.output.see(ttk.END)

    def _clear(self) -> None:
        self.output.configure(state=ttk.NORMAL)
        self.output.delete("1.0", ttk.END)
        self.output.configure(state=ttk.DISABLED)
