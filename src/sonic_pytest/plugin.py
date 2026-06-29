import os
from pathlib import Path
from typing import List
from sonic_protocol.schema import DeviceType
import pytest

from soniccontrol.app_config import get_simulation_exe
from sonic_pytest.plugin_data import SonicControlPlugin, Profile, get_sonic_control_plugin


def pytest_addoption(parser):
    parser.addoption(
        "--profile",
        action="store",
        default=os.getenv("TEST_PROFILE", Profile.simulation_postman_worker.name),
        choices=(profile.name for profile in Profile),
        help="Choose a profile to execute",
    )
    parser.addoption(
        "--serial-port",
        action="store",
        default=os.getenv("TEST_URL", None),
    )
    parser.addoption(
        "--modbus-serial-port",
        action="store",
        default=os.getenv("TEST_MODBUS_SERIAL_PORT", None),
    )
    parser.addoption(
        "--log-path",
        action="store",
        default=Path("./output/test_logs"),
        help="Choose the directory, where the logs should be placed",
    )
    parser.addoption(
        "--remote-server-url",
        action="store",
        default=os.getenv("TEST_REMOTE_SERVER_URL", None),
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "allowed_devices(*device_list): mark test to run only for certain selected devices",
    )
    config.addinivalue_line(
        "markers",
        "skip_if_proc_not_enabled(proc): mark test to run only if the proc is enabled on the device",
    )
    config.addinivalue_line(
        "markers",
        "skip_if_modbus_enabled: mark test to run only if device is not a modbus device",
    )
    config.addinivalue_line(
        "markers",
        "skip_remote_test_setup: skip the default remote test state reset fixture",
    )
    config.addinivalue_line(
        "markers",
        "reprepare_modbus_device: rerun shared modbus device preparation before this test",
    )

    profile = Profile[config.getoption("--profile")]
    serial_port = config.getoption("--serial-port")
    modbus_serial_port = config.getoption("--modbus-serial-port")
    log_path = Path(config.getoption("--log-path"))
    remote_server_url = config.getoption("--remote-server-url")
  
    device = None
    match profile:
        case Profile.simulation_descale | Profile.device_descale:
            device = DeviceType.DESCALE
        case Profile.simulation_worker | Profile.device_worker:
            device = DeviceType.MVP_WORKER
        case Profile.device_postman_worker | Profile.simulation_postman_worker:
            device = DeviceType.POSTMAN
        case _:
            raise NotImplementedError("This profile is not supported")
    
    is_simulation = profile in [
        Profile.simulation_descale, 
        Profile.simulation_worker, 
        Profile.simulation_postman_worker
    ]

    simulation_exe_path = get_simulation_exe()
    assert simulation_exe_path is not None, "Firmware build dir was not set in the environment variables"
    config._sonic_control_plugin = SonicControlPlugin(
        is_simulation, serial_port, modbus_serial_port,
        device, simulation_exe_path, log_path, remote_server_url
    )


def _get_skip_reason(item: pytest.Item) -> str | None:
    plugin = get_sonic_control_plugin(item.config)

    if item.get_closest_marker("skip_if_modbus_enabled") and plugin.modbus_serial_port is not None:
        return "The test is not supported for modbus devices"

    allowed_devices: List[DeviceType] = [ 
        arg 
        for mark in item.iter_markers(name="allowed_devices") 
        for arg in mark.args
    ]
    if len(allowed_devices) == 0:
        return None
    
    device_type = plugin.device_type
    if device_type not in allowed_devices:
        return f"The device type {device_type.name} is not supported for this test"

    return None


def pytest_collection_modifyitems(config, items):
    del config
    for item in items:
        skip_reason = _get_skip_reason(item)
        if skip_reason is not None:
            item.add_marker(pytest.mark.skip(reason=skip_reason))


def pytest_runtest_setup(item):
    skip_reason = _get_skip_reason(item)
    if skip_reason is not None:
        pytest.skip(skip_reason)




    

