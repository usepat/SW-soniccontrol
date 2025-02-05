@defgroup SonicControl
@addtogroup SonicControl
@{

# SonicControl {#SonicControl}

## Brief Description

@see soniccontrol

SonicControl is the core of the SonicControl suite.
It contains all necessary functionality to communicate with the device, send commands and get answers, execute scripts and execute procedures.

@startuml
!include soniccontrol/class_sonic_control.puml
@enduml

## Sonic Device

@see soniccontrol.sonic_device.SonicDevice

The SonicDevice is responsible for executing commands (sending them to the device) and validating and parsing the answer. It acts as remote control proxy. It basically represents the device and hides all the communication that occurs under the hood, so that you can program, like you execute commands on the device directly (Proxy Pattern).  
The amp has to be constructed with the [DeviceBuilder](@ref soniccontrol.builder.DeviceBuilder) after constructing the [Communicator](@ref soniccontrol.communication.communicator.Communicator).

## RemoteController

@see soniccontrol.remote_controller.RemoteController

The RemoteController provides a class that encapsulates everything. From accessing and setting attributes like frequency, to executing scripts and commands. 
It is used by @ref sonic_robot that is a library for the RobotFramework and basically just wraps the RemoteController.  
Also it will be used by the @ref soniccontrol_cli.

@}