@defgroup sonic_control_cli
@addtogroup sonic_control_cli
@{

# SonicControl - CLI {#sonic_control_cli}

The command line interface for sonic control, can be started with `soniccontrol_cli`. It uses the [RemoteController](@ref soniccontrol.remote_controller.RemoteController) in the background. 

For connecting you have to specify the `PORT` like */dev/USB0*. You can specify options, they have to be written before PORT.   Over `--baudrate` the baudrate can be set. If you want to connect to the simulation, you have to add `--connection process` and then supply the path to the simulation in `PORT`. With `--log-dir` the path for writing logs can be set.

After that you have to specify which action you want to perform:
 - `monitor`: Opens the serial monitor
 - `script`: Executes a script
 - `procedure`: Executes a procedure
 - `spectrum_measure`: Creates an experiment and executes spectrum measure. It writes the experiment to a HDF5 file.

With `--help` you get a list of possible options and arguments. NOT OF ALL arguments and options, tho. Only for the subaction specified. So `soniccontrol_cli --help` gives you a the options and arguments specified for connecting, however `soniccontrol_cli <PORT> monitor --help` gives you the options and arguments for the monitor command.  
Also there is a known issue, that it often tries to connect to the device first, before returning the help page.

## Monitor

The Monitor is a REPL (Read-Eval-Print-loop). It sends the input directly to the device and returns the result in the next line below. Logs and notification messages are not included.  
The answers are printed in red, if they are not valid. That means they could either not be parsed or contain error messages. 

If you send `help` it will build a markdown manual for the protocol used and display it to you in an terminal editor.  
If you send `exit` it will exit the monitor and stop the application.

## Script

The script action takes a `SCRIPT-FILE` argument. It will then execute the script and display a description for each step executed (command name and parameter values).

## Procedure

The procedure action is basically a group of subactions. Each procedure `ramp`, `tune`, `scan`, `wipe`, `auto` is its own subaction with own options. For example: 
```
soniccontrol_cli <PORT> procedure ramp --f-start 100000 --f-stop 200000 --t-on 500ms 
```
Use `--help` to get the options for the desired procedure. 

## Spectrum Measure

Spectrum Measure is at the moment the only action that is designed to be used in a experiment setup. It takes a `METADATA-FILE` as input. This should be a json file with all attributes defined in the [ExperimentMetaData](@ref soniccontrol.data_capturing.experiment.ExperimentMetaData) class. It also takes an option `--out-dir` that specifies where the resulting HDF5-file is written. Other options are the Spectrum Measure arguments, retrieve them with `--help`.

@}