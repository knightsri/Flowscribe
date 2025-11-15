"""
Integration tests for context initialization and validation.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestContextIntegration:
    """Integration tests for context setup and validation."""

    def test_api_config_integration(self, monkeypatch):
        """Test API configuration retrieval and validation."""
        import flowscribe_utils

        # Set up environment
        monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-or-v1-test-key-abc123')
        monkeypatch.setenv('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4')

        # Get config
        api_key, model = flowscribe_utils.get_api_config()

        # Validate
        assert api_key == 'sk-or-v1-test-key-abc123'
        assert model == 'anthropic/claude-sonnet-4'

        # Create client to ensure model validation works
        client = flowscribe_utils.LLMClient(api_key, model)
        assert client.model == model

    def test_workspace_and_output_paths(self, tmp_path):
        """Test workspace and output path creation."""
        workspace = tmp_path / "test-project"
        workspace.mkdir()

        # Create project structure
        src_dir = workspace / "src"
        src_dir.mkdir()

        # Create some sample files
        (src_dir / "main.py").write_text("# Main file")
        (src_dir / "utils.py").write_text("# Utils file")

        # Verify structure
        assert workspace.exists()
        assert src_dir.exists()
        assert (src_dir / "main.py").exists()
        assert (src_dir / "utils.py").exists()

        # Output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        assert output_dir.exists()

    def test_cost_tracking_integration(self, monkeypatch):
        """Test cost tracking with environment-based pricing."""
        import flowscribe_utils

        # Set custom pricing
        monkeypatch.setenv('OPENROUTER_MODEL_INPUT_COST_PER_1M', '5.0')
        monkeypatch.setenv('OPENROUTER_MODEL_OUTPUT_COST_PER_1M', '10.0')

        # Create tracker
        tracker = flowscribe_utils.CostTracker('custom/model')

        # Verify pricing loaded from environment
        assert tracker.pricing['input'] == 5.0
        assert tracker.pricing['output'] == 10.0
        assert tracker.pricing['source'] == 'environment'

        # Test cost calculation
        cost = tracker.calculate_cost(1_000_000, 500_000)
        assert cost == 10.0  # (1M * $5) + (0.5M * $10) = $5 + $5
