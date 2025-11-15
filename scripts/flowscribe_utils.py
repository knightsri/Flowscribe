#!/usr/bin/env python3
"""
Flowscribe Shared Utilities

Provides common functionality for all Flowscribe scripts:
- LLM API calls with cost tracking
- Model pricing configuration
- Metrics reporting
"""

import os
import json
import time
from datetime import datetime
import requests


class CostTracker:
    """Track costs and time for LLM operations"""
    
    def __init__(self, model):
        self.model = model
        self.pricing = self._get_model_pricing(model)
        self.total_cost = 0.0
        self.total_time = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        self.calls = []
        
    def _get_model_pricing(self, model):
        """Get pricing for model from environment or built-in database"""
        
        # Check for environment variable overrides first
        env_input_cost = os.environ.get('OPENROUTER_MODEL_INPUT_COST_PER_1M')
        env_output_cost = os.environ.get('OPENROUTER_MODEL_OUTPUT_COST_PER_1M')
        env_unified_cost = os.environ.get('OPENROUTER_MODEL_COST_PER_1M')
        
        if env_input_cost and env_output_cost:
            # Explicit input/output costs from environment
            return {
                'input': float(env_input_cost),
                'output': float(env_output_cost),
                'source': 'environment'
            }
        elif env_unified_cost:
            # Unified cost (same for input and output)
            cost = float(env_unified_cost)
            return {
                'input': cost,
                'output': cost,
                'source': 'environment (unified)'
            }
        
        # Built-in pricing for common models (as of Oct 2025)
        pricing_db = {
            'anthropic/claude-sonnet-4-20250514': {'input': 3.0, 'output': 15.0},
            'anthropic/claude-sonnet-4': {'input': 3.0, 'output': 15.0},
            'anthropic/claude-opus-4': {'input': 15.0, 'output': 75.0},
            'openai/gpt-4-turbo': {'input': 10.0, 'output': 30.0},
            'openai/gpt-4': {'input': 30.0, 'output': 60.0},
            'openai/gpt-4o': {'input': 2.5, 'output': 10.0},
            'x-ai/grok-2': {'input': 2.0, 'output': 10.0},
            'x-ai/grok-code-fast-1': {'input': 0.5, 'output': 1.5},
            'google/gemini-pro-1.5': {'input': 1.25, 'output': 5.0},
        }
        
        if model in pricing_db:
            pricing_db[model]['source'] = 'built-in'
            return pricing_db[model]
        
        # Default pricing for unknown models
        print(f"⚠ Warning: Unknown model pricing for '{model}'")
        print(f"  Using default: $3/$15 per 1M tokens")
        print(f"  Set OPENROUTER_MODEL_INPUT_COST_PER_1M and OPENROUTER_MODEL_OUTPUT_COST_PER_1M to override")
        return {
            'input': 3.0,
            'output': 15.0,
            'source': 'default'
        }
    
    def calculate_cost(self, input_tokens, output_tokens):
        """Calculate cost based on token usage"""
        input_cost = (input_tokens / 1_000_000) * self.pricing['input']
        output_cost = (output_tokens / 1_000_000) * self.pricing['output']
        return input_cost + output_cost
    
    def record_call(self, input_tokens, output_tokens, duration, cost_override=None, meta=None):
        """Record an API call"""
        cost = float(cost_override) if cost_override is not None else self.calculate_cost(input_tokens, output_tokens)
        
        self.total_cost += cost
        self.total_time += duration
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_tokens += (input_tokens + output_tokens)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost,
            'duration': duration
        }
        if isinstance(meta, dict):
            entry.update(meta)
        self.calls.append(entry)
    
    def get_summary(self):
        """Get cost summary"""
        return {
            'total_cost': self.total_cost,
            'total_time': self.total_time,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': self.total_tokens,
            'num_calls': len(self.calls),
            'model': self.model,
            'pricing': {
                'input_per_1m': self.pricing['input'],
                'output_per_1m': self.pricing['output'],
                'source': self.pricing['source']
            }
        }
    
    def print_summary(self, prefix=""):
        """Print formatted summary"""
        summary = self.get_summary()
        
        print(f"\n{prefix}Cost & Performance Summary:")
        print(f"{prefix}  Model:         {summary['model']}")
        print(f"{prefix}  Pricing:       ${summary['pricing']['input_per_1m']:.2f}/${summary['pricing']['output_per_1m']:.2f} per 1M ({summary['pricing']['source']})")
        print(f"{prefix}  Total Cost:    ${summary['total_cost']:.4f}")
        print(f"{prefix}  Total Time:    {summary['total_time']:.1f}s")
        print(f"{prefix}  Input Tokens:  {summary['total_input_tokens']:,}")
        print(f"{prefix}  Output Tokens: {summary['total_output_tokens']:,}")
        print(f"{prefix}  Total Tokens:  {summary['total_tokens']:,}")
        print(f"{prefix}  API Calls:     {summary['num_calls']}")
    
    def save_to_file(self, filepath):
        """Save metrics to JSON file"""
        summary = self.get_summary()
        summary['calls'] = self.calls
        summary['generated_at'] = datetime.now().isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)


