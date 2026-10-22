import logging
from pathlib import Path

from soniccontrol.logger import utils as logger_utils


def test_create_logger_for_connection_allows_configurable_rotation(tmp_path: Path):
    logger_name = "test.logger.utils.rotation"
    logger = logging.getLogger(logger_name)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    configured_logger = logger_utils.create_logger_for_connection(
        logger_name,
        tmp_path,
        max_bytes=1234,
        backup_count=56,
    )

    try:
        assert configured_logger is logger
        file_handlers = [
            handler
            for handler in configured_logger.handlers
            if isinstance(handler, logging.handlers.RotatingFileHandler)
        ]
        assert len(file_handlers) == 1

        handler = file_handlers[0]
        assert handler.maxBytes == 1234
        assert handler.backupCount == 56
        assert Path(handler.baseFilename) == tmp_path / "device_on_test.logger.utils.rotation.log"
    finally:
        for handler in list(configured_logger.handlers):
            configured_logger.removeHandler(handler)
            handler.close()


def test_remote_controller_rotation_constants_cover_20_gib() -> None:
    retained_bytes = logger_utils.REMOTE_CONTROLLER_LOG_ROTATION_MAX_BYTES * (
        logger_utils.REMOTE_CONTROLLER_LOG_ROTATION_BACKUP_COUNT + 1
    )

    assert retained_bytes >= 20 * 1024 * 1024 * 1024