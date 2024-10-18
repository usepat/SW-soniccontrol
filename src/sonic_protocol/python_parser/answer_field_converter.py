from typing import Any
from sonic_protocol.python_parser.converters import get_converter
from sonic_protocol.defs import AnswerFieldDef, ConverterType


class AnswerFieldToStringConverter:
    def __init__(self, field_def: AnswerFieldDef):
        assert (not isinstance(field_def.sonic_text_attrs, list))

        unit = ""
        si_prefix = field_def.field_type.si_prefix
        if si_prefix:
            unit += si_prefix.value
        si_unit = field_def.field_type.si_unit
        if si_unit:
            unit += si_unit.value
        self._format_str = field_def.sonic_text_attrs.prefix + "%s" + unit + field_def.sonic_text_attrs.postfix
        self._converter_ref = field_def.field_type.converter_ref
        self._target_class = field_def.field_type.field_type

    @property
    def format_str(self) -> str:
        return self._format_str
    
    @property
    def converter_ref(self) -> ConverterType | None:
        return self._converter_ref 
    
    def convert(self, value: Any) -> str:
        if self._converter_ref is not None:
            converter = get_converter(self._converter_ref, self._target_class)
            assert (converter.validate_val(value))
            converted_value = converter.convert_val(value)
            string_repr_value = converted_value
        else:
            string_repr_value = str(value)
        return self._format_str % string_repr_value