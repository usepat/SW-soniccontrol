import asyncio
import contextlib
from pathlib import Path
from async_tkinter_loop import main_loop
import pytest_asyncio
from ttkbootstrap.utility import enable_high_dpi_awareness

from sonic_pytest.plugin_data import SonicControlPlugin
from soniccontrol import DeviceType
from soniccontrol.app_config import APP_CONFIG
from soniccontrol.app_config import PLATFORM, System
from soniccontrol.data_capturing.device_performance.performance_monitor import PerformanceMonitor
from soniccontrol.fw_device import create_device_discovery
from soniccontrol_gui.plugins.device_plugin import register_device_plugins
from soniccontrol_gui.utils.image_loader import ImageLoader
from soniccontrol_gui.utils.widget_registry import WidgetRegistry
from soniccontrol_gui.views.core.connection_window import ConnectionWindow
from sonic_pytest.gui import widget_names
from sonic_pytest.gui.gui_controller import GuiController
from sonic_pytest.gui.workflows import postman_wait_for_worker_to_be_connected, send_over_serial_monitor
from sonic_pytest.fixtures import create_worker_process_impl
from soniccontrol_gui.views.core.postman_window import PostmanDeviceWindow


# NOTE: If you write a Test, it will automatically use the fixtures below, because they are autouse=True
# Also their scope is package, so they are executed once for the whole folder.
# They have an own event loop and you have to set loop_scope="package" on the Tests, 
# in order to tell pytest_asyncio, that the same event loop should be used to run the tests.


@pytest_asyncio.fixture(loop_scope="package", scope="package")
async def connection_window(request):
    loop = asyncio.get_running_loop()

    simulation_exe_path: Path = request.config._sonic_control_plugin.simulation_exe_path
    remote_server_url: str | None = request.config._sonic_control_plugin.remote_server_url

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

    tk_task = loop.create_task(main_loop(connection_window.view)) # type: ignore

    yield connection_window

    tk_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await tk_task

    root.update_idletasks()
    root.destroy()
    
    await WidgetRegistry.clean_up()
    ImageLoader.clear_resources()



create_worker_process = pytest_asyncio.fixture(create_worker_process_impl, scope="package")

@pytest_asyncio.fixture(loop_scope="package", scope="package", autouse=True)
async def device_window(request, connection_window, tmp_path_factory, create_worker_process):
    controller = GuiController()    

    plugin: SonicControlPlugin = request.config._sonic_control_plugin
    device_type = plugin.device_type
    data_dir = tmp_path_factory.mktemp("data")

    if not plugin.is_simulation:
        port: str | None = plugin.serial_port
        assert port is not None, "You have to provide a port"
        dev_info = await create_device_discovery(plugin.remote_server_url).get_fw_device_info_of(port)
        assert dev_info is not None, "Could find no device on the given port"
        
        controller.set_widget_text(widget_names.CONNECTION_PORTS_COMBOBOX, dev_info.display_name)
        controller.press_button(widget_names.CONNECTION_CONNECT_VIA_URL_BUTTON)
    else:
        if device_type == DeviceType.DESCALE:
            controller.set_widget_text(
                widget_names.CONNECTION_SIMULATION_CMD_ARGS, 
                f"--name=test_descale --profile=descale --data-dir=\"{data_dir}\""
            )
        elif device_type == DeviceType.MVP_WORKER:
            controller.set_widget_text(
                widget_names.CONNECTION_SIMULATION_CMD_ARGS, 
                f"--name=test_worker --profile=worker --data-dir=\"{data_dir}\""
            )
        elif device_type == DeviceType.POSTMAN:
            controller.set_widget_text(
                widget_names.CONNECTION_SIMULATION_CMD_ARGS, 
                f"--name=test_postman --profile=postman --data-dir=\"{data_dir}\""
            )
        else:
            raise NotImplementedError(f"For the {device_type} no case is implemented")

        controller.press_button(widget_names.CONNECTION_CONNECT_TO_SIMULATION_BUTTON)

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


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def performance_monitor(device_window):
    device = device_window.device
    assert device is not None

    monitor = PerformanceMonitor(device)
    yield monitor

    snap_shot = await monitor.sample_memory_snapshot()
    snap_shot.check_performance()


@pytest_asyncio.fixture(scope="function", loop_scope="package", autouse=True)
async def default_state(device_window):
    await send_over_serial_monitor("!freq=100000")
    await send_over_serial_monitor("!gain=100")
    await send_over_serial_monitor("!OFF")
    GuiController().clear_text_changed_flags()
