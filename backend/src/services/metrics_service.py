import time
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass, field
from enum import Enum


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsService:
    """
    Service for collecting and reporting performance metrics
    """
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.logger = logging.getLogger(__name__)
        self.start_times: Dict[str, float] = {}

    def start_timer(self, operation: str):
        """
        Start timing an operation
        """
        self.start_times[operation] = time.time()

    def stop_timer(self, operation: str) -> float:
        """
        Stop timing an operation and return elapsed time in seconds
        """
        if operation in self.start_times:
            elapsed = time.time() - self.start_times[operation]
            del self.start_times[operation]

            # Record the timing metric
            self.record_histogram(f"{operation}_duration_seconds", elapsed)
            return elapsed
        return 0.0

    def record_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        Record a counter metric
        """
        labels = labels or {}
        metric_key = f"{name}_{str(labels)}"

        if metric_key in self.metrics:
            self.metrics[metric_key].value += value
        else:
            self.metrics[metric_key] = Metric(
                name=name,
                type=MetricType.COUNTER,
                value=value,
                labels=labels
            )

    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record a gauge metric
        """
        labels = labels or {}
        metric_key = f"{name}_{str(labels)}"

        self.metrics[metric_key] = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            labels=labels
        )

    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record a histogram metric
        """
        labels = labels or {}
        metric_key = f"{name}_{str(labels)}"

        if metric_key in self.metrics:
            # For histogram, we'll keep track of stats
            existing = self.metrics[metric_key]
            existing.value = value  # Store the latest value
        else:
            self.metrics[metric_key] = Metric(
                name=name,
                type=MetricType.HISTOGRAM,
                value=value,
                labels=labels
            )

    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric by 1
        """
        self.record_counter(name, 1.0, labels)

    def get_metric(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[Metric]:
        """
        Get a specific metric by name and labels
        """
        labels = labels or {}
        metric_key = f"{name}_{str(labels)}"
        return self.metrics.get(metric_key)

    def get_all_metrics(self) -> Dict[str, Metric]:
        """
        Get all collected metrics
        """
        return self.metrics.copy()

    def reset_metrics(self):
        """
        Reset all metrics
        """
        self.metrics.clear()
        self.start_times.clear()

    def log_performance_metrics(self):
        """
        Log performance metrics for monitoring
        """
        for key, metric in self.metrics.items():
            self.logger.info(f"Metric: {metric.name}, Value: {metric.value}, Labels: {metric.labels}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance metrics
        """
        summary = {
            "total_metrics": len(self.metrics),
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }

        for key, metric in self.metrics.items():
            summary["metrics"][metric.name] = {
                "type": metric.type.value,
                "value": metric.value,
                "labels": metric.labels
            }

        return summary


# Global metrics service instance
metrics_service = MetricsService()