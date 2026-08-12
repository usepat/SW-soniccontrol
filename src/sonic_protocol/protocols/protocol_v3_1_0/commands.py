import numpy as np

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.groups import GROUPS
from sonic_protocol.schema import AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, FieldType, SonicTextCommandAttrs, Timestamp, UserManualAttrs

from enum import Enum


class FileType(Enum):
    BINARY = 0
    TEXT_UTF8 = 1


debug_test_command = CommandContract(
    CommandCode.DEBUG_TEST,
    CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs("!debug_test"),
        index_param=CommandParamDef(
            EFieldName.INDEX, 
            FieldType(np.uint8, min_value=np.uint8(0), max_value=np.uint8(255)), 
            user_manual_attrs=UserManualAttrs("Which debug test to execute")
        )
    ),
    AnswerDef(
        [ AnswerFieldDef(EFieldName.MESSAGE, str) ]
    ),
    user_manual_attrs=UserManualAttrs("This command is for testing internal behavior of the device. Its implementation can change during development."),
    is_release=False,
    is_admin_command=False,
) 

get_num_files = CommandContract(
    code=CommandCode.GET_NUM_FILES,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?num_files")
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.COUNT, field_type=FieldType(field_type=np.uint8))
    ]),
    user_manual_attrs=UserManualAttrs(
        description="Retrieves the number of available files"
    ),
    is_release=True,
    is_admin_command=True,
    group_id=GROUPS.misc,
    tags=["file"]
)


file_index_param = CommandParamDef(EFieldName.FILE_INDEX, param_type=FieldType(field_type=np.uint16))

get_file_info = CommandContract(
    code=CommandCode.GET_FILE_INFO,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?file_info"),
        index_param=file_index_param
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.FILE_NAME, str),
        AnswerFieldDef(EFieldName.FILE_TYPE, FileType),
        AnswerFieldDef(EFieldName.TIMESTAMP, Timestamp),
        AnswerFieldDef(EFieldName.SIZE, np.uint32),
    ]),
    user_manual_attrs=UserManualAttrs(
        description="get information about a file"
    ),
    is_release=True,
    is_admin_command=True,
    group_id=GROUPS.misc,
    tags=["file"]
)

get_file_data = CommandContract(
    code=CommandCode.GET_FILE_DATA,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(string_identifier="?file_data"),
        index_param=file_index_param,
        setter_param=CommandParamDef(EFieldName.INDEX, param_type=np.uint32, user_manual_attrs=UserManualAttrs("offset where to read from the file")),
    ),
    answer_def=AnswerDef([
        AnswerFieldDef(EFieldName.DATA, bytes),
    ]),
    user_manual_attrs=UserManualAttrs(
        description="fetch the data of a file at a given offset"
    ),
    is_release=True,
    is_admin_command=True,
    group_id=GROUPS.misc,
    tags=["file"]
)
