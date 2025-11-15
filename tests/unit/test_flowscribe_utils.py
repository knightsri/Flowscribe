"""
Unit tests for flowscribe_utils.py core functions.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Import the module under test
import flowscribe_utils
from constants import MAX_RESPONSE_SIZE


class TestCostTracker:
    """Tests for the CostTracker class."""

    def test_calculate_cost_basic(self):
        """Test basic cost calculation."""
        tracker = flowscribe_utils.CostTracker('anthropic/claude-sonnet-4-20250514')
        # Model has $3 input / $15 output per 1M tokens
        cost = tracker.calculate_cost(1_000_000, 1_000_000)
        assert cost == 18.0  # $3 + $15

    def test_calculate_cost_small_numbers(self):
        """Test cost calculation with small token counts."""
        tracker = flowscribe_utils.CostTracker('anthropic/claude-sonnet-4-20250514')
        cost = tracker.calculate_cost(1000, 500)
        # (1000/1M * 3) + (500/1M * 15) = 0.003 + 0.0075 = 0.0105
        assert abs(cost - 0.0105) < 0.0001

    def test_get_model_pricing_known_model(self):
        """Test pricing retrieval for known models."""
        tracker = flowscribe_utils.CostTracker('anthropic/claude-sonnet-4-20250514')
        assert tracker.pricing['input'] == 3.0
        assert tracker.pricing['output'] == 15.0
        assert tracker.pricing['source'] == 'built-in'

    def test_get_model_pricing_unknown_model(self, caplog):
        """Test pricing retrieval for unknown models."""
        tracker = flowscribe_utils.CostTracker('unknown/model')
        assert tracker.pricing['input'] == 3.0
        assert tracker.pricing['output'] == 15.0
        assert tracker.pricing['source'] == 'default'
        assert 'Unknown model pricing' in caplog.text

    def test_get_model_pricing_from_env(self, monkeypatch):
        """Test pricing retrieval from environment variables."""
        monkeypatch.setenv('OPENROUTER_MODEL_INPUT_COST_PER_1M', '5.0')
        monkeypatch.setenv('OPENROUTER_MODEL_OUTPUT_COST_PER_1M', '10.0')
        tracker = flowscribe_utils.CostTracker('any/model')
        assert tracker.pricing['input'] == 5.0
        assert tracker.pricing['output'] == 10.0
        assert tracker.pricing['source'] == 'environment'

    def test_get_model_pricing_unified_from_env(self, monkeypatch):
        """Test unified pricing from environment."""
        monkeypatch.setenv('OPENROUTER_MODEL_COST_PER_1M', '7.5')
        tracker = flowscribe_utils.CostTracker('any/model')
        assert tracker.pricing['input'] == 7.5
        assert tracker.pricing['output'] == 7.5
        assert tracker.pricing['source'] == 'environment (unified)'

    def test_record_call(self):
        """Test recording an API call."""
        tracker = flowscribe_utils.CostTracker('anthropic/claude-sonnet-4-20250514')
        tracker.record_call(1000, 500, 2.5)

        assert len(tracker.calls) == 1
        assert tracker.total_input_tokens == 1000
        assert tracker.total_output_tokens == 500
        assert tracker.total_tokens == 1500
        assert abs(tracker.total_time - 2.5) < 0.001
        assert tracker.total_cost > 0

    def test_record_call_with_cost_override(self):
        """Test recording an API call with cost override."""
        tracker = flowscribe_utils.CostTracker('anthropic/claude-sonnet-4-20250514')
        tracker.record_call(1000, 500, 2.5, cost_override=0.05)

        assert abs(tracker.total_cost - 0.05) < 0.0001

    def test_record_call_with_metadata(self):
        """Test recording an API call with metadata."""
        tracker = flowscribe_utils.CostTracker('anthropic/claude-sonnet-4-20250514')
        meta = {'id': 'test-123', 'model': 'test-model'}
        tracker.record_call(1000, 500, 2.5, meta=meta)

        assert tracker.calls[0]['id'] == 'test-123'
        assert tracker.calls[0]['model'] == 'test-model'

    def test_get_summary(self):
        """Test getting cost summary."""
        tracker = flowscribe_utils.CostTracker('anthropic/claude-sonnet-4-20250514')
        tracker.record_call(1000, 500, 2.5)
        tracker.record_call(2000, 1000, 3.0)

        summary = tracker.get_summary()
        assert summary['total_input_tokens'] == 3000
        assert summary['total_output_tokens'] == 1500
        assert summary['total_tokens'] == 4500
        assert summary['num_calls'] == 2
        assert summary['model'] == 'anthropic/claude-sonnet-4-20250514'


class TestLLMClient:
    """Tests for the LLMClient class."""

    def test_init_valid_model(self):
        """Test initialization with valid model name."""
        client = flowscribe_utils.LLMClient('test-key', 'anthropic/claude-sonnet-4')
        assert client.api_key == 'test-key'
        assert client.model == 'anthropic/claude-sonnet-4'
        assert client.tracker is not None

    def test_init_invalid_model_empty(self):
        """Test initialization with empty model name."""
        with pytest.raises(ValueError, match="Model must be a non-empty string"):
            flowscribe_utils.LLMClient('test-key', '')

    def test_init_invalid_model_format(self):
        """Test initialization with invalid model name format."""
        with pytest.raises(ValueError, match="Invalid model name format"):
            flowscribe_utils.LLMClient('test-key', 'model; DROP TABLE users;')

    def test_init_with_custom_tracker(self):
        """Test initialization with custom tracker."""
        tracker = flowscribe_utils.CostTracker('test/model')
        client = flowscribe_utils.LLMClient('test-key', 'test/model', tracker=tracker)
        assert client.tracker is tracker

    @patch('flowscribe_utils.requests.post')
    def test_call_success(self, mock_post):
        """Test successful API call."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150,
                'cost': 0.002
            },
            'model': 'anthropic/claude-sonnet-4',
            'id': 'test-id-123'
        }
        mock_post.return_value = mock_response

        client = flowscribe_utils.LLMClient('test-key', 'anthropic/claude-sonnet-4')
        result = client.call('Test prompt')

        assert result is not None
        assert result['content'] == 'Test response'
        assert result['input_tokens'] == 100
        assert result['output_tokens'] == 50
        assert result['total_tokens'] == 150
        assert result['id'] == 'test-id-123'

    @patch('flowscribe_utils.requests.post')
    def test_call_timeout(self, mock_post, caplog):
        """Test API call timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        client = flowscribe_utils.LLMClient('test-key', 'anthropic/claude-sonnet-4')
        result = client.call('Test prompt', timeout=1)

        assert result is None
        assert 'timed out' in caplog.text

    @patch('flowscribe_utils.requests.post')
    def test_call_request_error(self, mock_post, caplog):
        """Test API call with request error."""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException('Network error')

        client = flowscribe_utils.LLMClient('test-key', 'anthropic/claude-sonnet-4')
        result = client.call('Test prompt')

        assert result is None
        assert 'failed' in caplog.text

    @patch('flowscribe_utils.requests.post')
    def test_call_response_size_limit(self, mock_post, caplog):
        """Test API call with response size limit."""
        large_content = 'x' * (MAX_RESPONSE_SIZE + 1000)
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': large_content}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50},
            'model': 'test/model'
        }
        mock_post.return_value = mock_response

        client = flowscribe_utils.LLMClient('test-key', 'test/model')
        result = client.call('Test prompt')

        assert len(result['content']) == MAX_RESPONSE_SIZE
        assert 'truncated' in caplog.text


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_parse_llm_json_valid(self):
        """Test parsing valid JSON."""
        json_str = '{"key": "value", "number": 42}'
        result = flowscribe_utils.parse_llm_json(json_str)
        assert result == {"key": "value", "number": 42}

    def test_parse_llm_json_with_markdown_json(self):
        """Test parsing JSON wrapped in ```json blocks."""
        json_str = '```json\n{"key": "value"}\n```'
        result = flowscribe_utils.parse_llm_json(json_str)
        assert result == {"key": "value"}

    def test_parse_llm_json_with_markdown_generic(self):
        """Test parsing JSON wrapped in generic ``` blocks."""
        json_str = '```\n{"key": "value"}\n```'
        result = flowscribe_utils.parse_llm_json(json_str)
        assert result == {"key": "value"}

    def test_parse_llm_json_invalid(self, caplog):
        """Test parsing invalid JSON."""
        json_str = '{"key": invalid}'
        result = flowscribe_utils.parse_llm_json(json_str)
        assert result is None
        assert 'Failed to parse JSON' in caplog.text

    def test_get_api_config_success(self, monkeypatch):
        """Test getting API config from environment."""
        monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key-123')
        monkeypatch.setenv('OPENROUTER_MODEL', 'test/model')

        api_key, model = flowscribe_utils.get_api_config()
        assert api_key == 'test-key-123'
        assert model == 'test/model'

    def test_get_api_config_default_model(self, monkeypatch):
        """Test getting API config with default model."""
        monkeypatch.setenv('OPENROUTER_API_KEY', 'test-key-123')
        monkeypatch.delenv('OPENROUTER_MODEL', raising=False)

        api_key, model = flowscribe_utils.get_api_config()
        assert api_key == 'test-key-123'
        assert model == 'anthropic/claude-sonnet-4-20250514'

    def test_get_api_config_missing_key(self, monkeypatch):
        """Test getting API config without API key."""
        monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)

        with pytest.raises(ValueError, match="OPENROUTER_API_KEY not set"):
            flowscribe_utils.get_api_config()

    def test_format_cost_small(self):
        """Test formatting small costs."""
        assert flowscribe_utils.format_cost(0.00001) == "$0.000010"

    def test_format_cost_medium(self):
        """Test formatting medium costs."""
        assert flowscribe_utils.format_cost(0.001) == "$0.00100"

    def test_format_cost_large(self):
        """Test formatting large costs."""
        assert flowscribe_utils.format_cost(1.5) == "$1.5000"

    def test_format_duration_seconds(self):
        """Test formatting duration in seconds."""
        assert flowscribe_utils.format_duration(30.5) == "30.5s"

    def test_format_duration_minutes(self):
        """Test formatting duration in minutes."""
        assert flowscribe_utils.format_duration(120) == "2.0m"

    def test_format_duration_hours(self):
        """Test formatting duration in hours."""
        assert flowscribe_utils.format_duration(7200) == "2.0h"


class TestMermaidSafeId:
    """Tests for mermaid_safe_id function."""

    def test_mermaid_safe_id_valid(self):
        """Test with valid identifier."""
        assert flowscribe_utils.mermaid_safe_id('MyComponent') == 'MyComponent'

    def test_mermaid_safe_id_with_spaces(self):
        """Test with spaces."""
        assert flowscribe_utils.mermaid_safe_id('My Component') == 'My_Component'

    def test_mermaid_safe_id_with_special_chars(self):
        """Test with special characters."""
        assert flowscribe_utils.mermaid_safe_id('api/v1/users') == 'api_v1_users'

    def test_mermaid_safe_id_starts_with_digit(self):
        """Test with identifier starting with digit."""
        result = flowscribe_utils.mermaid_safe_id('123component')
        assert result.startswith('n_')
        assert '123component' in result

    def test_mermaid_safe_id_empty_string(self):
        """Test with empty string."""
        result = flowscribe_utils.mermaid_safe_id('')
        assert result.startswith('n_')

    def test_mermaid_safe_id_none(self):
        """Test with None."""
        result = flowscribe_utils.mermaid_safe_id(None)
        assert result.startswith('n_')


class TestMermaidIdRegistry:
    """Tests for MermaidIdRegistry class."""

    def test_uid_unique_names(self):
        """Test UID generation for unique names."""
        registry = flowscribe_utils.MermaidIdRegistry()
        id1 = registry.uid('Component1')
        id2 = registry.uid('Component2')
        assert id1 != id2
        assert id1 == 'Component1'
        assert id2 == 'Component2'

    def test_uid_duplicate_names(self):
        """Test UID generation for duplicate names."""
        registry = flowscribe_utils.MermaidIdRegistry()
        id1 = registry.uid('Component')
        id2 = registry.uid('Component')
        assert id1 != id2
        assert id1 == 'Component'
        assert '_' in id2  # Should have hash suffix

    def test_uid_sanitization(self):
        """Test UID generation with sanitization."""
        registry = flowscribe_utils.MermaidIdRegistry()
        id1 = registry.uid('My Component')
        assert id1 == 'My_Component'

    def test_reset(self):
        """Test registry reset."""
        registry = flowscribe_utils.MermaidIdRegistry()
        id1 = registry.uid('Component')
        registry.reset()
        id2 = registry.uid('Component')
        # After reset, same name should give same ID
        assert id1 == id2
