"""
Metrics Export for Flowscribe

Provides Prometheus-compatible metrics collection and export for monitoring
LLM API usage, costs, performance, and errors.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import time
from pathlib import Path
import json
from collections import defaultdict


@dataclass
class MetricValue:
    """Individual metric value with timestamp."""
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)


class Counter:
    """Counter metric - monotonically increasing value."""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        """
        Initialize counter.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names (optional)
        """
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[str, float] = defaultdict(float)

    def inc(self, value: float = 1.0, **labels) -> None:
        """Increment counter."""
        label_key = self._make_label_key(labels)
        self._values[label_key] += value

    def get(self, **labels) -> float:
        """Get counter value."""
        label_key = self._make_label_key(labels)
        return self._values.get(label_key, 0.0)

    def _make_label_key(self, labels: Dict[str, str]) -> str:
        """Create hashable key from labels."""
        return ','.join(f"{k}={v}" for k, v in sorted(labels.items()))

    def to_prometheus(self) -> str:
        """Export in Prometheus text format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} counter",
        ]

        for label_key, value in self._values.items():
            if label_key:
                lines.append(f"{self.name}{{{label_key}}} {value}")
            else:
                lines.append(f"{self.name} {value}")

        return '\n'.join(lines)


class Gauge:
    """Gauge metric - value that can go up or down."""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        """
        Initialize gauge.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names (optional)
        """
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[str, float] = defaultdict(float)

    def set(self, value: float, **labels) -> None:
        """Set gauge value."""
        label_key = self._make_label_key(labels)
        self._values[label_key] = value

    def inc(self, value: float = 1.0, **labels) -> None:
        """Increment gauge."""
        label_key = self._make_label_key(labels)
        self._values[label_key] += value

    def dec(self, value: float = 1.0, **labels) -> None:
        """Decrement gauge."""
        label_key = self._make_label_key(labels)
        self._values[label_key] -= value

    def get(self, **labels) -> float:
        """Get gauge value."""
        label_key = self._make_label_key(labels)
        return self._values.get(label_key, 0.0)

    def _make_label_key(self, labels: Dict[str, str]) -> str:
        """Create hashable key from labels."""
        return ','.join(f"{k}={v}" for k, v in sorted(labels.items()))

    def to_prometheus(self) -> str:
        """Export in Prometheus text format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} gauge",
        ]

        for label_key, value in self._values.items():
            if label_key:
                lines.append(f"{self.name}{{{label_key}}} {value}")
            else:
                lines.append(f"{self.name} {value}")

        return '\n'.join(lines)


class Histogram:
    """Histogram metric - distribution of values."""

    def __init__(self, name: str, description: str,
                 buckets: Optional[List[float]] = None,
                 labels: Optional[List[str]] = None):
        """
        Initialize histogram.

        Args:
            name: Metric name
            description: Metric description
            buckets: Bucket boundaries (optional, default: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
            labels: Label names (optional)
        """
        self.name = name
        self.description = description
        self.labels = labels or []

        if buckets is None:
            self.buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        else:
            self.buckets = sorted(buckets)

        self._buckets: Dict[str, List[int]] = defaultdict(lambda: [0] * (len(self.buckets) + 1))
        self._sums: Dict[str, float] = defaultdict(float)
        self._counts: Dict[str, int] = defaultdict(int)

    def observe(self, value: float, **labels) -> None:
        """Observe a value."""
        label_key = self._make_label_key(labels)

        # Update sum and count
        self._sums[label_key] += value
        self._counts[label_key] += 1

        # Update buckets
        for i, bucket in enumerate(self.buckets):
            if value <= bucket:
                self._buckets[label_key][i] += 1

        # +Inf bucket
        self._buckets[label_key][-1] += 1

    def _make_label_key(self, labels: Dict[str, str]) -> str:
        """Create hashable key from labels."""
        return ','.join(f"{k}={v}" for k, v in sorted(labels.items()))

    def to_prometheus(self) -> str:
        """Export in Prometheus text format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} histogram",
        ]

        for label_key in self._counts.keys():
            label_str = f"{{{label_key}}}" if label_key else ""

            # Buckets
            for i, bucket in enumerate(self.buckets):
                count = self._buckets[label_key][i]
                lines.append(f"{self.name}_bucket{{le=\"{bucket}\"{','+label_key if label_key else ''}}} {count}")

            # +Inf bucket
            count = self._buckets[label_key][-1]
            lines.append(f"{self.name}_bucket{{le=\"+Inf\"{','+label_key if label_key else ''}}} {count}")

            # Sum and count
            lines.append(f"{self.name}_sum{label_str} {self._sums[label_key]}")
            lines.append(f"{self.name}_count{label_str} {self._counts[label_key]}")

        return '\n'.join(lines)


