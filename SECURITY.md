# Security Policy

## Overview

This document outlines the security measures implemented in Flowscribe and provides guidelines for secure usage and development.

## Security Fixes Implemented

### 1. Command Injection Prevention (CRITICAL)

**Issue**: The `run_command()` method in `flowscribe-analyze.py` used `subprocess.run()` with `shell=True`, which could allow command injection attacks.

**Fix**:
- Changed `subprocess.run()` to use list-based arguments without `shell=True`
- All command arguments are now passed as a list, preventing shell interpretation
- Added comprehensive documentation for the secure command execution pattern

**Location**: `scripts/flowscribe-analyze.py:321-345`

**Impact**: Prevents malicious users from executing arbitrary commands through crafted inputs.

### 2. Path Traversal Protection

**Issue**: Insufficient validation of file paths could allow directory traversal attacks.

**Fixes**:

#### sanitize_output_files.py
- Added `.resolve()` to convert paths to absolute paths
- Validates that paths don't contain parent directory references (`..`)
- Raises `ValueError` if directory traversal is detected

**Location**: `scripts/sanitize_output_files.py:193-202`

#### flowscribe-analyze.py
- Validates workspace and output directories on initialization
- Resolves all paths to absolute paths
- Prevents path traversal through validation checks

**Location**: `scripts/flowscribe-analyze.py:257-263`

**Impact**: Prevents unauthorized access to files outside intended directories.

### 3. Input Validation Enhancement

**Issue**: GitHub URL validation was insufficient and could potentially be exploited.

