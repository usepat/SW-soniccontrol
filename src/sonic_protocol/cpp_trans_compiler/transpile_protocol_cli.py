import argparse
from pathlib import Path
from sonic_protocol.defs import Version, DeviceType, ProtocolType
from sonic_protocol.cpp_trans_compiler.cpp_trans_compiler import CppTransCompiler
from sonic_protocol.protocol_list import ProtocolList
from typing import List

def transpile_protocol_cli(protocol_list: ProtocolList, protocol_name: str, options: List[str] = []):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_lib_path", type=Path, required=True)
    parser.add_argument("--protocol_version", type=str, required=True)
    parser.add_argument("--device_type", type=str, required=True)
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()

    print("Generating protocol with args:")
    print(f"device_type={args.device_type}")
    print(f"protocol_version={args.protocol_version}")
    print(f"release={args.release}")

    protocol_version = Version.to_version(args.protocol_version)
    device_type = DeviceType(args.device_type)
    release = args.release
   
    compiler = CppTransCompiler()
    compiler.generate_sonic_protocol_lib(
        protocol_list=protocol_list,
        protocol_info=ProtocolType(protocol_version, device_type, release),
        output_dir=args.out_lib_path,
        options=options,
        protocol_name=protocol_name
    )
    print("Generated protocol library at ", args.out_lib_path)
