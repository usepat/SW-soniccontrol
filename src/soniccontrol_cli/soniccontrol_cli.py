import click

from soniccontrol.remote_controller import RemoteController
from soniccontrol_gui.constants import files
import pathlib
import asyncio
from enum import Enum
import logging


class ConnectionType(Enum):
    PROCESS = "process"
    SERIAL = "serial"

async_loop = asyncio.get_event_loop()



@click.group()
@click.option("--log-dir", type=click.Path(path_type=pathlib.Path, file_okay=False), default=files.LOG_DIR)
@click.argument("port", type=click.Path(path_type=pathlib.Path, dir_okay=False))
@click.option("--connection", type=click.Choice([ConnectionType.PROCESS.value, ConnectionType.SERIAL.value]), default=ConnectionType.SERIAL.value)
@click.option("--baudrate", type=click.Choice(["9600", "112500"]), default="112500")
@click.pass_context
def cli(ctx: click.Context, log_dir: pathlib.Path, port: pathlib.Path, connection: str, baudrate: str):    
    logging.getLogger().handlers.clear()

    remote_controller = RemoteController(log_path=log_dir)

    match ConnectionType(connection):
        case ConnectionType.PROCESS:
            async_loop.run_until_complete(remote_controller.connect_via_process(port))
        case ConnectionType.SERIAL:
            async_loop.run_until_complete(remote_controller.connect_via_serial(port, int(baudrate)))

    ctx.ensure_object(RemoteController)
    ctx.obj = remote_controller
    
@cli.result_callback()
@click.pass_context
def disconnect(ctx: click.Context, *args, **kwargs):
    remote_controller: RemoteController = ctx.obj
    if remote_controller.is_connected():
        async_loop.run_until_complete(remote_controller.disconnect())

@cli.command()
@click.pass_context
def monitor(ctx: click.Context):
    remote_controller: RemoteController = ctx.obj

@cli.command()
@click.pass_context
def procedure(ctx: click.Context):
    remote_controller: RemoteController = ctx.obj

@cli.command()
@click.pass_context
def script(ctx: click.Context):
    remote_controller: RemoteController = ctx.obj

if __name__ == "__main__":
    cli()