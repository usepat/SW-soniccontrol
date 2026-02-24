import attrs
from sonic_protocol.protocols.protocol_v3_0_0.types.types import TestInteraction
from soniccontrol.events import EventManager, PropertyChangeEvent

@attrs.define()
class TestResult:
    success: bool = attrs.field()
    assertion_msg: str = attrs.field(factory=str)

@attrs.define()
class SemiAutomatedStep:
    interaction: TestInteraction = attrs.field()
    message: str = attrs.field()


def _emit_test_result_changed(self, attr: attrs.Attribute, value):
    old_value = getattr(self, attr.name)

    if value != old_value:
        self.emit(PropertyChangeEvent("test_result", old_value, value))

    return value

@attrs.define()
class TestInfo(EventManager):
    index: int = attrs.field()
    test_name: str = attrs.field()
    suite_name: str = attrs.field()
    test_result: TestResult | None = attrs.field(default=None, on_setattr=_emit_test_result_changed)

    def __attrs_post_init__(self):
        super().__init__()