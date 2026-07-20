
from sonic_protocol.schema import AnswerFieldDef, FieldType, Version
from sonic_protocol.field_names import EFieldName

def create_version_field(name: EFieldName) -> AnswerFieldDef:
    return AnswerFieldDef(
        field_name=name, 
        field_type=FieldType(field_type=Version), 
    )