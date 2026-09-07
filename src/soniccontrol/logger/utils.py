import logging
import logging.handlers
from pathlib import Path
import os
import re


def is_sub_logger(child: logging.Logger, parent: logging.Logger) -> bool:
    return child.name.startswith(parent.name + ".")

def get_base_logger(logger: logging.Logger) -> logging.Logger:
    try:
        base_logger_name = logger.name.split(".").pop(0)
    except IndexError:
        base_logger_name = ""
    
    return logging.getLogger(base_logger_name)


def _sanitize_log_stem(connection_name: str) -> str:
    sanitized_name = re.sub(r"[^A-Za-z0-9._-]+", "_", connection_name).strip("._-")
    return sanitized_name or "connection"

def create_logger_for_connection(connection_name: str, out_dir=Path(".")) -> logging.Logger:
    logger = logging.getLogger(connection_name)
    logger.setLevel(logging.DEBUG)
    os.makedirs(out_dir, exist_ok=True)
    log_file_path = out_dir / f"device_on_{_sanitize_log_stem(connection_name)}.log"
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    log_file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=40000,
        backupCount=3
    )
    detailed_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)s:%(funcName)s - %(message)s - exception: %(exc_info)s")
    log_file_handler.setFormatter(detailed_formatter)
    logger.addHandler(log_file_handler)
    return logger

def add_logger_context_to_exception(e: Exception, logger: logging.Logger, should_overwrite: bool = False):
    """
    attaches logger information to an exception.
    It is better to only log exceptions in the final handler to avoid noisy logs.
    Therefore we also add information to exceptions, so we know which specific logger to use.
    """
    if not hasattr(e, "logger") or should_overwrite:
        setattr(e, "logger", logger)
    