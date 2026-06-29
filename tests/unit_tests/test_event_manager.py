import pytest
from unittest.mock import Mock

from soniccontrol.events import EventManager, Event, PropertyChangeEvent

@pytest.mark.asyncio
async def test_emit_notfifies_listeners_on_event():
    mocked_listener = Mock()
    event_manager = EventManager()
    event_name = "Party at my house"
    event_manager.subscribe(event_name, mocked_listener)

    event = Event(event_name)
    event_manager.emit(event)

    mocked_listener.assert_called_once_with(event)    

@pytest.mark.asyncio
async def test_emit_notifies_property_listeners_on_property_changed_event():
    mocked_listener = Mock()
    event_manager = EventManager()
    property_name = "party_location"
    event_manager.subscribe_property_listener(property_name, mocked_listener)

    event = PropertyChangeEvent(property_name, "my house", "your house")
    event_manager.emit(event)

    mocked_listener.assert_called_once_with(event) 
