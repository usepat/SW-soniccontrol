from typing import List
from sonic_protocol.schema import (
    FieldType, SonicTextCommandAttrs, UserManualAttrs, CommandDef, AnswerDef,
    AnswerFieldDef, CommandContract
)
from sonic_protocol.field_names import EFieldName
from sonic_protocol.command_codes import CommandCode

field_success = AnswerFieldDef(
    field_name=EFieldName.SUCCESS,
    field_type=FieldType(str)
)

flash_usb = CommandContract(
    code=CommandCode.SET_FLASH_USB,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!FLASH_USB"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_success]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Used for flashing the device with a new firmware."
    ),
    is_release=True,
    tags=["flashing"]
)

flash_uart9600 = CommandContract(
    code=CommandCode.SET_FLASH_9600,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!FLASH_UART_SLOW"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_success]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Used for flashing the device with a new firmware."
    ),
    is_release=True,
    tags=["flashing"]
)

flash_uart115200 = CommandContract(
    code=CommandCode.SET_FLASH_115200,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!FLASH_UART_FAST"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_success]
    ),
    user_manual_attrs=UserManualAttrs(
        description="Used for flashing the device with a new firmware."
    ),
    is_release=True,
    tags=["flashing"]
)


saveSettings = CommandContract(
    code=CommandCode.SET_SETTINGS,
    command_def=CommandDef(
        sonic_text_attrs=SonicTextCommandAttrs(
            string_identifier=["!saveSettings", "!commission"]
        )
    ),
    answer_def=AnswerDef(
        fields=[field_success]
    ),
    is_release=True,
    tags=["Settings", "Commissioning"]
)

flashing_command_contracts: List[CommandContract] = [
    flash_usb, 
    flash_uart9600, 
    flash_uart115200,
    saveSettings
]