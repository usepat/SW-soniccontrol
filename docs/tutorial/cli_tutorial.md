@defgroup CliTutorial
@ingroup Tutorial
@addtogroup CliTutorial
@{

# Cli Tutorial

The CLI can be started with `soniccontrol` in the command line after installing it in editable mode via pip `pip install -e <FOLDER/TO/SONIC_CONTROL>`.

The cli is very useful for cases, where we cannot use the gui (for example being connected over ssh) or want an interface to interact with sonic control via the command line (Useful for automation).
Cli
The cli offers 4 types of different actions we can perform on the device:
- monitor: opens a serial monitor, to send commands to the device
- spectrum: measures a spectrum
- procedure: executes a procedure on the device
- script: executes a script

## Connecting

SonicControl expects as argument the path to the port, it should connect to.
```bash
soniccontrol /dev/USB0
```
We can specify the baudrate
```bash
soniccontrol --baudrate=9600 /dev/USB0 
```

Also we can say, that we do not want to connect to a serial port, but instead to a process.
This allows us to start and connect to the firmware simulation.
```bash
soniccontrol --connection=process /path/to/simulation 
```

Also we can specify to which folder it should write the logs
```bash
soniccontrol --connection=process --log-dir=path/to/log_dir /path/to/simulation 
```

After specifying how to connect to the device, we can specify the action we want to perform.

## Monitor

This is the command for the monitor
```bash
soniccontrol /dev/USB0 monitor
```

Example output:
```
Welcome to the monitor. 
    Input 'help' to get the manual for the device and 
    input 'exit' to leave the monitor.
mvp_worker@v1.1.1>>> -
0#2250000 Hz#50 %#none#0 mK#0 uV#0 uA#0 u°#OFF#0 uV
mvp_worker@v1.1.1>>> ?info
mvp_worker#v1.1.1#v0.1.1#BuildHash#21.02.2025
mvp_worker@v1.1.1>>> !freq=100
The param value is 1007. That is lower than the minimum allowed of 100000
mvp_worker@v1.1.1>>> !freq=100000
100000 Hz              
mvp_worker@v1.1.1>>> 
```

Type `exit` to exit the monitor and `help` to get the manual for the protocol that lists you all possible commands.

## Spectrum

The spectrum is basically a ramp that measures each frequency set, exactly once.  
It needs as argument a json file that contains metadata information about the experiment.  
It creates a json file of the measured data. The output location of that file can be set with `--out-dir`. 
```bash
soniccontrol /dev/USB0 spectrum <metadata-file> --out-dir=path/to/dir
```

After starting the spectrum it will first ask you in the prompt, what values it should use for the parameters.  
But you can also specify those parameters directly in the cli command. If you specify them there, it will not ask you again for them later.
The parameters are the following:
- `--freq-center`
- `--half-range`
- `--step`
- `--hold-on`
- `--hold-off`
- `--time-offset-measure`

## Procedures

Procedures can be started by specifying which procedure you want to execute:
```bash
soniccontrol /dev/USB0 procedure ramp
```
Following procedures can be started:
- ramp
- tune
- wipe
- auto
- scan

Like for the spectrum, it will prompt you questions on what parameters it should use for the procedures, but you can also specify that previously as command line options.
```bash
soniccontrol /dev/USB0 procedure ramp --freq-start=100000 --freq-stop=200000 --freq-step=10000 
```

The program automatically finishes, after the procedure finished.

## Script

For executing the script, you have to specify path to the file as argument. 
It will then execute the script and prompt the lines executed after each other. 
That means also that it will unroll loops. So if you have a command "!ON" in a loop, that gets 
iterated five times, then it will prompt "!ON" five times.

```bash
soniccontrol /dev/USB0 script path/to/script
```

@}