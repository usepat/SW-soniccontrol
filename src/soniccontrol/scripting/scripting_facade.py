import abc
from typing import Any, Awaitable, Callable, Generator, Iterable, Optional
import attrs

from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.sonic_device import SonicDevice


@attrs.define()
class ScriptException(Exception):
    msg: str = attrs.field()
    line_begin: int = attrs.field()
    col_begin: int = attrs.field()
    line_end: Optional[int] = attrs.field(default=None)
    col_end: Optional[int] = attrs.field(default=None)

    def __str__(self) -> str:
        return self.msg


CommandFunc = Callable[[SonicDevice, ProcedureController], Awaitable[None]]

@attrs.define
class ExecutionStep:
    command: CommandFunc = attrs.field()
    line: int = attrs.field()
    description: str = attrs.field(default="")

class RunnableScript(abc.ABC):
    @abc.abstractmethod
    def __iter__(self) -> Generator[ExecutionStep, Any, None]: ...


class ScriptingFacade(abc.ABC):
    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def parse_script(self, text: str) -> RunnableScript: ...

