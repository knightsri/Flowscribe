"""
Regex Operation Optimizer

Provides optimized regex patterns and utilities for better performance
in sanitizing and processing Mermaid diagrams and other text operations.
"""

import re
from typing import Dict, List, Pattern
import time
from functools import lru_cache


class RegexOptimizer:
    """Optimized regex operations with pre-compiled patterns and caching."""

    def __init__(self):
        """Initialize with pre-compiled regex patterns."""
        # Pre-compile frequently used patterns for better performance
        self._patterns: Dict[str, Pattern] = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, Pattern]:
        """
        Compile all regex patterns upfront.

        Returns:
            Dictionary of compiled regex patterns
        """
        return {
            # Mermaid sanitization patterns
            'html_tags': re.compile(r'<[^>]+>'),
            'special_chars': re.compile(r'[^\w\s\-_.,;:()\[\]{}]'),
            'multiple_spaces': re.compile(r'\s+'),
            'leading_trailing_spaces': re.compile(r'^\s+|\s+$'),
            'multiple_newlines': re.compile(r'\n\n+'),

            # Code block patterns
            'code_block': re.compile(r'```[\s\S]*?```'),
            'inline_code': re.compile(r'`[^`]+`'),

            # URL patterns
            'url': re.compile(r'https?://[^\s]+'),

            # Path patterns
            'unix_path': re.compile(r'/[\w/\-_.]+'),
            'windows_path': re.compile(r'[A-Z]:\\[\w\\\-_.]+'),

            # Mermaid-specific patterns
            'mermaid_arrow': re.compile(r'(?:-->|->|==|.->)'),
            'mermaid_node_id': re.compile(r'\b[A-Za-z][A-Za-z0-9_]*\b'),
            'mermaid_quote': re.compile(r'"[^"]*"|\'[^\']*\''),

            # Sanitization patterns
            'unsafe_chars': re.compile(r'[<>&\'"\\]'),
            'control_chars': re.compile(r'[\x00-\x1f\x7f-\x9f]'),

            # Number patterns
            'number': re.compile(r'\b\d+\b'),
            'float': re.compile(r'\b\d+\.\d+\b'),

            # Identifier patterns
            'identifier': re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
            'camel_case': re.compile(r'[a-z]+[A-Z][a-zA-Z]*'),
            'snake_case': re.compile(r'[a-z]+(_[a-z]+)+'),
        }

    def get_pattern(self, name: str) -> Pattern:
        """
        Get a pre-compiled regex pattern.

        Args:
            name: Pattern name

        Returns:
            Compiled regex pattern

        Raises:
            KeyError: If pattern name doesn't exist
        """
        return self._patterns[name]

    @lru_cache(maxsize=1024)
    def sanitize_for_mermaid(self, text: str) -> str:
        """
        Sanitize text for use in Mermaid diagrams (cached version).

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text safe for Mermaid
        """
        if not text:
            return ""

        # Remove HTML tags
        text = self._patterns['html_tags'].sub('', text)

        # Remove control characters
        text = self._patterns['control_chars'].sub('', text)

        # Normalize whitespace
        text = self._patterns['multiple_spaces'].sub(' ', text)
        text = self._patterns['leading_trailing_spaces'].sub('', text)

        # Limit length
        if len(text) > 100:
            text = text[:97] + '...'

        return text

    @lru_cache(maxsize=512)
    def extract_code_blocks(self, text: str) -> List[str]:
        """
        Extract code blocks from markdown text (cached).

        Args:
            text: Markdown text

        Returns:
            List of code block contents
        """
        return self._patterns['code_block'].findall(text)

    @lru_cache(maxsize=512)
    def extract_urls(self, text: str) -> List[str]:
        """
        Extract URLs from text (cached).

        Args:
            text: Text containing URLs

        Returns:
            List of URLs
        """
        return self._patterns['url'].findall(text)

    def sanitize_unsafe_chars(self, text: str) -> str:
        """
        Replace unsafe characters for output.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        replacements = {
            '<': '&lt;',
            '>': '&gt;',
            '&': '&amp;',
            '"': '&quot;',
            "'": '&#39;',
            '\\': '\\\\',
        }

        def replace_unsafe(match):
            return replacements.get(match.group(0), '')

        return self._patterns['unsafe_chars'].sub(replace_unsafe, text)

    def optimize_sanitize_mermaid_diagram(self, diagram: str) -> str:
        """
        Optimized version of sanitize_mermaid_diagram function.

        This uses pre-compiled patterns and efficient string operations
        to improve performance over multiple regex.sub() calls.

        Args:
            diagram: Mermaid diagram code

        Returns:
            Sanitized diagram
        """
        if not diagram:
            return ""

        # Use pre-compiled patterns for better performance
        # Remove control characters first
        diagram = self._patterns['control_chars'].sub('', diagram)

        # Normalize whitespace efficiently
        diagram = self._patterns['multiple_spaces'].sub(' ', diagram)
        diagram = self._patterns['multiple_newlines'].sub('\n\n', diagram)

        # Remove leading/trailing spaces from each line
        lines = diagram.split('\n')
        lines = [self._patterns['leading_trailing_spaces'].sub('', line) for line in lines]
        diagram = '\n'.join(lines)

        return diagram

    def clear_cache(self):
        """Clear all LRU caches."""
        self.sanitize_for_mermaid.cache_clear()
        self.extract_code_blocks.cache_clear()
        self.extract_urls.cache_clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache info for each cached method
        """
        return {
            'sanitize_for_mermaid': self.sanitize_for_mermaid.cache_info()._asdict(),
            'extract_code_blocks': self.extract_code_blocks.cache_info()._asdict(),
            'extract_urls': self.extract_urls.cache_info()._asdict(),
        }


