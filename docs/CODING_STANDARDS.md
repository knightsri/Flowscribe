# Flowscribe Coding Standards

**Version:** 1.0
**Last Updated:** 2025-11-15

This document defines coding standards, conventions, and best practices for the Flowscribe project.

---

## Table of Contents

1. [Function Naming Conventions](#function-naming-conventions)
2. [Error Handling Strategy](#error-handling-strategy)
3. [Type Hints](#type-hints)
4. [Function Length Guidelines](#function-length-guidelines)
5. [Logging Practices](#logging-practices)
6. [Security Best Practices](#security-best-practices)

---

## Function Naming Conventions

Consistent function naming improves code readability and communicates intent clearly.

### Standard Prefixes

Use these prefixes to indicate function behavior:

| Prefix | Purpose | Example | Returns |
|--------|---------|---------|---------|
| `get_*()` | Retrieve existing data from memory/state | `get_api_config()` | Data structure or value |
| `load_*()` | Read data from file or external source | `load_deptrac_report()` | Loaded data or None |
| `read_*()` | Read and parse file content | `read_project_files()` | File content or structure |
| `generate_*()` | Create new content (especially with LLM) | `generate_markdown()` | Generated content |
| `build_*()` | Construct/assemble from existing data | `build_analysis_prompt()` | Constructed object |
| `parse_*()` | Parse and transform data format | `parse_llm_json()` | Parsed data structure |
| `sanitize_*()` | Clean/validate data | `sanitize_filename()` | Sanitized version |
| `validate_*()` | Check data validity | `validate_github_url()` | Bool or raises exception |
| `format_*()` | Format data for display | `format_cost()` | Formatted string |

### Examples

```python
# GOOD: Clear intent
def get_api_config() -> tuple[str, str]:
    """Get API configuration from environment variables."""
    ...

def load_deptrac_report(path: str) -> dict | None:
    """Load and parse deptrac report from file."""
    ...

def generate_markdown(data: dict) -> str:
    """Generate markdown documentation from analysis data."""
    ...

# AVOID: Ambiguous naming
def config():  # Too vague - get? load? create?
    ...

def process_file(path):  # What does "process" mean exactly?
    ...
```

---

## Error Handling Strategy

### When to Return Optional[T] vs Raise Exceptions

**Return `Optional[T]` (or `None`) when:**
- The failure is expected and recoverable
- The caller can reasonably handle the None case
- The operation is a query or lookup that might not find results
- Missing data is a valid state (not an error)

```python
def load_deptrac_report(path: str) -> dict | None:
    """Load deptrac report; returns None if file doesn't exist."""
    if not Path(path).exists():
        logger.warning(f"Deptrac report not found: {path}")
        return None

    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in deptrac report: {e}")
        return None
```

**Raise exceptions when:**
- The failure represents a programming error or invalid state
- The caller cannot reasonably continue without the data
- The error requires immediate attention
- Configuration or security violations occur

```python
def validate_github_url(url: str) -> str:
    """Validate GitHub URL; raises ValueError if invalid."""
    if not isinstance(url, str) or not url:
        raise ValueError("GitHub URL must be a non-empty string")

    if ';' in url or '&' in url:
        raise ValueError("Invalid GitHub URL: contains suspicious characters")

    return url
```

### Specific Exception Types

**Always use specific exception types instead of generic `Exception`:**

| Situation | Exception Type |
|-----------|---------------|
| Invalid JSON | `json.JSONDecodeError` |
| Type mismatch | `TypeError` |
| Invalid value | `ValueError` |
| File not found | `FileNotFoundError` |
| Permission denied | `PermissionError` |
| File I/O errors | `IOError` or `OSError` |
| Network requests | `requests.exceptions.RequestException` |
| Timeout | `subprocess.TimeoutExpired` or `requests.exceptions.Timeout` |

```python
# GOOD: Specific exception handling
try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    logger.warning(f"Failed to parse JSON: {e}")
    return None

# AVOID: Generic exception handling
try:
    data = json.loads(content)
except Exception:  # Too broad!
    pass
```

### Logging Exceptions

**All exception handlers must log the exception:**

```python
# Minimum: Log at debug level if truly expected
try:
    optional_config = load_optional_config()
except FileNotFoundError as e:
    logger.debug(f"Optional config not found: {e}")
    optional_config = {}

# Standard: Log at warning level for recoverable errors
try:
    data = parse_response(response)
except ValueError as e:
    logger.warning(f"Failed to parse response: {e}")
    return None

# Critical: Log at error level for serious issues
try:
    result = call_critical_api()
except requests.exceptions.RequestException as e:
    logger.error(f"Critical API call failed: {e}")
    raise
```

### Never Suppress Exceptions Silently

```python
# BAD: Silent failure
try:
    risky_operation()
except Exception:
    pass  # What happened? Why did it fail?

# GOOD: Log and document
try:
    risky_operation()
except SpecificException as e:
    logger.debug(f"Operation failed (expected): {e}")
    # Continue with fallback behavior
```

### Custom Exception Classes

For domain-specific errors, create custom exceptions:

```python
class FlowscribeError(Exception):
    """Base exception for Flowscribe errors."""
    pass

class AnalysisError(FlowscribeError):
    """Raised when analysis cannot be completed."""
    pass

class ConfigurationError(FlowscribeError):
    """Raised when configuration is invalid."""
    pass

# Usage
def analyze_project(path: str) -> dict:
    if not Path(path).exists():
        raise AnalysisError(f"Project directory not found: {path}")
    ...
```

---

## Type Hints

### Requirements

All public functions **must** have type hints for:
- All parameters
- Return values

```python
from typing import Dict, List, Optional, Tuple
from pathlib import Path

def sanitize_filename(name: str) -> str:
    """Sanitize a filename or path component."""
    return re.sub(r'[^a-zA-Z0-9._-]', '_', name)

def read_project_files(
    project_dir: str,
    max_file_size: int = 50_000
) -> Dict[str, str]:
    """Read relevant project files for context analysis."""
    ...

def load_deptrac_report(path: str) -> Optional[Dict]:
    """Load deptrac report; returns None if not found."""
    ...
```

### Modern Type Hint Syntax (Python 3.10+)

Prefer modern union syntax where available:

```python
# Modern (Python 3.10+)
def process_data(data: dict | None) -> list[str]:
    ...

# Legacy (for compatibility)
from typing import Dict, List, Optional

def process_data(data: Optional[Dict]) -> List[str]:
    ...
```

### Complex Types

```python
from typing import Callable, TypedDict

class ComponentData(TypedDict):
    name: str
    purpose: str
    file_path: str

def transform_components(
    components: List[ComponentData],
    transformer: Callable[[ComponentData], ComponentData]
) -> List[ComponentData]:
    ...
```

---

## Function Length Guidelines

### Maximum Function Length

**Target:** Functions should be **50 lines or fewer** (excluding docstrings and blank lines).

**Why:** Shorter functions are:
- Easier to understand and test
- More maintainable
- Easier to reuse
- Less likely to have bugs

### Refactoring Long Functions

When a function exceeds 50 lines:

1. **Extract helper functions** for distinct sub-tasks
2. **Use meaningful names** that describe what each helper does
3. **Keep helpers close** to their calling function if they're single-use
4. **Make helpers public** if they might be reused elsewhere

```python
# BEFORE: Long function (90+ lines)
def generate_deptrac_config_with_llm(project_dir, project_name, domain, repo_url, llm_client):
    """Generate deptrac.yaml configuration using LLM."""
    logger.info("\n📊 Analyzing project structure...")

    # Get directory structure (15 lines)
    structure = get_directory_tree(project_dir, max_depth=3)

    # Count PHP files (20 lines)
    php_files = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'vendor'}]
        for file in files:
            if file.endswith('.php'):
                php_files.append(os.path.join(root, file))

    logger.info(f"  Found {len(php_files)} PHP files")

    # Build prompt (50+ lines)
    prompt = f"""Analyze this PHP project..."""

    # Call LLM (20+ lines)
    result = llm_client.call(prompt)
    ...

# AFTER: Refactored into smaller functions
def generate_deptrac_config_with_llm(
    project_dir: str,
    project_name: str,
    domain: str,
    repo_url: str,
    llm_client: LLMClient
) -> Tuple[bool, Optional[str], Dict]:
    """Generate deptrac.yaml configuration using LLM."""
    logger.info("\n📊 Analyzing project structure...")

    structure = get_directory_tree(project_dir, max_depth=3)
    php_files = count_php_files(project_dir)

    logger.info(f"  Found {len(php_files)} PHP files")

    prompt = build_deptrac_prompt(project_name, domain, repo_url, structure, php_files)

    success, yaml_content, metrics = call_llm_for_deptrac_config(llm_client, prompt, project_dir)

    return success, yaml_content, metrics


def count_php_files(project_dir: str) -> List[str]:
    """Count PHP files in project directory, excluding vendor and tests."""
    php_files = []
    excluded_dirs = {'.git', 'node_modules', 'vendor', '.venv'}

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            if file.endswith('.php'):
                php_files.append(os.path.join(root, file))

    return php_files


def build_deptrac_prompt(
    project_name: str,
    domain: str,
    repo_url: str,
    structure: str,
    php_files: List[str]
) -> str:
    """Build LLM prompt for deptrac configuration generation."""
    return f"""Analyze this PHP project and generate a deptrac.yaml configuration file.

PROJECT INFORMATION:
- Name: {project_name}
- Domain: {domain}
- Repository: {repo_url}
- PHP Files: {len(php_files)}

DIRECTORY STRUCTURE:
{structure}

...
"""
```

---

## Logging Practices

### Structured Logging

Always use the logger module instead of `print()`:

```python
from logger import setup_logger

logger = setup_logger(__name__)

# GOOD: Using logger
logger.info("Loading configuration...")
logger.warning("Configuration file not found, using defaults")
logger.error("Failed to connect to API")
logger.debug("Processing 1500 files")

# AVOID: Using print
print("Loading configuration...")  # No timestamp, level, or structured format
```

### Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Detailed diagnostic information | `logger.debug(f"Processing file: {filename}")` |
| `INFO` | General informational messages | `logger.info("Analysis complete")` |
| `WARNING` | Unexpected but recoverable issues | `logger.warning("Using default config")` |
| `ERROR` | Serious problems | `logger.error("API call failed")` |
| `CRITICAL` | System-breaking errors | `logger.critical("Database corrupted")` |

### Debug Mode Support

All scripts should support a `--debug` flag:

```python
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
args = parser.parse_args()

if args.debug:
    from logger import set_debug_mode
    set_debug_mode(logger, debug=True)
```

---

## Security Best Practices

### Path Validation

Always validate and sanitize file paths:

```python
from pathlib import Path

def validate_project_path(path_str: str) -> Path:
    """Validate project directory path to prevent directory traversal."""
    # Convert to Path and resolve to absolute
    path = Path(path_str).resolve()

    # Check for directory traversal attempts
    if '..' in Path(path_str).parts:
        raise ValueError("Invalid path: directory traversal detected")

    # Verify path exists
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    return path
```

### Command Execution

Never use `shell=True` with `subprocess.run()`:

```python
# BAD: Vulnerable to command injection
subprocess.run(f"git clone {url}", shell=True)

# GOOD: Safe command execution
subprocess.run(['git', 'clone', url], shell=False)
```

### Input Sanitization

Validate all external inputs:

```python
def sanitize_model_name(model: str) -> str:
    """Validate model name to prevent injection attacks."""
    if not isinstance(model, str) or not model:
        raise ValueError("Model must be a non-empty string")

    # Allow only alphanumeric, hyphens, slashes, dots, underscores
    if not re.match(r'^[a-zA-Z0-9._/-]+$', model):
        raise ValueError(f"Invalid model name format: {model}")

    return model
```

---

## Code Review Checklist

Before submitting code, verify:

- [ ] All public functions have type hints
- [ ] No function exceeds 50 lines
- [ ] All exception handlers are specific (no bare `except Exception:`)
- [ ] All exceptions are logged
- [ ] Using `logger.*()` instead of `print()`
- [ ] Function names follow naming conventions
- [ ] File paths are validated and sanitized
- [ ] No `shell=True` in subprocess calls
- [ ] Docstrings present for all public functions
- [ ] Tests written for new functionality

---

## References

- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

---

**Document Version History:**

- v1.0 (2025-11-15): Initial version covering naming conventions, error handling, type hints, and security practices
