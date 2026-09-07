@defgroup ProtocolDefinition
@ingroup SonicProtocol
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

@see sonic_protocol.schema

A Protocol consists of a list of command contracts.  
Each command contract has a CommandCode as unique identifier and defines a command and the corresponding answer.  

### Command

@see sonic_protocol.schema.CommandDef

A Command Def defines which parameter the command takes. Note that we have index_param and setter_param. This has to do with the sonic text protocol syntax *!atf0=10000*, where the parameters are dependent on the syntax. So a command can only have 2 parameters max, a setter and an index. (Yes, this is because of the bad definition of the sonic text protocol. Could be refactored in the future. With keyword args we could improve this).  
A Command Parameter Definition has a unique name and a field type.  

### Answer

@see sonic_protocol.schema.AnswerDef

An Answer consists of a list of different values. Each item of this list is an Answer Field.  
Each Answer Field has a unique name and has a field type.

### Field Type

@see sonic_protocol.schema.FieldType

Field Types are the most basic component. They describe a single data value. they describe what type it has. It also describes the physical unit used. For example Mhz, kg, m, and so on...  
It is also used for validation by describing what the allowed values are or min and max values of the field.  
For that a Device Parameter Constant can be used, that are referenced over a Device parameter Constant Type.

### Constants

@see sonic_protocol.schema.DeviceParamConstants

Different devices can have different min max values for frequency, gain and so on. Therefore constants can be defined in an own constant struct in the protocol.

### Protocol list

Protocols change over time they may change, add or remove command contracts. Therefore each protocol list item references the previous one (for exampel v2.0.0 references v1.0.0). This item class can then apply changes to it.  
> Note: attention the naming is very bad. The ProtocolList class uses a template pattern. The single list items are subclasses of it. Those subclasses reference each other and create through that a linked list. Yes it is confusing and I may need to refactor this. Anyways...
The protocol list class provides also a function to create a protocol for a specific device with a specific version. The single subclasses of it are then calling each other recursively to create a list of command contracts and the constants needed.  
At this point I have to state that I am not very happy with this design. I will refactor this later on, so that there are not protocols for every device, but instead one giant protocol with all command contracts and a for each device a list of command codes that it can understand.  
Like that we make it more clear which commands are added, deleted, changed etc... And also the code will become less messy and more clear.

## Nested DataTypes and streams will never be supported

We could theoretically implement the ability to send nested data types like lists and dictionaries. Aside from that it can become quite complex to implement, We have also the problem that messages need to have a fixed size. We did this, because when the embedded device wants to receive or send a message it has to first create it in an internal buffer. However with lists and dicts such messages can become very fast very large, leading to overflows. Fixed size containers may work. But there exists  also variable length arrays sometimes and in either case it might not always be possible to store the resulting message in the buffer, because it is just too large. 
It makes then also no sense to send the whole message per se as packets, because it has to be reassembled anyways later and then we run into the same problem. So now for the moment we prefer to fetch the single items of lists and nested data types, and then construct the resulting type directly.

@}