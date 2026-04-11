from sonic_protocol.python_parser import commands as _commands

Command = _commands.Command


def __getattr__(name: str):
	return getattr(_commands, name)


def __dir__() -> list[str]:
	return sorted(set(globals()) | set(dir(_commands)))