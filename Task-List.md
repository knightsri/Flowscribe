# Flowscribe - Code Review Task List

**Generated:** 2025-11-14
**Based on:** Deep Code Review
**Total Estimated Effort:** 2-3 weeks

---

## 🎯 Current Status

**Currently Working On:**
- None (ready to start next task)

**Next Up:**
- [ ] **SEC-VERIFY: Verify Security Fixes** (Testing completed security work)
- [ ] **TEST-001: Set Up Testing Framework**
- [ ] **TEST-002: Install and Configure pytest**

**Recently Completed:**
- [x] **SEC-001: Fix Command Injection Vulnerability** (Completed: 2025-11-14)
- [x] **SEC-002: Sandbox LLM-Generated Code Execution** (Completed: 2025-11-14)
- [x] **SEC-003: Add Repository URL Validation** (Completed: 2025-11-14)

**Legend:**
- `[ ]` - Not started
- `[>]` - In progress (current task)
- `[x]` - Completed

---

## 🚨 CRITICAL PRIORITY (Fix Immediately)

**Estimated Effort:** 1-2 days

### Security Vulnerabilities

- [x] **SEC-001: Fix Command Injection Vulnerability** ✅ Completed 2025-11-14
  - **File:** `scripts/flowscribe-analyze.py:304-306`
  - **Issue:** `subprocess.run()` with `shell=True` is dangerous
  - **Action:** Change to `shell=False` and pass commands as list
  - **Example:**
    ```python
    # BEFORE (vulnerable):
    subprocess.run(cmd, shell=True, cwd=cwd)

    # AFTER (safe):
    subprocess.run(shlex.split(cmd), shell=False, cwd=cwd)
    ```
  - **Impact:** Prevents remote code execution
  - **Priority:** 🚨 CRITICAL

- [x] **SEC-002: Sandbox LLM-Generated Code Execution** ✅ Completed 2025-11-14
  - **File:** `scripts/flowscribe_utils.py:388-394`
  - **Issue:** Executes LLM-generated Python without proper sandboxing
  - **Current Mitigation:** 1KB truncation, 30s timeout (insufficient)
  - **Action:** Implement one of:
    - Option A: Run in isolated Docker container
    - Option B: Use RestrictedPython library
    - Option C: Disable code execution, require manual review
  - **Impact:** Prevents malicious code execution
  - **Priority:** 🚨 CRITICAL

- [x] **SEC-003: Add Repository URL Validation** ✅ Completed 2025-11-14
  - **File:** `scripts/flowscribe_utils.py:139-158`
  - **Issue:** No validation on repository URLs
  - **Action:** Add URL validation and sanitization
  - **Example:**
    ```python
    from urllib.parse import urlparse

    def validate_github_url(url):
        parsed = urlparse(url)
        if parsed.netloc not in ['github.com', 'www.github.com']:
            raise ValueError("Only GitHub URLs allowed")
        # Prevent path traversal
        if '..' in parsed.path:
            raise ValueError("Invalid path in URL")
        return url
    ```
  - **Impact:** Prevents directory traversal attacks
  - **Priority:** 🚨 CRITICAL

---

## ⚠️ HIGH PRIORITY (Fix Within 1 Week)

**Estimated Effort:** 3-5 days

### Security Verification

- [ ] **SEC-VERIFY: Verify Security Fixes**
  - **Action:** Test and verify all completed security fixes
  - **Test Cases:**
    - SEC-001: Test subprocess calls don't use shell=True
    - SEC-002: Verify RestrictedPython is in use for LLM-generated code
    - SEC-003: Test URL validation rejects invalid/malicious URLs
  - **Verification Steps:**
    ```bash
    # Test 1: Search for any remaining shell=True usage
    grep -r "shell=True" scripts/

    # Test 2: Verify RestrictedPython import exists
    grep -r "RestrictedPython" scripts/

    # Test 3: Test URL validation function
    python3 -c "from scripts.flowscribe_utils import validate_github_url; \
                validate_github_url('https://github.com/valid/repo')"
    ```
  - **Create:** Manual test cases document
  - **Priority:** ⚠️ HIGH

