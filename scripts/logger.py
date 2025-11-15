#!/usr/bin/env python3
"""
Logging configuration for Flowscribe.

Provides structured logging with configurable levels and JSON output support.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Optional, Dict, Any


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
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


def set_debug_mode(logger: logging.Logger, debug: bool = True) -> None:
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


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Formats log records as JSON objects for easier parsing and analysis.
    """

    def __init__(self, include_extra: bool = True):
        """
        Initialize JSON formatter.

        Args:
            include_extra: Include extra fields from LogRecord
        """
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add stack info if present
        if record.stack_info:
            log_data['stack_info'] = self.formatStack(record.stack_info)

        # Add extra fields if requested
        if self.include_extra:
            # Standard LogRecord attributes to exclude
            exclude_keys = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName',
                'relativeCreated', 'thread', 'threadName', 'exc_info',
                'exc_text', 'stack_info', 'getMessage', 'taskName'
            }

            # Add any extra fields
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in exclude_keys and not k.startswith('_')
            }

            if extra_fields:
                log_data['extra'] = extra_fields

        return json.dumps(log_data)


def setup_json_logger(
    name: str,
    level: int = logging.INFO,
    include_extra: bool = True
) -> logging.Logger:
    """
    Setup logger with JSON formatting.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        include_extra: Include extra fields in JSON output

    Returns:
        Configured logger instance with JSON formatter
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = JSONFormatter(include_extra=include_extra)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def setup_dual_logger(
    name: str,
    level: int = logging.INFO,
    json_output: bool = False
) -> logging.Logger:
    """
    Setup logger that can switch between text and JSON output.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        json_output: Use JSON format (True) or text format (False)

    Returns:
        Configured logger instance
    """
    if json_output:
        return setup_json_logger(name, level)
    else:
        return setup_logger(name, level)
