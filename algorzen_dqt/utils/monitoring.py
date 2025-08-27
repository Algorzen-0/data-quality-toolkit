"""
Performance monitoring utilities for the Algorzen Data Quality Toolkit.

This module provides performance monitoring, metrics collection, and
observability features for the data quality toolkit.
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage_percent: float
    network_io: Dict[str, int]
    timestamp: datetime


class PerformanceMonitor:
    """
    Performance monitoring and metrics collection.
    
    This class provides comprehensive performance monitoring including
    system metrics, custom metrics, and performance profiling.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize the performance monitor.
        
        Args:
            max_history: Maximum number of historical metrics to keep
        """
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.system_metrics: deque = deque(maxlen=max_history)
        self.active_timers: Dict[str, float] = {}
        self._lock = threading.Lock()
        
        logger.info("Performance monitor initialized")
    
    def start_timer(self, name: str) -> None:
        """
        Start a performance timer.
        
        Args:
            name: Timer name
        """
        with self._lock:
            self.active_timers[name] = time.time()
            logger.debug(f"Started timer: {name}")
    
    def stop_timer(self, name: str) -> Optional[float]:
        """
        Stop a performance timer and return elapsed time.
        
        Args:
            name: Timer name
            
        Returns:
            Elapsed time in seconds, or None if timer not found
        """
        with self._lock:
            if name not in self.active_timers:
                logger.warning(f"Timer not found: {name}")
                return None
            
            start_time = self.active_timers.pop(name)
            elapsed = time.time() - start_time
            
            self.record_metric(f"{name}_duration", elapsed, "seconds")
            logger.debug(f"Stopped timer {name}: {elapsed:.3f}s")
            
            return elapsed
    
    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "count",
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a custom metric.
        
        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            tags: Optional tags for categorization
        """
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        with self._lock:
            self.metrics[name].append(metric)
        
        logger.debug(f"Recorded metric {name}: {value} {unit}")
    
    def record_system_metrics(self) -> SystemMetrics:
        """
        Record current system metrics.
        
        Returns:
            System metrics object
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available=memory_available,
                disk_usage_percent=disk_usage_percent,
                network_io=network_io,
                timestamp=datetime.now()
            )
            
            with self._lock:
                self.system_metrics.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available=0,
                disk_usage_percent=0.0,
                network_io={},
                timestamp=datetime.now()
            )
    
    def get_metric_summary(
        self,
        name: str,
        window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a metric.
        
        Args:
            name: Metric name
            window: Time window for filtering (None for all time)
            
        Returns:
            Summary statistics
        """
        if name not in self.metrics:
            return {"error": f"Metric not found: {name}"}
        
        metrics = list(self.metrics[name])
        
        if window:
            cutoff = datetime.now() - window
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        if not metrics:
            return {"error": "No metrics found in specified window"}
        
        values = [m.value for m in metrics]
        
        return {
            "name": name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "latest": values[-1],
            "unit": metrics[0].unit,
            "window": str(window) if window else "all_time"
        }
    
    def get_system_summary(self, window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get system metrics summary.
        
        Args:
            window: Time window for filtering (None for all time)
            
        Returns:
            System metrics summary
        """
        if not self.system_metrics:
            return {"error": "No system metrics available"}
        
        metrics = list(self.system_metrics)
        
        if window:
            cutoff = datetime.now() - window
            metrics = [m for m in metrics if m.timestamp >= cutoff]
        
        if not metrics:
            return {"error": "No system metrics found in specified window"}
        
        cpu_values = [m.cpu_percent for m in metrics]
        memory_values = [m.memory_percent for m in metrics]
        disk_values = [m.disk_usage_percent for m in metrics]
        
        return {
            "cpu": {
                "current": cpu_values[-1],
                "average": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values)
            },
            "memory": {
                "current_percent": memory_values[-1],
                "average_percent": sum(memory_values) / len(memory_values),
                "available_mb": metrics[-1].memory_available / (1024 * 1024)
            },
            "disk": {
                "current_percent": disk_values[-1],
                "average_percent": sum(disk_values) / len(disk_values)
            },
            "sample_count": len(metrics),
            "window": str(window) if window else "all_time"
        }
    
    def export_metrics(self, format: str = "json") -> str:
        """
        Export all metrics in the specified format.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Exported metrics as string
        """
        if format.lower() == "json":
            data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {},
                "system_metrics": []
            }
            
            for name, metric_list in self.metrics.items():
                data["metrics"][name] = [
                    {
                        "name": m.name,
                        "value": m.value,
                        "unit": m.unit,
                        "timestamp": m.timestamp.isoformat(),
                        "tags": m.tags
                    }
                    for m in metric_list
                ]
            
            for metric in self.system_metrics:
                data["system_metrics"].append({
                    "cpu_percent": metric.cpu_percent,
                    "memory_percent": metric.memory_percent,
                    "memory_available": metric.memory_available,
                    "disk_usage_percent": metric.disk_usage_percent,
                    "network_io": metric.network_io,
                    "timestamp": metric.timestamp.isoformat()
                })
            
            return json.dumps(data, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        with self._lock:
            self.metrics.clear()
            self.system_metrics.clear()
            self.active_timers.clear()
        
        logger.info("Cleared all performance metrics")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Stop any remaining timers
        for timer_name in list(self.active_timers.keys()):
            self.stop_timer(timer_name)


class Timer:
    """Context manager for timing code blocks."""
    
    def __init__(self, monitor: PerformanceMonitor, name: str):
        """
        Initialize timer.
        
        Args:
            monitor: Performance monitor instance
            name: Timer name
        """
        self.monitor = monitor
        self.name = name
    
    def __enter__(self):
        """Start timer."""
        self.monitor.start_timer(self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer."""
        self.monitor.stop_timer(self.name)
