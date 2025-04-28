import abc
from typing import Awaitable, Callable, Optional
import attrs

from src.soniccontrol.sonic_device import SonicDevice


@attrs.define()
class ScriptException(Exception):
    msg: str = attrs.field()
    line_begin: int = attrs.field()
    col_begin: int = attrs.field()
    line_end: Optional[int] = attrs.field(default=None)
    col_end: Optional[int] = attrs.field(default=None)

CommandFunc = Callable[[SonicDevice], Awaitable[None]]

@attrs.define
class ExecutionStep:
    command: CommandFunc = attrs.field()
    line: int = attrs.field()

class RunnableScript(abc.ABC):
    @abc.abstractmethod
    def __iter__(self): ...
    
    @abc.abstractmethod
    def __next__(self): ...


class ScriptingFacade(abc.ABC):
    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def parse_script(self, text: str) -> RunnableScript: ...