### Testing Infrastructure

- [ ] **TEST-001: Set Up Testing Framework**
  - **Action:** Create `tests/` directory structure
  - **Structure:**
    ```
    tests/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    │   ├── test_flowscribe_utils.py
    │   ├── test_cost_tracker.py
    │   └── test_context.py
    ├── integration/
    │   ├── test_c4_generators.py
    │   └── test_llm_client.py
    └── fixtures/
        ├── sample_deptrac_report.json
        └── sample_prompts/
    ```
  - **Priority:** ⚠️ HIGH

- [ ] **TEST-002: Install and Configure pytest**
  - **Action:** Add to requirements.txt:
    ```
    pytest==7.4.3
    pytest-cov==4.1.0
    pytest-mock==3.12.0
    requests-mock==1.11.0
    ```
  - **Priority:** ⚠️ HIGH

- [ ] **TEST-003: Write Unit Tests for Core Utilities**
  - **Files to test:**
    - `sanitize_mermaid_diagram()` - flowscribe_utils.py:1466-1555
    - `CostTracker.calculate_cost()` - flowscribe_utils.py:591-595
    - `FlowscribeContext.validate_and_setup()` - flowscribe_utils.py:160-247
    - `mermaid_safe_id()` - flowscribe_utils.py:861-882
    - `sanitize_filename()` - flowscribe_utils.py:814-854
  - **Target:** 80%+ code coverage
  - **Priority:** ⚠️ HIGH

- [ ] **TEST-004: Write Integration Tests**
  - **Test Cases:**
    - LLM API calls (with mocking)
    - Deptrac execution
    - End-to-end C4 L1 generation
    - Context initialization and validation
  - **Priority:** ⚠️ HIGH

- [ ] **TEST-004-VERIFY: Run and Validate All Tests**
  - **Action:** Execute test suite and verify coverage
  - **Verification Steps:**
    ```bash
    # Run all tests with coverage
    pytest tests/ -v --cov=scripts --cov-report=term-missing

    # Verify coverage is ≥80%
    pytest tests/ --cov=scripts --cov-fail-under=80

    # Run specific test categories
    pytest tests/unit/ -v
    pytest tests/integration/ -v
    ```
  - **Success Criteria:**
    - All tests pass
    - Code coverage ≥80%
    - No test warnings or errors
  - **Priority:** ⚠️ HIGH

- [ ] **TEST-005: Add CI/CD Pipeline**
  - **Action:** Create `.github/workflows/ci.yml`
  - **Jobs:**
    - Linting (pylint, black)
    - Unit tests
    - Integration tests (with mocked LLM)
    - Security scanning (bandit)
  - **Priority:** ⚠️ HIGH

- [ ] **TEST-005-VERIFY: Verify CI/CD Pipeline**
  - **Action:** Test CI/CD pipeline is working correctly
  - **Verification Steps:**
    ```bash
    # Create a test branch and push to trigger CI
    git checkout -b test/ci-verification
    echo "# CI Test" >> README.md
    git add README.md
    git commit -m "Test CI pipeline"
    git push origin test/ci-verification

    # Check GitHub Actions UI for results
    # Verify all jobs pass: linting, tests, security scanning
    ```
  - **Success Criteria:**
    - All CI jobs complete successfully
    - Linting passes with no errors
    - All tests pass
    - Security scan completes with no critical issues
  - **Priority:** ⚠️ HIGH

### Dependencies & Environment

- [ ] **DEP-001: Create requirements.txt**
  - **Action:** Create `requirements.txt` with pinned versions:
    ```
    # Core dependencies
    pyyaml==6.0.1
    requests==2.31.0

    # Analysis tools (for Docker only)
    pyan3==1.2.0
    pylint==2.17.4
    networkx==3.1
    matplotlib==3.7.2
    pydeps==1.12.8

    # Development dependencies (separate file)
    # See requirements-dev.txt
    ```
  - **Priority:** ⚠️ HIGH

