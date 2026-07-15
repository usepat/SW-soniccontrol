import asyncio
import contextlib
from pathlib import Path
import pytest_asyncio
from ttkbootstrap.utility import enable_high_dpi_awareness

from soniccontrol import commands as cmds
from sonic_pytest.plugin_data import SonicControlPlugin, get_sonic_control_plugin
from soniccontrol import DeviceType
from soniccontrol.app_config import APP_CONFIG
from soniccontrol.app_config import PLATFORM, System
from soniccontrol.data_capturing.device_performance.performance_monitor import PerformanceMonitor
from soniccontrol.sonic_device import SonicDevice
from soniccontrol_gui.plugins.device_plugin import register_device_plugins
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.views.core.connection_window import ConnectionWindow
from soniccontrol_gui.constants import ui_labels
from sonic_pytest.gui import widget_names
from sonic_pytest.gui.gui_controller import GuiController
from sonic_pytest.gui.workflows import postman_wait_for_worker_to_be_connected, send_over_serial_monitor
from sonic_pytest.fixtures import create_worker_process_impl
from sonic_pytest.plugin_data import mark_modbus_device_prepared, modbus_device_preparation_is_required
from sonic_pytest.remote_controller.fixtures import prepare_modbus_device, resolve_device_info
from soniccontrol_gui.views.core.postman_window import PostmanDeviceWindow


# NOTE: If you write a Test, it will automatically use the fixtures below, because they are autouse=True
# Also their scope is package, so they are executed once for the whole folder.
# They have an own event loop and you have to set loop_scope="package" on the Tests, 
# in order to tell pytest_asyncio, that the same event loop should be used to run the tests.


@pytest_asyncio.fixture(loop_scope="package", scope="package")
async def connection_window(request):
    loop = asyncio.get_running_loop()

    plugin_config = get_sonic_control_plugin(request.config)
    simulation_exe_path: Path = plugin_config.simulation_exe_path
    remote_server_url: str | None = plugin_config.remote_server_url

    APP_CONFIG.remote_server_url = remote_server_url
    
    ImageLoader.clear_resources()
    WidgetRegistry.set_up(loop)
    register_device_plugins()

    connection_window = ConnectionWindow(simulation_exe_path)
    await connection_window.wait_finished_loading()
    root = connection_window.view.root 
    WidgetRegistry.root = root
    if PLATFORM != System.WINDOWS:
        enable_high_dpi_awareness(connection_window.view)

    yield connection_window

    root.update_idletasks()
    root.destroy()

    await WidgetRegistry.clean_up()

    ImageLoader.clear_resources()



create_worker_process = pytest_asyncio.fixture(create_worker_process_impl, scope="package")

def configure_simulation_connection(controller: GuiController, device_type: DeviceType, data_dir: Path) -> None:
    if device_type == DeviceType.DESCALE:
        controller.set_widget_text(
            widget_names.CONNECTION_SIMULATION_CMD_ARGS,
            f'--name=test_descale --profile=descale --data-dir="{data_dir}"',
        )
    elif device_type == DeviceType.MVP_WORKER:
        controller.set_widget_text(
            widget_names.CONNECTION_SIMULATION_CMD_ARGS,
            f'--name=test_worker --profile=worker --data-dir="{data_dir}"',
        )
    elif device_type == DeviceType.POSTMAN:
        controller.set_widget_text(
            widget_names.CONNECTION_SIMULATION_CMD_ARGS,
            f'--name=test_postman --profile=postman --data-dir="{data_dir}"',
        )
    else:
        raise NotImplementedError(f"For the {device_type} no case is implemented")

    controller.press_button(widget_names.CONNECTION_CONNECT_TO_SIMULATION_BUTTON)

