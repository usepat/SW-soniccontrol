@defgroup SonicRobot
@ingroup Testing
@addtogroup SonicRobot
@{

# Sonic Robot

@see sonic_robot

To test our application with the robot framework, we have to provide an interface for it.  
This is done by writing a robot library as API.

## Robot Remote Controller

@see sonic_robot.robot_remote_controller.RobotRemoteController

The RobotRemoteController wraps the [RemoteController](@ref soniccontrol.remote_controller.RemoteController) into a robot library.

## Robot Sonic Control GUI

@see sonic_robot.robot_sonic_control_gui.RobotSonicControlGui

The RobotSonicControlGui library contains functions to open the application and close it and provides functions to interact with the single widgets of the application.  
For that each widget has an own name, defined in [variables](@ref sonic_robot.variables). A widget can be clicked, the text of it can be read or set.  
It also contains functions to wait for changes in the gui. Waiting for a widget to change text for example or wait for a widget to appear (to be registered).

### How widgets are registered

All important widgets are registered in the [WidgetRegistry](@ref soniccontrol_gui.utils.widget_registry.WidgetRegistry) after they got instantiated. And when they get removed they are unregistered. This has to be done manually in the code for every widget, we are interested in.

TKinter already does have an unique name for all widgets. We could use that for retrieving them directly, instead of registering them.  
However, this is not desirable, as the widgets have hierarchical names and are dependent on the visual tree. So when we change the layout of our application, by wrapping the widgets in some frames, we also change their name and we have to update that then across all the test cases... Therefore I decided to register them manually and give them own unique names. 
Also this allowed me to create asyncio.flags for each widget, that are set true, when it got registered. This is useful, for when we want to wait for a widget to be registered.

@}