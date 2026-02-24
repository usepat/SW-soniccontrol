import asyncio
from enum import Enum, auto
import os
from pathlib import Path
from typing import List
import attrs
from sonic_protocol.schema import DeviceType
import pytest
import psutil


class Profile(Enum):
    simulation_worker = auto()
    simulation_descale = auto()
    simulation_postman_worker = auto()
    device_worker = auto()
    device_descale = auto()
    device_postman_worker = auto()

@attrs.define()
class SonicControlPlugin:
    is_simulation: bool = attrs.field()
    url: str | None = attrs.field()
    device_type: DeviceType = attrs.field()
    simulation_exe_path: Path = attrs.field()
    log_path: Path = attrs.field()


def pytest_addoption(parser):
    parser.addoption(
        "--profile",
        action="store",
        default=Profile.simulation_postman_worker.name,
        choices=(profile.name for profile in Profile),
        help="Choose a profile to execute",
    )
    parser.addoption(
        "--url",
        action="store",
        default=None,
        help="Choose the url for the serial port over that the device is connected",
    )
    parser.addoption(
        "--log-path",
        action="store",
        default=Path("./output/test_logs"),
        help="Choose the directory, where the logs should be placed",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "allowed_devices(*device_list): mark test to run only for certain selected devices",
    )

    profile = Profile[config.getoption("--profile")]
    url = config.getoption("--url")
    log_path = config.getoption("--log-path")
  
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

    assert "FIRMWARE_BUILD_DIR_PATH" in os.environ, "FIRMWARE_BUILD_DIR_PATH was not set as environment variable"
    simulation_exe_path = Path(os.environ["FIRMWARE_BUILD_DIR_PATH"]) / "linux/platform_linux/src/device/device_main"
    simulation_exe_path = simulation_exe_path.expanduser().resolve()

    config._sonic_control_plugin = SonicControlPlugin(is_simulation, url, device, simulation_exe_path, log_path)


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
        yield
    
