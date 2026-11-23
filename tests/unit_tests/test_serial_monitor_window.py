import asyncio
import os
import tkinter as tk

import pytest
import ttkbootstrap as ttk
from ttkbootstrap.publisher import Publisher

from soniccontrol_gui.plugins import ui_plugin
from soniccontrol_gui.ui_component import UIComponent
from soniccontrol_gui.views.core.connection_window import get_enabled_connection_modes


async def wait_until(predicate):
    async def poll():
        while not predicate():
            await asyncio.sleep(0.01)

    await asyncio.wait_for(poll(), timeout=2)


@pytest.mark.asyncio
async def test_serial_monitor_launcher_can_reconnect_without_losing_output(monkeypatch):
    pty = pytest.importorskip("pty")
    # ttkbootstrap keeps style and widget callbacks even after a test destroys its Tk root.
    monkeypatch.setattr(ttk.Style, "instance", None)
    monkeypatch.setattr(Publisher, "_Publisher__subscribers", {})
    try:
        root = ttk.Window()
    except tk.TclError as exc:
        pytest.skip(f"Tk display unavailable: {exc}")

    def report_callback_exception(_exc_type, exc, traceback):
        raise exc.with_traceback(traceback)

    monkeypatch.setattr(root, "report_callback_exception", report_callback_exception)
    monkeypatch.setattr(ui_plugin.UIPluginRegistry, "_registered_plugins", set())
    monkeypatch.setattr(ui_plugin, "discover_plugins", lambda _: [])
    master, slave = pty.openpty()
    window = None
    try:
        ui_plugin.register_ui_plugins()
        plugins = ui_plugin.UIPluginRegistry.get_ui_plugins()
        assert all(mode.value != "serial_monitor" for mode in get_enabled_connection_modes())
        assert [plugin.slot_name for plugin in plugins] == ["ConnectionWindow"]
        slot = ui_plugin.UIPluginSlotComponent(UIComponent(None, root), plugins, tabs=True)
        notebook = slot.view._notebook
        assert notebook.tab(0, "text") == "Serial Monitor"
        launcher = notebook.nametowidget(notebook.tabs()[0])
        launcher.open_button.invoke()
        window = launcher._window
        monitor = window.monitor

        assert monitor.send_button.instate(["disabled"])
        monitor.port.set(os.ttyname(slave))
        monitor.baudrate.set("0")
        monitor.open_button.invoke()
        assert monitor.status.get() == "Enter a positive baud rate."

        monitor.baudrate.set("9600")
        monitor.open_button.invoke()
        await wait_until(lambda: monitor.send_button.instate(["!disabled"]))
        os.write(master, b"boot message")
        await wait_until(lambda: monitor.output.get("1.0", "end-1c") == "boot message")
        monitor.command.set("hello")
        monitor.send_button.invoke()
        os.set_blocking(master, False)
        sent = bytearray()

        def received_line():
            try:
                sent.extend(os.read(master, 64))
            except BlockingIOError:
                pass
            return len(sent) >= len(b"hello\r")

        await wait_until(received_line)
        assert sent == b"hello\r"

        monitor.close_button.invoke()
        await wait_until(lambda: monitor.status.get() == "Disconnected")
        assert window.view.is_open
        assert monitor.port_entry.instate(["!disabled"])
        assert monitor.send_button.instate(["disabled"])
        monitor.baudrate.set("19200")
        monitor.open_button.invoke()
        await wait_until(lambda: monitor.status.get().endswith("at 19200 baud"))
        os.write(master, b"\nafter reconnect")
        await wait_until(lambda: monitor.output.get("1.0", "end-1c") == "boot message\nafter reconnect")

        window.close()
        await wait_until(lambda: window._session is None and window._is_closing)
        root.update_idletasks()
        assert not window.view.is_open
    finally:
        if window is not None and window._session is not None:
            await window._stop_session()
        os.close(slave)
        os.close(master)
        root.destroy()
