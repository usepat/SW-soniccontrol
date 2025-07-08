from typing import Dict, List
from sonic_protocol.python_parser.answer import AfterConverter, AnswerValidator
from sonic_protocol.python_parser.converters import Converter, get_converter
from sonic_protocol.schema import AnswerDef, AnswerFieldDef, ConverterType, EFieldName
import numpy as np


class AnswerValidatorBuilder:
    @staticmethod
    def create_answer_validator(answer_def: AnswerDef) -> AnswerValidator: 
        value_dict: Dict[EFieldName, Converter | AfterConverter] = {}
        for field in answer_def.fields:
            field_type = field.field_type.field_type
            value_dict[field.field_name] = get_converter(field.field_type.converter_ref, field_type)

        regex = AnswerValidatorBuilder._create_regex_for_answer(answer_def)
        
        return AnswerValidator(regex, value_dict)

    @staticmethod
    def _create_regex_for_answer(answer_def: AnswerDef) -> str:
        assert (not isinstance(answer_def.sonic_text_attrs, list))

        regex_patterns: List[str] = []

        # TODO: add command code to regex

        for answer_field in answer_def.fields:
            regex_patterns.append(AnswerValidatorBuilder._create_regex_for_answer_field(answer_field)) 

        return answer_def.sonic_text_attrs.separator.join(regex_patterns)
    
    @staticmethod
    def _create_regex_for_answer_field(answer_field: AnswerFieldDef) -> str:
        assert (not isinstance(answer_field.sonic_text_attrs, list))
        sonic_text_attrs = answer_field.sonic_text_attrs

        value_str = ""
        field_type = answer_field.field_type.field_type
        if answer_field.field_type.converter_ref is ConverterType.PRIMITIVE:
            if field_type is int or np.issubdtype(field_type, np.integer):
                value_str = r"[\+\-]?\d+"
            elif field_type is float:
                value_str = r"[\+\-]?\d+(\.\d+)?"
            elif field_type is bool:
                value_str = r"([Tt]rue)|([Ff]alse)|0|1"
            elif field_type is str:
                value_str = r".*"
            else:
                assert (False) # should never happen.
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