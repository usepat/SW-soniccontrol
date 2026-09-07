@defgroup plugin
@ingroup SonicControlGui
@addtogroup plugin
@{

# Plugins

## Requirements

Some functionalities should only be used internally in the company and should not be available for outstanding users.  
Also in the future the need may arise to create plugins for specific clients targeting their workflow and requirements.  
Therefore plugins are needed, so that it is possible to add functionality to soniccontrol from the outside.

## Implementation

Python offers a plugin like system via `pyproject.toml`. There can entry-points be defined that can be registered and then searched through. Those entry points are then also listed in an own file inside the python package. So it is possible to load them from the directory of bundled applications and zipped folders directly and not only over plugins installed via pip.  
The Plugins per se use the hooks and factory design patterns. SonicControl only provides the common interfaces and the hooks. The plugins the implementations.  
Note that plugins should be standalone. They should not depend on shared libraries and packages. Else wise we would need to stricter versionize them.

@}