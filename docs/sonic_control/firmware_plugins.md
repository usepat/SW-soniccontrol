@defgroup FirmwarePlugins
@ingroup SonicControl
@addtogroup FirmwarePlugins
@{

# Firmware Plugins

## Requirements

The firmware can have different plugins installed. Such plugins can expose variables and actions (that execute operations on those variables and the device). They also can expose procedures.

Now is the big question how should sonic control interact with the plugins. There is a plug-n-play and a static plugin approach for this:

### Discovering Plugin functionalities

We added to the API already functions for iterating the plugins, getting meta infos about them and also iterating their variables and actions.  
With that we could create own python classes dynamically that represent the plugin. This is nice, for a GUI that exposes everything and with that you can directly interact, without having to setup anything. 
However for programming (like with the remote controller), this is bad, because intellisense will not be able to deduce the right types and members of the class. Therefore it will be cumbersome and error prone to develop with firmware plugins.

### Using plugins for Plugins

Alternatively we could create for each Firmware Plugin a corresponding Sonic control plugin. Because this is static it would work better with intellisense and static analysis. Therefore be better for development. Also like this we can use the already existing formwidget, that expets an attrs class as argument.  
However we have to ensure that we handle versions now right, because we have to check that both APIs match each other in all their endpoints exactly. Also to use now a firmware plugin, you have to install the corresponding sonic control plugin. So we have to manage more distributions now.

## Implementation

I would go with the first approach and some addition to it. I would create a function that takes the discovered plugin and an interface class. Then it creates and returns a wrapper class instance that basically connects the interface methods with the right api endpoints from the discovered plugin.  
Like this it is quite easy to develop with plugins and having appropriate intellisense. However there could still be some issues to it.

@}
