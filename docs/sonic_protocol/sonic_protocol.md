@defgroup SonicProtocol
@addtogroup SonicProtocol
@{

# Sonic Protocol {#SonicProtocol}

## Description

The Sonic Protocol defines how the communication interface with the device. What commands it can understand and what it returns as an Answer.

## Diagram

@startuml
!include sonic_protocol/protocol.puml
@enduml

## Problem

The main problem is, that we have different devices that can understand different commands. As well that the answers for commands or commands them self, will sometimes be extended with additional data in the future. So the problem is to know which commands the device knows, how it understands them and what it will return as an answer.  
Another problem is that we need consistency between SonicControl, the Firmware and the User Manual (where all commands are listed and described) as all should refer to the exact same set of commands and answers (=Protocol).

## Implementation / Solution

The solution I came up with is as follows:

### Deducing the Protocol

I define a [protocol](@ref sonic_protocol.defs.Protocol) that contains [command contracts](@ref sonic_protocol.defs.CommandContract), that defines a command definition and an answer definition, that describe what the structure of commands and answers are.  
Such CommandContracts, as well as Command definitions and Answer definitions can be wrapped inside a [MetaExport](@ref sonic_protocol.defs.MetaExport) class. This class functions as wrapper to append additional information about for what devices and protocol versions the wrapped content is available.  
With the [ProtocolBuilder](@ref sonic_protocol.protocol_builder.ProtocolBuilder) a protocol for a specific device and protocol version can then be extracted. Also there exists a *?protocol* command, that gives back which protocol version, device_type, build type... gets understood by the device.

### Sonic Protocol Backends

The ProtocolBuilder returns a dictionary of [CommandLookUps](@ref sonic_protocol.protocol_builder.CommandLookUp), that are associated with a [CommandCode](@ref sonic_protocol.command_codes.CommandCode) as unique key. A Command Look Up contains the extracted CommandDef and AnswerDef as also additional Attributes (for specific backends).  
A Protocol Backend processes now this data further:
 - [CppTransCompiler](@ref sonic_protocol.cpp_trans_compiler.cpp_trans_compiler.CppTransCompiler): compiles the protocol to a hpp file, that is then included in the firmware code. 
 - [MarkdownManualCompiler](@ref sonic_protocol.user_manual_compiler.manual_compiler.MarkdownManualCompiler): compiles a manual for the protocol in markdown.
 - [PythonParser package](@ref sonic_protocol.python_parser): classes for parsing commands and answers, used by [SonicDevice](@ref soniccontrol.sonic_device.SonicDevice) class in SonicControl package.
@}