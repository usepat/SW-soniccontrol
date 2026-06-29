

import numpy as np
from sonic_protocol.command_codes import CommandCode
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import AnswerDef, AnswerFieldDef, CommandContract, CommandDef, CommandParamDef, FieldType, SonicTextCommandAttrs, UserManualAttrs


broadcast_modbus_server_id = CommandContract(
    code=CommandCode.BROADCAST_MODBUS_SERVER_ID,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!broadcast_server_id"]
        ),
        index_param=CommandParamDef(
            EFieldName.SNR,
            param_type=FieldType(str)
        ),
        setter_param=CommandParamDef(
            EFieldName.MODBUS_SERVER_ID,
            FieldType(
                np.uint8,
                min_value=np.uint8(1), # address 0 is for broadcasting
                max_value=np.uint8(247) # addresses from 248 to 255 are reserved
            )
        )
    ),
    answer_def=AnswerDef(
        fields=[
            AnswerFieldDef(
                EFieldName.SUCCESS,
                str
            )
        ]
    ),
    user_manual_attrs=UserManualAttrs(
        description="This command supports broadcast. If a device matches the provided serial number, it sets its MODBUS server ID."
    ),
    is_release=True,
    tags=["MODBUS"]
)