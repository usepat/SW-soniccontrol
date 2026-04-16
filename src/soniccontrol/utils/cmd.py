import asyncio
import logging
import subprocess
from typing import List


async def execute_command(command: List[str] | str, logger: logging.Logger):
    if isinstance(command, str):
        command_str = command
        command = command.split(" ")
    else:
        command_str = " ".join(map(str, command))
        
    logger.debug("Running command: %s", command_str)
    proc = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    retcode = proc.returncode if proc.returncode is not None else -1
    out_str = out.decode(errors='replace') if out else ""
    err_str: str = err.decode(errors='replace') if err else ""
    logger.debug("'%s' returncode=%s stdout=%s stderr=%s", command_str, retcode, out_str, err_str)
    if retcode != 0:
        logger.error("command '%s' failed (rc=%s): %s", command_str, retcode, err_str)
        raise subprocess.CalledProcessError(retcode, command, output=out_str, stderr=err_str)
    return out_str
