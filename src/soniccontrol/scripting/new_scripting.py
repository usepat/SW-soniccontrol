import time
from typing import Any, Dict, Optional, Tuple
import lark
import attrs
import abc
import asyncio

import sonic_protocol.python_parser.commands as cmds
from sonic_protocol.schema import Version
from sonic_protocol.si_unit import SIVar
from soniccontrol.procedures.holder import convert_to_holder_args, HolderArgs
from soniccontrol.procedures.legacy_procs.auto import AutoLegacyArgs
from soniccontrol.procedures.legacy_procs.wipe import WipeLegacyArgs
from soniccontrol.procedures.procedure import ProcedureArgs, ProcedureType
from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.procedures.procs.auto import AutoArgs
from soniccontrol.procedures.procs.ramper import RamperArgs
from soniccontrol.procedures.procs.scan import ScanArgs
from soniccontrol.procedures.procs.tune import TuneArgs
from soniccontrol.procedures.procs.wipe import WipeArgs
from soniccontrol.scripting.scripting_facade import CommandFunc, ExecutionStep, RunnableScript, ScriptException, ScriptingFacade
from soniccontrol.sonic_device import SonicDevice

 
@attrs.define()
class Parameter:
    name: str = attrs.field()
    type_: type[Any] = attrs.field()


@attrs.define()
class Function(abc.ABC):
    parameters: Tuple[Parameter, ...] = attrs.field(factory=tuple)

    @abc.abstractmethod
    def create_command(self, *params) -> Tuple[str, CommandFunc]: ...


class HoldCommand(Function):
    def __init__(self):
        super().__init__((
            Parameter("amount_time", HolderArgs),
        ))

    def create_command(self, *params) -> Tuple[str, CommandFunc]:
        amount_time, = params
        duration = amount_time.duration if amount_time.unit == "s" else amount_time.duration / 1000

        async def hold(_device: SonicDevice, _proc_controller: ProcedureController, duration=duration):
            await asyncio.sleep(duration)
        
        return f"hold amount_time={str(amount_time)}", hold
    
class BreakPointCommand(Function):
    def __init__(self):
        super().__init__(())
    
    def create_command(self, *_params) -> Tuple[str, CommandFunc]:
        async def interrupt(_device: SonicDevice, _proc_controller: ProcedureController):
            raise asyncio.CancelledError() # raise a cancel error to interrupt interpretation. It will pause execution
        
        return "breakpoint", interrupt

class SendCommand(Function):
    def __init__(self):
        super().__init__((
            Parameter("cmd_str", str),
        ))

    def create_command(self, *params) -> Tuple[str, CommandFunc]:
        cmd_str, = params

        async def send(device: SonicDevice, _proc_controller: ProcedureController, cmd_str=cmd_str):
            await device.execute_command(cmd_str)
        
        return f"send cmd_str=\"{cmd_str}\"", send
    
class ProtocolCommand(Function):
    def __init__(self, parameters: Tuple[Parameter, ...], command_cls: type[cmds.Command]):
        super().__init__(parameters)
        self._command_cls = command_cls

    def create_command(self, *params) -> Tuple[str, CommandFunc]:

        async def command(device: SonicDevice, _proc_controller: ProcedureController, params=params):
            await device.execute_command(self._command_cls(*params))
        
        description = f"{self._command_cls.__name__} { ' '.join([str(param) for param in params ]) }"
        return description, command
    
class ProcedureCommand(Function):
    def __init__(self, proc_args_class: type, proc_type: ProcedureType):
        parameters = []
        if issubclass(proc_args_class, ProcedureArgs):
            args_dict = proc_args_class.fields_dict_with_alias()
            for name, field in args_dict.items():
                assert field.type is not None

                parameters.append(
                    Parameter(name, field.type)
                )  
        else:
            for name, field in attrs.fields_dict(proc_args_class).items():
                assert field.type is not None

                parameters.append(
                    Parameter(name, field.type)
                )

        super().__init__(tuple(parameters))
        self._proc_args_class = proc_args_class
        self._proc_type = proc_type
        

    def create_command(self, *params) -> Tuple[str, CommandFunc]:
        args = self._proc_args_class.from_tuple(params)

        async def command(device: SonicDevice, _proc_controller: ProcedureController, args=args):
            try:
                _proc_controller.execute_proc(self._proc_type, args)
                await _proc_controller.wait_for_proc_to_finish()
            except asyncio.CancelledError:
                await _proc_controller.stop_proc()
                raise
            except Exception:
                raise
        
        description = f"Executing {self._proc_type.value} { ' '.join([f'{k}={v}' for k, v in attrs.asdict(args).items() ]) }"
        return description, command


