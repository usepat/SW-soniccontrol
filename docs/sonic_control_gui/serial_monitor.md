@defgroup SerialMonitor
@ingroup SonicControlGui
@addtogroup SerialMonitor

@{

# Serial Monitor {#SerialMonitor}

## Brief Description

With the serial monitor can be communicated directly with the device.

## Use Cases

The User should be able to send commands.

The Answers of the commands should be displayed.

If the "read" button is switched on, then everything the devices sends should be displayed as it was received without processing.

There exists internal commands:
- Help: displays a help menu
- Clear: clears the console output

Also the user can select commands with from the command history via arrow keys.

So the serial monitor should provide similar functionalities to the terminal.

## Implementation

@see soniccontrol.views.control.serialmonitor.SerialMonitor

The SerialMonitor uses the [Communicator](@ref  soniccontrol.communication.communicator.Communicator) in the background. It provides the GUI interface. 
Commands are sent via [send_and_wait_for_answer](@ref  soniccontrol.communication.communicator.Communicator.send_and_wait_for_answer) and the received answer gets displayed.

### Read button

@see Communication

If the read button is switched to on, that it starts the [MessageFetcher](@ref soniccontrol.state_fetching.message_fetcher.MessageFetcher) and displays the messages received. It uses the [read_message](@ref soniccontrol.communication.communicator.Communicator.read_message) function of Communicator.

@}
