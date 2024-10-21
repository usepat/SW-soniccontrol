
from pathlib import Path
from sonic_protocol.defs import AnswerDef, AnswerFieldDef, CommandDef, CommandParamDef, FieldType
from sonic_protocol.protocol_builder import CommandLookUpTable 

def nullopt_if_none(value):
    cpp_nullopt_t = "std::nullopt"
    return cpp_nullopt_t if value is None else value

class TransCompiler:
    def __init__(self):
        self._var_id_counter: int = 0
        self._transpiled_output: str = ""

    def create_transpiled_protocol_lib(self, command_list: CommandLookUpTable, output_dir: Path): 
        pass

    def transpile_command_contracts(
            self, command_list: CommandLookUpTable) -> str:
        ...

    def _transpile_command_def(self, command_def: CommandDef) -> str:
        ...

    def _transpile_param_def(self, param_def: CommandParamDef) -> str:
        ...

    def _transpile_answer_def(self, answer_def: AnswerDef) -> str:
        ...

    def _transpile_answer_field(self, field: AnswerFieldDef) -> str:
        ...

    def _transpile_field_type(self, field_type: FieldType) -> str:
        cpp_field_limits: str = f"""
            FieldLimits<> {{
                .min = {nullopt_if_none(field_type.min_value)},
                .max = {nullopt_if_none(field_type.max_value)},
            }}
        """ 
        cpp_limits_var: str = f"limits_{self._var_id_counter}"
        self._transpiled_output += f"constexpr {cpp_limits_var} {{ {cpp_field_limits} }};\n"
        
        cpp_field_type_def: str = ""
        
        return cpp_field_type_def

