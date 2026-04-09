from pathlib import Path
import click
import subprocess
import jinja2
import importlib.resources as rs
import soniccontrol
import os
import sys

@click.command
@click.option("--port", type=click.INT, default=8080)
def enable_server_on_startup(port: int):
    """
        Helper script to create on linux a systemd unit file 
        and register the server as a service that gets executed
        after start up.

        You have to run this script with sudo.
    """
    import pwd

    uid = os.getuid()
    user = pwd.getpwuid(uid).pw_name
    python_venv = Path(sys.prefix)

    template_file = rs.files(soniccontrol) / "network/enable_server_on_startup/sonic_control_server.service.j2"
    template_content = template_file.read_text()
    template = jinja2.Template(template_content)
    content = template.render(
        user=user,
        python_venv=python_venv,
        port=port
    )

    service_name = "sonic_control_server"    
    unit_file_path = Path("/etc/systemd/system") / f"{service_name}.service"
    with open(unit_file_path, "w") as f:
        f.write(content)

    os.chmod(unit_file_path, 0o644) # writable only by root, readable by all

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", service_name], check=True)


if __name__ == "__main__":
    enable_server_on_startup()
