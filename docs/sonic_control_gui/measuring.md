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

@see data_capturing

The MeasuringTab enforces you to first create an experiment, then select the target (procedure, scripting, free, sonic_measure), then insert meta data and then you can finally start capturing.  
Because of this whole sequence of states, Measuring Tab is kind of a little state machine.  
For creating the meta data form, the [FormWidget](@ref soniccontrol_gui.widgets.form_widget.FormWidget) class is used, that deduces it automatically from the [ExperimentMetaData](@ref soniccontrol.data_capturing.experiment.ExperimentMetaDAta) class over attrs introspection.

## Spectrum Measure

@see soniccontrol.procedures.procs.specrum_measure.SpectrumMeasure

SpectrumMeasure is implemented as a local procedure. It deactivates the Updater, so that it stops to fetch automatically in the background. Then after setting each frequency, it uses the updater to force an update. I wanted it to use the updater to enforce updating all its dependent subscribers and therefore updating the rest of the application.

### Plotting

To handle plotting more easily, a [Plot](@ref soniccontrol_gui.utils.plotlib.plot.Plot) class was made and the creation of plots was moved to the [PlotBuilder](@ref soniccontrol_gui.utils.plotlib.plot_builder.PlotBuilder).

@startuml
!include sonic_control_gui/measuring.puml
@enduml

@}