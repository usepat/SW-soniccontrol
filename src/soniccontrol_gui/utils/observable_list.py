
from typing import Literal
from soniccontrol.utils.events import Event, EventManager


class ObservableList(EventManager):
    EVENT_ITEM_ADDED: Literal["Item Added"] = "Item Added"
    EVENT_ITEM_DELETED: Literal["Item Deleted"] = "Item Deleted"
    EVENT_LIST_CLEARED: Literal["List Cleared"] = "List Cleared"

    def __init__(self, init=[]):
        super().__init__()
        self._list: list = init
    
    def append(self, item):
        self._list.append(item)
        self.emit(Event(ObservableList.EVENT_ITEM_ADDED, item=item, list_new=self._list))

    def remove(self, item):
        self._list.remove(item)
        self.emit(Event(ObservableList.EVENT_ITEM_DELETED, item=item, list_new=self._list))

    def remove_at(self, index: int) -> None:
        item = self._list.pop(index)
        self.emit(Event(ObservableList.EVENT_ITEM_DELETED, item=item, list_new=self._list))

    def clear(self):
        self._list.clear()
        self.emit(Event(ObservableList.EVENT_LIST_CLEARED, list_new=self._list))

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        self._list[index] = value

    def __len__(self):
        return len(self._list)

    def __iter__(self):
        return iter(self._list)

    def __repr__(self):
        return repr(self._list)