- [ ] **DEP-002: Create requirements-dev.txt**
  - **Action:** Create separate dev requirements:
    ```
    -r requirements.txt

    # Testing
    pytest==7.4.3
    pytest-cov==4.1.0
    pytest-mock==3.12.0
    requests-mock==1.11.0

    # Code quality
    black==23.12.1
    pylint==2.17.4
    mypy==1.7.1
    bandit==1.7.5

    # Documentation
    sphinx==7.2.6
    ```
  - **Priority:** ⚠️ HIGH

- [ ] **DEP-003: Pin npm Package Versions**
  - **File:** `Dockerfile:40-56`
  - **Action:** Pin exact versions:
    ```dockerfile
    RUN npm install -g \
        madge@6.1.0 \
        dependency-cruiser@15.5.0 \
        jsdoc@4.0.2 \
        @mermaid-js/mermaid-cli@10.6.1
    ```
  - **Priority:** ⚠️ HIGH

- [ ] **DEP-004: Include Lock Files in Version Control**
  - **Action:** Remove from .gitignore:
    ```
    # Remove this line:
    # composer.lock
    ```
  - **Action:** Generate and commit:
    - `package-lock.json` (npm)
    - Keep `composer.lock` (PHP)
  - **Priority:** ⚠️ HIGH

- [ ] **DEP-VERIFY: Verify Dependencies Installation**
  - **Action:** Test all dependencies are correctly installed and working
  - **Verification Steps:**
    ```bash
    # Test Python dependencies
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    python3 -c "import yaml, requests; print('Python deps OK')"

    # Test npm packages
    madge --version
    dependency-cruiser --version
    mmdc --version

    # Verify lock files exist
    test -f package-lock.json && echo "npm lock file exists"

    # Run a simple import test for all major modules
    python3 -c "
    from scripts.flowscribe_utils import FlowscribeContext, CostTracker
    print('All Python imports successful')
    "
    ```
  - **Success Criteria:**
    - All dependencies install without errors
    - Version checks return expected versions
    - Lock files are committed
    - No dependency conflicts
  - **Priority:** ⚠️ HIGH

### Logging & Observability

- [ ] **LOG-001: Replace print() with logging Module**
  - **Files to update:** All Python scripts
  - **Action:** Create `scripts/logger.py`:
    ```python
    import logging
    import sys

    def setup_logger(name, level=logging.INFO):
        """Setup structured logger"""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Format
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)8s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger
    ```
  - **Priority:** ⚠️ HIGH

- [ ] **LOG-002: Update All Scripts to Use Logger**
  - **Example conversion:**
    ```python
    # BEFORE:
    print("✓ Loading configuration...")

    # AFTER:
    from logger import setup_logger
    logger = setup_logger(__name__)
    logger.info("Loading configuration...")
    ```
  - **Priority:** ⚠️ HIGH

- [ ] **LOG-003: Add Debug Mode Support**
  - **Action:** Add `--debug` flag to all scripts
  - **Example:**
    ```python
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')

    if args.debug:
        logger.setLevel(logging.DEBUG)
    ```
  - **Priority:** ⚠️ HIGH

- [ ] **LOG-VERIFY: Verify Logging Implementation**
  - **Action:** Test logging is working correctly across all scripts
  - **Verification Steps:**
    ```bash
    # Test logger module exists
    test -f scripts/logger.py && echo "Logger module exists"

    # Verify no print() statements remain (except in specific cases)
    ! grep -r "print(" scripts/*.py | grep -v "# print" | grep -v "__name__"

    # Test debug mode on a sample script
    python3 scripts/flowscribe-analyze.py --help | grep -q "debug"

    # Run a script and verify logging output format
    # Should see timestamps and log levels
    python3 scripts/flowscribe-analyze.py --debug 2>&1 | head -5
    ```
  - **Success Criteria:**
    - Logger module exists and imports correctly
    - All print() replaced with logger calls (except special cases)
    - Debug flag available in all main scripts
    - Log output shows proper formatting with timestamps and levels
  - **Priority:** ⚠️ HIGH

