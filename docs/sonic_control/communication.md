
@defgroup Communication
@ingroup SonicControl
@addtogroup Communication
@{

# Communication {#Communication}

## Brief Description

SonicControl communicates with the device connected to the computer. The communication package is responsible for sending and receiving messages.

# Diagram

@startuml
!include soniccontrol/class_communication.puml
@enduml

# Implementation

## Connection

The connection is established by the [ConnectionFactory](@ref soniccontrol.communication.connection_factory.ConnectionFactory) and can either be to a serial port or to a process (that simulates the device).
In future also a connection with tcp or udp over a server could be added. 

## SonicMessageProtocol

@see soniccontrol.communication.message_protocol.SonicMessageProtocol

This protocol class is responsible for parsing the messages received by the communicator, as well for defining a terminator for a message.  
There a currently three types of messages defined:
- COM#{ID}={COMMAND}: Command. With a unique id (different for each message sent).
- ANS#{ID}={ANSWER}: Answer. With the id of the command, the answer responds to.
- LOG={LOG}: Device Log.
- NOTIFY={NOTIFY_MESSAGE}: For notifications. Messages that are send by pushing not pulling. Similar to logs but can be interpreted
Commands are sent by SonicControl and Answers and Logs by the device.

## Communicator

@see soniccontrol.communication.communicator.Communicator

The Communicator is responsible for establishing and also putting down a connection with the [ConnectionFactory](@ref soniccontrol.communication.connection_factory.ConnectionFactory).
Over the Communicator Messages can be send and received. It offers mainly two methods for that:
- [send_and_wait_for_answer](@ref soniccontrol.communication.communicator.Communicator.send_and_wait_for_response): for sending a request and waiting then for the response.
- [read_message](@ref soniccontrol.communication.communicator.Communicator.read_message): for fetching whatever message just got read by the Communicator
So we have a method that pushes and waits and a method for pulling.

### New Communicator

The new communicator uses internally a [MessageFetcher](@ref soniccontrol.communication.message_fetcher.MessageFetcher) that runs in the background and constantly reads messages from the input stream. It stores then the messages in a dictionary (Key is the ID of the answer). The Communicator can then get the answer via [get_answer_of_request](@ref soniccontrol.communication.message_fetcher.MessageFetcher.get_answer_of_request). The method is awaitable. So we can support like this concurrency.


@}