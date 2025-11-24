@defgroup Correspondence
@ingroup SonicControl
@addtogroup Correspondence
@{

# Correspondence

## Brief Description

This document describes how commands and answers are represented in code, constructed and processed.  
How exactly they are parsed and validated is part of the [sonic protocol parsing submodule](@ref Parsing).

## Diagram

@startuml
!include soniccontrol/class_correspondence.puml
@enduml

## Implementation

The SonicDevice is responsible as proxy to serialize the commands and send them to the device over the [Communicator](@ref soniccontrol.communication.communicator.Communicator) class. As also to receive the answers, parse and validate them.  
So it glues together the @ref Parsing module and the @ref Communication module for correspondence.

To determine which commands can be used the [ProtocolBuilder](@ref sonic_protocol.protocol_builder.ProtocolBuiler) extracts them from the [Protocol](@ref sonic_protocol.protocol.protocol) and saves them into a command look up table.  
There is also defined, how to parse the commands and answers. What information is contained.
@See SonicProtocol

Every Command (and the corresponding Answer) has a [command code](@ref sonic_protocol.command_codes.CommandCode). With that the SonicDevice can query its command look up table to extract the right [command definition](@ref sonic_protocol.defs.CommandDef) and [answer definition](@ref sonic_protocol.defs.AnswerDef), that describe how to parse/serialize the commands and answers. 

For providing more flexibility for the user, you can not only send Commands (classes) but also plain strings via [execute_command](@ref soniccontrol.sonic_device.SonicDevice.execute_command). The SonicDevice class will try to parse the string first to a command with CommandDeserializer. So that it can look it up and find the corresponding answer validator.  
If for a command or string, there exists an answer validator, it will be used to parse and validate the answer. This does not only ensure correctness, but also extracts the answer fields into a field_value_dict. Else wise this dict will be empty.

### Legacy - Communication with Crystal Plus

TODO: Thomas
TODO: Ich glaube Kommentare in der Klasse sind nützlicher als wie Dokumentation hier. Ich würde die Beschreibung hier kurz halten.


@}