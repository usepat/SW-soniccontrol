@defgroup Scripting
@ingroup SonicControl
@addtogroup Scripting
@{

# Scripting {#Scripting}

## Brief Description

Scripting can take complex sequences of commands as scripts to execute.

## Use Cases

For our lab and many users it is  nice to execute scripts for experiments. 
The scripts are basically just a sequence of commands.
But it should also support a sleep function and simple loops.

Complex constructs are yet not required.

Also SonicControl provides for that a Editor where you can also debug through a script step by step. 
For that it is needed that we can also execute the script step by step and that it provides us also with the information which line and command it executes (for highlighting that line in the editor).

## Implementation

In the past legacy code was used for the scripting. Now it is replaced with new one. To ease the replacement interfaces and facades were defined.  
The whole interpreter logic is hidden in the facade [ScriptingFacade](@ref soniccontrol.scripting.scripting_facade.ScriptingFacade).
It provides the method parse_text that returns you a [RunnableScript](@ref soniccontrol.scripting.scripting_facade.RunnableScript) that is an iterator (so it can be executed step by step), that returns [ExecutionStep](@ref soniccontrol.scripting.scripting_facade.ExecutionStep) that contains the command to be executed, the line number and a description.  

The [InterpreterEngine](@ref soniccontrol.scripting.interpreter_engine.InterpreterEngine) takes a RunnableScript and executes it. With that it is possible to stop and resume execution. So it can step line by line through a script like a debugger.

### New Scripting

The new scripting uses the lark library to define a grammar for the custom programming language. This grammar is then used with lark to parse the script into an abstract syntax tree. If you know nothing about how Compilers, Interpreters and Parsers are designed, then I recommend you the online book [Crafting Interpreters](https://craftinginterpreters.com/). It is important that you know what a grammar, AST, Parser and Interpreter is to understand this module.  
Then the AST gets executed by the [Interpreter](@ref soniccontrol.scripting.new_scripting.Interpreter) that inherits from [RunnableScript](@ref soniccontrol.scripting.scripting_facade.RunnableScript). The Interpreter does not execute the whole AST, but instead steps through it and yields the result. This is needed, so we can step through the script with [InterpreterEngine](@ref soniccontrol.scripting.interpreter_engine.InterpreterEngine). It also does returns the command to be executed. This is done to simplify testing (We do only check if the right commands are returned and do not have to execute them) and to avoid async, as that adds complexity.

@}

