from sonic_protocol.defs import AnswerDef, AnswerFieldDef, CommandCode, CommandContract, CommandDef, CommandExport, CommandListExport, DeviceParamConstants, DeviceType, MetaExport, MetaExportDescriptor, Protocol, SonicTextCommandAttrs, Version
import pytest

from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocol_builder import ProtocolBuilder


cdef_get_frequency = CommandDef(SonicTextCommandAttrs(string_identifier="?f"))
cdef_set_frequency_new = CommandDef(SonicTextCommandAttrs(string_identifier=["!f", "!freq", "!frequency"]))
cdef_set_frequency_old = CommandDef(SonicTextCommandAttrs(string_identifier="!f"))
cdef_set_swf = CommandDef(SonicTextCommandAttrs(string_identifier="!swf"))
adef_frequency = AnswerDef(
    fields=[AnswerFieldDef(EFieldName.FREQUENCY, int)]
)
adef_swf = AnswerDef(
    fields=[AnswerFieldDef(EFieldName.SWF, int)]
)
    

v_new = Version(1, 0, 0)
v_mid = Version(0, 7, 0)
v_old = Version(0, 0, 0)

get_frequency_command = CommandContract(
    code=CommandCode.GET_FREQ,
    command_defs=cdef_get_frequency,
    answer_defs=adef_frequency,
    is_release=True
)

set_frequency_command = CommandContract(
    code=CommandCode.SET_FREQ,
    command_defs=[
        MetaExport(
            exports=cdef_set_frequency_new,
            descriptor=MetaExportDescriptor(
                v_new
            )
        ),
        MetaExport(
            exports=cdef_set_frequency_old,
            descriptor=MetaExportDescriptor(
                min_protocol_version=v_old,
                deprecated_protocol_version=v_mid
            )
        ),
    ],
    answer_defs=adef_frequency,
    is_release=True
)

set_switching_frequency_command = CommandContract(
    code=CommandCode.SET_SWF,
    command_defs=cdef_set_swf,
    answer_defs=adef_swf,
    is_release=False
)


# Protocol instance
protocol = Protocol(
    version=Version(1, 0, 0),
    consts=DeviceParamConstants(),
    commands=[
        CommandListExport(
            exports=[
                get_frequency_command,
                set_frequency_command,
            ],
            descriptor = MetaExportDescriptor(
                min_protocol_version=v_old,
                excluded_device_types=[DeviceType.DESCALE]
            )
        ),
        CommandExport(
            exports=set_switching_frequency_command,
            descriptor = MetaExportDescriptor(
                min_protocol_version=v_new,
                included_device_types=[DeviceType.DESCALE]
            )
        )
    ]
)

@pytest.mark.parametrize("version, release, device_type, expected_command_code, expected_command_def", [
    (v_new, False, DeviceType.MVP_WORKER, CommandCode.SET_FREQ, cdef_set_frequency_new),
    (v_old, False, DeviceType.MVP_WORKER, CommandCode.SET_FREQ, cdef_set_frequency_old),
    (v_new, False, DeviceType.MVP_WORKER, CommandCode.GET_FREQ, cdef_get_frequency),
    (v_old, False, DeviceType.MVP_WORKER, CommandCode.GET_FREQ, cdef_get_frequency),
    (v_new, False, DeviceType.MVP_WORKER, CommandCode.SET_SWF, None),
    (v_new, False, DeviceType.DESCALE, CommandCode.SET_SWF, cdef_set_swf),
    (v_new, False, DeviceType.DESCALE, CommandCode.SET_FREQ, None),
    (v_new, True,  DeviceType.DESCALE, CommandCode.SET_SWF, None),
    (v_old, False, DeviceType.DESCALE, CommandCode.SET_SWF, None),
])
def test_build_protocol_chooses_the_right_definitions(device_type, version, release, expected_command_code, expected_command_def):
    protocol_builder = ProtocolBuilder(protocol)

    lookup_table = protocol_builder.build(device_type, version, release)

    command_lookup = lookup_table.get(expected_command_code)
    if expected_command_def is None:
        assert command_lookup is None  
    else:
        assert command_lookup is not None
        assert command_lookup.command_def == expected_command_def


# TODO: add test that check that an error is thrown. If a command is defined,
#  where it is possible with a specific version and device type to have no valid command def or answer def

def test_build_protocol_throws_error_if_no_def_for_version_of_exported_command():
    protocol_builder = ProtocolBuilder(protocol)

    with pytest.raises(LookupError):
        protocol_builder.build(DeviceType.MVP_WORKER, v_mid, True)
