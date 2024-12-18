from sonic_protocol.defs import Procedure, InputSource
from robot.api.deco import keyword


@keyword("Convert to procedure")
def to_procedure(enum_member: str) -> Procedure:
    try:
        return Procedure[enum_member.upper()]
    except KeyError:
        raise ValueError(f"Invalid procedure name: {enum_member}")
    
@keyword("Convert to input source")
def to_input_source(enum_member: str) -> InputSource:
    try:
        return InputSource[enum_member.upper()]
    except KeyError:
        raise ValueError(f"Invalid input source name: {enum_member}")
