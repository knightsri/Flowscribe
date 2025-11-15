# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Error message sanitizer (`error_sanitizer.py`) to prevent leaking sensitive information in logs
- Configuration validator (`config_validator.py`) with comprehensive validation functions
- `CONTRIBUTING.md` with code style, testing, and PR guidelines
- `CHANGELOG.md` following Keep a Changelog format
- Model names extracted to constants (`models.py`) with LLMModel enum
- Configuration schema (`config_schema.py`) using dataclasses

### Changed
- **BREAKING**: Removed `--api-key` CLI argument from all scripts - API key must now be provided via `OPENROUTER_API_KEY` environment variable only
- Updated all error messages to only reference environment variables for API keys

### Security
- Enhanced API key security by requiring environment variable usage only
- Added comprehensive path validation to prevent directory traversal attacks
- Added input sanitization for all external inputs
- Improved error message sanitization to prevent information disclosure

## [1.0.0] - 2025-11-15

### Added
- Automated C4 Level 1-4 document generation
- AI-driven architecture review using premium LLMs (Sonnet 4.5, Xi Fast Code)
- Cost-aware metrics and usage validation (OpenRouter accounting)
- Provenance stamping and audit logging
- Extensible Mermaid-based visualization with Deptrac layer integration
- Canonical metrics schema (v1.0) across all scripts for uniform cost tracking
- Usage-first cost tracking approach using OpenRouter API usage data
- Comprehensive security improvements:
  - Input validation and sanitization
  - Path traversal prevention
  - Command injection protection
  - Secure subprocess handling
  - No shell=True usage
- Coding standards documentation (`CODING_STANDARDS.md`)
- Comprehensive test suite with unit and integration tests
- Docker and docker-compose support
- GitHub Actions CI/CD workflows
- Security policy (`SECURITY.md`)
- Task tracking system (`Task-List.md`)

### Changed
- Migrated to usage-first cost tracking (OpenRouter `usage.cost` as source of truth)
- Improved error handling with specific exception types
- Enhanced logging practices with structured logging
- Refactored long functions into smaller, testable units

### Fixed
- Critical security vulnerabilities across all Python scripts
- Path validation issues
- Input sanitization gaps
- Subprocess security issues

### Security
- Comprehensive security audit completed
- All critical security issues resolved
- Security best practices documented in `CODING_STANDARDS.md`

## Project Versioning

### Version Format
- `MAJOR.MINOR.PATCH` (e.g., 1.2.3)

### When to Increment
- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)

### Release Process
1. Update version in relevant files
2. Update CHANGELOG.md with release date
3. Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub release with changelog excerpt

## Categories

### Added
For new features.

### Changed
For changes in existing functionality.

### Deprecated
For soon-to-be removed features.

### Removed
For now removed features.

### Fixed
For any bug fixes.

### Security
In case of vulnerabilities.

---

[Unreleased]: https://github.com/knightsri/Flowscribe/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/knightsri/Flowscribe/releases/tag/v1.0.0
