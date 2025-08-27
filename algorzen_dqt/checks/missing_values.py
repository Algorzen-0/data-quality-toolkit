"""
Missing Values Quality Check Implementation.

This module provides comprehensive missing value detection and analysis
for various data types and patterns.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from .base import QualityCheck, CheckConfig, CheckResult
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MissingValuesConfig(CheckConfig):
    """Configuration for missing values check."""
    
    # Thresholds
    missing_threshold: float = 0.1  # 10% missing data threshold
    critical_threshold: float = 0.5  # 50% missing data critical threshold
    
    # Detection methods
    detect_empty_strings: bool = True
    detect_whitespace: bool = True
    detect_na_values: bool = True
    detect_custom_na: List[str] = ["N/A", "NULL", "null", "None", "none", ""]
    
    # Analysis options
    analyze_patterns: bool = True
    analyze_correlations: bool = True
    suggest_imputation: bool = True
    
    # Reporting
    include_heatmap: bool = True
    include_patterns: bool = True
    include_recommendations: bool = True


class MissingValuesCheck(QualityCheck):
    """
    Advanced missing values quality check.
    
    This check provides comprehensive analysis of missing data including:
    - Statistical analysis of missing patterns
    - Pattern detection and correlation analysis
    - Imputation recommendations
    - Visual heatmap generation
    """
    
    def __init__(self, config: Optional[MissingValuesConfig] = None):
        """Initialize the missing values check."""
        if config is None:
            config = MissingValuesConfig()
        config.check_name = "Missing Values Analysis"
        config.check_type = "missing_values"
        super().__init__(config)
        self.config = self.config  # Type hint for IDE
        
    def validate_config(self) -> bool:
        """Validate the configuration."""
        if not 0 <= self.config.missing_threshold <= 1:
            logger.error("Missing threshold must be between 0 and 1")
            return False
        
        if not 0 <= self.config.critical_threshold <= 1:
            logger.error("Critical threshold must be between 0 and 1")
            return False
            
        if self.config.missing_threshold >= self.config.critical_threshold:
            logger.error("Missing threshold must be less than critical threshold")
            return False
            
        return True
    
    async def execute(self, data: pd.DataFrame) -> CheckResult:
        """Execute the missing values check."""
        start_time = datetime.now()
        
        try:
            # Validate configuration
            if not self.validate_config():
                raise ValueError("Invalid configuration")
            
            # Analyze missing values
            missing_analysis = self._analyze_missing_values(data)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(missing_analysis)
            
            # Determine status
            status = self._determine_status(quality_score, missing_analysis)
            
            # Generate detailed results
            details = self._generate_details(missing_analysis)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CheckResult(
                check_name="Missing Values Analysis",
                check_type="missing_values",
                status=status,
                score=quality_score,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                details=details,
                affected_rows=missing_analysis["total_rows"],
                affected_columns=list(data.columns)
            )
            
        except Exception as e:
            logger.error(f"Error in missing values check: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CheckResult(
                check_name="Missing Values Analysis",
                check_type="missing_values",
                status="error",
                score=0.0,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                details={"error": str(e)}
            )
    
    def _analyze_missing_values(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze missing values in the dataset."""
        analysis = {
            "total_rows": len(data),
            "total_columns": len(data.columns),
            "missing_counts": {},
            "missing_percentages": {},
            "columns_with_missing": 0,
            "overall_missing_percentage": 0.0,
            "missing_patterns": {},
            "correlations": {},
            "recommendations": []
        }
        
        # Analyze each column
        for column in data.columns:
            missing_count = self._count_missing_values(data[column])
            missing_percentage = missing_count / len(data)
            
            analysis["missing_counts"][column] = missing_count
            analysis["missing_percentages"][column] = missing_percentage
            
            if missing_count > 0:
                analysis["columns_with_missing"] += 1
        
        # Calculate overall statistics
        total_missing = sum(analysis["missing_counts"].values())
        total_cells = analysis["total_rows"] * analysis["total_columns"]
        analysis["overall_missing_percentage"] = total_missing / total_cells
        
        # Analyze patterns if enabled
        if self.config.analyze_patterns:
            analysis["missing_patterns"] = self._analyze_missing_patterns(data)
        
        # Analyze correlations if enabled
        if self.config.analyze_correlations:
            analysis["correlations"] = self._analyze_missing_correlations(data)
        
        # Generate recommendations if enabled
        if self.config.suggest_imputation:
            analysis["recommendations"] = self._generate_imputation_recommendations(analysis)
        
        return analysis
    
    def _count_missing_values(self, series: pd.Series) -> int:
        """Count missing values in a series using multiple detection methods."""
        missing_count = 0
        
        # Standard pandas missing values
        if self.config.detect_na_values:
            missing_count += series.isna().sum()
        
        # Empty strings
        if self.config.detect_empty_strings:
            missing_count += (series == "").sum()
        
        # Whitespace-only strings
        if self.config.detect_whitespace:
            missing_count += series.astype(str).str.strip().eq("").sum()
        
        # Custom NA values
        if self.config.detect_custom_na:
            for na_value in self.config.detect_custom_na:
                missing_count += (series == na_value).sum()
        
        return int(missing_count)
    
    def _analyze_missing_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in missing data."""
        patterns = {
            "row_patterns": {},
            "column_patterns": {},
            "systematic_missing": []
        }
        
        # Analyze row patterns (rows with similar missing patterns)
        missing_matrix = data.isna()
        row_patterns = missing_matrix.apply(tuple, axis=1)
        pattern_counts = row_patterns.value_counts()
        
        # Find systematic missing patterns
        for pattern, count in pattern_counts.items():
            if count > len(data) * 0.1:  # Pattern appears in >10% of rows
                patterns["systematic_missing"].append({
                    "pattern": pattern,
                    "count": count,
                    "percentage": count / len(data)
                })
        
        patterns["row_patterns"] = pattern_counts.head(10).to_dict()
        
        return patterns
    
    def _analyze_missing_correlations(self, data: pd.DataFrame) -> Dict[str, float]:
        """Analyze correlations between missing values in different columns."""
        correlations = {}
        
        # Create missing value matrix
        missing_matrix = data.isna().astype(int)
        
        # Calculate correlations between missing value patterns
        for i, col1 in enumerate(missing_matrix.columns):
            for j, col2 in enumerate(missing_matrix.columns):
                if i < j:  # Avoid duplicate calculations
                    corr = missing_matrix[col1].corr(missing_matrix[col2])
                    if not pd.isna(corr) and abs(corr) > 0.3:  # Only significant correlations
                        correlations[f"{col1}_vs_{col2}"] = corr
        
        return correlations
    
    def _generate_imputation_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate imputation recommendations based on missing data analysis."""
        recommendations = []
        
        # Overall recommendations
        if analysis["overall_missing_percentage"] > self.config.critical_threshold:
            recommendations.append("CRITICAL: Dataset has >50% missing data. Consider data source investigation.")
        elif analysis["overall_missing_percentage"] > self.config.missing_threshold:
            recommendations.append("WARNING: Dataset has >10% missing data. Implement imputation strategies.")
        
        # Column-specific recommendations
        for column, percentage in analysis["missing_percentages"].items():
            if percentage > self.config.critical_threshold:
                recommendations.append(f"CRITICAL: Column '{column}' has {percentage:.1%} missing data")
            elif percentage > self.config.missing_threshold:
                recommendations.append(f"WARNING: Column '{column}' has {percentage:.1%} missing data")
        
        # Pattern-based recommendations
        if analysis["missing_patterns"]["systematic_missing"]:
            recommendations.append("PATTERN: Systematic missing data detected. Investigate data collection process.")
        
        # Correlation-based recommendations
        if analysis["correlations"]:
            recommendations.append("CORRELATION: Missing values are correlated between columns. Consider joint imputation.")
        
        return recommendations
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate quality score based on missing data analysis."""
        base_score = 1.0
        
        # Penalize based on overall missing percentage
        missing_penalty = analysis["overall_missing_percentage"] * 0.5
        base_score -= missing_penalty
        
        # Penalize based on number of columns with missing data
        columns_penalty = (analysis["columns_with_missing"] / analysis["total_columns"]) * 0.2
        base_score -= columns_penalty
        
        # Penalize for systematic missing patterns
        if analysis["missing_patterns"]["systematic_missing"]:
            base_score -= 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))
    
    def _determine_status(self, quality_score: float, analysis: Dict[str, Any]) -> str:
        """Determine the status based on quality score and analysis."""
        if quality_score >= 0.9:
            return "passed"
        elif quality_score >= 0.7:
            return "warning"
        elif quality_score >= 0.5:
            return "failed"
        else:
            return "critical"
    
    def _generate_details(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed results for reporting."""
        return {
            "summary": {
                "total_missing_cells": sum(analysis["missing_counts"].values()),
                "overall_missing_percentage": f"{analysis['overall_missing_percentage']:.2%}",
                "columns_with_missing": analysis["columns_with_missing"],
                "critical_columns": [
                    col for col, pct in analysis["missing_percentages"].items()
                    if pct > self.config.critical_threshold
                ]
            },
            "column_analysis": {
                col: {
                    "missing_count": count,
                    "missing_percentage": f"{analysis['missing_percentages'][col]:.2%}",
                    "status": "critical" if analysis["missing_percentages"][col] > self.config.critical_threshold
                             else "warning" if analysis["missing_percentages"][col] > self.config.missing_threshold
                             else "good"
                }
                for col, count in analysis["missing_counts"].items()
                if count > 0
            },
            "patterns": analysis["missing_patterns"],
            "correlations": analysis["correlations"],
            "recommendations": analysis["recommendations"]
        }