---

## 💡 MEDIUM PRIORITY (Technical Debt)

**Estimated Effort:** 1-2 weeks

### Code Quality Improvements

- [ ] **CODE-001: Extract Magic Numbers to Constants**
  - **Files:**
    - `scripts/c4-level1-generator.py:87` - max_file_size, max_files
    - `scripts/c4-level2-generator.py:135` - max_rows
    - `scripts/flowscribe_utils.py:316` - truncation size
  - **Action:** Create `scripts/constants.py`:
    ```python
    # File processing limits
    MAX_FILE_SIZE = 50_000
    MAX_FILES_TO_ANALYZE = 25

    # LLM generated code safety
    MAX_GENERATED_SCRIPT_SIZE = 1024
    SCRIPT_EXECUTION_TIMEOUT = 30

    # Display limits
    MAX_VIOLATION_ROWS = 100
    MAX_FILES_PER_CELL = 3
    ```
  - **Priority:** 💡 MEDIUM

- [ ] **CODE-002: Refactor Long Functions**
  - **Functions to refactor:**
    - `sanitize_mermaid_diagram()` - flowscribe_utils.py:1466-1555 (90 lines)
    - `generate_deptrac_config_with_llm()` - flowscribe-analyze.py:84-254 (170 lines)
    - `FlowscribeAnalyzer.run_analysis()` - likely >100 lines
  - **Action:** Break into smaller, testable functions (max 50 lines)
  - **Priority:** 💡 MEDIUM

- [ ] **CODE-003: Add Type Hints to All Public Functions**
  - **Action:** Add type hints systematically:
    ```python
    from typing import Dict, List, Optional, Tuple

    def sanitize_filename(name: str) -> str:
        """Sanitize a filename or path component."""
        # ...
    ```
  - **Tools:** Use mypy for type checking
  - **Priority:** 💡 MEDIUM

- [ ] **CODE-003-VERIFY: Verify Type Hints with mypy**
  - **Action:** Run mypy type checker on all Python files
  - **Verification Steps:**
    ```bash
    # Install mypy if not already installed
    pip install mypy==1.7.1

    # Run mypy on all scripts
    mypy scripts/*.py --strict

    # Check for type coverage
    mypy scripts/*.py --strict --html-report mypy-report

    # Verify key functions have type hints
    grep -A 5 "^def " scripts/flowscribe_utils.py | grep -E "(->|:.*=)"
    ```
  - **Success Criteria:**
    - mypy runs with no errors in strict mode
    - All public functions have complete type hints
    - Type coverage ≥90%
  - **Priority:** 💡 MEDIUM

- [ ] **CODE-004: Fix Generic Exception Handling**
  - **Files:** All Python scripts
  - **Action:** Replace bare `except Exception:` with specific exceptions
  - **Example:**
    ```python
    # BEFORE:
    try:
        data = json.loads(content)
    except Exception:
        pass

    # AFTER:
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return None
    ```
  - **Priority:** 💡 MEDIUM

- [ ] **CODE-005: Remove Silent Failures**
  - **File:** `scripts/flowscribe_utils.py:1371-1372`
  - **Action:** Log all exceptions at minimum:
    ```python
    except Exception as e:
        logger.debug(f"Failed to detect version: {e}")
        # Continue with fallback
    ```
  - **Priority:** 💡 MEDIUM

- [ ] **CODE-006: Standardize Error Handling Strategy**
  - **Action:** Document error handling patterns:
    - Functions return `Optional[T]` for recoverable errors
    - Functions raise exceptions for unrecoverable errors
    - Use custom exceptions for domain errors
  - **Create:** `docs/CODING_STANDARDS.md`
  - **Priority:** 💡 MEDIUM

- [ ] **CODE-007: Clean Up Commented Code**
  - **Files:**
    - `docker-compose.yml:1` - commented version
    - `docker-compose.yml:19` - commented alternative config
  - **Action:** Remove or document in comments why it's there
  - **Priority:** 💡 MEDIUM

