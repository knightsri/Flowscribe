#!/usr/bin/env python3
"""
Flowscribe Constants

Centralized constants for magic numbers and configuration values.
"""

# File processing limits
MAX_FILE_SIZE = 50_000  # Maximum file size to analyze (bytes)
MAX_FILES_TO_ANALYZE = 25  # Maximum number of files to analyze

# LLM generated code safety
MAX_GENERATED_SCRIPT_SIZE = 1024  # Maximum size of LLM-generated scripts (bytes)
SCRIPT_EXECUTION_TIMEOUT = 30  # Timeout for script execution (seconds)

# Display limits
MAX_VIOLATION_ROWS = 100  # Maximum number of violation rows to display
MAX_FILES_PER_CELL = 3  # Maximum number of files to show per cell

# API limits
MAX_RESPONSE_SIZE = 10_000_000  # Maximum LLM response size (10MB)
DEFAULT_API_TIMEOUT = 180  # Default API request timeout (seconds)

# Model defaults
DEFAULT_MODEL = 'anthropic/claude-sonnet-4-20250514'

# Pricing defaults (per 1M tokens)
DEFAULT_INPUT_COST = 3.0
DEFAULT_OUTPUT_COST = 15.0
