import asyncio
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict
from flask import Flask, Response, request, abort, jsonify, Blueprint, current_app
from serial.tools.list_ports import comports as get_comports
import time
import threading
import attrs
import click
from functools import wraps
from werkzeug.exceptions import HTTPException

from soniccontrol.app_config import get_simulation_exe
from soniccontrol.communication.connection import CLIConnection, Connection, SerialConnection
from soniccontrol.network.plugin import register_server_plugins


@attrs.define()
class ConnectionObject:
    connection: Connection = attrs.field()
    reader: asyncio.StreamReader = attrs.field()
    writer: asyncio.StreamWriter = attrs.field()
    timestamp: float = attrs.field(factory=time.time)

CONNECTIONS_REGISTRY = "connections"
EVENT_LOOP = "event_loop"

ALREADY_ACTIVE_CONNECTION_ERROR_STR = "there is already an active connection for this port"

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


@server_bp.get("/scan_available_ports")
def scan_available_ports():
    ports = [port.device for port in get_comports()]
    return jsonify({ "ports": ports }), HTTP_OK

@server_bp.post("/is_port_free/<string:port>")
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
        baudrate = request.args.get("baudrate", 9600, type=int)
        port_path = Path("/dev") / port
        if not port_path.exists():
            abort(HTTP_SERVER_ERROR, description=f"The given port {port} is not registered in dev")
        
        connection = SerialConnection(port, port_path, baudrate)
    
    reader, writer = await connection.open_connection()
    connections[port] = ConnectionObject(connection, reader, writer)

    return http_ok()

@server_bp.post("/write/<string:port>")
@execute_in_event_loop
async def write(port: str):
    connections: Dict[str, ConnectionObject] = current_app.extensions[CONNECTIONS_REGISTRY]
    if port not in connections:
        abort(HTTP_CLIENT_ERROR, description="there is no active connection for this port")

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
        abort(HTTP_CLIENT_ERROR, description="there is no active connection for this port")

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
        abort(HTTP_CLIENT_ERROR, description="there is no active connection for this port")

    await connections[port].connection.close_connection()
    del connections[port]

    return http_ok()


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

    app = Flask(__name__)
    app.extensions[CONNECTIONS_REGISTRY] = connection_registry
    app.extensions[EVENT_LOOP] = loop
    app.register_blueprint(server_bp)
    register_server_plugins(app)

    app.run(host, port)


if __name__ == "__main__":
    start_server()
