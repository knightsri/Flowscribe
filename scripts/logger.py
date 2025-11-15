#!/usr/bin/env python3
"""
Logging configuration for Flowscribe.

Provides structured logging with configurable levels.
"""
import logging
import sys


def setup_logger(name, level=logging.INFO):
    """
    Setup structured logger for Flowscribe scripts.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Format with timestamp, level, and message
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)8s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def set_debug_mode(logger, debug=True):
    """
    Enable or disable debug mode for a logger.

    Args:
        logger: Logger instance
        debug: Enable (True) or disable (False) debug mode
    """
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
