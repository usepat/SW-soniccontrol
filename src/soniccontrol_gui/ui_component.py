import logging
from typing import Optional

from soniccontrol_gui.view import View
from soniccontrol.events import EventManager


class UIComponent(EventManager):
    def __init__(self, parent: Optional["UIComponent"], view: View, logger: logging.Logger = logging.getLogger("ui")):
        super().__init__()
        self._parent = parent
        self._view = view
        self._logger = logger

    @property 
    def top_level_window(self) -> "UIComponent | None":
        return self._parent.top_level_window if self._parent else None
    
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
    
    