class RegexProfiler:
    """Profiler for regex operations to identify bottlenecks."""

    def __init__(self):
        """Initialize profiler."""
        self.stats: Dict[str, Dict[str, float]] = {}

    def profile_pattern(self, pattern: str, text: str, iterations: int = 1000) -> Dict[str, float]:
        """
        Profile a regex pattern's performance.

        Args:
            pattern: Regex pattern string
            text: Test text
            iterations: Number of iterations

        Returns:
            Dictionary with timing statistics
        """
        # Test with compilation each time
        start = time.perf_counter()
        for _ in range(iterations):
            re.search(pattern, text)
        compile_each_time = time.perf_counter() - start

        # Test with pre-compiled pattern
        compiled = re.compile(pattern)
        start = time.perf_counter()
        for _ in range(iterations):
            compiled.search(text)
        pre_compiled_time = time.perf_counter() - start

        speedup = compile_each_time / pre_compiled_time if pre_compiled_time > 0 else 0

        return {
            'compile_each_time': compile_each_time,
            'pre_compiled_time': pre_compiled_time,
            'speedup_factor': speedup,
            'iterations': iterations,
            'avg_time_compiled': compile_each_time / iterations,
            'avg_time_precompiled': pre_compiled_time / iterations,
        }

    def compare_patterns(self, patterns: List[str], text: str) -> Dict[str, Dict[str, float]]:
        """
        Compare performance of multiple patterns.

        Args:
            patterns: List of regex pattern strings
            text: Test text

        Returns:
            Dictionary mapping pattern to stats
        """
        results = {}
        for pattern in patterns:
            results[pattern] = self.profile_pattern(pattern, text)
        return results


# Global instance for easy import
regex_optimizer = RegexOptimizer()


# Convenience functions using the global instance
def sanitize_for_mermaid(text: str) -> str:
    """Sanitize text for Mermaid diagrams."""
    return regex_optimizer.sanitize_for_mermaid(text)


def extract_code_blocks(text: str) -> List[str]:
    """Extract code blocks from markdown."""
    return regex_optimizer.extract_code_blocks(text)


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    return regex_optimizer.extract_urls(text)


if __name__ == '__main__':
    # Example usage and benchmarking
    print("Regex Optimizer - Performance Testing")
    print("=" * 50)

    optimizer = RegexOptimizer()
    profiler = RegexProfiler()

    # Test sanitization
    test_text = "This is a <b>test</b> with\n\nmultiple   spaces and\tcontrol chars"
    sanitized = optimizer.sanitize_for_mermaid(test_text)
    print(f"Original: {repr(test_text)}")
    print(f"Sanitized: {repr(sanitized)}")
    print()

    # Profile a pattern
    stats = profiler.profile_pattern(r'\s+', test_text * 100, iterations=1000)
    print("Pattern profiling results:")
    print(f"  Speedup from pre-compilation: {stats['speedup_factor']:.2f}x")
    print(f"  Avg time (compiled): {stats['avg_time_compiled']*1000:.4f}ms")
    print(f"  Avg time (pre-compiled): {stats['avg_time_precompiled']*1000:.4f}ms")
    print()

    # Show cache stats
    print("Cache statistics:")
    cache_info = optimizer.get_cache_info()
    for method, info in cache_info.items():
        print(f"  {method}: {info['hits']} hits, {info['misses']} misses")
