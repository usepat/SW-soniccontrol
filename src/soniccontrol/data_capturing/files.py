from datetime import datetime
from typing import List, Tuple

from sonic_protocol.field_names import EFieldName
from soniccontrol.sonic_device import SonicDevice
import sonic_protocol.python_parser.commands as cmds
from sonic_protocol.protocols.protocol_v3_1_0.protocol_v3_1_0 import FileType
import attrs


@attrs.define()
class FileDescription:
    file_index: int
    name: str
    file_type: FileType
    time_stamp: datetime
    file_size: int


def get_file_extension_for_file_type(file_type: FileType) -> str:
    match file_type:
        case FileType.BINARY:
            return "bin"
        case FileType.TEXT_UTF8:
            return "txt"
        case _:
            raise NotImplementedError()


async def discover_files(device: SonicDevice) -> List[FileDescription]:
    answer = await device.execute_command(cmds.GetNumFiles())
    num_files: int = answer.field_value_dict[EFieldName.COUNT]

    file_descriptions: List[FileDescription] = []
    for i in range(num_files):
        answer = await device.execute_command(cmds.GetFileInfo(i))
        file_descriptions.append(
            FileDescription(
                i,
                answer.field_value_dict[EFieldName.FILE_NAME],
                answer.field_value_dict[EFieldName.FILE_TYPE],
                answer.field_value_dict[EFieldName.TIMESTAMP],
                answer.field_value_dict[EFieldName.SIZE],
            )
        )

    return file_descriptions


async def load_file(device: SonicDevice, file_index: int) -> Tuple[FileDescription, bytes]:
    answer = await device.execute_command(cmds.GetFileInfo(file_index))
    file_description = FileDescription(
        file_index,
        answer.field_value_dict[EFieldName.FILE_NAME],
        answer.field_value_dict[EFieldName.FILE_TYPE],
        answer.field_value_dict[EFieldName.TIMESTAMP],
        answer.field_value_dict[EFieldName.SIZE]
    )

    data = bytearray()
    while len(data) < file_description.file_size:
        answer = await device.execute_command(cmds.GetFileData(file_index, len(data)))
        data.append(answer.field_value_dict[EFieldName.DATA])

    return file_description, bytes(data)
