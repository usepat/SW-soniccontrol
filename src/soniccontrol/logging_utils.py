import logging
import logging.handlers
from pathlib import Path

def get_base_logger(logger: logging.Logger) -> logging.Logger:
    try:
        base_logger_name = logger.name.split(".").pop(0)
    except IndexError:
        base_logger_name = ""
    
    return logging.getLogger(base_logger_name)

def create_logger_for_connection(connection_name: str, out_dir=Path(".")) -> logging.Logger:
    logger = logging.getLogger(connection_name)
    logger.setLevel(logging.DEBUG)
    log_file_handler = logging.handlers.RotatingFileHandler(
        out_dir / f"device_on_{connection_name}.log",
        maxBytes=40000,
        backupCount=3
    )
    detailed_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)s:%(funcName)s - %(message)s - exception: %(exc_info)s")
    log_file_handler.setFormatter(detailed_formatter)
    logger.addHandler(log_file_handler)
    return logger