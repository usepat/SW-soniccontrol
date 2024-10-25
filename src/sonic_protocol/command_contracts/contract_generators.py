
from typing import List
from sonic_protocol.defs import AnswerDef, AnswerFieldDef, ConverterType, FieldType, MetaExport, MetaExportDescriptor, Version, VersionTuple
from sonic_protocol.command_contracts.fields import field_unknown_answer
from sonic_protocol.field_names import EFieldName

def create_version_field(name: EFieldName) -> AnswerFieldDef:
    return AnswerFieldDef(
        field_path=[name], 
        field_type=FieldType(Version, converter_ref=ConverterType.VERSION), 
    )

def create_list_with_unknown_answer_alternative(
        answer_def: AnswerDef, 
        old_version: Version | VersionTuple = (0, 0, 0), 
        new_version: Version | VersionTuple = (1, 0, 0)
    ) -> List[MetaExport]:
    return [
        MetaExport(
            answer_def,
            MetaExportDescriptor(min_protocol_version=new_version)
        ),
        MetaExport(
            AnswerDef(fields=[field_unknown_answer]),
            MetaExportDescriptor(
                min_protocol_version=old_version,
                deprecated_protocol_version=new_version
            )
        ),
    ]