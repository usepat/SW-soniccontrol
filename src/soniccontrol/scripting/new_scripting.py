import enum
from typing import Tuple
import lark
import attrs
import abc
import asyncio

from src.soniccontrol.procedures.holder import convert_to_holder_args
from src.soniccontrol.scripting.scripting_facade import CommandFunc, ExecutionStep, RunnableScript, ScriptException, ScriptingFacade
from src.soniccontrol.sonic_device import SonicDevice

class Type(enum.Enum):
    TIME = 0,
    INT = enum.auto(),
    STRING = enum.auto(),
    BOOL = enum.auto()
 

@attrs.define()
class Parameter:
    name: str = attrs.field()
    type: Type = attrs.field()


@attrs.define()
class Function(abc.ABC):
    parameters: Tuple[Parameter, ...] = attrs.field(factory=tuple)

    @abc.abstractmethod
    def create_command(self, *params) -> CommandFunc: ...


class HoldCommand(Function):
    def __init__(self):
        super().__init__((
            Parameter("amount_time", Type.TIME),
        ))

    def create_command(self, *params) -> CommandFunc:
        amount_time, = params
        duration = amount_time.duration if amount_time.unit == "s" else amount_time.duration / 1000

        async def hold(sonic_device: SonicDevice, duration=duration):
            await asyncio.sleep(duration)
        
        return hold
    
class SendCommand(Function):
    def __init__(self):
        super().__init__((
            Parameter("cmd_str", Type.STRING),
        ))

    def create_command(self, *params) -> CommandFunc:
        cmd_str, = params

        async def send(sonic_device: SonicDevice, cmd_str=cmd_str):
            await sonic_device.execute_command(cmd_str)
        
        return send

class Interpreter(RunnableScript):
    def __init__(self, ast):
        self.ast = ast
        self.function_table = {
            "send": SendCommand(),
            "hold": HoldCommand() 
        }

    def __iter__(self): #type: ignore
        return self
    
    def __next__(self): #type: ignore
        yield self._start(self.ast)
        
    def _start(self, tree):
        for child in tree.children:
            yield self._statement(child)
        raise StopIteration()

    def _statement(self, tree):
        if tree.data == "loop":
            yield self._loop(tree)
        elif tree.data == "command":
            yield self._command(tree)

    def _loop(self, tree):
        times, block = tree.children
        for _ in range(int(times)):
            yield self._code_block(block)

    def _code_block(self, tree):
        for child in tree:
            yield self._statement(child)

    def _command(self, tree):
        command_name, args = tree

        if command_name not in self.function_table:
            raise ScriptException(f"There exists no command with the name \"{command_name}\"", 
                                  line_begin=tree.meta.line, col_begin=tree.meta.column)
        function =  self.function_table[command_name]

        # validate params
        num_params = len(function.parameters)
        num_provided_params = len(args.children)
        if num_provided_params != num_params:
            raise ScriptException(f"The command {command_name} expects {num_params} params but {num_provided_params} were given", 
                                  line_begin=tree.meta.line, col_begin=tree.meta.column)

        for i, param in enumerate(function.parameters):
            if args.children[i].type != param.type.name:
                raise ScriptException(f"The command {command_name} expected the type {param.type.name} for its parameter {param.name}, but got {args.children[i].type}", 
                                      line_begin=args.children[i].meta.line, col_begin=args.children[i].meta.column) 

        # convert args and create command
        arg_values = [ self._value(token) for token in args.children ]
        command = function.create_command(*arg_values)
        line = tree.meta.line

        return ExecutionStep(command, line)


    def _value(self, token):
        if token.type == "INT":
            return int(token.value)
        elif token.type == "TIME":
            return convert_to_holder_args(token.value)
        elif token.type == "BOOl":
            return token.value.lower() in ("true", "on")
        elif token.type == "STRING":
            return token.value[1:-1] # remove "" at beginning and end


class NewScriptingFacade(ScriptingFacade):
    GRAMMAR = """
        // ignore whitespace and comments

        %import common.WS
        %ignore WS

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
        %import common.STRING
        %import common.CNAME    -> IDENTIFIER
        %import common.NEWLINE

        start: statement+

        statement:  loop        -> loop
                |   command     -> command

        loop: "loop" INT "times" code_block

        code_block: "begin" statement+ "end"

        command: IDENTIFIER args NEWLINE

        args: _value*

        value: _constant

        constant: INT | STRING | BOOL | TIME

        BOOL: "true" | "false" | "on" | "off"

        TIME: NUMBER ("ms"| "s")
    """

    def __init__(self):
        self.parser = lark.Lark(NewScriptingFacade.GRAMMAR, start="start")

    def parse_script(self, text: str) -> RunnableScript:
        try:
            ast = self.parser.parse(text, propagate_positions=True)
        except Exception as e:
            # TODO: convert this into a ScriptingError
            raise e

        interpreter = Interpreter(ast)
        return interpreter

        