import logging
from typing import List, Optional, Dict, Any, Union, Tuple
import copy
import attrs
from soniccontrol.events import EventManager
from soniccontrol.procedures.holder import Holder, convert_to_holder_args
from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.scripting.scripting_facade import BuiltInFunctions, Script, ScriptingFacade
from soniccontrol.sonic_device import SonicDevice
from soniccontrol.logging_utils import get_base_logger



class SonicParser:
    SUPPORTED_TOKENS: List[str] = [
        "frequency",
        "gain",
        "ramp_freq_range",
        "ramp_freq",
        # "ramp_gain",
        "on",
        "off",
        "hold",
        "startloop",
        "endloop",
        # "chirp_ramp_freq",
        # "chirp_ramp_gain",
        "!AUTO",
        "AUTO",
        "auto",
    ]

    def parse_text(self, text: str) -> dict[str, Union[tuple[Any, ...], str]]:
        lines: list[str] = list(filter(None, text.rstrip().splitlines()))
        commands, arguments, comment = self.parse_lines(lines)
        loops: tuple[dict[str, int], ...] = self.parse_for_loops(commands, arguments)

        self.check_syntax_acception(loops, commands, arguments)
        return_dict: Dict[str, Any] = {
            "commands": commands,
            "arguments": arguments,
            "loops": loops,
            "comments": comment,
        }
        return return_dict

    def values_correctly_converted(
        self, arg: Union[int, tuple[Union[int, str], ...]]
    ) -> bool:
        return (
            not isinstance(arg, int) and arg.isnumeric()
            if not isinstance(arg, tuple)
            else any(self.values_correctly_converted(value) for value in arg)
        )

    def parse_lines(self, lines: list[str]) -> tuple[Any, ...]:
        commands: list[str] = list()
        arguments: list[Union[str, int]] = list()
        comments: str = str()
        for line in lines:
            if "#" in line:
                comments += f"{line}\n"
                continue
            if line.startswith(("!", "?")):
                commands.append(line)
                arguments.append(tuple())
                continue

            command, argument = self._parse_line(line)
            commands.append(command)
            arguments.append(argument)

        return (tuple(commands), tuple(arguments), comments)

    def parse_for_loops(
        self, commands: list[str], arguments: list[Union[str, int]]
    ) -> tuple[dict[str, int], ...]:
        loops: list[dict[str, int]] = list()
        for i, command in enumerate(commands):
            if command == "startloop":
                quantifier: int = int(
                    arguments[i]
                    if arguments[i] is not None and isinstance(arguments[i], int)
                    else -1
                )
                loops.insert(i, {"begin": i, "quantifier": quantifier})

            elif command == "endloop":
                loops.insert(i, {})
                for loop in reversed(loops):
                    if len(loop) != 2:
                        continue
                    loop.update({"end": i})
                    break

            else:
                loops.insert(i, {})
        return tuple(loops)

    def _parse_line(self, line: str) -> Tuple[Union[str, int, Tuple], ...]:
        if line is None or line == "":
            return ((), ())

        tmp_line_list: List[List[str]] = [i.split(",") for i in line.split(" ")]
        line_list: List[Union[str, int]] = list(
            filter(None, [item for sublist in tmp_line_list for item in sublist])
        )

        for i, part in enumerate(line_list):
            if part[-1:] == "s" and part[-2:] != "ms" and part[:-1].isnumeric():
                line_list.insert(i + 1, part[-1:])
                line_list[i] = int(part[:-1])
            elif part[-2:] == "ms" and part[:-2].isnumeric():
                line_list.insert(i + 1, part[-2:])
                line_list[i] = int(part[:-2])
            elif part.isnumeric():
                line_list[i] = int(part)

        command: str = line_list[0]
        line_list.pop(0)
        return (command, line_list[0] if len(line_list) == 1 else tuple(line_list))

    def check_syntax_acception(self, loops, commands, arguments) -> None:
        if any(
            (len(loop) != 3 and loop is not None and len(loop) != 0) for loop in loops
        ):
            raise ValueError(
                "Syntax of loops is invalid. Maybe you forgot to close a loop?"
            )

        if any(self.values_correctly_converted(arg) for arg in arguments):
            raise ValueError(
                "Argument(s) could not have been correctly converted to  integers,\nplease call for support or try again"
            )

        if any(
            command not in self.SUPPORTED_TOKENS and not command.startswith(("!", "?"))
            for command in commands
        ):
            raise ValueError("One or more commands are illegal or written wrong")


