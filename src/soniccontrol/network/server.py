import asyncio
import concurrent.futures
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List
import sys
import cattrs
from flask import Flask, Response, request, abort, jsonify, Blueprint, current_app
import time
import threading
import attrs
import click
import uuid
from functools import wraps
from werkzeug.exceptions import HTTPException

from soniccontrol.app_config import get_simulation_exe
from soniccontrol.communication.connection import CLIConnection, Connection, SerialConnection
from soniccontrol.fw_device.fw_device_info import FwDeviceInfo
from soniccontrol.fw_device import create_device_discovery
from soniccontrol.network.plugin import register_server_plugins

if sys.platform.startswith("linux"):
    import pyudev
else:
    pyudev = None


def get_tty_device_from_name(name: str) -> Any | None:
    if pyudev is None:
        return None

    context = pyudev.Context()
    device: Any | None = None
    for subsystem in ["tty", "usb"]:
        try: 
            device = pyudev.Devices.from_name(context, subsystem, name)
        except pyudev.DeviceNotFoundByNameError:
            pass
        else:
            break
    
    if device is None:
        return None

    if device.subsystem == "usb":
        for tty_dev in context.list_devices(subsystem="tty"):
            parent_dev = tty_dev.find_parent(subsystem="usb", device_type="usb_device")
            if parent_dev and parent_dev.sys_name == device.sys_name:
                return tty_dev
        return None

    return device


@attrs.define()
class ConnectionObject:
    connection: Connection = attrs.field()
    reader: asyncio.StreamReader = attrs.field()
    writer: asyncio.StreamWriter = attrs.field()
    timestamp: float = attrs.field(factory=time.time)

CONNECTIONS_REGISTRY = "connections"
FUTURE_REGISTRY = "futures"
EVENT_LOOP = "event_loop"

ALREADY_ACTIVE_CONNECTION_ERROR_STR = "there is already an active connection for this port"
NO_ACTIVE_CONNECTION_ERROR_STR = "there is no active connection for this port"

HTTP_OK = 200
HTTP_CLIENT_ERROR = 400
HTTP_SERVER_ERROR = 500

server_bp = Blueprint("remote_soniccontrol", __name__)

def execute_in_event_loop(func: Callable[..., Coroutine[Any, Any, Any]]):
    """
    decorator so we can use the same eventloop for all endpoints. 
    Note flask[async] creates eventloops for each request. 
    """
    @wraps(func) # provide original function meta data.
    def _execute(*args, **kwargs):
        loop: asyncio.AbstractEventLoop = current_app.extensions[EVENT_LOOP]
        coro = func(*args, **kwargs)
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    return _execute

def http_ok():
    return jsonify({"status": "ok"}), HTTP_OK

@server_bp.errorhandler(Exception)
def handle_exception(e) -> tuple[Response, int]:
    if isinstance(e, HTTPException):
        # e.code is Optional[int], default to 500
        code = e.code or HTTP_SERVER_ERROR
        return jsonify({"error": e.description}), code
    if isinstance(e, (ValueError, TypeError)):
        # handle input validation errors
        return jsonify({"error": str(e)}), HTTP_CLIENT_ERROR
    # fallback for non-HTTP exceptions
    return jsonify({"error": str(e)}), HTTP_SERVER_ERROR


def is_it_true(value):
  return value.lower() == 'true'

@server_bp.get("/devices")
@execute_in_event_loop
async def get_devices():
    # type is a callable that converts the param string to the value
    include_ttys = request.args.get("include_ttys", True, type=is_it_true) 
    include_disks = request.args.get("include_disks", True, type=is_it_true)
    include_unverified_ttys = request.args.get("include_unverified_ttys", False, type=is_it_true)
    device_infos: List[FwDeviceInfo] = await create_device_discovery().list_fw_device_infos(
        include_ttys,
        include_disks,
        include_unverified_ttys,
    )
    plain_data = cattrs.Converter().unstructure(device_infos)
    return jsonify(plain_data), HTTP_OK

@server_bp.get("/is_port_free/<string:port>")
def is_port_free(port: str):
    connections: Dict[str, ConnectionObject] = current_app.extensions[CONNECTIONS_REGISTRY]
    return jsonify({ "is_connected": port in connections }), HTTP_OK

@server_bp.post("/connect/<string:port>")
@execute_in_event_loop
async def connect(port: str):
    connections: Dict[str, ConnectionObject] = current_app.extensions[CONNECTIONS_REGISTRY]
    if port in connections:
        abort(HTTP_CLIENT_ERROR, description=ALREADY_ACTIVE_CONNECTION_ERROR_STR)

    if port == "simulation":
        simulation_exe_path = get_simulation_exe()
        if simulation_exe_path is None:
            abort(HTTP_SERVER_ERROR, description="No simulation_exe_path defined in the server environment")

        cmd_args = request.args.get("cmd_args", "", type=str).split(" ")
        connection = CLIConnection("simulation", simulation_exe_path, cmd_args)

    else:
        tty_device = get_tty_device_from_name(port)
        if tty_device is None:
            abort(HTTP_SERVER_ERROR, description=f"The given port {port} does not exist or is not a tty or usb device")
        
        assert tty_device.device_node, "the tty device has no registered device node"
        port_path = Path(tty_device.device_node)        
        baudrate = request.args.get("baudrate", 9600, type=int)
        connection = SerialConnection(port, port_path, baudrate)
    
    reader, writer = await connection.open_connection()
    connections[port] = ConnectionObject(connection, reader, writer)

    return http_ok()

