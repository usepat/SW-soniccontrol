from typing import Dict, List
from sonic_protocol.python_parser.answer import AfterConverter, AnswerValidator
from sonic_protocol.python_parser.converters import Converter, get_converter
from sonic_protocol.defs import AnswerDef, AnswerFieldDef, ConverterType, FieldPath


class AnswerValidatorBuilder:
    def create_answer_validator(self, answer_def: AnswerDef) -> AnswerValidator: 
        value_dict: Dict[FieldPath, Converter | AfterConverter] = {}
        for field in answer_def.fields:
            field_type = field.field_type.field_type
            value_dict[field.field_path] = get_converter(field.field_type.converter_ref, field_type)

        regex = self._create_regex_for_answer(answer_def)
        
        return AnswerValidator(regex, value_dict)

    def _create_regex_for_answer(self, answer_def: AnswerDef) -> str:
        assert (not isinstance(answer_def.sonic_text_attrs, list))

        regex_patterns: List[str] = []

        # TODO: add command code to regex

        for answer_field in answer_def.fields:
            regex_patterns.append(self._create_regex_for_answer_field(answer_field)) 

        return answer_def.sonic_text_attrs.separator.join(regex_patterns)
    
    def _create_regex_for_answer_field(self, answer_field: AnswerFieldDef) -> str:
        assert (not isinstance(answer_field.sonic_text_attrs, list))
        sonic_text_attrs = answer_field.sonic_text_attrs

        value_str = ""

        if answer_field.field_type.converter_ref is ConverterType.PRIMITIVE:
            if answer_field.field_type is int:
                value_str = r"[\+\-]?\d+"
            elif answer_field.field_type is float:
                value_str = r"[\+\-]?\d+(\.\d+)?"
            elif answer_field.field_type is bool:
                value_str = r"([Tt]rue)|([Ff]alse)|0|1"
            elif answer_field.field_type is str:
                value_str = r".*"
        else:
            value_str = r".*"

        result_str = "(" + value_str + ")" # make a regex group

        si_prefix = answer_field.field_type.si_prefix
        si_unit = answer_field.field_type.si_unit
        if si_prefix and si_unit:
            result_str += " " + si_prefix.value + si_unit.value
        elif si_unit:
            result_str += " " + si_unit.value
     
        
        return sonic_text_attrs.prefix + result_str + sonic_text_attrs.postfix