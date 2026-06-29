@defgroup SystemTests
@ingroup Testing
@addtogroup SystemTests
@{

# System and Integration Testing {#SystemTests}

In contrast to [Unit testing](@ref UnitTests), System testing is about testing the whole system and not just a single unit of it.
There is also integration testing, that focus on testing if a collection of units works together as expected. The transition from integration testing to system testing is fluid.

For the integration testing we use a binary of our [firmware](https://github.com/usepat/FW-sonic-firmware/tree/stable) that simulates it locally on the pc (but only for Linux). 
We can start this binary as a process in the command line and can communicate with it over `stdout` and `stdin`.
In the code we do this over [CLIConnectionFactory](@ref soniccontrol.ConnectionFactory.CLIConnectionFactory).

For testing the GUI we use the GuiController class. Every widget gets registered over a name in the WidgetRegistry and the GuiController offers methods to interact with the widgets programmatically. Additionally to that there is a file called workflows, that contains functions for simulating user interactions (like filling out an experiment form).

Because for the simulation and real device (and also for different device types like postman and worker) we need to interact differently with the GUI to open the device window. Therefore we use a Strategy pattern for Connecting with the Device and opening the Device Window. (This is not implemented yet)


### How widgets are registered and used for integration testing

All important widgets are registered in the [WidgetRegistry](@ref soniccontrol_gui.utils.widget_registry.WidgetRegistry) after they got instantiated. And when they get removed they are unregistered. This has to be done manually in the code for every widget, we are interested in.

TKinter already does have an unique name for all widgets. We could use that for retrieving them directly, instead of registering them.  
However, this is not desirable, as the widgets have hierarchical names and are dependent on the visual tree. So when we change the layout of our application, by wrapping the widgets in some frames, we also change their name and we have to update that then across all the test cases... Therefore I decided to register them manually and give them own unique names. 
Also this allowed me to create asyncio.flags for each widget, that are set true, when it got registered. This is useful, for when we want to wait for a widget to be registered.  

Registered widgets have also a flag, that gets set when the text of the widget changed. Text changes are detected not via an callback, but simply over a task that runs in the background, goes through all registered widgets and checks, if they changed. There is also a method to unset the text_changed flag. It is important to call it, before waiting for a text change, because the text change flag could have been already set by some other action. Waiting for a text change via wait_for_widget_to_change_text also resets the flag afterwards.

## pytest quirks

For using pytest together with async/await, we use the library pytest_asyncio. It runs each test in an own event loop. However for some fixtures, we want to instantiate them only once for the whole package, because they are expensive. The event loop of such a fixture is not automatically shared, you have to set `loop_scope="package"` to use it.  

Also because the tkinter event loop (has nothing to do with the asyncio event loop) runs in an own task, the gui updates only if that task gets scheduled. Therefore it is important to use `await gui_controller.execute_events_until_idle()` that updates tkinter and yields (lets other tasks execute) after button presses or other simulated user interactions.

@}