#!/usr/bin/env python3

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path


def format_command(args: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(args)

    return shlex.join(args)


def require_file(path: Path, description: str) -> None:
    if not path.is_file():
        print(f"{description} not found at {path}", file=sys.stderr)
        raise SystemExit(1)


def require_dir(path: Path, description: str) -> None:
    if not path.is_dir():
        print(f"{description} not found at {path}", file=sys.stderr)
        raise SystemExit(1)


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    workspace_dir = script_dir.parent

    main_script = Path(
        os.environ.get(
            "MAIN_SCRIPT",
            str(workspace_dir / "src" / "soniccontrol_gui" / "build_main.py"),
        )
    )
    sonic_script_examples = Path(
        os.environ.get(
            "SONIC_SCRIPT_EXAMPLES",
            str(workspace_dir / "sonic_script_examples"),
        )
    )
    dist_dir = Path(os.environ.get("DIST_DIR", str(workspace_dir / "build" / "dist")))
    work_dir = Path(os.environ.get("WORK_DIR", str(workspace_dir / "build" / "temp")))
    spec_dir = Path(os.environ.get("SPEC_DIR", str(workspace_dir / "build" / "spec")))
    icon_file = os.environ.get("ICON_FILE", "")
    version_file = os.environ.get("VERSION_FILE", "")

    dry_run = False
    extra_args: list[str] = []

    for arg in sys.argv[1:]:
        if arg == "--dry-run":
            dry_run = True
            continue

        extra_args.append(arg)

    require_file(main_script, "SonicControl entrypoint")
    require_dir(sonic_script_examples, "sonic_script_examples")

    if icon_file:
        require_file(Path(icon_file), "Icon file")

    if version_file:
        require_file(Path(version_file), "Version file")

    dist_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)

    data_separator = ";" if os.name == "nt" else ":"
    pyinstaller_args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "SonicControl",
        "--collect-all",
        "soniccontrol_gui",
        "--collect-all",
        "soniccontrol",
        "--collect-all",
        "sonic_protocol",
        "--collect-all",
        "tkinter",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=PIL._imagingtk",
        "--collect-all",
        "PIL",
        *extra_args,
        "--add-data",
        f"{sonic_script_examples}{data_separator}sonic_script_examples",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
    ]

    if icon_file:
        pyinstaller_args.extend(["--icon", icon_file])

    if version_file:
        pyinstaller_args.extend(["--version-file", version_file])

    pyinstaller_args.append(str(main_script))

    print("bundle application with pyinstaller")
    print("PyInstaller will be called with the following arguments:")
    print(format_command(pyinstaller_args))

    if dry_run:
        return 0

    return subprocess.run(pyinstaller_args, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())