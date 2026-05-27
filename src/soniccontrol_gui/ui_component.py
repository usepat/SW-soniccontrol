import asyncio
import logging
from typing import Coroutine, Optional

from soniccontrol_gui.view import View
from soniccontrol.events import EventManager


class UIComponent(EventManager):
    def __init__(self, parent: Optional["UIComponent"], view: View, logger: logging.Logger = logging.getLogger("ui")):
        super().__init__()
        self._parent = parent
        self._view = view
        self._logger = logger

    @property 
    def top_level_window(self) -> "TopLevelWindow":
        assert self._parent is not None
        return self._parent.top_level_window
    
    @property
    def component_name(self) -> str | None:
        return None

    @property
    def view(self):
        return self._view
    
    @property
    def parent(self):
        return self._parent
    
    @property
    def logger(self):
        return self._logger
    
    
class TopLevelWindow(UIComponent):
    def __init__(self, parent: Optional["UIComponent"], view: View, logger: logging.Logger = logging.getLogger("ui")):
        super().__init__(parent, view, logger)
        self._tasks: list[asyncio.Task] = []

    @property 
    def top_level_window(self):
        return self
    
    def pass_loading_task(self, task: asyncio.Task | Coroutine):
        """
            Used for passing async loading tasks up to the top level window, the caller code of that window can then 
            await all the tasks with wait_finished_loading
        """
        # TODO: maybe we should separate component from TopLevelWindow?
        # we cannot use lock here, because I have to call this inside a constructor, no async functions allowed
        self._tasks.append(task if isinstance(task, asyncio.Task) else asyncio.get_event_loop().create_task(task))

    async def wait_finished_loading(self):
        """
            Used together with pass_loading_task on the toplevel window 
        """
        tasks = self._tasks
        self._tasks = [] # FIXME: this line could be a race condition
        await asyncio.gather(*tasks)