@pytest_asyncio.fixture(loop_scope="package", scope="package", autouse=True)
async def device_window(request, connection_window, tmp_path_factory, create_worker_process):
    controller = GuiController()    

    plugin: SonicControlPlugin = get_sonic_control_plugin(request.config)
    device_type = plugin.device_type
    data_dir = tmp_path_factory.mktemp("data")

    if not plugin.is_simulation:
        if modbus_device_preparation_is_required(plugin, request.node):
            await prepare_modbus_device(plugin, plugin.log_path)
            mark_modbus_device_prepared(plugin)

        port: str | None = plugin.serial_port if plugin.modbus_serial_port is None else plugin.modbus_serial_port 
        assert port is not None, "You have to provide a port"
        dev_info = await resolve_device_info(port, plugin.remote_server_url)
        assert dev_info is not None, "Could find no device on the given port"
        if plugin.modbus_serial_port is not None:
            controller.press_button(widget_names.CONNECTION_IS_MODBUS_DEVICE_CHECKBOX)
        controller.set_widget_text(widget_names.CONNECTION_PORTS_COMBOBOX, dev_info.display_name)
        controller.press_button(widget_names.CONNECTION_CONNECT_VIA_URL_BUTTON)
    else:
        configure_simulation_connection(controller, device_type, data_dir)

    # This is for the edge case, that if we connect to a remote device with an already ongoing connection
    # In that case remove the old connection, by pressing yes on the message box
    await controller.execute_events_until_idle()
    try:
        await controller.wait_for_widget_to_be_registered(widget_names.MESSAGE_BOX_OPTION_YES, 2.0)
    except asyncio.TimeoutError:
        pass
    else:
        controller.press_button(widget_names.MESSAGE_BOX_OPTION_YES)

    device_window = await connection_window.wait_until_window_loaded()
    # handle all events from tkinter. Ensure everything is loaded
    await controller.execute_events_until_idle()

    if device_type == DeviceType.POSTMAN:
        await postman_wait_for_worker_to_be_connected()

        # connect to the worker over the postman window
        # the fixture create_worker_process is responsible for starting the worker simulation process
        controller.press_button(widget_names.widget_of_window(widget_names.POSTMAN, widget_names.CONNECT_TO_WORKER_BUTTON))

        assert isinstance(device_window, PostmanDeviceWindow) # for correct type hints
        device_window = await asyncio.wait_for(device_window.wait_until_worker_window_loaded(), 5) 
        
    yield device_window

    with contextlib.suppress(Exception):
        device_window.close()
        await controller.execute_events_until_idle()


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def performance_monitor(device_window, request):
    device: SonicDevice = device_window.device
    assert device is not None

    monitor = PerformanceMonitor(device)
    updater = getattr(device_window, "_updater", None)
    was_updater_running = bool(updater is not None and updater.running.is_set())

    yield monitor

    if updater is not None and was_updater_running:
        await updater.stop()

    should_skip_performance_check = "skip_performance_monitor_check" in request.node.keywords
    should_check_performance = not should_skip_performance_check

    if should_check_performance and device.communicator.connection_opened.is_set() and device.has_command(cmds.GetNumAllocators()):
        snap_shot = await monitor.sample_memory_snapshot()
        snap_shot.check_performance()

    if updater is not None and was_updater_running and device.communicator.connection_opened.is_set():
        updater.start()


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def default_state(device_window):
    controller = GuiController()
    updater = getattr(device_window, "_updater", None)
    device = device_window.device

    if (
        updater is not None
        and not updater.running.is_set()
        and device is not None
        and device.communicator.connection_opened.is_set()
    ):
        updater.start()
        await controller.execute_events_until_idle()

    await send_over_serial_monitor("!stop", allow_fail=True)
    if device.info.device_type == DeviceType.MVP_WORKER:
        await send_over_serial_monitor("!freq=100000")
    if device.info.device_type == DeviceType.DESCALE:
        await send_over_serial_monitor("!swf=5")
    await send_over_serial_monitor("!gain=50")
    await send_over_serial_monitor("!OFF")

    if device is not None and device.info.device_type == DeviceType.DESCALE:
        await controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_SWF_LABEL, "5", 5.0)
    else:
        await controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_FREQ_LABEL, "100000", 5.0)

    await controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_GAIN_LABEL, "50", 5.0)
    await controller.wait_for_widget_text_to_contain(widget_names.STATUS_BAR_SIGNAL_LABEL, "off", 5.0)

    if controller.is_widget_registered(widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL):
        running_proc_label = controller.get_widget_text(widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL)
        if running_proc_label != ui_labels.PROC_NOT_RUNNING:
            await controller.wait_for_widget_text(
                widget_names.PROC_CONTROLLING_RUNNING_PROC_LABEL,
                lambda text: text == ui_labels.PROC_NOT_RUNNING,
                5.0,
            )

    controller.clear_text_changed_flags()
