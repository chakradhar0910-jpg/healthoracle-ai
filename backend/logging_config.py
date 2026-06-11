"""
HealthOracle AI — Enterprise Logging Engine
===========================================
Registers a logger that outputs structured logs to standard output (console)
and saves rotating logs locally under the `logs/` directory.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from backend.config import LOG_FILE_PATH, LOG_LEVEL


def setup_logging():
    """Configures the root and healthoracle-specific loggers."""
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Base configuration for standard output
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    root_logger.setLevel(LOG_LEVEL)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVEL)
    root_logger.addHandler(console_handler)

    # Rotating File Handler
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=5 * 1024 * 1024,  # 5MB size limit per log file
            backupCount=5,              # Keep up to 5 historical log files
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(LOG_LEVEL)
        root_logger.addHandler(file_handler)
        
        # Log basic system details
        logging.getLogger("healthoracle.init").info(
            "Persistent logging initiated at %s", LOG_FILE_PATH
        )
    except Exception as e:
        # Fallback if log directory write fails
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        root_logger.error("⚠️ Failed to initialize rotating file logger: %s", e)
