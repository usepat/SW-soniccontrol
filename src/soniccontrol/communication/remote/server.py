import asyncio
from pathlib import Path
from typing import Dict
from flask import Flask, Response, request, abort, jsonify
from serial.tools.list_ports import comports as get_comports
import time
import threading
import attrs
from werkzeug.exceptions import HTTPException

from soniccontrol.app_config import get_simulation_exe
from soniccontrol.communication.connection import CLIConnection, Connection, SerialConnection


@attrs.define()
class ConnectionObject:
    connection: Connection = attrs.field()
    reader: asyncio.StreamReader = attrs.field()
    writer: asyncio.StreamWriter = attrs.field()
    timestamp: float = attrs.field(factory=time.time)

connections: Dict[str, ConnectionObject] = {} 

def cleanup_task():
    # expiration in seconds
    EXPIRATION = 300  # 5 minutes
    while True:
        now = time.time()
        expired = [
            obj_id for obj_id, obj in connections.items() 
            if now - obj.timestamp > EXPIRATION
        ]
        for obj_id in expired:
            del connections[obj_id]
            app.logger.warning(f"Deleted expired object {obj_id}")
        time.sleep(60)  # run every minute

# start cleanup thread
threading.Thread(target=cleanup_task, daemon=True).start()


app = Flask(__name__)
HTTP_OK = 200
HTTP_CLIENT_ERROR = 400
HTTP_SERVER_ERROR = 500


def http_ok():
    return jsonify({"status": "ok"}), HTTP_OK

@app.errorhandler(Exception)
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


@app.get("/scan_available_ports")
def scan_available_ports():
    ports = [port.device for port in get_comports()]
    return jsonify({ "ports": ports }), HTTP_OK

@app.post("/connect/<string:port>")
async def connect(port: str):
    if port in connections:
        abort(HTTP_CLIENT_ERROR, description="there is already an active connection for this port")

    if port == "simulation":
        simulation_exe_path = get_simulation_exe()
        if simulation_exe_path is None:
            abort(HTTP_SERVER_ERROR, description="No simulation_exe_path defined in the server environment")

        cmd_args = request.args.get("cmd_args", "", type=str).split(" ")
        connection = CLIConnection("simulation", simulation_exe_path, cmd_args)

    else:
        baudrate = request.args.get("baudrate", 9600, type=int)
        connection = SerialConnection(Path(port).name, port, baudrate)
    
    reader, writer = await connection.open_connection()
    connections[port] = ConnectionObject(connection, reader, writer)

    return http_ok()

@app.post("/write/<string:port>")
async def write(port: str):
    if port not in connections:
        abort(HTTP_CLIENT_ERROR, description="there is no active connection for this port")

    if request.content_type != "application/octet-stream":
        abort(HTTP_CLIENT_ERROR, description="Invalid content type")

    data = request.data
    writer = connections[port].writer

    writer.write(data)
    await writer.drain()

    return http_ok()

@app.get("/read/<string:port>")
async def read(port: str):
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

@app.post("/disconnect/<string:port>")
async def disconnect(port: str):
    if port not in connections:
        abort(HTTP_CLIENT_ERROR, description="there is no active connection for this port")

    await connections[port].connection.close_connection()
    del connections[port]

    return http_ok()


