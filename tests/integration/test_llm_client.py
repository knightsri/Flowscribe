"""
Integration tests for LLM client functionality.
"""
import pytest
from unittest.mock import Mock, patch
import flowscribe_utils


class TestLLMClientIntegration:
    """Integration tests for LLM client with cost tracking."""

    @patch('flowscribe_utils.requests.post')
    def test_llm_call_with_tracking(self, mock_post):
        """Test complete LLM call flow with cost tracking."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Generated C4 diagram'}}],
            'usage': {
                'prompt_tokens': 500,
                'completion_tokens': 1000,
                'total_tokens': 1500,
                'cost': 0.018
            },
            'model': 'anthropic/claude-sonnet-4-20250514',
            'id': 'test-generation-123'
        }
        mock_post.return_value = mock_response

        # Create client with tracker
        tracker = flowscribe_utils.CostTracker('anthropic/claude-sonnet-4-20250514')
        client = flowscribe_utils.LLMClient('test-key', 'anthropic/claude-sonnet-4-20250514', tracker=tracker)

        # Make call
        result = client.call('Generate a C4 diagram')

        # Verify response
        assert result is not None
        assert result['content'] == 'Generated C4 diagram'
        assert result['input_tokens'] == 500
        assert result['output_tokens'] == 1000

        # Verify tracking
        assert tracker.total_input_tokens == 500
        assert tracker.total_output_tokens == 1000
        assert tracker.total_tokens == 1500
        assert len(tracker.calls) == 1

        # Verify summary
        summary = tracker.get_summary()
        assert summary['num_calls'] == 1
        assert summary['total_cost'] > 0

    @patch('flowscribe_utils.requests.post')
    def test_multiple_llm_calls_tracking(self, mock_post):
        """Test multiple LLM calls with cumulative tracking."""
        # Mock API responses
        mock_response1 = Mock()
        mock_response1.json.return_value = {
            'choices': [{'message': {'content': 'Response 1'}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 200, 'cost': 0.003},
            'model': 'test/model'
        }

        mock_response2 = Mock()
        mock_response2.json.return_value = {
            'choices': [{'message': {'content': 'Response 2'}}],
            'usage': {'prompt_tokens': 150, 'completion_tokens': 250, 'cost': 0.004},
            'model': 'test/model'
        }

        mock_post.side_effect = [mock_response1, mock_response2]

        # Create client with tracker
        tracker = flowscribe_utils.CostTracker('test/model')
        client = flowscribe_utils.LLMClient('test-key', 'test/model', tracker=tracker)

        # Make multiple calls
        result1 = client.call('Prompt 1')
        result2 = client.call('Prompt 2')

        # Verify cumulative tracking
        assert tracker.total_input_tokens == 250  # 100 + 150
        assert tracker.total_output_tokens == 450  # 200 + 250
        assert tracker.total_tokens == 700  # 250 + 450
        assert len(tracker.calls) == 2
        assert abs(tracker.total_cost - 0.007) < 0.0001  # 0.003 + 0.004

    @patch('flowscribe_utils.requests.post')
    def test_llm_call_with_json_response(self, mock_post):
        """Test LLM call that returns JSON and parsing."""
        # Mock API response with JSON content
        json_content = '```json\n{"layers": ["Presentation", "Business", "Data"]}\n```'
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': json_content}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50},
            'model': 'test/model'
        }
        mock_post.return_value = mock_response

        # Create client and make call
        client = flowscribe_utils.LLMClient('test-key', 'test/model')
        result = client.call('Generate architecture layers')

        # Parse JSON response
        parsed = flowscribe_utils.parse_llm_json(result['content'])
        assert parsed is not None
        assert 'layers' in parsed
        assert len(parsed['layers']) == 3
        assert 'Presentation' in parsed['layers']