class MetricsRegistry:
    """Registry for all metrics."""

    def __init__(self):
        """Initialize registry."""
        self.metrics: Dict[str, Any] = {}

    def register(self, metric: Any) -> None:
        """Register a metric."""
        self.metrics[metric.name] = metric

    def counter(self, name: str, description: str, labels: Optional[List[str]] = None) -> Counter:
        """Create and register a counter."""
        counter = Counter(name, description, labels)
        self.register(counter)
        return counter

    def gauge(self, name: str, description: str, labels: Optional[List[str]] = None) -> Gauge:
        """Create and register a gauge."""
        gauge = Gauge(name, description, labels)
        self.register(gauge)
        return gauge

    def histogram(self, name: str, description: str,
                  buckets: Optional[List[float]] = None,
                  labels: Optional[List[str]] = None) -> Histogram:
        """Create and register a histogram."""
        histogram = Histogram(name, description, buckets, labels)
        self.register(histogram)
        return histogram

    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus text format."""
        output = []
        for metric in self.metrics.values():
            output.append(metric.to_prometheus())
        return '\n\n'.join(output)

    def export_json(self) -> str:
        """Export all metrics in JSON format."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {}
        }

        for name, metric in self.metrics.items():
            if isinstance(metric, Counter):
                data['metrics'][name] = {
                    'type': 'counter',
                    'description': metric.description,
                    'values': dict(metric._values)
                }
            elif isinstance(metric, Gauge):
                data['metrics'][name] = {
                    'type': 'gauge',
                    'description': metric.description,
                    'values': dict(metric._values)
                }
            elif isinstance(metric, Histogram):
                data['metrics'][name] = {
                    'type': 'histogram',
                    'description': metric.description,
                    'counts': dict(metric._counts),
                    'sums': dict(metric._sums)
                }

        return json.dumps(data, indent=2)

    def save_to_file(self, path: Path, format: str = 'prometheus') -> None:
        """Save metrics to file."""
        if format == 'prometheus':
            content = self.export_prometheus()
        elif format == 'json':
            content = self.export_json()
        else:
            raise ValueError(f"Unknown format: {format}")

        path.write_text(content, encoding='utf-8')


# Global registry
metrics_registry = MetricsRegistry()

# Flowscribe-specific metrics
llm_api_calls_total = metrics_registry.counter(
    'flowscribe_llm_api_calls_total',
    'Total number of LLM API calls',
    labels=['model', 'status']
)

llm_api_latency = metrics_registry.histogram(
    'flowscribe_llm_api_latency_seconds',
    'LLM API call latency in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    labels=['model']
)

llm_cost_total = metrics_registry.counter(
    'flowscribe_llm_cost_total_usd',
    'Total LLM API cost in USD',
    labels=['model']
)

llm_tokens_total = metrics_registry.counter(
    'flowscribe_llm_tokens_total',
    'Total number of tokens processed',
    labels=['model', 'type']  # type: input, output
)

cache_hits_total = metrics_registry.counter(
    'flowscribe_cache_hits_total',
    'Total number of cache hits',
    labels=['cache_type']
)

cache_misses_total = metrics_registry.counter(
    'flowscribe_cache_misses_total',
    'Total number of cache misses',
    labels=['cache_type']
)

errors_total = metrics_registry.counter(
    'flowscribe_errors_total',
    'Total number of errors',
    labels=['error_type']
)

c4_diagrams_generated = metrics_registry.counter(
    'flowscribe_c4_diagrams_generated_total',
    'Total number of C4 diagrams generated',
    labels=['level']
)

generation_duration = metrics_registry.histogram(
    'flowscribe_generation_duration_seconds',
    'Duration of diagram generation in seconds',
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    labels=['level']
)


if __name__ == '__main__':
    # Example usage
    print("Metrics Export - Example Usage")
    print("=" * 50)

    # Simulate some metrics
    llm_api_calls_total.inc(model='claude-sonnet-4', status='success')
    llm_api_calls_total.inc(model='claude-sonnet-4', status='success')
    llm_api_calls_total.inc(model='gpt-4', status='error')

    llm_api_latency.observe(1.5, model='claude-sonnet-4')
    llm_api_latency.observe(2.3, model='claude-sonnet-4')
    llm_api_latency.observe(0.8, model='gpt-4')

    llm_cost_total.inc(0.05, model='claude-sonnet-4')
    llm_tokens_total.inc(1500, model='claude-sonnet-4', type='input')
    llm_tokens_total.inc(500, model='claude-sonnet-4', type='output')

    cache_hits_total.inc(5, cache_type='llm_response')
    cache_misses_total.inc(2, cache_type='llm_response')

    c4_diagrams_generated.inc(level='1')
    c4_diagrams_generated.inc(level='2')
    generation_duration.observe(45.0, level='1')

    # Export metrics
    print("\n=== Prometheus Format ===")
    print(metrics_registry.export_prometheus())

    print("\n\n=== JSON Format ===")
    print(metrics_registry.export_json())

    print("\nMetrics module loaded successfully.")
