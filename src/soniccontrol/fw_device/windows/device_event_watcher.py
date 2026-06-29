import asyncio
from enum import Enum
import time

import wmi


_watcher_instance: "_DeviceEventWatcher | None" = None


def get_device_event_watcher(loop: asyncio.AbstractEventLoop | None = None) -> "_DeviceEventWatcher":
    global _watcher_instance

    if loop is None:
        loop = asyncio.get_running_loop()

    if _watcher_instance is None:
        _watcher_instance = _DeviceEventWatcher(loop)

    return _watcher_instance



class DeviceEvent(Enum):
    CONNECTED = 2
    REMOVED = 3

class _DeviceEventWatcher:
    """
        Windows and its whole api system is a cluster fuck.  
        wmi.watcher is blocking and therefore we have to use this class to integrate it with asyncio.  
        This is designed as a singleton thread that starts once and then runs forever in the background.
        Why? Because the watcher can block indefinitely and tasks are cooperative scheduled, meaning they have
        to stop voluntary by them self and cannot be cancelled directly. 
        To avoid multiple threads spawning and running forever. I want a singleton, so that only one thread runs forever.
        The events detected are pushed onto a event queue, that async functions inside the eventloop can then await.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._event_queue = asyncio.Queue(maxsize=10)
        self._worker = loop.create_task(
            asyncio.to_thread(self._watch_worker_thread)
        )    

    @property
    def event_queue(self):
        return self._event_queue

    def _push_event(self, event: DeviceEvent):
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            self._event_queue.get_nowait()
            self._event_queue.put_nowait(event)

    def _watch_worker_thread(self):
        c = wmi.WMI()
        watcher = c.watch_for(
            notification_type="Creation",
            wmi_class="Win32_DeviceChangeEvent"
        )

        while True:
            win_event = watcher()

            try:
                event = DeviceEvent(win_event.EventType)
            except ValueError:
                continue

            if event in (DeviceEvent.CONNECTED, DeviceEvent.REMOVED):
                time.sleep(0.3)  # stabilize enumeration
                
                self._loop.call_soon_threadsafe(self._push_event, event)
