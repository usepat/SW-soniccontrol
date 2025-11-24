from sonic_protocol.command_codes import CommandCode

for code in CommandCode:
    globals()["CODE_" + code.name.upper()] = code.value
