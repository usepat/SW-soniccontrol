@defgroup Network
@ingroup SonicControl
@addtogroup Network
@{

# Network

## Requirements

Software engineers like to work remote. However this has its implications, because with ssh you cannot access the GUI and RDP and other remote desktop clients and servers, may be slow or not work for complicated reasons.  

This is why I thought of creating a remote Soniccontrol server. To that we should be able to connect via the GUI, that uses in the background a client.

## Implementation

The Server provides endpoints for listing com ports, for connecting and disconnecting a comport and writing and reading data. It really only serves as a bridge. It does not understand the sonic protocol or commands, does not create a device etc. It really is just for transmitting plain bytes over a network and then redirecting them over the actual serial connection. 

On the soniccontrol side a ClientConnection class is used that creates a connection, that in background uses the client to transmit and receive all the data to the server.

For that I had to do my own asyncio.Transport implementation, so that I could reuse the StreamReader and StreamWriter classes from asyncio. So basically I dependency injected all the client logic. 

Also the server can be extended with plugins. For that you have to create a Flask Blueprint, that you then can register on the app instance.

@startuml
!include soniccontrol/class_network.puml
@enduml

@}
