import asyncio
import logging
import pytest
import pytest_asyncio
from soniccontrol.system import PLATFORM
from soniccontrol.command import Command
from soniccontrol.communication.package_parser import Package, PackageParser
from soniccontrol.communication.serial_communicator import SerialCommunicator
from tests.soniccontrol.communication.mock_connection_factory import connection # Needed. Do not delete. Intellisense is shit
from unittest.mock import Mock


@pytest_asyncio.fixture()
async def communicator(connection):
    communicator = SerialCommunicator()
    await communicator.open_communication(connection)
    yield communicator
    if communicator.connection_opened.is_set():
        await communicator.close_communication()

@pytest.mark.asyncio
async def test_communicator_close_communication_closes_streamwriter(communicator, connection):
    await communicator.close_communication()

    connection.writer.close.assert_called_once()
    connection.writer.wait_closed.assert_called_once()

@pytest.mark.asyncio
async def test_communicator_close_communication_raises_event_once(communicator):
    mock_close_callback = Mock()
    communicator.subscribe(communicator.DISCONNECTED_EVENT, mock_close_callback)
    
    await communicator.close_communication()

    mock_close_callback.assert_called_once()

@pytest.mark.asyncio
async def test_communicator_send_and_wait_returns_answer(communicator, connection):
    msg = "hello communicator!"
    msg_id = 1
    msg_str = PackageParser.write_package(Package("0", "0", msg_id, msg))
    connection.reader.feed_data(data=msg_str.encode(PLATFORM.encoding))
    command = Command(message="?greet")

    await communicator.send_and_wait_for_answer(command)
    assert command.answer.string == msg

@pytest.mark.asyncio
async def test_communicator_send_and_wait_throws_connection_error_if_parsing_error(communicator, connection):
    msg_str = "<0#Hello Parsing Error>"
    connection.reader.feed_data(data=msg_str.encode(PLATFORM.encoding))
    
    with pytest.raises(ConnectionError):
        await communicator.send_and_wait_for_answer(Command(message="-"))

@pytest.mark.asyncio
async def test_communicator_send_and_wait_connection_error_on_timeout(communicator):
    logger = logging.getLogger()
    logger.warn = Mock()
    communicator._logger = logger
    with pytest.raises(ConnectionError):
        await communicator.send_and_wait_for_answer(Command(message="-"))

@pytest.mark.asyncio
async def test_communicator_send_and_wait_connection_error_if_disconnect(communicator):
    await communicator.close_communication()

    with pytest.raises(ConnectionError):
        await communicator.send_and_wait_for_answer(Command(message="-"))

# TODO: Make a test for pulling constantly messages while also using send_and_wait
