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

Complex constructs are yet not required.

Also SonicControl provides for that a Editor where you can also debug through a script step by step. 
For that it is needed that we can also execute the script step by step and that it provides us also with the information which line and command it executes (for highlighting that line in the editor).

## Implementation

There exists two versions of the parser. A old one and a new one. The new one was written after the programmer realized what the standard for writing parsers is (We all made those mistakes as beginners). However the new parser lies at the moment in its own repo and will replace the old one in the future.

To make replacement easier the whole interpreter logic is hidden in the facade [LegacyScriptingFacade](@ref legacy_scripting.LegacyScriptingFacade).
It provides the method [LegacyScriptingFacade.parse_text](@ref soniccontrol.scripting.scripting_facade.ScriptingFacade.parse_text) that returns you a [Script](@ref soniccontrol.scripting.scripting_facade.Script) that is an async iterator (so it can be executed step by step), that returns the line number and command name of the currently executed command.

The [Interpreter Engine](@ref soniccontrol.scripting.interpreter_engine.InterpreterEngine) takes a parsed script and executes it. With that it is possible to stop and resume execution.

### Legacy

The [LegacyScriptingFacade](@ref legacy_scripting.LegacyScriptingFacade) uses internally the @ref soniccontrol.scripting.legacy_scripting.SonicParser to parse the text to a list of commands, arguments and loops. The loops are a list of dicts, that specify start or stop index and the quantifier (how many times to run a loop). 
Those results are then taken by the [LegacySequencer](@ref soniccontrol.scripting.legacy_scripting.LegacySequencer) that is a subclass of [Script](@ref soniccontrol.scripting.scripting_facade.Script). So this is the interpreter.

### New

The new parser defines a clear syntax with a lexer for parsing. It creates an Abstract Syntax Tree that then can be iterated by an Interpreter.  
This was implemented by Ilja and resides in some old branch. Sadly, it was until now not merged into the new code. Probably it also never will, because if the user really wants to create more complex scripts, then he can also just use python with the soniccontrol package. So there is not really such a big need for this feature.

@}

