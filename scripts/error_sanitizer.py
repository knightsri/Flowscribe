#!/usr/bin/env python3
"""
Error Message Sanitizer

Sanitizes error messages to prevent leaking sensitive information such as:
- API keys and tokens
- Internal file paths
- Environment variables
- Credentials
"""

import re
from pathlib import Path
from typing import Optional


class ErrorSanitizer:
    """Sanitizes error messages to prevent information disclosure"""

    # Patterns to detect and sanitize
    API_KEY_PATTERN = re.compile(
        r'(api[_-]?key|token|bearer|authorization)["\s:=]+([a-zA-Z0-9_\-]{20,})',
        re.IGNORECASE
    )

    # Match common API key formats
    COMMON_KEY_PATTERN = re.compile(
        r'\b([a-zA-Z0-9_\-]{32,})\b'  # 32+ chars of alphanumeric
    )

    # Environment variable patterns
    ENV_VAR_PATTERN = re.compile(
        r'([A-Z_]+_(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL))["\s:=]+([^\s"\']+)',
        re.IGNORECASE
    )

    # File path patterns (both absolute and relative)
    UNIX_PATH_PATTERN = re.compile(
        r'(/(?:home|root|workspace|usr|opt|var)/[^\s"\']+)'
    )

    WINDOWS_PATH_PATTERN = re.compile(
        r'([A-Z]:\\(?:[^\s"\'<>|]+\\)*[^\s"\'<>|]+)',
        re.IGNORECASE
    )

    # Credentials in URLs
    URL_CREDENTIALS_PATTERN = re.compile(
        r'(https?://)[^:]+:[^@]+@',
        re.IGNORECASE
    )

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize sanitizer

        Args:
            base_path: Base path to replace with generic placeholder (e.g., project root)
        """
        self.base_path = Path(base_path).resolve() if base_path else None

    def sanitize(self, message: str) -> str:
        """
        Sanitize an error message

        Args:
            message: The error message to sanitize

        Returns:
            Sanitized error message
        """
        if not message:
            return message

        sanitized = message

        # Sanitize API keys and tokens
        sanitized = self._sanitize_api_keys(sanitized)

        # Sanitize environment variables with sensitive names
        sanitized = self._sanitize_env_vars(sanitized)

        # Sanitize file paths
        sanitized = self._sanitize_paths(sanitized)

        # Sanitize credentials in URLs
        sanitized = self._sanitize_url_credentials(sanitized)

        return sanitized

    def _sanitize_api_keys(self, message: str) -> str:
        """Sanitize API keys and tokens"""
        # Replace full API key patterns
        message = self.API_KEY_PATTERN.sub(r'\1: [REDACTED]', message)

        # Be cautious with common key pattern - only replace if it looks like a key
        # (e.g., appears after '=' or ':' or in quotes)
        def replace_possible_key(match):
            key = match.group(1)
            # Only redact if it's 40+ chars and looks like a hex or base64 string
            if len(key) >= 40 and re.match(r'^[a-zA-Z0-9_\-]+$', key):
                return '[REDACTED]'
            return key

        return message

    def _sanitize_env_vars(self, message: str) -> str:
        """Sanitize environment variable values"""
        return self.ENV_VAR_PATTERN.sub(r'\1: [REDACTED]', message)

    def _sanitize_paths(self, message: str) -> str:
        """Sanitize file paths"""
        # If base_path is set, replace it with a generic placeholder
        if self.base_path:
            base_path_str = str(self.base_path)
            message = message.replace(base_path_str, '[PROJECT_ROOT]')

        # Sanitize Unix-style paths
        message = self.UNIX_PATH_PATTERN.sub(self._redact_path, message)

        # Sanitize Windows-style paths
        message = self.WINDOWS_PATH_PATTERN.sub(self._redact_path, message)

        return message

    def _redact_path(self, match) -> str:
        """Redact a file path intelligently"""
        path = match.group(1)

        # Keep the filename but redact the directory
        path_obj = Path(path)
        filename = path_obj.name

        # Determine path type
        if path.startswith('/home'):
            return f'/home/[USER]/.../{filename}'
        elif path.startswith('/root'):
            return f'/root/.../{filename}'
        elif path.startswith('/workspace'):
            return f'/workspace/.../{filename}'
        elif path.startswith(('/usr', '/opt', '/var')):
            # System paths are generally OK to show
            return path
        elif ':' in path:  # Windows path
            drive = path_obj.drive
            return f'{drive}/.../{filename}'
        else:
            return f'[PATH]/.../{filename}'

    def _sanitize_url_credentials(self, message: str) -> str:
        """Sanitize credentials in URLs"""
        return self.URL_CREDENTIALS_PATTERN.sub(r'\1[REDACTED]:[REDACTED]@', message)


# Global sanitizer instance
_global_sanitizer: Optional[ErrorSanitizer] = None


def init_sanitizer(base_path: Optional[str] = None) -> None:
    """
    Initialize the global sanitizer

    Args:
        base_path: Base path to replace with generic placeholder
    """
    global _global_sanitizer
    _global_sanitizer = ErrorSanitizer(base_path)


def sanitize_error(message: str) -> str:
    """
    Sanitize an error message using the global sanitizer

    Args:
        message: The error message to sanitize

    Returns:
        Sanitized error message
    """
    global _global_sanitizer

    if _global_sanitizer is None:
        _global_sanitizer = ErrorSanitizer()

    return _global_sanitizer.sanitize(message)


def safe_log_error(logger, message: str, *args, **kwargs) -> None:
    """
    Log an error message after sanitizing it

    Args:
        logger: Logger instance
        message: Error message to log
        *args: Additional arguments for logger.error()
        **kwargs: Additional keyword arguments for logger.error()
    """
    sanitized = sanitize_error(message)
    logger.error(sanitized, *args, **kwargs)


def safe_log_warning(logger, message: str, *args, **kwargs) -> None:
    """
    Log a warning message after sanitizing it

    Args:
        logger: Logger instance
        message: Warning message to log
        *args: Additional arguments for logger.warning()
        **kwargs: Additional keyword arguments for logger.warning()
    """
    sanitized = sanitize_error(message)
    logger.warning(sanitized, *args, **kwargs)
