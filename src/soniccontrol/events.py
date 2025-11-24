from typing import Any, Callable, Literal

import attrs


@attrs.define
class Event:
    _type: str = attrs.field()
    _data: dict[str, Any] = attrs.field()

    def __init__(self, event_type: str, **kwargs) -> None:
        self.__attrs_init__(event_type, dict(**kwargs)) #type: ignore

    @property
    def type_(self) -> str:
        return self._type

    @property
    def data(self) -> dict[str, Any]:
        return self._data

@attrs.define
class PropertyChangeEvent(Event):
    _property_name: str = attrs.field()
    _old_value: Any = attrs.field()
    _new_value: Any = attrs.field()
    _sender: Any = attrs.field()

    PROPERTY_CHANGE_EVENT: Literal["<<PropertyChange>>"] = "<<PropertyChange>>"

    def __init__(self, property_name: str, old_value: Any, new_value: Any, sender: Any = None, **kwargs) -> None:
        self.__attrs_init__(PropertyChangeEvent.PROPERTY_CHANGE_EVENT, dict(**kwargs), property_name, old_value, new_value, sender) #type: ignore

    @property
    def property_name(self) -> str:
        return self._property_name

    @property
    def old_value(self) -> Any:
        return self._old_value

    @property
    def new_value(self) -> Any:
        return self._new_value
    
    @property
    def sender(self) -> Any:
        return self._sender


class EventManager:
    def __init__(self):
        self._listeners: dict[str, set[Callable[[Event], None]]] = {}
        self._property_listeners: dict[str, set[Callable[[PropertyChangeEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[Event], None]) -> None:
        if self._listeners.get(event_type) is None:
            self._listeners[event_type] = set()
        self._listeners[event_type].add(listener)
    
    def unsubscribe(self, event_type: str, listener: Callable[[Event], None]) -> None:
        if self._listeners.get(event_type) is None:
            if listener in self._listeners[event_type]:
                self._listeners[event_type].remove(listener)

    def subscribe_property_listener(self, property_name: str, listener: Callable[[PropertyChangeEvent], None]) -> None:
        if self._property_listeners.get(property_name) is None:
            self._property_listeners[property_name] = set()
        self._property_listeners[property_name].add(listener)

    def emit(self, event: Event) -> None:
        if event.type_ in self._listeners:
            self._emit_for_listeners(event)
        elif isinstance(event, PropertyChangeEvent):
            self._emit_for_property_listeners(event)

    def _emit_for_listeners(self, event: Event) -> None:
        if event._type not in self._listeners:
            return
        for listener in self._listeners[event._type]:
            listener(event)

    def _emit_for_property_listeners(self, event: PropertyChangeEvent) -> None:
        if event.property_name not in self._property_listeners:
            return
        for listener in self._property_listeners[event.property_name]:
            listener(event)
