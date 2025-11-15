"""
Safe File I/O Operations

Provides safe file reading operations with size checks and error handling
to prevent memory issues and improve security.
"""

from pathlib import Path
from typing import Optional, List, Union
import os


class FileSizeError(Exception):
    """Raised when file size exceeds the allowed limit."""
    pass


class FileNotReadableError(Exception):
    """Raised when file cannot be read."""
    pass


def safe_read_file(
    path: Union[str, Path],
    max_size: int = 1_000_000,
    encoding: str = 'utf-8',
    errors: str = 'strict'
) -> str:
    """
    Read file with size limit check.

    Args:
        path: Path to file
        max_size: Maximum file size in bytes (default: 1MB)
        encoding: Text encoding (default: utf-8)
        errors: Error handling strategy (strict, ignore, replace)

    Returns:
        File contents as string

    Raises:
        FileSizeError: If file exceeds max_size
        FileNotFoundError: If file doesn't exist
        FileNotReadableError: If file cannot be read
        ValueError: If path is invalid
    """
    # Convert to Path object
    file_path = Path(path)

    # Validate path
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    # Check file size before reading
    try:
        stat = file_path.stat()
        file_size = stat.st_size

        if file_size > max_size:
            raise FileSizeError(
                f"File too large: {file_size:,} bytes "
                f"(limit: {max_size:,} bytes) - {file_path}"
            )

        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            raise FileNotReadableError(f"File not readable: {file_path}")

        # Read file
        return file_path.read_text(encoding=encoding, errors=errors)

    except (OSError, IOError) as e:
        raise FileNotReadableError(f"Failed to read file {file_path}: {e}")


def safe_read_file_bytes(
    path: Union[str, Path],
    max_size: int = 1_000_000
) -> bytes:
    """
    Read file as bytes with size limit check.

    Args:
        path: Path to file
        max_size: Maximum file size in bytes (default: 1MB)

    Returns:
        File contents as bytes

    Raises:
        FileSizeError: If file exceeds max_size
        FileNotFoundError: If file doesn't exist
        FileNotReadableError: If file cannot be read
        ValueError: If path is invalid
    """
    # Convert to Path object
    file_path = Path(path)

    # Validate path
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    # Check file size before reading
    try:
        stat = file_path.stat()
        file_size = stat.st_size

        if file_size > max_size:
            raise FileSizeError(
                f"File too large: {file_size:,} bytes "
                f"(limit: {max_size:,} bytes) - {file_path}"
            )

        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            raise FileNotReadableError(f"File not readable: {file_path}")

        # Read file
        return file_path.read_bytes()

    except (OSError, IOError) as e:
        raise FileNotReadableError(f"Failed to read file {file_path}: {e}")


def safe_read_lines(
    path: Union[str, Path],
    max_size: int = 1_000_000,
    max_lines: Optional[int] = None,
    encoding: str = 'utf-8',
    errors: str = 'strict'
) -> List[str]:
    """
    Read file lines with size and line count limits.

    Args:
        path: Path to file
        max_size: Maximum file size in bytes (default: 1MB)
        max_lines: Maximum number of lines to read (None = all)
        encoding: Text encoding (default: utf-8)
        errors: Error handling strategy (strict, ignore, replace)

    Returns:
        List of lines (without newline characters)

    Raises:
        FileSizeError: If file exceeds max_size
        FileNotFoundError: If file doesn't exist
        FileNotReadableError: If file cannot be read
        ValueError: If path is invalid
    """
    content = safe_read_file(path, max_size, encoding, errors)
    lines = content.splitlines()

    if max_lines is not None and len(lines) > max_lines:
        return lines[:max_lines]

    return lines


def check_file_size(path: Union[str, Path]) -> int:
    """
    Check file size without reading it.

    Args:
        path: Path to file

    Returns:
        File size in bytes

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If path is not a file
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    return file_path.stat().st_size


def is_file_too_large(path: Union[str, Path], max_size: int) -> bool:
    """
    Check if file exceeds size limit without reading it.

    Args:
        path: Path to file
        max_size: Maximum allowed size in bytes

    Returns:
        True if file is too large, False otherwise

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If path is not a file
    """
    file_size = check_file_size(path)
    return file_size > max_size


def get_human_readable_size(size_bytes: int) -> str:
    """
    Convert bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def safe_read_with_fallback(
    path: Union[str, Path],
    max_size: int = 1_000_000,
    encoding: str = 'utf-8',
    fallback_encodings: Optional[List[str]] = None
) -> Optional[str]:
    """
    Try to read file with fallback encodings if primary fails.

    Args:
        path: Path to file
        max_size: Maximum file size in bytes
        encoding: Primary encoding to try
        fallback_encodings: List of fallback encodings (default: ['latin-1', 'cp1252'])

    Returns:
        File contents or None if all encodings fail
    """
    if fallback_encodings is None:
        fallback_encodings = ['latin-1', 'cp1252']

    # Try primary encoding
    try:
        return safe_read_file(path, max_size, encoding, errors='strict')
    except (UnicodeDecodeError, FileNotReadableError):
        pass

    # Try fallback encodings
    for fallback_enc in fallback_encodings:
        try:
            return safe_read_file(path, max_size, fallback_enc, errors='replace')
        except (UnicodeDecodeError, FileNotReadableError):
            continue

    return None


class SafeFileReader:
    """Context manager for safe file reading."""

    def __init__(
        self,
        path: Union[str, Path],
        max_size: int = 1_000_000,
        encoding: str = 'utf-8',
        errors: str = 'strict'
    ):
        """
        Initialize safe file reader.

        Args:
            path: Path to file
            max_size: Maximum file size in bytes
            encoding: Text encoding
            errors: Error handling strategy
        """
        self.path = Path(path)
        self.max_size = max_size
        self.encoding = encoding
        self.errors = errors
        self.content: Optional[str] = None

    def __enter__(self) -> str:
        """Read file on context entry."""
        self.content = safe_read_file(
            self.path,
            self.max_size,
            self.encoding,
            self.errors
        )
        return self.content

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up on context exit."""
        self.content = None
        return False


if __name__ == '__main__':
    # Example usage and testing
    import tempfile

    print("Safe File I/O - Example Usage")
    print("=" * 50)

    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        test_file = Path(f.name)
        f.write("Hello, World!\n" * 100)

    try:
        # Check file size
        size = check_file_size(test_file)
        print(f"File size: {get_human_readable_size(size)}")

        # Read file safely
        content = safe_read_file(test_file, max_size=10_000)
        print(f"Read {len(content)} characters")

        # Read with context manager
        with SafeFileReader(test_file, max_size=10_000) as file_content:
            lines = file_content.count('\n')
            print(f"File has {lines} lines")

        # Test size limit
        try:
            safe_read_file(test_file, max_size=100)
        except FileSizeError as e:
            print(f"Caught expected error: {e}")

    finally:
        # Clean up
        test_file.unlink()

    print("\nModule loaded successfully.")
