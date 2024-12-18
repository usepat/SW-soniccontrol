from sonic_protocol.defs import Procedure
from robot.api.deco import keyword


@keyword("Convert to procedure")
def to_procedure(enum_member: str) -> Procedure:
    try:
        return Procedure[enum_member.upper()]
    except KeyError:
        raise ValueError(f"Invalid procedure name: {enum_member}")
