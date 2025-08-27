"""
Algorzen Data Quality Toolkit

Enterprise-grade data quality solution for comprehensive data validation,
monitoring, and reporting across multiple data sources and formats.
"""

__version__ = "0.1.0"
__author__ = "Rishi R Carloni & the Algorzen team"
__email__ = "contact@algorzen.com"

from .core.engine import DataQualityEngine
from .core.validator import DataValidator
from .core.processor import DataProcessor

__all__ = [
    "DataQualityEngine",
    "DataValidator", 
    "DataProcessor",
]
