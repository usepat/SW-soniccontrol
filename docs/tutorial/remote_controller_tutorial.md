@defgroup RemoteControllerTutorial
@ingroup Tutorial
@addtogroup RemoteControllerTutorial
@{

# RemoteController Tutorial

@see soniccontrol.remote_controller.RemoteController

The RemoteController is a class for communicating with a device over a serial connection. It is used as simplified interface (Facade Pattern) for the soniccontrol package.

```py
# Importing the RemoteController, commands and EFieldNames
from soniccontrol.remote_controller import RemoteController
import sonic_protocol.python_parser.commands as cmds
from sonic_protocol.field_names import EFieldName

import asyncio

# This is our main function.
async def main():
    # creating the remote controller
    controller = RemoteController()

    # connecting over serial to a USB port
    await controller.connect_via_serial(Path("/dev/ttyUSB0"))

    # The controller uses internally an updater that fetches updates via the dash command from the device.
    # Disable it, if you want better latency. (Faster response times)
    # But be careful, because some functions of the controller depend on the updater. (To determine if procedures are running for example). 
    await controller.stop_updater()

    # We cen send commands to the device.
    # We can send directly commands as strings 
    # (Do not use this, except you want to directly send user input to the device)
    # (You should not use this, because you can easily make typos and intellisense cannot detect it)
    await controller.send_command("?protocol")
    # Or we can send them by predefined command classes 
    # (This is the preferred way. Typos are detected by intellisense, because it is a class and not a string)
    await controller.send_command(cmds.GetProtocol())

    # For every command send an answer is returned
    answer_gain = await controller.send_command(cmds.GetGain())
    
    # An answer is a tuple consisting of the message received, a dictionary that contains the parsed contents, a bool that is True, if the answer is valid
    answer_message_str, answer_field_dict, is_valid = await controller.send_command(cmds.SetAtf(1, 100000)) # some commands take arguments as input
    
    print(answer_message_str)
    if is_valid:
        # We can access the parsed contents of the answer by its field name. 
        print(answer_field_dict[EFieldName.ATF])

    # We disconnect the controller
    await controller.disconnect()

if __name__ == "__main__":
    # The asyncio framework executes our async main function in a loop.
    asyncio.run(main())
```

@}