import asyncio
from enum import Enum, auto
import os
import sys
from pathlib import Path
from typing import List
import attrs
from sonic_protocol.schema import DeviceType
import pytest
import psutil

from soniccontrol.app_config import get_simulation_exe


class Profile(Enum):
    simulation_worker = auto()
    simulation_descale = auto()
    simulation_postman_worker = auto()
    device_worker = auto()
    device_descale = auto()
    device_postman_worker = auto()

@attrs.define()
class SonicControlPlugin:
    is_simulation: bool
    serial_port: str | None
    modbus_serial_port: str | None
    device_type: DeviceType
    simulation_exe_path: Path
    log_path: Path
    remote_server_url: str | None


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
        "skip_remote_test_setup: skip the default remote test state reset fixture",
    )

    profile = Profile[config.getoption("--profile")]
    serial_port = config.getoption("--serial-port")
    modbus_serial_port = config.getoption("--modbus-serial-port")
    log_path = config.getoption("--log-path")
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


def kill_all(process_name: str):
    """
    Needed to ensure that the previous simulation process get killed, before starting a new one
    """
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == process_name:
            proc.kill()


@pytest.fixture(scope="session", autouse=True)
def process_management():
    # This ensures that no simulation is running before and after the tests
    kill_all("device_main")

    yield

    kill_all("device_main")


@pytest.fixture
def progress_writer():
    def write(message: str):
        if sys.__stdout__:
            sys.__stdout__.write(message + "\n")
            sys.__stdout__.flush()
    return write


async def create_worker_process_impl(request, tmp_path_factory):
    # creates a worker process needed for the postman simulation
    
    plugin_config = request.config._sonic_control_plugin
    is_simulation: bool = plugin_config.is_simulation
    device_type: DeviceType = plugin_config.device_type

    if is_simulation and device_type == DeviceType.POSTMAN:
        data_dir = tmp_path_factory.mktemp("data_worker")

        simulation_file = plugin_config.simulation_exe_path
        process = await asyncio.create_subprocess_exec(
            str(simulation_file),
            "--profile=worker_modbus", "--name=test_worker_with_postman", f"--data-dir={data_dir}",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

        yield

        if process.returncode is None:
            process.terminate() # We need to gracefully shutdown the process, so that the socket gets properly freed
            await asyncio.wait_for(process.wait(), timeout=1)
    else:
        # For some reason return breaks the code. Probably because pytest_async expects a Generator
        # However yielding works fine
        
        # In case that no simulation is running, we need nothing to set it up. So just empty dummy here
        yield 
    
