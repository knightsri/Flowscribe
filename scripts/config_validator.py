#!/usr/bin/env python3
"""
Configuration Validator

Validates configuration values for Flowscribe scripts to ensure:
- Required environment variables are set
- Values are within acceptable ranges
- Paths are safe and valid
- Model names are properly formatted
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigValidator:
    """Validates configuration values"""

    # Valid model name pattern (provider/model-name)
    MODEL_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9._/-]+$')

    # Minimum and maximum values for common parameters
    MIN_TIMEOUT = 10  # seconds
    MAX_TIMEOUT = 600  # seconds
    MIN_FILE_SIZE = 1000  # bytes
    MAX_FILE_SIZE = 10_000_000  # 10MB
    MIN_MAX_FILES = 1
    MAX_MAX_FILES = 1000

    @staticmethod
    def validate_api_key(api_key: Optional[str], key_name: str = "API key") -> str:
        """
        Validate API key

        Args:
            api_key: The API key to validate
            key_name: Name of the key for error messages

        Returns:
            The validated API key

        Raises:
            ConfigValidationError: If the API key is invalid
        """
        if not api_key:
            raise ConfigValidationError(f"{key_name} is required but not set")

        if not isinstance(api_key, str):
            raise ConfigValidationError(f"{key_name} must be a string")

        # Remove whitespace
        api_key = api_key.strip()

        if len(api_key) < 20:
            raise ConfigValidationError(f"{key_name} is too short (minimum 20 characters)")

        if len(api_key) > 200:
            raise ConfigValidationError(f"{key_name} is too long (maximum 200 characters)")

        # Check for suspicious characters
        if any(char in api_key for char in ['\n', '\r', '\t', ' ']):
            raise ConfigValidationError(f"{key_name} contains invalid whitespace characters")

        return api_key

    @staticmethod
    def validate_model_name(model: str) -> str:
        """
        Validate model name

        Args:
            model: The model name to validate

        Returns:
            The validated model name

        Raises:
            ConfigValidationError: If the model name is invalid
        """
        if not model:
            raise ConfigValidationError("Model name is required")

        if not isinstance(model, str):
            raise ConfigValidationError("Model name must be a string")

        model = model.strip()

        if not ConfigValidator.MODEL_NAME_PATTERN.match(model):
            raise ConfigValidationError(
                f"Invalid model name format: {model}. "
                "Must contain only alphanumeric characters, dots, hyphens, slashes, and underscores"
            )

        if len(model) > 100:
            raise ConfigValidationError(f"Model name is too long: {model}")

        return model

    @staticmethod
    def validate_project_path(path_str: str, must_exist: bool = True) -> Path:
        """
        Validate and resolve a project directory path

        Args:
            path_str: The path string to validate
            must_exist: Whether the path must exist

        Returns:
            The validated and resolved Path object

        Raises:
            ConfigValidationError: If the path is invalid
        """
        if not path_str:
            raise ConfigValidationError("Path is required")

        if not isinstance(path_str, str):
            raise ConfigValidationError("Path must be a string")

        # Check for directory traversal attempts
        if '..' in Path(path_str).parts:
            raise ConfigValidationError("Invalid path: directory traversal detected")

        # Check for null bytes
        if '\0' in path_str:
            raise ConfigValidationError("Invalid path: contains null bytes")

        try:
            path = Path(path_str).resolve()
        except (ValueError, OSError) as e:
            raise ConfigValidationError(f"Invalid path: {e}")

        if must_exist and not path.exists():
            raise ConfigValidationError(f"Path does not exist: {path}")

        return path

    @staticmethod
    def validate_output_path(path_str: str, create_parent: bool = False) -> Path:
        """
        Validate an output file path

        Args:
            path_str: The path string to validate
            create_parent: Whether to create parent directories

        Returns:
            The validated and resolved Path object

        Raises:
            ConfigValidationError: If the path is invalid
        """
        # Use the same validation as project path but don't require existence
        path = ConfigValidator.validate_project_path(path_str, must_exist=False)

        # Check for directory traversal
        if '..' in Path(path_str).parts:
            raise ConfigValidationError("Invalid output path: directory traversal detected")

        if create_parent:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise ConfigValidationError(f"Cannot create parent directory: {e}")

        return path

    @staticmethod
    def validate_timeout(timeout: int) -> int:
        """
        Validate timeout value

        Args:
            timeout: Timeout in seconds

        Returns:
            The validated timeout

        Raises:
            ConfigValidationError: If the timeout is invalid
        """
        if not isinstance(timeout, int):
            raise ConfigValidationError("Timeout must be an integer")

        if timeout < ConfigValidator.MIN_TIMEOUT:
            raise ConfigValidationError(
                f"Timeout too small: {timeout}s (minimum: {ConfigValidator.MIN_TIMEOUT}s)"
            )

        if timeout > ConfigValidator.MAX_TIMEOUT:
            raise ConfigValidationError(
                f"Timeout too large: {timeout}s (maximum: {ConfigValidator.MAX_TIMEOUT}s)"
            )

        return timeout

    @staticmethod
    def validate_file_size(size: int) -> int:
        """
        Validate file size limit

        Args:
            size: File size in bytes

        Returns:
            The validated file size

        Raises:
            ConfigValidationError: If the file size is invalid
        """
        if not isinstance(size, int):
            raise ConfigValidationError("File size must be an integer")

        if size < ConfigValidator.MIN_FILE_SIZE:
            raise ConfigValidationError(
                f"File size too small: {size} bytes (minimum: {ConfigValidator.MIN_FILE_SIZE} bytes)"
            )

        if size > ConfigValidator.MAX_FILE_SIZE:
            raise ConfigValidationError(
                f"File size too large: {size} bytes (maximum: {ConfigValidator.MAX_FILE_SIZE} bytes)"
            )

        return size

    @staticmethod
    def validate_max_files(max_files: int) -> int:
        """
        Validate maximum number of files

        Args:
            max_files: Maximum number of files

        Returns:
            The validated max files value

        Raises:
            ConfigValidationError: If the value is invalid
        """
        if not isinstance(max_files, int):
            raise ConfigValidationError("Max files must be an integer")

        if max_files < ConfigValidator.MIN_MAX_FILES:
            raise ConfigValidationError(
                f"Max files too small: {max_files} (minimum: {ConfigValidator.MIN_MAX_FILES})"
            )

        if max_files > ConfigValidator.MAX_MAX_FILES:
            raise ConfigValidationError(
                f"Max files too large: {max_files} (maximum: {ConfigValidator.MAX_MAX_FILES})"
            )

        return max_files

    @staticmethod
    def validate_github_url(url: str) -> str:
        """
        Validate GitHub URL

        Args:
            url: GitHub repository URL

        Returns:
            The validated URL

        Raises:
            ConfigValidationError: If the URL is invalid
        """
        if not url:
            raise ConfigValidationError("GitHub URL is required")

        if not isinstance(url, str):
            raise ConfigValidationError("GitHub URL must be a string")

        url = url.strip()

        # Check for suspicious characters that could indicate injection
        if any(char in url for char in [';', '&', '|', '\n', '\r', '\0']):
            raise ConfigValidationError("Invalid GitHub URL: contains suspicious characters")

        # Must start with https:// or git@
        if not (url.startswith('https://') or url.startswith('git@')):
            raise ConfigValidationError("GitHub URL must start with https:// or git@")

        # Must contain github.com
        if 'github.com' not in url.lower():
            raise ConfigValidationError("URL must be a GitHub repository")

        return url

    @staticmethod
    def validate_environment_config() -> Dict[str, Any]:
        """
        Validate environment configuration

        Returns:
            Dictionary of validated configuration values

        Raises:
            ConfigValidationError: If required environment variables are missing or invalid
        """
        config = {}

        # Validate API key
        api_key = os.environ.get('OPENROUTER_API_KEY')
        config['api_key'] = ConfigValidator.validate_api_key(api_key, "OPENROUTER_API_KEY")

        # Validate model (optional, has default)
        model = os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4-20250514')
        config['model'] = ConfigValidator.validate_model_name(model)

        return config

    @staticmethod
    def validate_all(
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        project_path: Optional[str] = None,
        output_path: Optional[str] = None,
        timeout: Optional[int] = None,
        max_file_size: Optional[int] = None,
        max_files: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate multiple configuration values at once

        Args:
            api_key: API key to validate
            model: Model name to validate
            project_path: Project directory path to validate
            output_path: Output file path to validate
            timeout: Timeout to validate
            max_file_size: Max file size to validate
            max_files: Max files to validate

        Returns:
            Dictionary of validated values

        Raises:
            ConfigValidationError: If any validation fails
        """
        validated = {}

        if api_key is not None:
            validated['api_key'] = ConfigValidator.validate_api_key(api_key)

        if model is not None:
            validated['model'] = ConfigValidator.validate_model_name(model)

        if project_path is not None:
            validated['project_path'] = ConfigValidator.validate_project_path(project_path)

        if output_path is not None:
            validated['output_path'] = ConfigValidator.validate_output_path(output_path)

        if timeout is not None:
            validated['timeout'] = ConfigValidator.validate_timeout(timeout)

        if max_file_size is not None:
            validated['max_file_size'] = ConfigValidator.validate_file_size(max_file_size)

        if max_files is not None:
            validated['max_files'] = ConfigValidator.validate_max_files(max_files)

        return validated
