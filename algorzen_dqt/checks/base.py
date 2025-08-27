"""
Base quality check class.

This module defines the base interface for all quality checks in the
Algorzen Data Quality Toolkit.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import pandas as pd
from pydantic import BaseModel, Field

from ..utils.logging import get_logger

logger = get_logger(__name__)


class CheckConfig(BaseModel):
    """Configuration for quality checks."""
    check_name: Optional[str] = None
    check_type: Optional[str] = None
    enabled: bool = True
    severity: str = "medium"  # low, medium, high, critical
    threshold: float = 0.8
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class CheckResult(BaseModel):
    """Result of a quality check execution."""
    check_name: str
    check_type: str
    status: str  # passed, failed, warning, error
    score: float  # 0.0 to 1.0
    details: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float
    timestamp: str
    affected_rows: Optional[int] = None
    affected_columns: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class QualityCheck(ABC):
    """
    Abstract base class for quality checks.
    
    All quality checks must implement this interface to ensure
    consistent behavior and result format.
    """
    
    def __init__(self, config: CheckConfig):
        """
        Initialize the quality check.
        
        Args:
            config: Check configuration
        """
        self.config = config
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        
        self.logger.debug(f"Initialized {self.__class__.__name__}: {config.check_name or 'unnamed'}")
    
    @abstractmethod
    async def execute(self, data: pd.DataFrame) -> CheckResult:
        """
        Execute the quality check on the provided data.
        
        Args:
            data: Data to check
            
        Returns:
            Check result with status, score, and details
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate the check configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    async def run(self, data: pd.DataFrame) -> CheckResult:
        """
        Run the quality check with timing and error handling.
        
        Args:
            data: Data to check
            
        Returns:
            Check result
        """
        if not self.config.enabled:
            return CheckResult(
                check_name=self.config.check_name or self.__class__.__name__,
                check_type=self.config.check_type or "unknown",
                status="skipped",
                score=1.0,
                details={"reason": "Check disabled"},
                execution_time=0.0,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        
        if not self.validate_config():
            return CheckResult(
                check_name=self.config.check_name or self.__class__.__name__,
                check_type=self.config.check_type or "unknown",
                status="error",
                score=0.0,
                details={"error": "Invalid configuration"},
                execution_time=0.0,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        
        start_time = time.time()
        
        try:
            result = await self.execute(data)
            result.execution_time = time.time() - start_time
            result.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            self.logger.info(
                f"Check {self.config.check_name or self.__class__.__name__} completed: {result.status} "
                f"(score: {result.score:.3f}, time: {result.execution_time:.3f}s)"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.logger.error(f"Check {self.config.check_name or self.__class__.__name__} failed: {str(e)}")
            
            return CheckResult(
                check_name=self.config.check_name or self.__class__.__name__,
                check_type=self.config.check_type or "unknown",
                status="error",
                score=0.0,
                details={"error": str(e)},
                execution_time=execution_time,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
            )
    
    def get_description(self) -> str:
        """Get the check description."""
        return self.config.description or f"{self.config.check_type or 'unknown'} check"
    
    def get_severity(self) -> str:
        """Get the check severity level."""
        return self.config.severity
    
    def is_enabled(self) -> bool:
        """Check if the quality check is enabled."""
        return self.config.enabled
    
    def update_config(self, **kwargs) -> None:
        """Update the check configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self.logger.info(f"Updated configuration for {self.config.check_name or self.__class__.__name__}")
    
    def __str__(self) -> str:
        """String representation of the quality check."""
        return f"{self.__class__.__name__}({self.config.check_name or 'unnamed'})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the quality check."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.config.check_name or 'unnamed'}', "
            f"type='{self.config.check_type or 'unknown'}', "
            f"enabled={self.config.enabled}, "
            f"severity='{self.config.severity}')"
        )
