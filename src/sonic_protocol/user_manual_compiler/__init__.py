import argparse
from enum import Enum
from pathlib import Path
from sonic_protocol.schema import DeviceType, Version
from sonic_protocol.user_manual_compiler.jinja_manual_compiler import HtmlManualCompiler
from sonic_protocol.user_manual_compiler.manual_compiler import MarkdownManualCompiler


class FileType(Enum):
    HTML = "html"
    MARKDOWN = "md"


def build_manual():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("./"))
    parser.add_argument("--protocol-version", type=str,required=True)
    parser.add_argument("--device-type", type=DeviceType, required=True)
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--file-type", type=FileType, default=FileType.HTML)
    args = parser.parse_args()

    device_type: DeviceType = args.device_type
    protocol_version: Version = Version.to_version(args.protocol_version)
    is_release: bool = args.release
    output_dir: Path = args.output_dir
    file_type: FileType = args.file_type

    version_str = args.protocol_version.replace('.', '_')
    build_str = "release" if is_release else "debug"
    file_name = output_dir / f"manual_{device_type.value}_{version_str}_{build_str}.{file_type.value}"
    
    if not output_dir.is_dir(): 
        raise Exception(f"The output-dir must be a directory, but is instead a file: {str(output_dir)}")


    manual_compiler = HtmlManualCompiler() if file_type == FileType.HTML else MarkdownManualCompiler()
    manual = manual_compiler.compile_manual_for_specific_device(device_type, protocol_version, is_release)

    with open(file_name, "w") as file:
        file.write(manual)
