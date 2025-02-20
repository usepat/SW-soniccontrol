@defgroup Measuring
@ingroup SonicControlGui
@addtogroup Measuring
@{

# Measuring {#Measuring}

## Brief Description

With Measuring we can capture the state of the device over time. This is very useful for experiments and monitoring.

## Use Cases

The User should be able to start and stop a capture manually. It should also be possible to synchronize the capture with a script or procedure.

There should be a sonic measure procedure, that does a ramp and captures exactly one data point for every frequency.

There should be a graph of the captured data points.

There should be generated a csv table for each measurement.

## Implementation

An [Updater](@ref soniccontrol.updater.Updater) runs in the backgrounds and fetches the whole time the device status over the dash command. 

### Starting and Stopping Captures

There exists a [Capture](@ref soniccontrol_gui.state_fetching.capture.Capture) class that is responsible for turning on and off the capturing  and sets up and tears down the [Capture Target](@ref soniccontrol_gui.state_fetching.capture_target.CaptureTarget). It gets the updates form the Updater over events.
The captured data points are then propagated through events to the [CsvWriter](@ref soniccontrol_gui.state_fetching.csv_writer.CsvWriter) and the [DataProvider](@ref soniccontrol_gui.state_fetching.data_provider.DataProvider).  
- CsvWriter is responsible for writing the csv file
- The data provider saves only the last 100 data points and provides them to the plots.

### Plotting

To handle plotting more easily, a [Plot](@ref soniccontrol_gui.utils.plotlib.plot.Plot) class was made and the creation of plots was moved to the [PlotBuilder](@ref soniccontrol_gui.utils.plotlib.plot_builder.PlotBuilder).

@startuml
!include sonic_control_gui/measuring.puml
@enduml

@}