@attrs.define()
class LegacySequencer(Script):
    _sonicamp: SonicDevice = attrs.field(repr=False)
    _logger: logging.Logger = attrs.field()
    _proc_controller: ProcedureController = attrs.field()
    _commands: List[Any] = attrs.field(factory=list)
    _original_commands: List[Any] = attrs.field(factory=list)
    _current_line: int = attrs.field(default=0)
    _commands_aliases: List[BuiltInFunctions] = attrs.field(init=False, default=list(BuiltInFunctions))
    _current_command: str = attrs.field(init=False, default="")

    def __init__(
        self,
        sonicamp: SonicDevice,
        logger: logging.Logger,
        proc_controller: ProcedureController,
        commands: List[Any],
        original_commands: List[Any],
        include_command_aliases: Optional[List[BuiltInFunctions]] = None,
        exclude_command_aliases: Optional[List[BuiltInFunctions]] = None
    ) -> None:
        super().__init__()
        logger = logging.getLogger(logger.name + "." + LegacySequencer.__name__)
        self.__attrs_init__(sonicamp, logger, proc_controller, commands, original_commands)
        if include_command_aliases:
            self._commands_aliases = include_command_aliases.copy()
        if exclude_command_aliases:
            for alias in exclude_command_aliases:
                self._commands_aliases.remove(alias)

    @property
    def current_line(self) -> int:
        return self._current_line

    @property
    def current_task(self) -> str: 
        return self._current_command

    @property
    def is_finished(self) -> bool:
        return self._current_line >= len(self._commands)

    async def _before_script(self) -> None:
        await self._sonicamp.get_overview()

    async def _after_script(self) -> None:
        await self._sonicamp.set_signal_off()

    async def _execute_step(self) -> None: 
        if self._commands[self._current_line]["command"] == "startloop":
            self.startloop_response()
        elif self._commands[self._current_line]["command"] == "endloop":
            self.endloop_response()
        else:
            await self.execute_command(self._current_line)
            self._current_line += 1

    def startloop_response(self) -> None:
        loop: Dict[str, int] = self._commands[self._current_line]["loop"]
        if (
            loop.get("quantifier")
            and isinstance(loop.get("quantifier"), int)
            and loop.get("quantifier") != -1
        ):
            loop["quantifier"] -= 1
            self._current_line += 1
        elif loop.get("quantifier") == -1:
            self._current_line += 1
        else:
            self._logger.debug("Jumping to %d; quantifier = 0", loop['end'] + 1)
            self._current_line = loop["end"] + 1

    def endloop_response(self) -> None:
        self._logger.debug("'endloop' @ %d", self._current_line)
        loop_command: dict[str, int] = list(
            filter(
                lambda x: (x["loop"].get("end") == self._current_line), self._commands
            )
        )[0]
        loop: Dict[str, Any] = loop_command["loop"]
        self._commands[loop["begin"] + 1 : loop["end"] - 1] = copy.deepcopy(
            self._original_commands[loop["begin"] + 1 : loop["end"] - 1]
        )
        self._current_line = loop["begin"]

    async def _execute_command_alias(self, command: Dict[str, Any]) -> None:
        enum_type = next((elem for elem in BuiltInFunctions if elem.value == command["command"]), None)
        match enum_type:
            case BuiltInFunctions.FREQUENCY:
                await self._sonicamp.set_frequency(command["argument"])
            case BuiltInFunctions.GAIN:
                await self._sonicamp.set_gain(command["argument"])
            case BuiltInFunctions.RAMP_FREQ:
                self._current_command = "ramp_freq"
                await self._proc_controller.ramp_freq(*command["argument"])
            case BuiltInFunctions.RAMP_FREQ_RANGE:
                self._current_command = "ramp_freq"
                await self._proc_controller.ramp_freq_range(*command["argument"])
            case "!AUTO" | "AUTO" | BuiltInFunctions.AUTO:
                await self._sonicamp.set_signal_auto()
            case BuiltInFunctions.HOLD:
                self._current_command = "Hold"
                holder_args = convert_to_holder_args(command["argument"])
                await Holder.execute(holder_args)
            case BuiltInFunctions.ON:
                await self._sonicamp.set_signal_on()
            case BuiltInFunctions.OFF:
                await self._sonicamp.set_signal_off()
            case _:
                raise ValueError(f"{command} is not valid.") # FIXME program halts when this error gets raised


    async def execute_command(self, line: int) -> None:
        command: Dict[str, Any] = self._commands[self._current_line]
        self._current_command = f'Executing {command["command"]} {command["argument"]}'
        self._logger.info(f"Executing command: '%s'", str(command))

        if command["command"].startswith(("?", "!")):
            await self._sonicamp.execute_command(command["command"])
        else:
            await self._execute_command_alias(command)


class LegacyScriptingFacade(ScriptingFacade):
    def __init__(self, device: SonicDevice, procedure_controller: ProcedureController, **kwargs):
        self._device = device
        self._proc_controller = procedure_controller
        self._parser = SonicParser()
        self._logger = get_base_logger(device._logger)
        self._include_command_aliases: Optional[List[BuiltInFunctions]] = kwargs.get("include_command_aliases", None)
        self._exclude_command_aliases: Optional[List[BuiltInFunctions]] = kwargs.get("exclude_command_aliases", None)

    def parse_script(self, text: str) -> LegacySequencer:
        self._logger.debug("Parse script:\n%s", text)
        parsed_test = self._parser.parse_text(text)
        parsed_test = zip(
            parsed_test["commands"], parsed_test["arguments"], parsed_test["loops"]
        )

        commands = list(
            {"command": command, "argument": argument, "loop": loop}
            for command, argument, loop in parsed_test
        )
        original_commands = copy.deepcopy(commands)
        
        self._logger.debug("parsed commands:\n%s", str(original_commands))
        interpreter = LegacySequencer(
            self._device, self._logger, self._proc_controller, 
            commands=commands, original_commands=original_commands,
            include_command_aliases=self._include_command_aliases,
            exclude_command_aliases=self._exclude_command_aliases
        )     
        return interpreter

    def lint_text(self, text: str) -> str: ...
