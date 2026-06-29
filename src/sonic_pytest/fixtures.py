import asyncio
from pathlib import Path
import sys
from sonic_protocol.schema import DeviceType
import pytest
import psutil
from sonic_pytest.plugin_data import get_sonic_control_plugin


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
    
    plugin_config = get_sonic_control_plugin(request.config)
    is_simulation: bool = plugin_config.is_simulation
    device_type: DeviceType = plugin_config.device_type

    if is_simulation and device_type == DeviceType.POSTMAN:
        data_dir = tmp_path_factory.mktemp("data_worker")

        simulation_file = plugin_config.simulation_exe_path
        process = await asyncio.create_subprocess_exec(
            str(simulation_file),
            "--profile=worker_modbus", 
            "--name=test_worker_with_postman", 
            "--gui=false",
            "--board-type=simulation",
            f"--data-dir={data_dir}",
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
    