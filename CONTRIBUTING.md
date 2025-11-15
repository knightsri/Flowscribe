# Contributing to Flowscribe

Thank you for your interest in contributing to Flowscribe! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Assume good intentions
- Respect differing viewpoints and experiences

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Flowscribe.git
   cd Flowscribe
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/knightsri/Flowscribe.git
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Docker (optional, for containerized development)

### Local Development

1. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

4. **Run tests to verify setup**:
   ```bash
   pytest tests/
   ```

### Docker Development

```bash
docker-compose up -d
docker-compose exec flowscribe bash
```

## Code Style Guidelines

Flowscribe follows strict coding standards documented in [CODING_STANDARDS.md](docs/CODING_STANDARDS.md). Key points:

### Python Style

- **PEP 8 compliance**: Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- **Type hints**: All public functions must have type hints
- **Docstrings**: Use Google-style docstrings for all public functions
- **Line length**: Maximum 100 characters per line
- **Imports**: Use absolute imports, group by standard library, third-party, local

### Function Naming

Use descriptive prefixes that indicate function behavior:

- `get_*()` - Retrieve existing data from memory/state
- `load_*()` - Read data from file or external source
- `generate_*()` - Create new content (especially with LLM)
- `build_*()` - Construct/assemble from existing data
- `parse_*()` - Parse and transform data format
- `sanitize_*()` - Clean/validate data
- `validate_*()` - Check data validity
- `format_*()` - Format data for display

### Error Handling

- Use specific exception types (not generic `Exception`)
- Always log exceptions
- Return `Optional[T]` for expected failures, raise exceptions for unexpected errors
- Never suppress exceptions silently

### Security Best Practices

- **Never** use `shell=True` with `subprocess.run()`
- Always validate and sanitize file paths
- Validate all external inputs
- Use the `error_sanitizer` module for logging errors that might contain sensitive data
- Use the `config_validator` module for validating configuration values

### Example Code

```python
from typing import Optional, Dict
from pathlib import Path
from logger import setup_logger

logger = setup_logger(__name__)

def load_config_file(path: str) -> Optional[Dict]:
    """
    Load configuration from JSON file.

    Args:
        path: Path to configuration file

    Returns:
        Parsed configuration dictionary, or None if file doesn't exist

    Raises:
        ValueError: If JSON is malformed
    """
    config_path = Path(path)

    if not config_path.exists():
        logger.warning(f"Config file not found: {path}")
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        raise ValueError(f"Malformed config file: {path}")
```

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scripts --cov-report=html

# Run specific test file
pytest tests/unit/test_flowscribe_utils.py

# Run tests matching a pattern
pytest -k "test_cost_tracker"
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names: `test_<function>_<scenario>_<expected_result>`
- Use fixtures for common test setup
- Mock external API calls

Example test:

```python
def test_sanitize_filename_removes_special_chars():
    """Test that sanitize_filename removes special characters"""
    from flowscribe_utils import sanitize_filename

    result = sanitize_filename("my/file:name*.txt")
    assert result == "my_file_name_.txt"
```

### Test Coverage

- Aim for 80%+ code coverage
- All new functions must have tests
- Critical paths (security, data validation) require 100% coverage

## Pull Request Process

### Before Submitting

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**:
   ```bash
   pytest
   ```

3. **Run linters**:
   ```bash
   # Check code style
   flake8 scripts/

   # Check type hints
   mypy scripts/
   ```

4. **Update documentation** if you've:
   - Added new features
   - Changed APIs
   - Modified configuration options

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat: add support for Gemini models`
- `fix: correct API key validation regex`
- `docs: update CONTRIBUTING.md with testing guidelines`
- `refactor: extract cost calculation to separate function`
- `test: add tests for error sanitizer`
- `chore: update dependencies`

### Creating the Pull Request

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub** with:
   - **Clear title** describing the change
   - **Description** explaining:
     - What problem does this solve?
     - How does it solve it?
     - Any breaking changes?
   - **Link related issues** using `Fixes #123` or `Relates to #456`
   - **Screenshots/output** if UI or output changed

3. **PR Checklist**:
   - [ ] Tests pass locally
   - [ ] Code follows style guidelines
   - [ ] Docstrings added/updated
   - [ ] Type hints present on all new functions
   - [ ] CHANGELOG.md updated (for notable changes)
   - [ ] Documentation updated if needed

### Review Process

- Maintainers will review your PR within 1-2 weeks
- Address feedback by pushing new commits
- Once approved, maintainers will merge your PR
- Your contribution will be included in the next release

## Reporting Issues

### Bug Reports

Use the GitHub issue tracker and include:

1. **Clear title** summarizing the bug
2. **Steps to reproduce**:
   ```
   1. Run command X
   2. With configuration Y
   3. See error Z
   ```
3. **Expected behavior**: What should happen?
4. **Actual behavior**: What actually happens?
5. **Environment**:
   - OS (Linux, macOS, Windows)
   - Python version
   - Flowscribe version
6. **Error messages** (sanitized to remove API keys)
7. **Relevant configuration** (sanitized)

### Security Issues

**Do not** open public issues for security vulnerabilities. Instead:

1. Email security concerns to the maintainers
2. Provide details about the vulnerability
3. Allow time for a fix before public disclosure

See [SECURITY.md](SECURITY.md) for details.

## Feature Requests

Feature requests are welcome! Please:

1. **Search existing issues** to avoid duplicates
2. **Describe the problem** you're trying to solve
3. **Propose a solution** (if you have one)
4. **Provide use cases** showing why this feature is valuable
5. **Consider implementation complexity** and project scope

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions/improvements

### Merging Strategy

- PRs are squash-merged to main branch
- Maintain a clean, linear history
- Main branch is always deployable

## Questions?

- **Documentation**: Check [README.md](README.md) and [docs/](docs/)
- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Search existing issues or create a new one

---

**Thank you for contributing to Flowscribe!** Your contributions help make architecture documentation better for everyone.
