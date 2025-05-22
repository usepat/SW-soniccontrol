@defgroup data_capturing
@ingroup SonicControl
@addtogroup data_capturing
@{

# Data capturing {#data_capturing}

## Requirements

The lab guys (STS and CG) want to conduct experiments, where they need not only to measure consistently but also save those results.  
A established Data Format should be used for that. It should efficiently save large data chunks as experiments can go on for days. Also it should be able to save metadata. It is important to specify the experiment setup, to put the collected data into context.  
It should be possible to synchronize an experiment with a procedure or script (The experiment should only collect the data produced during the procedure run. Or in other words: an experiment should last as long as the execution of a procedure).

## Implementation

### File Format

As file format HDF5 is used. It is a widely established format for writing experiment data. It is hierarchical structured. Each node can contain attributes that describe meta information or data and each node contains a table for storing the actual data points. PyTables library is used for writing HDF5 files and the [HDF5ExperimentStore](@ref soniccontrol.data_capturing.experiment_store.HDF5ExperimentStore) class is responsible for writing the experiments. It inherits from [ExperimentStore](@ref soniccontrol.data_capturing.experiment_store.ExperimentStore) that is a general interface for writing experiments to some kind of store like a file. The interface was introduced, because maybe in the future we want to send experiments data to a data base or to a server, maybe we want also to use a different file format.

### Experiment class

[ExperimentMetaData](@ref soniccontrol.data_capturing.experiment.ExperimentMetaData) define the meta data attributes we want the user to provide. The user can also add own custom meta data to it.  
[Experiment](@ref soniccontrol.data_capturing.experiment.Experiment) uses then this meta data and sets additionally other meta data attributes that can be deduced by the program. For example the device type, protocol used, the arguments to a procedure, procedure type, script to be executed, etc..

To make serializing easier we use marshmallow-annotations. It converts an attrs class into a marshmallow schema. A marshmallow schema defines how custom classes should be parsed to plain python types: int, float, bool, str, dict, list. Those can then be further processed by other serialization methods like `json.dumps`. It also makes it convenient to write own serializers for it like [HDF5ExperimentStore](@ref soniccontrol.data_capturing.experiment_store.HDF5ExperimentStore).

### Capturing Data

An [Updater](@ref soniccontrol.updater.Updater) runs in the backgrounds and fetches the whole time the device status over the dash command. It emits then update events, that are subscribed by different classes. 

One of the classes subscribed to it is the [Capture](@ref soniccontrol.data_capturing.capture.Capture) class, that is responsible for turning on and off the capturing, writing [Experiments](@ref soniccontrol.data_capturing.experiment.Experiment) to the [ExperimentStore](@ref soniccontrol.data_capturing.experiment_store.ExperimentStore), and sets up and tears down the [CaptureTargets](@ref soniccontrol.data_capturing.capture_target.CaptureTarget).  

A CaptureTarget follows the [Strategy Pattern](https://refactoring.guru/design-patterns/strategy). It defines the method for starting the target execution and hooks for setting up and tearing down the target. The [CaptureScript](@ref soniccontrol.data_capturing.capture_target.CaptureScript) for example, loads the script, then executes it, then does additional cleanup afterwards. CaptureTargets have also an [args](@ref soniccontrol.data_capturing.capture_target.CaptureTarget.args) method that returns the arguments. This data is then injected into the experiment metadata.
 
The [DataProvider](@ref soniccontrol.state_fetching.data_provider.DataProvider) saves only the last 100 data points and provides them to the plots in the gui. It gets the data from the Capture class.

@startuml
!include soniccontrol/class_data_capturing.puml
@enduml

@}