class Timer():
    def __init__(self, duration: HolderArgs, line):
        self._line = line
        self._duration_s = duration.duration_in_ms / 1000
        self._time_passed: float = 0.

    def wrap_command_func(self, func: CommandFunc) -> CommandFunc:
        async def _func(device: SonicDevice, proc_controller: ProcedureController):
            time_now = time.time()
            await func(device, proc_controller)
            self._time_passed += time.time() - time_now
        return _func
    
    def create_wait_remaining_time_execution_step(self) -> ExecutionStep:
        time_remaining = self._duration_s - self._time_passed
        async def _func(device: SonicDevice, proc_controller: ProcedureController, time_remaining=time_remaining):
            if time_remaining >= 0.:
                await asyncio.sleep(time_remaining)
            else:
                pass # TODO: throw error or log warning
        
        return ExecutionStep(_func, self._line, f"waiting remaining time: {round(time_remaining, 3)} s")
    

class Interpreter(RunnableScript):
    FUNCTION_TABLE: Dict[str, Function] = {
        "send": SendCommand(),
        "hold": HoldCommand(),
        "frequency": ProtocolCommand((Parameter("frequency", int),), cmds.SetFrequency), 
        "gain": ProtocolCommand((Parameter("gain", int),), cmds.SetGain), 
        "on": ProtocolCommand((), cmds.SetOn), 
        "off": ProtocolCommand((), cmds.SetOff), 
        "ramp": ProcedureCommand(RamperArgs, ProcedureType.RAMP),
        "auto": ProcedureCommand(AutoArgs, ProcedureType.AUTO),
        "wipe": ProcedureCommand(WipeArgs, ProcedureType.WIPE),
        "tune": ProcedureCommand(TuneArgs, ProcedureType.TUNE),
        "scan": ProcedureCommand(ScanArgs, ProcedureType.SCAN),
        "auto_legacy": ProcedureCommand(AutoLegacyArgs, ProcedureType.AUTO_LEGACY),
        "wipe_legacy": ProcedureCommand(WipeLegacyArgs, ProcedureType.WIPE_LEGACY),
        "breakpoint": BreakPointCommand(),
    }

    def __init__(self, ast):
        self._version = Version(1, 0, 0)
        self._ast = ast
        self._function_table = Interpreter.FUNCTION_TABLE.copy()

    def __iter__(self):
        yield from self._start(self._ast)
        
    def _start(self, tree):
        for child in tree.children:
            if child.data == "header":
                self._header(child)
                continue
            yield from self._statement(child)

    def _header(self, tree):
        version_str = self._value(tree.children[0])
        version = Version.to_version(version_str)

        if version > self._version:
            raise ScriptException(f"The interpreter is of version {self._version} and may not understand the script of version {version} correctly.", 
                                  line_begin=tree.meta.line, col_begin=tree.meta.column)

    def _statement(self, tree):
        if tree.data == "loop":
            yield from self._loop(tree.children[0])
        elif tree.data == "command":
            yield self._command(tree.children[0])
        elif tree.data == "timed_section":
            yield from self._timed_section(tree.children[0])

    def _loop(self, tree):
        n_times, statement = tree.children
        for _ in range(int(n_times)):
            yield from self._code_block(statement)

    def _code_block(self, tree):
        for statement in tree.children:
            yield from self._statement(statement)

    def _timed_section(self, tree):
        timing_spec, statement = tree.children
        duration_time = self._value(timing_spec)
        timer = Timer(duration_time, tree.meta.line) # type: ignore
        for execution_step in self._code_block(statement):
            execution_step.command = timer.wrap_command_func(execution_step.command) # type: ignore
            yield execution_step
        yield timer.create_wait_remaining_time_execution_step()

    def _command(self, tree: lark.Tree):
        command_name, *args = tree.children

        if command_name not in self._function_table:
            raise ScriptException(f"There exists no command with the name \"{command_name}\"", 
                                  line_begin=tree.meta.line, col_begin=tree.meta.column)
        function =  self._function_table[str(command_name)]

        # validate params
        for param in function.parameters:
            if issubclass(param.type_, ProcedureArgs):
                # Params should not be ProcedureArgs classes but should always be unpacked
                assert False
        num_params = len(function.parameters)
        num_provided_params = len(args)
        if num_provided_params != num_params:
            raise ScriptException(f"The command {command_name} expects {num_params} params but {num_provided_params} were given", 
                                  line_begin=tree.meta.line, col_begin=tree.meta.column)

        arg_values = [ self._value(token) for token in args ]
        for i, param in enumerate(function.parameters):
            value = arg_values[i]
            token = args[i]
            assert isinstance(token, lark.Token)

            parameter_type = param.type_.underlying_type() if issubclass(param.type_, SIVar) else param.type_
            
            # allow implicit conversions from float to int and back.
            # So ramp_f_start can also be set by an int value
            if parameter_type is float and isinstance(value, int):
                value = float(value)
            if parameter_type is int and isinstance(value, float):
                value = int(value)

            if not isinstance(value, parameter_type):
                raise ScriptException(f"The command {command_name} expected the type {parameter_type.__name__} for its parameter {param.name}, but got {type(value).__name__}", 
                                      line_begin=token.line, col_begin=token.column) #type: ignore

        # convert args and create command
        description, command = function.create_command(*arg_values)
        line = tree.meta.line

        return ExecutionStep(command, line, description)


    def _value(self, token):
        if token.type == "INT":
            return int(token.value)
        elif token.type == "TIME":
            return convert_to_holder_args(token.value)
        elif token.type == "BOOl":
            return token.value.lower() in ("true", "on")
        elif token.type == "ESCAPED_STRING":
            return token.value[1:-1] # remove "" at beginning and end