@server_bp.post("/write/<string:port>")
@execute_in_event_loop
async def write(port: str):
    connections: Dict[str, ConnectionObject] = current_app.extensions[CONNECTIONS_REGISTRY]
    if port not in connections:
        abort(HTTP_CLIENT_ERROR, description=NO_ACTIVE_CONNECTION_ERROR_STR)

    if request.content_type != "application/octet-stream":
        abort(HTTP_CLIENT_ERROR, description="Invalid content type")

    data = request.data
    writer = connections[port].writer

    writer.write(data)
    await writer.drain()

    return http_ok()

@server_bp.get("/read/<string:port>")
@execute_in_event_loop
async def read(port: str):
    connections: Dict[str, ConnectionObject] = current_app.extensions[CONNECTIONS_REGISTRY]
    if port not in connections:
        abort(HTTP_CLIENT_ERROR, description=NO_ACTIVE_CONNECTION_ERROR_STR)

    reader = connections[port].reader

    max_bytes = 1024
    data = bytes([])
    try:
        data = await asyncio.wait_for(reader.read(max_bytes), 0.2)
    except TimeoutError:
        pass

    return Response(data, mimetype="application/octet-stream"), HTTP_OK

@server_bp.post("/disconnect/<string:port>")
@execute_in_event_loop
async def disconnect(port: str):
    connections: Dict[str, ConnectionObject] = current_app.extensions[CONNECTIONS_REGISTRY]
    if port not in connections:
        abort(HTTP_CLIENT_ERROR, description=NO_ACTIVE_CONNECTION_ERROR_STR)

    await connections[port].connection.close_connection()
    del connections[port]

    return http_ok()

@server_bp.get("/poll_future/<uuid:future_id>")
@execute_in_event_loop
async def poll_future(future_id: uuid.UUID):
    future_registry: Dict[uuid.UUID, concurrent.futures.Future[Any]] = current_app.extensions[FUTURE_REGISTRY]

    if future_id not in future_registry:
        abort(HTTP_CLIENT_ERROR, description="there exists no future with this id")

    future = future_registry[future_id]
    if future.done():
        del future_registry[future_id]

    result = None
    exception = None
    if future.done():
        if future.cancelled():
            exception = "Future was cancelled"
        elif future.exception():
            exception =str(future.exception())
        else:
            result = future.result()

    return jsonify({ "done": future.done(), "result": result, "exception": exception }), HTTP_OK


@server_bp.post("/wait_for_device_redetection")
def wait_for_device_redetection():
    if request.content_type != "application/json":
        abort(HTTP_CLIENT_ERROR, description="Invalid content type")

    data = request.get_json()
    dev_info = cattrs.Converter().structure(data, FwDeviceInfo)

    async def redetection_task(): 
        coro = create_device_discovery().wait_for_device_redetection(dev_info)
        dev_info_new = await asyncio.wait_for(coro, 3 * 60) # 3 minutes timeout
        return dev_info_new
    
    future_registry: Dict[uuid.UUID, concurrent.futures.Future[Any]] = current_app.extensions[FUTURE_REGISTRY]
    loop: asyncio.AbstractEventLoop = current_app.extensions[EVENT_LOOP]

    future_id = uuid.uuid4()
    future = asyncio.run_coroutine_threadsafe(redetection_task(), loop)
    future_registry[future_id] = future

    return jsonify({"future_id": str(future_id)}), HTTP_OK


@click.command()
@click.option("--host", default=None)
@click.option("--port", type=click.INT, default=None)
def start_server(host: str | None, port: int | None):
    loop = asyncio.new_event_loop()
    threading.Thread(target=lambda: loop.run_forever(), daemon=True).start()

    connection_registry: Dict[str, ConnectionObject] = {}
    
    # start cleanup thread
    async def cleanup_task():
        # expiration in seconds
        EXPIRATION = 300  # 5 minutes
        while True:
            now = time.time()
            expired = [
                obj_id for obj_id, obj in connection_registry.items() 
                if now - obj.timestamp > EXPIRATION
            ]
            for obj_id in expired:
                await connection_registry[obj_id].connection.close_connection()
                del connection_registry[obj_id]
            await asyncio.sleep(60)  # run every minute
    asyncio.run_coroutine_threadsafe(cleanup_task(), loop)

    future_registry: Dict[uuid.UUID, concurrent.futures.Future[Any]] = {}

    app = Flask(__name__)
    app.extensions[CONNECTIONS_REGISTRY] = connection_registry
    app.extensions[EVENT_LOOP] = loop
    app.extensions[FUTURE_REGISTRY] = future_registry
    app.register_blueprint(server_bp)
    register_server_plugins(app)

    app.run(host, port)


if __name__ == "__main__":
    start_server()
