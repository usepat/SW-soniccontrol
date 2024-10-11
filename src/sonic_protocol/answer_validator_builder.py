from typing import Callable, Dict, List
from sonic_protocol.answer import AfterConverter, AnswerValidator, Converter
from sonic_protocol.defs import AnswerDef, AnswerFieldDef, ConverterType, FieldPath


class AnswerValidatorBuilder:
    def create_answer_validator(self, answer_def: AnswerDef) -> AnswerValidator:
        converters: Dict[ConverterType, Callable | Converter] = {
            ConverterType.SIGNAL: lambda x: x.lower() == "on"
            # TODO: add other converters
            # TODO: add converter for validation
        }
        
        value_dict: Dict[FieldPath, Callable | Converter | AfterConverter] = {}
        for field in answer_def.fields:
            if field.converter_ref:
                value_dict[field.field_path] = converters[field.converter_ref]
            else:
                value_dict[field.field_path] = field.field_type.field_type

        regex = self._create_regex_for_answer(answer_def)
        
        return AnswerValidator(regex, value_dict)

    def _create_regex_for_answer(self, answer_def: AnswerDef) -> str:
        regex_patterns: List[str] = []

        # TODO: add command code to regex

        for answer_field in answer_def.fields:
            regex_patterns.append(self._create_regex_for_answer_field(answer_field)) 

        return answer_def.separator.join(regex_patterns)
    
    def _create_regex_for_answer_field(self, answer_field: AnswerFieldDef) -> str:
        value_str = ""

        if answer_field.converter_ref is None:
            if answer_field.field_type is int:
                value_str = r"([\+\-]?\d+)"
            elif answer_field.field_type is float:
                value_str = r"([\+\-]?\d+(\.\d+)?)"
            elif answer_field.field_type is bool:
                value_str = r"([Tt]rue)|([Ff]alse)|0|1"
            elif answer_field.field_type is str:
                value_str = r".*"
        else:
            value_str = r".*"

        si_prefix = answer_field.field_type.si_prefix
        si_unit = answer_field.field_type.si_unit
        if si_prefix and si_unit:
            value_str += " " + si_prefix.value + si_unit.value
     
        
        return answer_field.prefix + value_str + answer_field.postfix