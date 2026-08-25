import datetime

from soniccontrol import commands as cmds
from soniccontrol import (
    RemoteController, EFieldName, AbsoluteFrequencySIVar, SIPrefix,
    DeviceType, SpectrumMeasureArgs, 
    HDF5ExperimentWriter, DataTableWorker, Experiment, ExperimentMetaData
)
from soniccontrol.app_config import SOFTWARE_VERSION, PLATFORM, get_simulation_exe
from soniccontrol.data_capturing.capture import CaptureFree, Capture
from soniccontrol.data_capturing.capture_target import CaptureTargets
from soniccontrol.procedures.procedure import ProcedureType
from soniccontrol.procedures.procs import RamperArgs

import asyncio
from pathlib import Path
import pandas as pd

from soniccontrol.updater import Updater


# This is our main function.
async def main():

    # === Connecting the controller to a device === 

    # Do not use RemoteController constructor directly instead use the static connect methods

    # connecting over serial to a USB port
    # controller = await RemoteController.connect_via_serial(Path("/dev/ttyUSB0"))

    sim_exe = get_simulation_exe()
    assert sim_exe is not None, "No path defined in env to firmware directory"
    controller = await RemoteController.connect_via_simulation(
        sim_exe, 
        ['--profile=worker']
    )

    # device_info attribute gives you information about the connected device.
    # ensure that it is in operator mode and really the device you expect (Sometimes devices can be misconfigured or have the wrong firmware flashed or some weird firmware bugs)
    assert controller.device_info.device_type == DeviceType.MVP_WORKER, "the device is no worker or not in operator mode"

    # The controller uses internally an updater that fetches updates via the dash command from the device.
    # Disable it, if you want better latency. (Faster response times)
    # But be careful, because some functions of the controller depend on the updater. (To determine if procedures are running for example). 
    await controller.stop_updater()

    # the device could be in service mode or procedures could run on it.
    # stop running processes ensures that the device is in an idle mode and no special state,
    # by going out of service mode and stopping all running procedures.
    await controller.stop_running_processes()


    # === Executing Commands === 

    # We cen send commands to the device.
    # We can send directly commands as strings 
    # (Do not use this, except you want to directly send user input to the device)
    # (You should not use this, because you can easily make typos and intellisense cannot detect it)
    await controller.send_command("?protocol")
    # Or we can send them by predefined command classes 
    # (This is the preferred way. Typos are detected by intellisense, because it is a class and not a string)
    await controller.send_command(cmds.GetProtocol())

    # For every command send an answer is returned
    # with raise_exception=True, it will raise an exception if the command fails or was invalid.
    answer_gain = await controller.send_command(cmds.GetGain(), raise_exception=False)
    
    answer = await controller.send_command(cmds.SetAtf(1, 100000)) # some commands take arguments as input
    
    print(answer.message) # the full message as string
    if answer.is_valid: # if the command could not be executed is_valid will be false
        # We can access the parsed contents of the answer by its field name. 
        print(answer[EFieldName.ATF])

    # # after you are finished you should disconnect the controller
    # await controller.disconnect()


    # === Executing Procedures === 

    # you should check if the procedure you want to run is enabled at all
    if not controller.is_procedure_enabled(ProcedureType.RAMP):
        raise NotImplementedError("ramp is not enabled on this device")

    # for using procedures the updater has to be active. 
    # Because for checking if they still are running, the remote controller needs to fetch constantly updates
    controller.start_updater()
    
    # we define the arguments for the procedure here
    # procedures are defined in src/soniccontrol/procedures/procs. Look up their definitions 
    proc_args = RamperArgs(
        # procedures use si vars as arguments
        f_start = AbsoluteFrequencySIVar(1500, SIPrefix.KILO),
         
        # but you can also provide a simple number and it will convert it automatically to an si var (in this case to Hz). 
        f_stop = 2_000_000, 
        # However it is better to use Si vars directly. Different arguments may use different si vars with different units. KILO vs MEGA for example. Better be explicit to avoid bugs.

        # if the other arguments are not specified then their default values are used.
    )

    # we start the procedure. It will run in the background
    controller.start_procedure(ProcedureType.RAMP, proc_args)

    # we wait until the procedure is finished
    await controller.wait_for_procedure_to_finish()

    # start the procedure again
    controller.start_procedure(ProcedureType.RAMP, proc_args)

    # wait 2 seconds
    await asyncio.sleep(2)

    # we can stop the procedure directly too
    await controller.stop_procedure() 

    await controller.stop_updater()


    # === Executing Scripts === 

    # for executing scripts this method can be used
    await controller.execute_script("""
        # A loop executes a block of commands n times

        frequency 2000000
        gain 70

        loop 5 times
        begin
            on
            hold 5s
            off
            hold 2s
        end
    """)
    # however scripts are more intended for users without programming experience.
    # If you use soniccontrol via python directly, then you will not need it.


    # === Doing Experiments === 

    # the remote controller only supports at the moment doing experiments for spectrum measure.
    # However the Experiments classes can also be directly used for recording data (but it needs more setup).
   
    # in the output dir the final recorded experiment is placed as hdf5 file
    output_dir = Path("~/Documents/").expanduser().resolve()
    spectrum_measure_args = SpectrumMeasureArgs(
        # todo... fill in args
    )
    # those fields have to be filled out.
    # Meta data should describe the experiment setup and give context. Without it the recorded data per se cannot be reason about.
    meta_data = ExperimentMetaData(
        experiment_name = "test",
        authors = ["DW"],
        transducer_id = "TRANS007",
        add_on_id = "bo",
        connector_type = "bo",
        medium = "water"
    )
    await controller.measure_spectrum(output_dir, spectrum_measure_args, meta_data)


    # If we want to create an experiment on our own for procedures or other stuff, we need to add first all necessary information
    experiment = Experiment(
        meta_data, controller.device_info,
        SOFTWARE_VERSION, PLATFORM.value, 
        CaptureTargets.FREE
    )

    # experiments can be recorded manually or via capture


    # === Recording an experiment manually ===

    # For recording experiments manually, the HDF5ExperimentWriter has to be used. Via it meta data and data points can be written to the final output file
    writer = HDF5ExperimentWriter(
        output_dir / "test_experiment", # file where to write at
        DataTableWorker    # format of the data table. (Descale and worker devices have different columns) 
    )
    writer.write_metadata(experiment)

    # to add a datapoint to the experiment the device status has to be fetched via an update command and then be added explicitly

    answer = await controller.get_update() # use the get_update() method directly instead of commands.GetUpdate(), because there are different update commands for different devices and the method automatically chooses the right one.

    # timestamp needs to be added
    answer[EFieldName.TIMESTAMP] = pd.to_datetime(datetime.datetime.now(), format="%Y-%m-%d %H:%M:%S")
    row  = { field_name.name: value for field_name, value in answer.field_value_dict.items() }
    writer.add_row(row)

    # do not forget to close the writer afterwards
    writer.close()


    # === Recording an experiment via capture ===

    # instead of fetching updates manually and adding them as datapoints,
    # we can instead also make use of the Updater together with the Capture class

    capture = Capture(output_dir)

    # the capture class needs to subscribe the updaters update event in order to receive status updates
    controller._updater.subscribe(Updater.UPDATE_EVENT, lambda e: capture.on_update(e.data["status"]))

    # updater is needed for fetching updates in the background
    controller.start_updater()

    # besides capture free there exist also other capture target, used by soniccontrol gui to sync data capturing with procedure and script execution. 
    # However for manually recording experiments they are not feasible
    await capture.start_capture(experiment, CaptureFree())

    # do some stuff
    await controller.send_command(cmds.SetOn())
    for i in range(5):
        await controller.send_command(cmds.SetFrequency(10_000 * i + 1_000_000))
        await asyncio.sleep(1) # wait 1s
    await controller.send_command(cmds.SetOff())

    await capture.end_capture() # stop capture

    await controller.stop_updater()


    # We disconnect the controller
    await controller.disconnect()


if __name__ == "__main__":
    # The asyncio framework executes our async main function in a loop.
    asyncio.run(main())