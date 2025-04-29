import enum
from typing import Any, Tuple
import lark
import attrs
import abc
import asyncio

import sonic_protocol.python_parser.commands as cmds
from soniccontrol.procedures.holder import convert_to_holder_args, HolderArgs
from soniccontrol.procedures.procedure import Procedure, ProcedureType
from soniccontrol.procedures.procedure_controller import ProcedureController
from soniccontrol.procedures.procs.auto import AutoProc
from soniccontrol.procedures.procs.ramper import Ramper, RamperRemote
from soniccontrol.procedures.procs.scan import ScanProc
from soniccontrol.procedures.procs.tune import TuneProc
from soniccontrol.procedures.procs.wipe import WipeProc
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
    def __init__(self, procedure: Procedure, proc_type: ProcedureType):
        parameters = []
        for name, field in attrs.fields_dict(procedure.get_args_class()).items():
            assert field.type is not None
            parameters.append(
                Parameter(name, field.type)
            )

        super().__init__(tuple(parameters))
        self._procedure = procedure
        self._proc_type = proc_type

    def create_command(self, *params) -> Tuple[str, CommandFunc]:
        args = {}
        args_class = self._procedure.get_args_class()
        param_names = attrs.fields_dict(args_class).keys()
        for i, name in enumerate(param_names):
            args[name] = params[i]
        args = args_class(**args)

        async def command(device: SonicDevice, _proc_controller: ProcedureController, args=args):
            try:
                _proc_controller.execute_procedure(self._procedure, self._proc_type, args)
                await _proc_controller.wait_for_proc_to_finish()
            except asyncio.CancelledError:
                await _proc_controller.stop_proc()
                raise
        
        description = f"Executing {self._proc_type.value} { ' '.join([f'{k}={v}' for k, v in attrs.asdict(args).items() ]) }"
        return description, command

class Interpreter(RunnableScript):
    def __init__(self, ast):
        self.ast = ast
        self.function_table = {
            "send": SendCommand(),
            "hold": HoldCommand(),
            "frequency": ProtocolCommand((Parameter("frequency", int),), cmds.SetFrequency), 
            "gain": ProtocolCommand((Parameter("gain", int),), cmds.SetGain), 
            "on": ProtocolCommand((), cmds.SetOn), 
            "off": ProtocolCommand((), cmds.SetOff), 
            "ramp": ProcedureCommand(RamperRemote(), ProcedureType.RAMP),
            "auto": ProcedureCommand(AutoProc(), ProcedureType.AUTO),
            "wipe": ProcedureCommand(WipeProc(), ProcedureType.WIPE),
            "tune": ProcedureCommand(TuneProc(), ProcedureType.TUNE),
            "scan": ProcedureCommand(ScanProc(), ProcedureType.SCAN),
        }

    def __iter__(self):
        yield from self._start(self.ast)
        
    def _start(self, tree):
        for child in tree.children:
            yield from self._statement(child)

    def _statement(self, tree):
        if tree.data == "loop":
            yield from self._loop(tree.children[0])
        elif tree.data == "command":
            yield self._command(tree.children[0])

    def _loop(self, tree):
        n_times, block = tree.children
        for _ in range(int(n_times)):
            yield from self._code_block(block)

    def _code_block(self, tree):
        for child in tree.children:
            yield from self._statement(child)

    def _command(self, tree: lark.Tree):
        command_name, *args = tree.children

        if command_name not in self.function_table:
            raise ScriptException(f"There exists no command with the name \"{command_name}\"", 
                                  line_begin=tree.meta.line, col_begin=tree.meta.column)
        function =  self.function_table[str(command_name)]

        # validate params
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

            if not isinstance(value, param.type_):
                raise ScriptException(f"The command {command_name} expected the type {param.type_.__name__} for its parameter {param.name}, but got {type(value).__name__}", 
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
    GRAMMAR = """
        // ignore whitespace and comments

        %import common.WS_INLINE
        %ignore WS_INLINE

        %import common.SH_COMMENT
        %import common.C_COMMENT
        %import common.CPP_COMMENT

        %ignore SH_COMMENT
        %ignore C_COMMENT
        %ignore CPP_COMMENT

        
        // define grammar

        %import common.DIGIT    
        %import common.INT
        %import common.NUMBER
        %import common.LETTER
        %import common.ESCAPED_STRING
        %import common.CNAME    -> IDENTIFIER

        start: statement+

        statement:  loop        -> loop
                |   command     -> command
                | empty_line    -> empty_line

        loop: "loop" INT "times" "\\n" code_block

        code_block: "begin" "\\n" statement+ "end" "\\n" 

        command: IDENTIFIER _arg* "\\n"

        empty_line: "\\n"

        _arg: _constant

        _constant: INT | ESCAPED_STRING | BOOL | TIME

        BOOL: "true" | "false" | "on" | "off"

        TIME: NUMBER ("ms"| "s")
    """

    def __init__(self):
        self.parser = lark.Lark(NewScriptingFacade.GRAMMAR, start="start", propagate_positions=True)

    def parse_script(self, text: str) -> RunnableScript:
        try:
            ast = self.parser.parse(text)
        except lark.exceptions.UnexpectedInput as e:
            raise ScriptException(f"Syntax Error unexpected input\n: {e.get_context(text)}", e.line, e.column)
        interpreter = Interpreter(ast)
        return interpreter

def main():
    test_script = """
        send "!freq=100000"
        gain 100
        loop 5 times
        begin
            send "!ON"
            hold 2s
            off
            hold 500ms
            ramp 100000 200000 10000 1s 500ms
        end
    """ 
    scripting = NewScriptingFacade()
    script = scripting.parse_script(test_script)
    for execution_step in script:
        print(f"Executing on line {execution_step.line} command {execution_step.description}")

if __name__ == "__main__":
    main()
        