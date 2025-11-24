from sonic_protocol.field_names import EFieldName

for field_name in EFieldName:
    globals()["FIELD_" + field_name.name.upper()] = field_name.name
