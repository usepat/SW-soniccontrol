import os
from pathlib import Path
from typing import List
from sonic_protocol.schema import DeviceType
import pytest

from soniccontrol.app_config import get_simulation_exe
from sonic_pytest.plugin_data import SonicControlPlugin, Profile
from sonic_pytest.fixtures import process_management



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
        "skip_remote_test_setup: skip the default remote test state reset fixture",
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


def pytest_runtest_setup(item):
    # Here we check for each test, if it can be executed by checking the allowed_devices marker
    allowed_devices: List[DeviceType] = [ 
        arg 
        for mark in item.iter_markers(name="allowed_devices") 
        for arg in mark.args
    ]
    if len(allowed_devices) == 0:
        return 
    
    device_type = item.config._sonic_control_plugin.device_type
    if device_type not in allowed_devices:
        pytest.skip(f"The device type {device_type.name} is not supported for this test")  




    
