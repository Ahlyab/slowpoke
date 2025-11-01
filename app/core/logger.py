import logging
import os
from logging.handlers import RotatingFileHandler

from ..utils.config import get_settings
from ..utils.contants import LOG_DIR

settings = get_settings()


def get_logger(module_name: str, level: str = "") -> logging.Logger:
    """
    Creates and returns a logger for the given module. Log files are rotated at 1MB with 3 backups.

    Args:
        module_name (str): The name of the module for which the logger is created.
        level (str, optional): The logging level. If not provided, the level is fetched from the LOG_LEVEL environment variable.
                               Default level is INFO.

    Returns:
        logging.Logger: Configured logger instance for the specified module.
    """

    log_level = level or settings.log_level
    print(f"Log Level for module: {module_name}:", log_level)

    log_file = os.path.join(LOG_DIR, f"{module_name}.log")

    logger = logging.getLogger(module_name)
    logger.setLevel(getattr(logging, log_level))

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler
        handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
