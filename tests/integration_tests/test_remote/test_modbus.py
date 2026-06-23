import os
from pathlib import Path
from typing import NamedTuple

import pytest
import pytest_asyncio
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusIOException
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


class ModbusClientContext(NamedTuple):
    client: AsyncModbusSerialClient
    slave_id: int
    port: str
    baudrate: int
    parity: str
    stopbits: int


async def create_modbus_client(
    port: str,
    baudrate: int,
    parity: str,
    stopbits: int,
) -> AsyncModbusSerialClient:
    client = AsyncModbusSerialClient(
        port,
        baudrate=baudrate,
        parity=parity,
        stopbits=stopbits,
        timeout=1.5,
        retries=1,
    )
    await client.connect()
    return client


def get_invalid_slave_id(slave_id: int) -> int:
    return slave_id + 1 if slave_id < 247 else slave_id - 1


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
    (9600, "E", 1),
    (9600, "O", 1),
    (9600, "N", 1),
    (115200, "E", 1),
    (115200, "O", 1),
    (115200, "N", 1),
    (115200, "E", 2),
    (115200, "E", 5),
    (115200, "E", 19),
])
async def modbus_client(request, remote_controller):
    baudrate, parity, slave_id = request.param
    
    if parity == "E":
        prot_parity = Parity.EVEN
    elif parity == "O":
        prot_parity = Parity.ODD
    else:
        prot_parity = Parity.NO
    await remote_controller.send_command(commands.SetModbusParity(prot_parity))
    await remote_controller.send_command(commands.SetModbusBaudrate(baudrate))
    await remote_controller.send_command(commands.SetModbusServerAddress(slave_id))

    await remote_controller.restart()

    port: str | None = request.config._sonic_control_plugin.modbus_serial_port

    if port is None:
        pytest.skip("No modbus serial port was set. Skip modbus compliance tests")

    stopbits = 1 if prot_parity != Parity.NO else 2
    client = await create_modbus_client(port, baudrate, parity, stopbits)
    yield ModbusClientContext(client, slave_id, port, baudrate, parity, stopbits)
    client.close()

@pytest.mark.allowed_devices(DeviceType.POSTMAN, DeviceType.MVP_WORKER, DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
async def test_modbus_write_and_read_multiple_registers(modbus_client: AsyncModbusSerialClient):
    # note. first register should be 0, 
    # because that address corresponds to the execute_command_flag, 
    # that we do not want to set
    client, slave_id, *_ = modbus_client
    data = [0, 1, 2, 3, 0]
    answer = await client.write_registers(1024, data, device_id=slave_id)
    assert not answer.isError(), "modbus write failed"
    answer = await client.read_input_registers(1024, count=len(data), device_id=slave_id)
    assert not answer.isError(), "modbus read failed"

    assert answer.registers == data, "The data read does not correspond to the data written"


@pytest.mark.allowed_devices(DeviceType.POSTMAN, DeviceType.MVP_WORKER, DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
async def test_modbus_invalid_slave_id_gets_no_response(modbus_client: ModbusClientContext):
    invalid_slave_id = get_invalid_slave_id(modbus_client.slave_id)

    with pytest.raises(ModbusIOException, match="No response received"):
        await modbus_client.client.read_input_registers(1024, count=1, device_id=invalid_slave_id)


@pytest.mark.allowed_devices(DeviceType.POSTMAN, DeviceType.MVP_WORKER, DeviceType.DESCALE)
@pytest.mark.asyncio(loop_scope="package")
async def test_modbus_slave_id_persists_after_second_restart(
    modbus_client: ModbusClientContext,
    remote_controller: RemoteController,
):
    await remote_controller.restart()

    modbus_client.client.close()
    restarted_client = await create_modbus_client(
        modbus_client.port,
        modbus_client.baudrate,
        modbus_client.parity,
        modbus_client.stopbits,
    )
    try:
        answer = await restarted_client.read_input_registers(1024, count=1, device_id=modbus_client.slave_id)
        assert not answer.isError(), "stored slave id should still respond after a second restart"

        with pytest.raises(ModbusIOException, match="No response received"):
            await restarted_client.read_input_registers(
                1024,
                count=1,
                device_id=get_invalid_slave_id(modbus_client.slave_id),
            )
    finally:
        restarted_client.close()

