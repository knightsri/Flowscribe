"""
LLM Response Caching Layer

Provides caching functionality for LLM API responses to reduce costs
and improve performance by avoiding redundant API calls.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class LLMCache:
    """Cache layer for LLM responses with TTL support."""

    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        """
        Initialize LLM cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours (default: 24)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, prompt: str, model: str, temperature: float = 0.0) -> str:
        """
        Generate cache key from prompt, model, and temperature.

        Args:
            prompt: The prompt text
            model: Model name/identifier
            temperature: Model temperature parameter

        Returns:
            SHA256 hash as cache key
        """
        content = f"{model}:{temperature}:{prompt}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, prompt: str, model: str, temperature: float = 0.0) -> Optional[Dict[str, Any]]:
        """
        Get cached response if exists and not expired.

        Args:
            prompt: The prompt text
            model: Model name/identifier
            temperature: Model temperature parameter

        Returns:
            Cached response dict or None if not found/expired
        """
        cache_key = self.get_cache_key(prompt, model, temperature)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)

            # Check if cache is expired
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            expiry_time = cached_time + timedelta(hours=self.ttl_hours)

            if datetime.now() > expiry_time:
                # Cache expired, remove it
                cache_path.unlink()
                return None

            return cached_data['response']

        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            # Invalid cache file, remove it
            if cache_path.exists():
                cache_path.unlink()
            return None

    def set(self, prompt: str, model: str, response: Dict[str, Any],
            temperature: float = 0.0) -> None:
        """
        Cache LLM response.

        Args:
            prompt: The prompt text
            model: Model name/identifier
            response: Response data to cache
            temperature: Model temperature parameter
        """
        cache_key = self.get_cache_key(prompt, model, temperature)
        cache_path = self._get_cache_path(cache_key)

        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'temperature': temperature,
            'prompt_hash': cache_key,
            'response': response
        }

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except OSError as e:
            # Log error but don't fail - caching is optional
            pass

    def clear_expired(self) -> int:
        """
        Remove all expired cache entries.

        Returns:
            Number of entries removed
        """
        removed_count = 0

        for cache_file in self.cache_dir.glob('*.json'):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)

                cached_time = datetime.fromisoformat(cached_data['timestamp'])
                expiry_time = cached_time + timedelta(hours=self.ttl_hours)

                if datetime.now() > expiry_time:
                    cache_file.unlink()
                    removed_count += 1

            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                # Invalid cache file, remove it
                cache_file.unlink()
                removed_count += 1

        return removed_count

    def clear_all(self) -> int:
        """
        Remove all cache entries.

        Returns:
            Number of entries removed
        """
        removed_count = 0

        for cache_file in self.cache_dir.glob('*.json'):
            try:
                cache_file.unlink()
                removed_count += 1
            except OSError:
                pass

        return removed_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_entries = 0
        expired_entries = 0
        total_size_bytes = 0

        for cache_file in self.cache_dir.glob('*.json'):
            total_entries += 1
            total_size_bytes += cache_file.stat().st_size

            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)

                cached_time = datetime.fromisoformat(cached_data['timestamp'])
                expiry_time = cached_time + timedelta(hours=self.ttl_hours)

                if datetime.now() > expiry_time:
                    expired_entries += 1

            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                expired_entries += 1

        return {
            'total_entries': total_entries,
            'valid_entries': total_entries - expired_entries,
            'expired_entries': expired_entries,
            'total_size_bytes': total_size_bytes,
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2)
        }
