import numpy as np

from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, FieldType, SonicTextCommandAttrs, UserManualAttrs


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

