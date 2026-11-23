import importlib.resources as rs
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import click
import jinja2

import soniccontrol

@click.command
@click.option("--port", type=click.INT, default=8080)
def enable_server_on_startup(port: int):
    """
        Helper script to create on linux a systemd unit file 
        and register the server as a service that gets executed
        after start up.

        Requests sudo for installation and systemctl, but runs the service
        as the invoking non-root user.
    """
    import grp
    import pwd

    uid = os.getuid()
    if uid == 0:
        try:
            uid = int(os.environ["SUDO_UID"])
        except (KeyError, ValueError) as exc:
            raise click.ClickException("Run this command as a non-root user.") from exc
    if uid <= 0:
        raise click.ClickException("The service must run as a non-root user.")
    try:
        account = pwd.getpwuid(uid)
        group = grp.getgrgid(account.pw_gid).gr_name
    except KeyError as exc:
        raise click.ClickException(f"Cannot resolve the service account for UID {uid}.") from exc
    python_venv = Path(sys.prefix)

    template_file = rs.files(soniccontrol) / "network/enable_server_on_startup/sonic_control_server.service.j2"
    template_content = template_file.read_text()
    template = jinja2.Template(template_content)
    content = template.render(
        user=account.pw_name,
        group=group,
        python_venv=python_venv,
        port=port
    )

    service_name = "sonic_control_server"    
    unit_file_path = Path("/etc/systemd/system") / f"{service_name}.service"
    privilege_prefix = ["sudo"] if os.geteuid() != 0 else []
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            subprocess.run(
                [*privilege_prefix, "install", "-o", "root", "-g", "root",
                 "-m", "644", f.name, str(unit_file_path)],
                check=True,
            )
        subprocess.run([*privilege_prefix, "systemctl", "daemon-reload"], check=True)
        subprocess.run([*privilege_prefix, "systemctl", "enable", service_name], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise click.ClickException(f"Failed to enable the server on startup: {exc}") from exc


if __name__ == "__main__":
    enable_server_on_startup()
