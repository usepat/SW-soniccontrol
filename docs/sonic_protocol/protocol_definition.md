@defgroup ProtocolDefinition
@defgroup SonicProtocol
@addtogroup ProtocolDefinition
@{

# Protocol Definition {#ProtocolDefinition}

## Description

This describes the structure of a protocol, what the single components are, that define it.

## Diagram

@startuml
!include sonic_protocol/defs.puml
@enduml

## Implementation

@see sonic_protocol.defs

A Protocol consists of a list of command contracts.  
Each command contract has a CommandCode as unique identifier and defines a command and the corresponding answer.  

### Command

@see sonic_protocol.defs.CommandDef

A Command Def defines which parameter the command takes. Note that we have index_param and setter_param. This has to do with the sonic text protocol syntax *!atf0=10000*, where the parameters are dependent on the syntax. So a command can only have 2 parameters max, a setter and an index. (Yes, this is because of the bad definition of the sonic text protocol. Could be refactored in the future. With keyword args we could improve this).  
A Command Parameter Definition has a unique name and a field type.  

### Answer

@see sonic_protocol.defs.AnswerDef

An Answer consists of a list of different values. Each item of this list is an Answer Field.  
Each Answer Field has a unique name and has a field type.

### Field Type

@see sonic_protocol.defs.FieldType

Field Types are the most basic component. They describe a single data value. they describe what type it has and references a Converter to convert it (Gets used in the back ends for parsing). It also describes the physical unit used. For example Mhz, kg, m, and so on...  
It is also used for validation by describing what the allowed values are or min and max values of the field.  
For that a Device Parameter Constant can be used, that are referenced over a Device parameter Constant Type.

### MetaExport

@see sonic_protocol.defs.MetaExport

A wrapper class that attaches information about for what devices, protocol_versions the wrapped content is available.

@}