- [ ] **CODE-008: Establish Naming Conventions**
  - **Issue:** Inconsistent function names
    - `get_api_config()` vs `get_context()` vs `get_file_patterns_from_llm()`
  - **Action:** Document and enforce conventions:
    - `get_*()` - retrieve existing data
    - `load_*()` - read from file/external source
    - `generate_*()` - create new content (especially with LLM)
    - `build_*()` - construct from existing data
  - **Priority:** 💡 MEDIUM

### Security Improvements

- [ ] **SEC-004: Remove API Keys from CLI Arguments**
  - **Files:** All generator scripts
  - **Action:** Accept API keys only via environment variables
  - **Remove:** `--api-key` argument option
  - **Priority:** 💡 MEDIUM

- [ ] **SEC-005: Sanitize Error Messages**
  - **Action:** Create error message sanitizer:
    ```python
    def sanitize_error_message(error: Exception, debug: bool = False) -> str:
        """Sanitize error message to avoid exposing internal paths"""
        if debug:
            return str(error)

        msg = str(error)
        # Remove absolute paths
        msg = re.sub(r'/[^\s]+/workspace/[^\s]+', '<project_path>', msg)
        # Remove API keys
        msg = re.sub(r'sk-[a-zA-Z0-9-]+', '<api_key>', msg)
        return msg
    ```
  - **Priority:** 💡 MEDIUM

- [ ] **SEC-006: Add Configuration Validation**
  - **Action:** Create `scripts/config_validator.py`:
    ```python
    def validate_api_key(key: str) -> bool:
        """Validate OpenRouter API key format"""
        return key.startswith('sk-or-v1-') and len(key) > 20

    def validate_model_name(model: str) -> bool:
        """Validate model name format"""
        return '/' in model and len(model.split('/')) == 2

    def validate_cost_config(input_cost: float, output_cost: float) -> bool:
        """Validate cost configuration"""
        return input_cost > 0 and output_cost > 0
    ```
  - **Priority:** 💡 MEDIUM

- [ ] **SEC-VERIFY-2: Verify Additional Security Improvements**
  - **Action:** Test security improvements (SEC-004, SEC-005, SEC-006)
  - **Verification Steps:**
    ```bash
    # Test 1: Verify no --api-key argument in scripts
    ! grep -r "add_argument.*--api-key" scripts/

    # Test 2: Verify error message sanitization
    python3 -c "
    from scripts.flowscribe_utils import sanitize_error_message
    msg = sanitize_error_message(Exception('/workspace/secret/file.py'))
    assert '/workspace' not in msg
    print('Error sanitization OK')
    "

    # Test 3: Verify configuration validation exists
    test -f scripts/config_validator.py && echo "Config validator exists"
    python3 -c "
    from scripts.config_validator import validate_api_key, validate_model_name
    assert validate_api_key('sk-or-v1-abcdef123456789012345')
    assert validate_model_name('anthropic/claude-sonnet-4')
    print('Config validation OK')
    "
    ```
  - **Success Criteria:**
    - No CLI arguments accept API keys
    - Error messages are properly sanitized
    - Configuration validation functions work correctly
  - **Priority:** 💡 MEDIUM

### Documentation

- [ ] **DOC-001: Add LICENSE File**
  - **Action:** Add MIT license (per README.md:107)
  - **File:** Create `LICENSE`
  - **Priority:** 💡 MEDIUM

- [ ] **DOC-002: Add CONTRIBUTING.md**
  - **Content:**
    - Code style guidelines
    - How to run tests
    - How to submit PRs
    - Development setup
  - **Priority:** 💡 MEDIUM

- [ ] **DOC-003: Add CHANGELOG.md**
  - **Format:** Keep a Changelog format
  - **Sections:** Unreleased, Versions with Added/Changed/Fixed/Removed
  - **Priority:** 💡 MEDIUM

