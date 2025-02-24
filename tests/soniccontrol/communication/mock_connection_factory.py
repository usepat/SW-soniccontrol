import asyncio
from typing import Tuple
from unittest.mock import Mock
import pytest
from soniccontrol.communication.connection import Connection


class MockConnectionFactory(Connection):
    def __init__(self):
        self.reader = Mock(wraps=asyncio.StreamReader)()
        self.writer = Mock(spec=asyncio.StreamWriter)

    async def open_connection(self) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        return self.reader, self.writer

    async def close_connection(self):
        return

@pytest.fixture()
def connection(event_loop):
    connection_factory = MockConnectionFactory()
    return connection_factory