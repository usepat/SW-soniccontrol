from typing import Any
from sonic_protocol.python_parser.converters import get_converter
from sonic_protocol.schema import AnswerFieldDef, ConverterType


class AnswerFieldToStringConverter:
    def __init__(self, field_def: AnswerFieldDef):
        assert (not isinstance(field_def.sonic_text_attrs, list))

        self._unit = ""
        si_prefix = field_def.field_type.si_prefix
        if si_prefix:
            self._unit += si_prefix.symbol
        si_unit = field_def.field_type.si_unit
        if si_unit:
            self._unit += si_unit.value
        self._prefix = field_def.sonic_text_attrs.prefix
        self._postfix = field_def.sonic_text_attrs.postfix
        self._converter_ref = field_def.field_type.converter_ref
        self._target_class = field_def.field_type.field_type
    
    @property
    def converter_ref(self) -> ConverterType | None:
        return self._converter_ref 
    
    def convert(self, value: Any) -> str:
        if self._converter_ref is not None:
            converter = get_converter(self._converter_ref, self._target_class)
            assert (converter.validate_val(value)) # TODO:this should not be an assert probably
            converted_value = converter.convert_val_to_str(value)
            string_repr_value = converted_value
        else:
            string_repr_value = str(value)
        if self._unit != "":
            string_repr_value += " " + self._unit
        return self._prefix + string_repr_value + self._postfix
        