**Fix**:
- Added validation for suspicious characters (`;`, `&`, `|`, `` ` ``, `$`, newlines)
- Validates owner and repository names against GitHub naming conventions
- Comprehensive error messages for invalid inputs
- Type checking for input parameters

**Location**: `scripts/flowscribe-analyze.py:295-342`

**Impact**: Prevents injection attacks through crafted GitHub URLs.

## Security Best Practices

### For Users

1. **API Key Management**
   - Never commit your `.env` file to version control
   - Store API keys in environment variables or secure vaults
   - Rotate API keys regularly
   - Use `.env.example` as a template

2. **Input Validation**
   - Only provide trusted GitHub repository URLs
   - Verify workspace and output directories before running scripts
   - Avoid using special characters in directory paths

3. **File Permissions**
   - Ensure output directories have appropriate permissions
   - Review generated files before sharing
   - Be cautious when running scripts with elevated privileges

### For Developers

1. **Command Execution**
   - NEVER use `shell=True` with `subprocess.run()`
   - Always pass commands as lists: `['command', 'arg1', 'arg2']`
   - Validate all user inputs before using them in commands
   - Use `shlex.quote()` if you must construct shell commands

2. **File Operations**
   - Always use `Path.resolve()` to get absolute paths
   - Validate paths don't contain `..` or other traversal attempts
   - Use `Path` objects from `pathlib` instead of string concatenation
   - Never trust user-provided file paths without validation

3. **Input Validation**
   - Validate all external inputs (URLs, file paths, API responses)
   - Use allowlists rather than denylists when possible
   - Sanitize data before using in system calls or file operations
   - Implement type checking for function parameters

4. **API Security**
   - Use environment variables for API keys
   - Implement rate limiting for API calls
   - Validate API responses before processing
   - Use HTTPS for all API communications

## Reporting Security Vulnerabilities

If you discover a security vulnerability in Flowscribe, please report it by:

1. **DO NOT** open a public GitHub issue
2. Contact the maintainers directly via GitHub security advisories
3. Provide detailed information about the vulnerability
4. Include steps to reproduce if possible

We will respond to security reports within 48 hours and provide updates on the fix timeline.

## Security Audit History

### 2025-11-15: Second Comprehensive Security Audit

**Conducted by**: Automated security review and manual code analysis

**Critical Vulnerabilities Found and Fixed**:

#### 1. Path Traversal Vulnerabilities (CRITICAL) - **FIXED**
Affected 6 Python scripts that accepted file path arguments without proper validation:
- `c4-level1-generator.py` - Added path validation for `project_dir` and `output` arguments
- `c4-level2-generator.py` - Added path validation for `deptrac_json` and `output` arguments
- `c4-level3-generator.py` - Added path validation for `deptrac_report`, `project_dir`, and `output` arguments
- `c4-level4-generator.py` - Added path validation for `project_dir`, `deptrac_json`, and `output_dir` arguments
- `c4-architecture-review.py` - Added path validation for `output_dir` argument
- `create-master-index.py` - Added path validation for `output` argument

**Fixes Applied**:
- All path arguments now use `Path.resolve()` to convert to absolute paths
- All scripts check for `'..'` in path components to prevent directory traversal
- Clear error messages for invalid paths
- Paths are validated before any file operations

**Lines Fixed**: Multiple locations across all 6 files

#### 2. TOCTOU Race Conditions (HIGH) - **FIXED**
Fixed Time-of-Check Time-of-Use vulnerabilities in file operations:
- `sanitize_output_files.py:43-66` - Refactored `apply_renames()` to use atomic operations with try/except instead of checking `exists()` before file moves

**Fix Applied**:
- Changed from check-then-act pattern to atomic operations
- Files are now moved directly with exception handling
- Prevents symlink attacks and race conditions

#### 3. Missing Input Validation (MEDIUM) - **FIXED**
- `flowscribe_utils.py:156-169` - Added model name validation in LLMClient.__init__()
  - Validates model name is a non-empty string
  - Checks model name against regex pattern to allow only safe characters
  - Prevents potential injection through model parameter

#### 4. Unlimited Response Size (MEDIUM) - **FIXED**
- `flowscribe_utils.py:204-207` - Added response size limit in LLMClient.call()
  - Maximum response size set to 10MB
  - Prevents memory exhaustion from unexpectedly large API responses
  - Logs warning if response is truncated

**Security Improvements**:
- ✅ All path inputs now properly validated
- ✅ All file operations use atomic patterns
- ✅ Model names validated against injection
- ✅ Response sizes limited to prevent DoS
- ✅ Comprehensive error handling added

**Status**: All CRITICAL, HIGH, and MEDIUM vulnerabilities have been addressed.

### 2025-11-15: Initial Security Audit

**Conducted by**: Automated security review

**Findings**:
- ✅ No hardcoded secrets or API keys found
- ⚠️ Command injection vulnerability in `flowscribe-analyze.py` - **FIXED**
- ⚠️ Path traversal risks in file operations - **FIXED**
- ⚠️ Insufficient input validation for GitHub URLs - **FIXED**
- ✅ No use of dangerous functions (`eval`, `exec`)
- ✅ Proper API key management using environment variables

**Status**: All critical vulnerabilities from initial audit have been addressed.

## Security Checklist for Pull Requests

Before submitting a pull request, ensure:

- [ ] No hardcoded secrets or API keys
- [ ] No use of `shell=True` in subprocess calls
- [ ] All file paths are validated and resolved
- [ ] User inputs are properly validated and sanitized
- [ ] No use of `eval()` or `exec()` on untrusted data
- [ ] API keys are loaded from environment variables
- [ ] Error messages don't leak sensitive information
- [ ] Dependencies are up to date and from trusted sources

## Dependencies Security

Regularly update dependencies to patch known vulnerabilities:

```bash
pip install --upgrade -r requirements.txt
```

Monitor dependencies for security advisories:
- Use tools like `pip-audit` or `safety` to scan dependencies
- Review security advisories for `requests`, `openrouter`, and other dependencies
- Keep Python version updated to the latest stable release

## Compliance

Flowscribe follows security best practices aligned with:
- OWASP Top 10 security risks
- CWE (Common Weakness Enumeration) guidelines
- Secure coding standards for Python

## License

This security policy is part of the Flowscribe project and is licensed under the MIT License.
