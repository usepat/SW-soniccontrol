import attrs
import click

from sonic_protocol.field_names import EFieldName
from soniccontrol.procedures.procs.spectrum_measure import SpectrumMeasureArgs
from soniccontrol.remote_controller import RemoteController
from soniccontrol_cli.monitor import Monitor
from soniccontrol_cli.procedures import add_procedure_commands, create_click_option
from soniccontrol_gui.constants import files
import pathlib
import asyncio
from enum import Enum
import logging
import io


class ConnectionType(Enum):
    PROCESS = "process"
    SERIAL = "serial"

REMOTE_CONTROLLER = "REMOTE_CONTROLLER"
ASYNC_LOOP = "ASYNC_LOOP"

@click.group()
@click.option("--log-dir", type=click.Path(path_type=pathlib.Path, file_okay=False), default=files.LOG_DIR)
@click.argument("port", type=click.Path(path_type=pathlib.Path, dir_okay=False))
@click.option("--connection", type=click.Choice([ConnectionType.PROCESS.value, ConnectionType.SERIAL.value]), default=ConnectionType.SERIAL.value)
@click.option("--baudrate", type=click.Choice(["9600", "112500"]), default="112500")
@click.pass_context
def cli(ctx: click.Context, log_dir: pathlib.Path, port: pathlib.Path, connection: str, baudrate: str):        
    logging.getLogger().handlers.clear()

    click.echo("Connecting to the device...")

    remote_controller = RemoteController(log_path=log_dir)
    async_loop = asyncio.get_event_loop()

    match ConnectionType(connection):
        case ConnectionType.PROCESS:
            async_loop.run_until_complete(remote_controller.connect_via_process(port))
        case ConnectionType.SERIAL:
            async_loop.run_until_complete(remote_controller.connect_via_serial(port, int(baudrate)))

    click.echo("Connected to device")

    ctx.ensure_object(dict)
    ctx.obj[REMOTE_CONTROLLER] = remote_controller
    ctx.obj[ASYNC_LOOP] = async_loop
    
@cli.result_callback()
@click.pass_context
def disconnect(ctx: click.Context, *args, **kwargs):
    remote_controller: RemoteController = ctx.obj[REMOTE_CONTROLLER]
    async_loop: asyncio.AbstractEventLoop = ctx.obj[ASYNC_LOOP]
    if remote_controller.is_connected():
        click.echo("Disconnecting from the device...")
        async_loop.run_until_complete(remote_controller.disconnect())
        click.echo("Disconnected from device")

@cli.command()
@click.pass_context
def monitor(ctx: click.Context):
    remote_controller: RemoteController = ctx.obj[REMOTE_CONTROLLER]
    async_loop: asyncio.AbstractEventLoop = ctx.obj[ASYNC_LOOP]
    async_loop.run_until_complete(remote_controller.stop_updater())
    monitor = Monitor(remote_controller, async_loop)
    monitor.cmdloop()

@cli.group()
@click.pass_context
def procedure(ctx: click.Context):
    pass

@procedure.result_callback()
@click.pass_context
def procedure_result_callback(ctx: click.Context, *args, **kwargs):
    remote_controller: RemoteController = ctx.obj[REMOTE_CONTROLLER]
    async_loop: asyncio.AbstractEventLoop = ctx.obj[ASYNC_LOOP]
    
    # TODO: print updates until proc finished
    click.echo("Procedure is being executed")

    assert (remote_controller._proc_controller)
    async_loop.run_until_complete(remote_controller._proc_controller.wait_for_proc_to_finish())
    click.echo("Procedure finished")

add_procedure_commands(procedure)

@cli.command()
@click.argument("script-file", type=click.File("r"))
@click.pass_context
def script(ctx: click.Context, script_file: io.IOBase):
    remote_controller: RemoteController = ctx.obj[REMOTE_CONTROLLER]
    async_loop: asyncio.AbstractEventLoop = ctx.obj[ASYNC_LOOP]
    
    script_text = script_file.read()
    async_loop.run_until_complete(remote_controller.execute_script(script_text, 
        callback=lambda task_desc: click.echo(task_desc)
    ))


@cli.command(
    params=[
        create_click_option(arg_name, arg_type)
        for arg_name, arg_type in attrs.fields_dict(SpectrumMeasureArgs).items()
    ]
)
@click.option("--out-dir", type=click.Path(path_type=pathlib.Path, file_okay=False), default=files.LOG_DIR)
@click.option("--fields", type=str, default="", help="Comma separated list of fields to include")
@click.pass_context
def spectrum(ctx: click.Context, *args, **kwargs):
    remote_controller: RemoteController = ctx.obj[REMOTE_CONTROLLER]
    async_loop: asyncio.AbstractEventLoop = ctx.obj[ASYNC_LOOP]

    out_dir: pathlib.Path = kwargs.pop("out_dir") # type: ignore
    fields: str = kwargs.pop("fields") # type: ignore
    spectrum_args = SpectrumMeasureArgs(**kwargs)

    if len(fields) > 0:
        data_fields = [ EFieldName(field) for field in fields.split(",") ]
    else:
        data_fields = []

    click.echo("Measuring spectrum")
    async_loop.run_until_complete(
        remote_controller.measure_spectrum(out_dir, spectrum_args, data_fields=data_fields)
    )


if __name__ == "__main__":
    cli()