- [ ] **DOC-004: Create CODING_STANDARDS.md**
  - **Content:**
    - Error handling patterns
    - Naming conventions
    - Type hint requirements
    - Documentation standards
  - **Priority:** 💡 MEDIUM

- [ ] **DOC-005: Document Project Clone Location**
  - **Issue:** `Core/` directory is untracked
  - **Action:** Add to README:
    ```markdown
    ## Directory Structure

    - `projects/` - Clone target repositories here (gitignored)
    - `output/` - Generated C4 documentation
    - `scripts/` - Generation scripts
    - `docs/prompts/` - LLM prompt templates
    ```
  - **Priority:** 💡 MEDIUM

### Configuration

- [ ] **CONF-001: Extract Model Names to Constants**
  - **Action:** Create `scripts/models.py`:
    ```python
    from enum import Enum

    class LLMModel(str, Enum):
        CLAUDE_SONNET_4 = "anthropic/claude-sonnet-4-20250514"
        CLAUDE_OPUS_4 = "anthropic/claude-opus-4"
        GPT4_TURBO = "openai/gpt-4-turbo"
        GROK_CODE_FAST = "x-ai/grok-code-fast-1"
    ```
  - **Priority:** 💡 MEDIUM

- [ ] **CONF-002: Create Configuration Schema**
  - **Action:** Create `scripts/config_schema.py` with dataclasses:
    ```python
    from dataclasses import dataclass
    from typing import Optional

    @dataclass
    class FlowscribeConfig:
        api_key: str
        model: str
        workspace: Path
        max_file_size: int = 50_000
        max_files: int = 25
        debug: bool = False

        def validate(self) -> None:
            """Validate configuration"""
            if not self.api_key:
                raise ValueError("API key required")
            # ... more validation
    ```
  - **Priority:** 💡 MEDIUM

- [ ] **CONF-VERIFY: Verify Configuration System**
  - **Action:** Test configuration schema and model constants
  - **Verification Steps:**
    ```bash
    # Test models.py exists and imports correctly
    test -f scripts/models.py && echo "Models file exists"
    python3 -c "
    from scripts.models import LLMModel
    assert LLMModel.CLAUDE_SONNET_4.value.startswith('anthropic/')
    print('Models enum OK')
    "

    # Test config schema exists and validates
    test -f scripts/config_schema.py && echo "Config schema exists"
    python3 -c "
    from scripts.config_schema import FlowscribeConfig
    from pathlib import Path

    # Test valid config
    config = FlowscribeConfig(
        api_key='sk-or-v1-test123',
        model='anthropic/claude-sonnet-4',
        workspace=Path('/tmp')
    )
    config.validate()
    print('Config schema OK')

    # Test invalid config raises error
    try:
        bad_config = FlowscribeConfig(api_key='', model='test', workspace=Path('/tmp'))
        bad_config.validate()
        assert False, 'Should have raised error'
    except ValueError:
        print('Config validation works')
    "
    ```
  - **Success Criteria:**
    - Model constants file exists and contains all required models
    - Config schema validates correct configurations
    - Config schema rejects invalid configurations
  - **Priority:** 💡 MEDIUM

---

## 🌟 LOW PRIORITY (Nice to Have)

**Estimated Effort:** As time permits

### Performance Optimizations

- [ ] **PERF-001: Implement LLM Response Caching**
  - **Action:** Create caching layer for LLM responses
  - **Implementation:**
    ```python
    import hashlib
    from pathlib import Path
    import json

    class LLMCache:
        def __init__(self, cache_dir: Path, ttl_hours: int = 24):
            self.cache_dir = cache_dir
            self.ttl_hours = ttl_hours

        def get_cache_key(self, prompt: str, model: str) -> str:
            """Generate cache key from prompt and model"""
            content = f"{model}:{prompt}"
            return hashlib.sha256(content.encode()).hexdigest()

        def get(self, prompt: str, model: str) -> Optional[dict]:
            """Get cached response if exists and not expired"""
            # Implementation

        def set(self, prompt: str, model: str, response: dict) -> None:
            """Cache LLM response"""
            # Implementation
    ```
  - **Priority:** 🌟 LOW