class LLMClient:
    """OpenRouter API client with cost tracking"""

    # Security: Maximum response size to prevent memory exhaustion
    MAX_RESPONSE_SIZE = 10_000_000  # 10MB

    def __init__(self, api_key, model, tracker=None):
        self.api_key = api_key

        # Security: Validate model name format to prevent injection
        if not isinstance(model, str) or not model:
            raise ValueError("Model must be a non-empty string")

        # Allow alphanumeric, hyphens, slashes, dots, and underscores in model names
        import re
        if not re.match(r'^[a-zA-Z0-9._/-]+$', model):
            raise ValueError(f"Invalid model name format: {model}")

        self.model = model
        self.tracker = tracker or CostTracker(model)
    
    
    def call(self, prompt, timeout=180):
        """Call OpenRouter API and track costs (usage-first)."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/flowscribe",
            "X-Title": "Flowscribe"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            # Ask OpenRouter to include authoritative usage/cost in the response
            "usage": {"include": True}
        }
        
        start_time = time.time()
        started_at = datetime.utcnow().isoformat() + "Z"
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            
            duration = time.time() - start_time
            finished_at = datetime.utcnow().isoformat() + "Z"
            
            # Extract content, usage, ids and model
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')

            # Security: Limit response size to prevent memory exhaustion
            if len(content) > self.MAX_RESPONSE_SIZE:
                print(f"⚠ Warning: Response truncated (exceeded {self.MAX_RESPONSE_SIZE:,} chars)")
                content = content[:self.MAX_RESPONSE_SIZE]

            usage = result.get('usage', {}) or {}
            input_tokens = int(usage.get('prompt_tokens', 0) or 0)
            output_tokens = int(usage.get('completion_tokens', 0) or 0)
            total_tokens = int(usage.get('total_tokens', input_tokens + output_tokens) or (input_tokens + output_tokens))
            cost_usd = float(usage.get('cost', 0.0) or 0.0)
            resp_model = result.get('model') or self.model
            resp_id = result.get('id') or result.get('generation_id')
            
            # Track with usage-first cost
            self.tracker.record_call(
                input_tokens,
                output_tokens,
                duration,
                cost_override=cost_usd,
                meta={
                    'id': resp_id,
                    'model': resp_model,
                    'started_at': started_at,
                    'finished_at': finished_at
                }
            )
            
            return {
                'content': content,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'cost': cost_usd if cost_usd > 0 else self.tracker.calculate_cost(input_tokens, output_tokens),
                'duration': duration,
                'usage': usage,
                'model': resp_model,
                'id': resp_id,
                'started_at': started_at,
                'finished_at': finished_at
            }
            
        except requests.exceptions.Timeout:
            print(f"✗ API request timed out after {timeout}s")
            return None
        except requests.exceptions.RequestException as e:
            print(f"✗ API request failed: {e}")
            return None
        except (KeyError, IndexError, ValueError) as e:
            print(f"✗ Unexpected API response format: {e}")
            return None



def parse_llm_json(response_text):
    """Parse JSON from LLM response, handling markdown code blocks"""
    cleaned = response_text.strip()
    
    # Remove markdown code blocks
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]
    
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse JSON: {e}")
        print(f"Response text:\n{response_text[:500]}")
        return None


def get_api_config():
    """Get API configuration from environment"""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    model = os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4-20250514')
    
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not set. "
            "Set it in .env file or environment."
        )
    
    return api_key, model


def format_cost(cost):
    """Format cost for display"""
    if cost < 0.0001:
        return f"${cost:.6f}"
    elif cost < 0.01:
        return f"${cost:.5f}"
    else:
        return f"${cost:.4f}"


def format_duration(seconds):
    """Format duration for display"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


# -----------------------------
# Mermaid ID sanitization utils
# -----------------------------
import re as _re
import hashlib as _hashlib

def mermaid_safe_id(name: str) -> str:
    """
    Return a Mermaid-safe node id:
    - only [A-Za-z0-9_]
    - prefix with 'n_' if starts with a digit or becomes empty
    """
    base = _re.sub(r'[^A-Za-z0-9_]', '_', str(name or ''))
    if not base or base[0].isdigit():
        base = 'n_' + base
    return base

class MermaidIdRegistry:
    """
    Keeps node ids unique within a diagram while preserving readable labels.
    """
    __slots__ = ('_used',)

    def __init__(self):
        self._used = set()

    def uid(self, name: str) -> str:
        sid = mermaid_safe_id(name)
        if sid in self._used:
            h = _hashlib.md5(str(name).encode('utf-8')).hexdigest()[:6]
            sid = f"{sid}_{h}"
        self._used.add(sid)
        return sid

    def reset(self):
        self._used.clear()