class NewScriptingFacade(ScriptingFacade):
    GRAMMAR = r"""
        // ignore whitespace and comments

        %import common.WS_INLINE
        %ignore WS_INLINE

        %import common.SH_COMMENT
        %import common.C_COMMENT
        %import common.CPP_COMMENT

        %ignore SH_COMMENT
        %ignore C_COMMENT
        %ignore CPP_COMMENT
        
        // ignore multiline C comments
        %ignore /(?s)\/\*(\*(?!\/)|[^*])*\*\//
        
        // define grammar

        %import common.DIGIT    
        %import common.INT
        %import common.NUMBER
        %import common.LETTER
        %import common.ESCAPED_STRING

        start: header? _statement+

        header: _NEW_LINE* "%script_version" ESCAPED_STRING _NEW_LINE+

        _statement: _NEW_LINE* statement _NEW_LINE*
        
        statement:  loop            -> loop
                |   timed_section   -> timed_section
                |   command         -> command

        loop: "loop" INT "times" _NEW_LINE code_block

        timed_section: "section" "lasts" TIME _NEW_LINE code_block

        code_block: "begin" _NEW_LINE (_statement)+ "end" _NEW_LINE 

        command: IDENTIFIER _arg* _NEW_LINE

        %import common.CNAME -> IDENTIFIER
        
        _arg: _constant

        _NEW_LINE: /\s*\n/

        _constant: INT | ESCAPED_STRING | BOOL | TIME

        BOOL: "true" | "false" | "on" | "off"

        TIME: NUMBER ("ms"| "s")
    """

    def __init__(self):
        self.parser = lark.Lark(NewScriptingFacade.GRAMMAR, start="start", propagate_positions=True)

    def parse_script(self, text: str) -> RunnableScript:
        try:
            # all commands need to end with a newline.
            # Add newline here to make it more robust. So people do not have to remind them selfs to add a newline at the end of the script 
            ast = self.parser.parse(text + "\n")
        except lark.exceptions.UnexpectedInput as e:
            raise ScriptException(f"Syntax Error unexpected input\n: {e.get_context(text)}", e.line, e.column)
        interpreter = Interpreter(ast)
        return interpreter

def main():
    test_script = """
        %script_version "v1.0.0"

        send "!freq=100000"
        gain 100

        loop 5 times
        begin
            section lasts 60s
            begin

                send "!ON"
                hold 2s
                off
                hold 500ms
                ramp 100000 200000 10000 1s 500ms
            end
        end
    """ 
    scripting = NewScriptingFacade()
    script = scripting.parse_script(test_script)
    for execution_step in script:
        print(f"Executing on line {execution_step.line} command {execution_step.description}")

if __name__ == "__main__":
    main()
        