- [ ] **PERF-002: Add Async/Parallel Processing**
  - **Action:** Use `asyncio` for parallel C4 generation
  - **Example:**
    ```python
    import asyncio

    async def generate_all_levels():
        tasks = [
            generate_level1(),
            generate_level2(),
            generate_level3(),
            generate_level4(),
        ]
        results = await asyncio.gather(*tasks)
        return results
    ```
  - **Priority:** 🌟 LOW

- [ ] **PERF-003: Optimize Regex Operations**
  - **Action:** Profile `sanitize_mermaid_diagram()` and optimize
  - **Tools:** Use `cProfile` to identify bottlenecks
  - **Priority:** 🌟 LOW

- [ ] **PERF-004: Add File Size Checks Before Reading**
  - **Files:** `scripts/flowscribe_utils.py:1050, 1364`
  - **Action:** Check file size before reading:
    ```python
    def safe_read_file(path: Path, max_size: int = 1_000_000) -> str:
        """Read file with size limit"""
        stat = path.stat()
        if stat.st_size > max_size:
            raise ValueError(f"File too large: {stat.st_size} bytes")
        return path.read_text(encoding='utf-8')
    ```
  - **Priority:** 🌟 LOW

### Observability

- [ ] **OBS-001: Add Metrics Export**
  - **Action:** Add Prometheus metrics endpoint
  - **Metrics to track:**
    - LLM API call count
    - LLM API latency
    - Cost per generation
    - Error rates
    - Cache hit rate
  - **Priority:** 🌟 LOW

- [ ] **OBS-002: Add Structured Logging Output**
  - **Action:** Support JSON logging format:
    ```python
    import json
    import logging

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                'timestamp': self.formatTime(record),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
            }
            return json.dumps(log_data)
    ```
  - **Priority:** 🌟 LOW

- [ ] **OBS-003: Add Health Check Endpoint**
  - **Action:** Create health check script:
    ```python
    def health_check():
        """Check system health"""
        checks = {
            'api_key': check_api_key(),
            'workspace': check_workspace(),
            'dependencies': check_dependencies(),
        }
        return all(checks.values()), checks
    ```
  - **Priority:** 🌟 LOW

### Docker & Deployment

- [ ] **DOCK-001: Consider Alpine Linux Base Image**
  - **Action:** Create `Dockerfile.alpine`
  - **Benefits:** Smaller image size (100MB vs 500MB+)
  - **Trade-offs:** May need to rebuild some packages
  - **Priority:** 🌟 LOW

- [ ] **DOCK-002: Multi-Stage Docker Build**
  - **Action:** Optimize Dockerfile with multi-stage build:
    ```dockerfile
    # Build stage
    FROM ubuntu:22.04 AS builder
    # Install build dependencies

    # Runtime stage
    FROM ubuntu:22.04
    # Copy only runtime dependencies
    ```
  - **Priority:** 🌟 LOW

- [ ] **DOCK-003: Add Docker Health Check**
  - **Action:** Add to Dockerfile:
    ```dockerfile
    HEALTHCHECK --interval=30s --timeout=3s \
      CMD python3 -c "import sys; sys.exit(0)"
    ```
  - **Priority:** 🌟 LOW

- [ ] **DOCK-VERIFY: Verify Docker Improvements**
  - **Action:** Test Docker image builds and runs correctly
  - **Verification Steps:**
    ```bash
    # Build the Docker image
    docker build -t flowscribe:test .

    # Check image size
    docker images flowscribe:test --format "{{.Size}}"

    # Run container and verify health check
    docker run -d --name flowscribe-test flowscribe:test
    sleep 35  # Wait for health check
    docker inspect flowscribe-test --format='{{.State.Health.Status}}'

    # Test container can execute scripts
    docker exec flowscribe-test python3 -c "
    from scripts.flowscribe_utils import FlowscribeContext
    print('Container scripts OK')
    "

    # Cleanup
    docker stop flowscribe-test
    docker rm flowscribe-test
    ```
  - **Success Criteria:**
    - Docker image builds without errors
    - Image size is reasonable (check if Alpine saves space)
    - Health check passes
    - Scripts execute correctly in container
  - **Priority:** 🌟 LOW

