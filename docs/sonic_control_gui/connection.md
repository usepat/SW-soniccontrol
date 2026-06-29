@defgroup EstablishingConnection
@ingroup SonicControlGui
@addtogroup EstablishingConnection
@{

# Establishing a Connection {#EstablishingConnection}

## Brief Description

The application can connect to different devices new and old.

## Use Cases

The user should be able to choose to wich device (port) to connect.

For each connection there should be opened an own Window for the connected device.

It should be possible to connect to new devices and also to the old ones.

## Implementation

The [ConnectionFactory](@ref soniccontrol.connection.connection_factory.ConnectionFactory) together with the [CommunicatorBuilder](@ref soniccontrol.connection.communicator_builder.CommunicatorBuilder) are used to establish a connection and then with [DeviceBuilder](@ref soniccontrol.builder.DeviceBuilder) a [Device](@ref soniccontrol.sonic_device.SonicDevice) is build.  
There is a [LegacySerialCommunicator](@ref soniccontrol.connection.serial_communicator.LegacySerialCommunicator) for the old devices and a [SerialCommunicator](@ref soniccontrol.connection.serial_communicator.SerialCommunicator) for the new ones.  
All this code lies inside [soniccontrol](#SonicControl).

The code for choosing a connection and handling different connections through a GUI lies in [soniccontrol_gui](#SonicControlGui).

@startuml
!include sonic_control_gui/connection.puml
@enduml

### Connection Window

@see sonic_control_gui.views.core.connection_window.ConnectionWindow

The ConnectionWindow lets you select one from different connections over a drop down menu.  
On pressing connect the [_attempt_connection](@ref sonic_control_gui.views.core.connection_window.ConnectionWindow._attempt_connection) method gets called internally, that tries to connect to the device and opens then a DeviceWindow.  
If it fails it opens a RescueWindow instead.

### DeviceWindowManager

@see sonic_control_gui.views.core.connection_window.DeviceWindowManager

The DeviceWindowManager is a simple helper class that opens and stores the windows opened. It also adds a callback to them, that on close the windows delete the references to them self.

### Device Window

Base class for device windows that contains a reference to the communicator and handles closing itself on a disconnect.

It has also a [AppState](@ref sonic_control_gui.views.core.app_state.AppState) that is used for global state for a single window. This is useful, when we want to disable some buttons, because a procedure, script is executing, or the device got disconnected.

#### Known Device Window

@see sonic_control_gui.views.core.device_window.KnownDeviceWindow

This is a window for one device with SerialMonitor, Flashing, Logging and so on. 
It contains basically all the interesting tabs. 

#### Rescue Window

@see sonic_control_gui.views.core.device_window.RescueWindow

The RescueWindow has only the tabs [SerialMonitor](@ref sonic_control_gui.views.control.serialmonitor.SerialMonitor) and [Logging](@ref sonic_control_gui.views.control.logging.Logging). The ConnectionWindow initializes it with a [LegacyCommunicator](@ref soniccontrol.connection.serial_communicator.LegacySerialCommunicator). It is used for very old devices, with that we cannot connect in other ways, but also for debugging, if a connection is not possible.

### Postman Window

For the postman exists an own Device Window, because it is a shallow router and only needs a tab for establishing a connection with the worker and configuring modbus settings. All the other tabs for the other devices make no sense for the postman.

@}