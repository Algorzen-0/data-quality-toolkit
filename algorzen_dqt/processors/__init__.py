"""
Big Data Processors for the Algorzen Data Quality Toolkit.

This package provides:
- Apache Spark processing
- Dask distributed computing
- Real-time streaming with Kafka
- Large-scale data quality checks
"""

from .spark_processor import SparkProcessor
from .dask_processor import DaskProcessor
from .streaming_processor import StreamingProcessor

__all__ = [
    "SparkProcessor",
    "DaskProcessor", 
    "StreamingProcessor"
]
