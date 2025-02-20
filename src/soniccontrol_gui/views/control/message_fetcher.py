import asyncio
from typing import Optional
from soniccontrol.communication.communicator import Communicator
from soniccontrol.events import Event, EventManager


class MessageFetcher(EventManager):
    MESSAGE_RECEIVED_EVENT = "MESSAGE_RECEIVED"

    def __init__(self, communicator: Communicator):
        super().__init__()
        self._communicator = communicator
        self._worker: Optional[asyncio.Task] = None

    def run(self):
        assert (self._worker is None)
        self._worker = asyncio.create_task(self._fetching())

    async def stop(self):
        assert (self._worker is not None)
        self._worker.cancel()
        await self._worker
        self._worker = None

    @property
    def is_running(self) -> bool:
        return self._worker is not None

    async def _fetching(self):
        try:
            while True:
                message = await self._communicator.read_message()
                self.emit(Event(MessageFetcher.MESSAGE_RECEIVED_EVENT, message=message))
        except asyncio.CancelledError:
            pass
    