### Git & Version Control

- [ ] **GIT-001: Set Up Branch Protection**
  - **Action:** Configure GitHub repository settings:
    - Require PR reviews
    - Require status checks
    - Require up-to-date branches
  - **Priority:** 🌟 LOW

- [ ] **GIT-002: Add Pre-Commit Hooks**
  - **Action:** Create `.pre-commit-config.yaml`:
    ```yaml
    repos:
      - repo: https://github.com/psf/black
        rev: 23.12.1
        hooks:
          - id: black
      - repo: https://github.com/pycqa/pylint
        rev: v2.17.4
        hooks:
          - id: pylint
    ```
  - **Priority:** 🌟 LOW

- [ ] **GIT-003: Add Issue Templates**
  - **Action:** Create `.github/ISSUE_TEMPLATE/`:
    - bug_report.md
    - feature_request.md
    - question.md
  - **Priority:** 🌟 LOW

- [ ] **GIT-004: Add Pull Request Template**
  - **Action:** Create `.github/pull_request_template.md`
  - **Priority:** 🌟 LOW

---

## 📊 Progress Tracking

### Overall Progress
- **Total Tasks:** 82 (includes verification tasks)
- **Completed:** 3 ✅
- **In Progress:** 0
- **Not Started:** 79

### By Priority
- 🚨 **CRITICAL:** ~~3 tasks~~ → **All completed!** ✅
- ⚠️ **HIGH:** 18 tasks (4-6 days) - **Next focus area** (includes 5 verification tasks)
- 💡 **MEDIUM:** 31 tasks (1-2 weeks) (includes 3 verification tasks)
- 🌟 **LOW:** 30 tasks (as time permits) (includes 1 verification task)

### Completion Rate
- **Critical Priority:** 100% (3/3) ✅
- **High Priority:** 0% (0/18)
- **Medium Priority:** 0% (0/31)
- **Low Priority:** 0% (0/30)
- **Overall:** 3.7% (3/82)

### Verification Tasks Added
To ensure quality, 9 verification tasks have been added:
- **SEC-VERIFY**: Verify completed security fixes
- **TEST-004-VERIFY**: Run and validate all tests
- **TEST-005-VERIFY**: Verify CI/CD pipeline
- **DEP-VERIFY**: Verify dependencies installation
- **LOG-VERIFY**: Verify logging implementation
- **CODE-003-VERIFY**: Verify type hints with mypy
- **SEC-VERIFY-2**: Verify additional security improvements
- **CONF-VERIFY**: Verify configuration system
- **DOCK-VERIFY**: Verify Docker improvements

### Recommended Workflow

1. ~~**Week 1:** Complete all CRITICAL tasks (SEC-001 to SEC-003)~~ ✅ **DONE**
2. **Week 2:** Complete HIGH priority tasks (TEST-001 to LOG-003) ← **Current Focus**
3. **Week 3-4:** Work through MEDIUM priority tasks
4. **Ongoing:** Address LOW priority tasks as needed

---

## 📝 Notes

- This task list is based on the Deep Code Review completed on 2025-11-14
- **2025-11-15 Update:** Added verification/testing tasks after major implementation tasks
- Priorities may change based on business requirements
- Estimated efforts are approximate and may vary
- Each task should be completed in a separate branch/PR for easier review
- Update checkboxes as tasks are completed
- Add notes and blockers in task descriptions as needed
- **Testing Philosophy:** Every major implementation task now has a corresponding verification task

---

## 🔗 References

- Deep Code Review Report (see git history)
- README.md - Project overview and architecture
- .env.example - Configuration template
- scripts/flowscribe_utils.py - Core utilities (1,810 LOC)

---

**Last Updated:** 2025-11-15
**Next Review:** After completing HIGH priority tasks (testing infrastructure complete)
