import os
from pathlib import Path

import pytest
import pytest_asyncio
from pymodbus.client import AsyncModbusSerialClient
from sonic_protocol.schema import DeviceType
from soniccontrol import RemoteController, commands, Parity

"""
I think it makes only sense to test a single read and write multiple registers here.
Because all modbus tests that could be implemented are better to implement directly 
as unit tests for the application_server and application_client classes in the firmware.
The only thing really needed to test would be timing, crc, issues, slave addressing, but
that can also be tested in the firmware with a loopback.

So this here is just a simple test for compliance. To check if it works at all with an 
extern implementation of modbus with different serial settings.
"""


@pytest_asyncio.fixture(scope="function", loop_scope="package")
async def remote_controller():
    test_url = os.getenv("TEST_URL")
    if test_url is None:
        pytest.skip("TEST_URL is not set. Skip modbus compliance tests")

    controller = await RemoteController.connect_via_serial(Path(test_url))
    await controller.stop_updater()
    await controller.stop_running_processes()
    yield controller
    await controller.disconnect()

@pytest_asyncio.fixture(scope="function", loop_scope="package", params=[
    (9600, "N"),
    # (9600, "O"),
    # (9600, "N"),
])
async def modbus_client(request, remote_controller):
    baudrate, parity = request.param
    
    if parity == "E":
        prot_parity = Parity.EVEN
    elif parity == "O":
        prot_parity = Parity.ODD
    else:
        prot_parity = Parity.NO
    await remote_controller.send_command(commands.SetModbusParity(prot_parity))
    await remote_controller.send_command(commands.SetModbusBaudrate(baudrate))
    await remote_controller.send_command(commands.SetModbusServerAddress(1))

    port: str | None = request.config._sonic_control_plugin.modbus_serial_port

    if port is None:
        pytest.skip("No modbus serial port was set. Skip modbus compliance tests")

    client = AsyncModbusSerialClient(port, baudrate=baudrate, parity=parity, timeout=1.5, retries=1)
    await client.connect()
    yield client
    client.close()

@pytest.mark.allowed_devices(DeviceType.POSTMAN, DeviceType.MVP_WORKER, DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
async def test_modbus_write_and_read_multiple_registers(modbus_client: AsyncModbusSerialClient):
    # note. first register should be 0, 
    # because that address corresponds to the execute_command_flag, 
    # that we do not want to set
    data = [0, 1, 2, 3, 0]
    answer = await modbus_client.write_registers(1024, data, device_id=1)
    assert not answer.isError(), "modbus write failed"
    answer = await modbus_client.read_input_registers(1024, count=len(data), device_id=1)
    assert not answer.isError(), "modbus read failed"

    assert answer.registers == data, "The data read does not correspond to the data written"

