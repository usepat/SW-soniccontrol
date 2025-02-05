@defgroup Logging
@ingroup SonicControl
@addtogroup Logging
@{

# Logging {#Logging}

## Use Cases

Logging is very important for every software. Logs can contain vital insights into the history of an application. This can be very useful for debugging. Imagine a client has a crash and you have no logs, that give you any hint of what happened.

## Implementation

Logging is implemented in sonic control in a way that each class gets passed an instance of the callers logger and the class derives then its own logger from it. So for example the caller has the logger "caller_logger" and then the class gets this one passed and derives its own from it "caller_logger.class_logger".

Also the SonicControl GUI application creates an own logger for each connection. So you have normally something like `connection.class1.class2` as logger names, where class1 instantiated class2. For example `COM1.SerialCommunicator.PackageFetcher`.

The log files get written into a file with the same name as the connection normally. This is defined in the method [create_logger_for_connection](@ref soniccontrol.logging.create_logger_for_connection).  
Also the directory for the logs is dependent on the operating system:
 - Linux: "~/.SonicControl"
 - Mac: "/Library/Application Support/SonicControl"
 - Windows: "%APPDATA\SonicControl"
Implementation for this is in the function [create_appdata_directory](@ref soniccontrol.system.create_appdata_directory)

The device can also send logs. Those are parsed and then forwarded to an own Device Logger.
@see soniccontrol.communication.message_protocol.SonicMessageProtocol

SonicControl uses Log handlers to display then the logs in the **Logging Window**.

@}