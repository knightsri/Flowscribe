"""
pytest configuration and shared fixtures for Flowscribe tests.
"""
import os
import sys
from pathlib import Path
import pytest

# Add scripts directory to Python path
SCRIPTS_DIR = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def sample_workspace(tmp_path):
    """Create a temporary workspace directory for tests."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return "sk-or-v1-test-key-1234567890abcdef"


@pytest.fixture
def sample_config(sample_workspace, mock_api_key):
    """Provide a sample configuration dictionary."""
    return {
        'api_key': mock_api_key,
        'model': 'anthropic/claude-sonnet-4-20250514',
        'workspace': str(sample_workspace),
        'max_file_size': 50000,
        'max_files': 25,
        'debug': False
    }


@pytest.fixture
def sample_mermaid_diagram():
    """Provide a sample Mermaid diagram for testing."""
    return """graph TD
    A[Client] -->|HTTP Request| B(API Gateway)
    B --> C{Load Balancer}
    C --> D[Service 1]
    C --> E[Service 2]
    """
