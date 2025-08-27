"""
Outlier Detection Quality Check Implementation.

This module provides comprehensive outlier detection using multiple statistical methods:
- Z-score method
- IQR (Interquartile Range) method
- Modified Z-score method
- Isolation Forest
- Local Outlier Factor (LOF)
- DBSCAN clustering
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import warnings
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import DBSCAN

from .base import QualityCheck, CheckConfig, CheckResult
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')


class OutliersConfig(CheckConfig):
    """Configuration for outlier detection check."""
    
    # Detection methods
    zscore_method: bool = True
    iqr_method: bool = True
    modified_zscore: bool = True
    isolation_forest: bool = False  # More computationally intensive
    local_outlier_factor: bool = False
    dbscan_method: bool = False
    
    # Thresholds
    zscore_threshold: float = 3.0  # Standard deviations for Z-score
    iqr_multiplier: float = 1.5  # IQR multiplier
    modified_zscore_threshold: float = 3.5  # Modified Z-score threshold
    
    # Isolation Forest parameters
    if_contamination: float = 0.1  # Expected proportion of outliers
    if_random_state: int = 42
    
    # LOF parameters
    lof_contamination: float = 0.1
    lof_n_neighbors: int = 20
    
    # DBSCAN parameters
    dbscan_eps: float = 0.5
    dbscan_min_samples: int = 5
    
    # Analysis options
    analyze_outlier_patterns: bool = True
    suggest_treatment: bool = True
    include_visualization: bool = True
    
    # Performance options
    max_rows_for_ml: int = 100000  # Use ML methods only for datasets <= this size
    use_sampling: bool = True
    sample_size: int = 10000


class OutliersCheck(QualityCheck):
    """
    Advanced outlier detection quality check.
    
    This check provides comprehensive outlier detection including:
    - Multiple statistical methods for outlier detection
    - Pattern analysis and correlation detection
    - Treatment recommendations
    - Performance optimization for large datasets
    """
    
    def __init__(self, config: Optional[OutliersConfig] = None):
        """Initialize the outliers check."""
        if config is None:
            config = OutliersConfig()
        config.check_name = "Outlier Detection Analysis"
        config.check_type = "outliers"
        super().__init__(config)
        self.config = self.config  # Type hint for IDE
        
    def validate_config(self) -> bool:
        """Validate the configuration."""
        if self.config.zscore_threshold <= 0:
            logger.error("Z-score threshold must be positive")
            return False
        
        if self.config.iqr_multiplier <= 0:
            logger.error("IQR multiplier must be positive")
            return False
            
        if not 0 < self.config.if_contamination < 0.5:
            logger.error("Isolation Forest contamination must be between 0 and 0.5")
            return False
            
        if not 0 < self.config.lof_contamination < 0.5:
            logger.error("LOF contamination must be between 0 and 0.5")
            return False
            
        return True
    
    async def execute(self, data: pd.DataFrame) -> CheckResult:
        """Execute the outlier detection check."""
        start_time = datetime.now()
        
        try:
            # Validate configuration
            if not self.validate_config():
                raise ValueError("Invalid configuration")
            
            # Detect outliers using multiple methods
            outlier_analysis = await self._detect_outliers(data)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(outlier_analysis)
            
            # Determine status
            status = self._determine_status(quality_score, outlier_analysis)
            
            # Generate detailed results
            details = self._generate_details(outlier_analysis)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CheckResult(
                check_name="Outlier Detection Analysis",
                check_type="outliers",
                status=status,
                score=quality_score,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                details=details,
                affected_rows=outlier_analysis["total_outlier_rows"],
                affected_columns=outlier_analysis["numeric_columns"]
            )
            
        except Exception as e:
            logger.error(f"Error in outlier detection check: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CheckResult(
                check_name="Outlier Detection Analysis",
                check_type="outliers",
                status="error",
                score=0.0,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                details={"error": str(e)}
            )
    
    async def _detect_outliers(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect outliers using multiple methods."""
        analysis = {
            "total_rows": len(data),
            "numeric_columns": [],
            "outlier_results": {},
            "total_outlier_rows": 0,
            "outlier_percentage": 0.0,
            "outlier_patterns": {},
            "recommendations": []
        }
        
        # Identify numeric columns
        numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
        analysis["numeric_columns"] = numeric_columns
        
        if not numeric_columns:
            logger.warning("No numeric columns found for outlier detection")
            return analysis
        
        # Use sampling for large datasets
        if len(data) > self.config.max_rows_for_ml and self.config.use_sampling:
            sample_data = data.sample(n=min(self.config.sample_size, len(data)), random_state=42)
            logger.info(f"Using sampling for outlier detection: {len(sample_data)} rows")
        else:
            sample_data = data
        
        # Detect outliers using different methods
        if self.config.zscore_method:
            analysis["outlier_results"]["zscore"] = self._detect_zscore_outliers(sample_data, numeric_columns)
        
        if self.config.iqr_method:
            analysis["outlier_results"]["iqr"] = self._detect_iqr_outliers(sample_data, numeric_columns)
        
        if self.config.modified_zscore:
            analysis["outlier_results"]["modified_zscore"] = self._detect_modified_zscore_outliers(sample_data, numeric_columns)
        
        if self.config.isolation_forest and len(sample_data) <= self.config.max_rows_for_ml:
            analysis["outlier_results"]["isolation_forest"] = await self._detect_isolation_forest_outliers(sample_data, numeric_columns)
        
        if self.config.local_outlier_factor and len(sample_data) <= self.config.max_rows_for_ml:
            analysis["outlier_results"]["lof"] = await self._detect_lof_outliers(sample_data, numeric_columns)
        
        if self.config.dbscan_method and len(sample_data) <= self.config.max_rows_for_ml:
            analysis["outlier_results"]["dbscan"] = await self._detect_dbscan_outliers(sample_data, numeric_columns)
        
        # Aggregate outlier results
        all_outlier_rows = set()
        for method_name, method_results in analysis["outlier_results"].items():
            if isinstance(method_results, dict) and "outlier_rows" in method_results:
                all_outlier_rows.update(method_results["outlier_rows"])
        
        analysis["total_outlier_rows"] = len(all_outlier_rows)
        analysis["outlier_percentage"] = analysis["total_outlier_rows"] / analysis["total_rows"]
        
        # Analyze patterns if enabled
        if self.config.analyze_outlier_patterns:
            analysis["outlier_patterns"] = self._analyze_outlier_patterns(sample_data, all_outlier_rows, numeric_columns)
        
        # Generate recommendations if enabled
        if self.config.suggest_treatment:
            analysis["recommendations"] = self._generate_treatment_recommendations(analysis)
        
        return analysis
    
    def _detect_zscore_outliers(self, data: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Detect outliers using Z-score method."""
        outlier_rows = set()
        column_outliers = {}
        
        for column in numeric_columns:
            # Remove NaN values for calculation
            clean_data = data[column].dropna()
            if len(clean_data) == 0:
                continue
            
            # Calculate Z-scores
            z_scores = np.abs(stats.zscore(clean_data))
            outlier_mask = z_scores > self.config.zscore_threshold
            
            if outlier_mask.any():
                outlier_indices = clean_data[outlier_mask].index.tolist()
                outlier_rows.update(outlier_indices)
                column_outliers[column] = {
                    "count": len(outlier_indices),
                    "indices": outlier_indices,
                    "z_scores": z_scores[outlier_mask].tolist()
                }
        
        return {
            "outlier_rows": list(outlier_rows),
            "column_outliers": column_outliers,
            "total_outliers": len(outlier_rows),
            "method": "zscore",
            "threshold": self.config.zscore_threshold
        }
    
    def _detect_iqr_outliers(self, data: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Detect outliers using IQR method."""
        outlier_rows = set()
        column_outliers = {}
        
        for column in numeric_columns:
            # Remove NaN values for calculation
            clean_data = data[column].dropna()
            if len(clean_data) == 0:
                continue
            
            # Calculate Q1, Q3, and IQR
            Q1 = clean_data.quantile(0.25)
            Q3 = clean_data.quantile(0.75)
            IQR = Q3 - Q1
            
            # Define bounds
            lower_bound = Q1 - self.config.iqr_multiplier * IQR
            upper_bound = Q3 + self.config.iqr_multiplier * IQR
            
            # Find outliers
            outlier_mask = (clean_data < lower_bound) | (clean_data > upper_bound)
            
            if outlier_mask.any():
                outlier_indices = clean_data[outlier_mask].index.tolist()
                outlier_rows.update(outlier_indices)
                column_outliers[column] = {
                    "count": len(outlier_indices),
                    "indices": outlier_indices,
                    "bounds": {"lower": lower_bound, "upper": upper_bound},
                    "iqr": IQR
                }
        
        return {
            "outlier_rows": list(outlier_rows),
            "column_outliers": column_outliers,
            "total_outliers": len(outlier_rows),
            "method": "iqr",
            "multiplier": self.config.iqr_multiplier
        }
    
    def _detect_modified_zscore_outliers(self, data: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Detect outliers using modified Z-score method (more robust to extreme values)."""
        outlier_rows = set()
        column_outliers = {}
        
        for column in numeric_columns:
            # Remove NaN values for calculation
            clean_data = data[column].dropna()
            if len(clean_data) == 0:
                continue
            
            # Calculate median and MAD (Median Absolute Deviation)
            median = clean_data.median()
            mad = np.median(np.abs(clean_data - median))
            
            if mad == 0:
                continue
            
            # Calculate modified Z-scores
            modified_z_scores = 0.6745 * (clean_data - median) / mad
            outlier_mask = np.abs(modified_z_scores) > self.config.modified_zscore_threshold
            
            if outlier_mask.any():
                outlier_indices = clean_data[outlier_mask].index.tolist()
                outlier_rows.update(outlier_indices)
                column_outliers[column] = {
                    "count": len(outlier_indices),
                    "indices": outlier_indices,
                    "modified_z_scores": modified_z_scores[outlier_mask].tolist()
                }
        
        return {
            "outlier_rows": list(outlier_rows),
            "column_outliers": column_outliers,
            "total_outliers": len(outlier_rows),
            "method": "modified_zscore",
            "threshold": self.config.modified_zscore_threshold
        }
    
    async def _detect_isolation_forest_outliers(self, data: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Detect outliers using Isolation Forest algorithm."""
        try:
            # Prepare data for ML
            ml_data = data[numeric_columns].fillna(data[numeric_columns].median())
            
            # Initialize and fit Isolation Forest
            iso_forest = IsolationForest(
                contamination=self.config.if_contamination,
                random_state=self.config.if_random_state,
                n_estimators=100
            )
            
            # Fit and predict
            predictions = iso_forest.fit_predict(ml_data)
            
            # -1 indicates outliers
            outlier_mask = predictions == -1
            outlier_indices = data[outlier_mask].index.tolist()
            
            return {
                "outlier_rows": outlier_indices,
                "total_outliers": len(outlier_indices),
                "method": "isolation_forest",
                "contamination": self.config.if_contamination,
                "anomaly_scores": iso_forest.decision_function(ml_data).tolist()
            }
            
        except Exception as e:
            logger.warning(f"Isolation Forest failed: {e}")
            return {
                "outlier_rows": [],
                "total_outliers": 0,
                "method": "isolation_forest",
                "error": str(e)
            }
    
    async def _detect_lof_outliers(self, data: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Detect outliers using Local Outlier Factor algorithm."""
        try:
            # Prepare data for ML
            ml_data = data[numeric_columns].fillna(data[numeric_columns].median())
            
            # Initialize and fit LOF
            lof = LocalOutlierFactor(
                contamination=self.config.lof_contamination,
                n_neighbors=self.config.lof_n_neighbors
            )
            
            # Fit and predict
            predictions = lof.fit_predict(ml_data)
            
            # -1 indicates outliers
            outlier_mask = predictions == -1
            outlier_indices = data[outlier_mask].index.tolist()
            
            return {
                "outlier_rows": outlier_indices,
                "total_outliers": len(outlier_indices),
                "method": "local_outlier_factor",
                "contamination": self.config.lof_contamination,
                "n_neighbors": self.config.lof_n_neighbors,
                "outlier_scores": lof.negative_outlier_factor_.tolist()
            }
            
        except Exception as e:
            logger.warning(f"Local Outlier Factor failed: {e}")
            return {
                "outlier_rows": [],
                "total_outliers": 0,
                "method": "local_outlier_factor",
                "error": str(e)
            }
    
    async def _detect_dbscan_outliers(self, data: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Detect outliers using DBSCAN clustering algorithm."""
        try:
            # Prepare data for ML
            ml_data = data[numeric_columns].fillna(data[numeric_columns].median())
            
            # Initialize and fit DBSCAN
            dbscan = DBSCAN(
                eps=self.config.dbscan_eps,
                min_samples=self.config.dbscan_min_samples
            )
            
            # Fit and predict
            predictions = dbscan.fit_predict(ml_data)
            
            # -1 indicates outliers (noise points)
            outlier_mask = predictions == -1
            outlier_indices = data[outlier_mask].index.tolist()
            
            return {
                "outlier_rows": outlier_indices,
                "total_outliers": len(outlier_indices),
                "method": "dbscan",
                "eps": self.config.dbscan_eps,
                "min_samples": self.config.dbscan_min_samples,
                "n_clusters": len(set(predictions)) - (1 if -1 in predictions else 0)
            }
            
        except Exception as e:
            logger.warning(f"DBSCAN failed: {e}")
            return {
                "outlier_rows": [],
                "total_outliers": 0,
                "method": "dbscan",
                "error": str(e)
            }
    
    def _analyze_outlier_patterns(self, data: pd.DataFrame, outlier_rows: set, numeric_columns: List[str]) -> Dict[str, Any]:
        """Analyze patterns in outlier data."""
        patterns = {
            "column_distribution": {},
            "outlier_clusters": {},
            "correlation_analysis": {}
        }
        
        if not outlier_rows:
            return patterns
        
        outlier_data = data.loc[list(outlier_rows)]
        
        # Analyze column distribution
        for column in numeric_columns:
            if column in outlier_data.columns:
                column_outliers = outlier_data[column].dropna()
                if len(column_outliers) > 0:
                    patterns["column_distribution"][column] = {
                        "count": len(column_outliers),
                        "mean": float(column_outliers.mean()),
                        "std": float(column_outliers.std()),
                        "min": float(column_outliers.min()),
                        "max": float(column_outliers.max())
                    }
        
        # Analyze outlier clusters (rows with multiple outlier values)
        # Simple approach: count rows that appear in multiple outlier detection methods
        patterns["outlier_clusters"] = {
            "rows_with_multiple_outliers": 0,  # Will be updated if we implement method overlap analysis
            "max_outliers_per_row": 1  # Default value
        }
        
        return patterns
    
    def _generate_treatment_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate treatment recommendations for outliers."""
        recommendations = []
        
        # Overall recommendations
        if analysis["outlier_percentage"] > 0.1:
            recommendations.append("CRITICAL: Dataset has >10% outliers. Investigate data quality immediately.")
        elif analysis["outlier_percentage"] > 0.05:
            recommendations.append("WARNING: Dataset has >5% outliers. Consider outlier treatment strategies.")
        
        # Method-specific recommendations
        method_results = analysis["outlier_results"]
        
        if "zscore" in method_results and method_results["zscore"]["total_outliers"] > 0:
            recommendations.append(f"Z-SCORE: {method_results['zscore']['total_outliers']} outliers detected. Consider adjusting threshold.")
        
        if "iqr" in method_results and method_results["iqr"]["total_outliers"] > 0:
            recommendations.append(f"IQR: {method_results['iqr']['total_outliers']} outliers detected. Review IQR multiplier.")
        
        if "isolation_forest" in method_results and method_results["isolation_forest"]["total_outliers"] > 0:
            recommendations.append(f"ISOLATION FOREST: {method_results['isolation_forest']['total_outliers']} outliers detected. Adjust contamination parameter.")
        
        # Pattern-based recommendations
        try:
            if analysis["outlier_patterns"]["outlier_clusters"]["rows_with_multiple_outliers"] > 0:
                recommendations.append("PATTERN: Multiple outliers per row detected. Investigate systematic data quality issues.")
        except (KeyError, TypeError):
            pass  # Skip if pattern analysis is not available
        
        # General recommendations
        if analysis["outlier_percentage"] > 0:
            recommendations.extend([
                "TREATMENT: Consider winsorization for extreme outliers",
                "TREATMENT: Use robust statistical methods for analysis",
                "TREATMENT: Investigate root causes of outlier generation"
            ])
        
        return recommendations
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate quality score based on outlier analysis."""
        base_score = 1.0
        
        # Penalize based on outlier percentage
        outlier_penalty = analysis["outlier_percentage"] * 0.4
        base_score -= outlier_penalty
        
        # Penalize based on number of methods detecting outliers
        methods_with_outliers = sum([
            1 for method_results in analysis["outlier_results"].values()
            if isinstance(method_results, dict) and method_results.get("total_outliers", 0) > 0
        ])
        
        if methods_with_outliers > 0:
            method_penalty = min(0.2, methods_with_outliers * 0.05)
            base_score -= method_penalty
        
        # Penalize for systematic outlier patterns
        try:
            if analysis["outlier_patterns"]["outlier_clusters"]["rows_with_multiple_outliers"] > 0:
                base_score -= 0.1
        except (KeyError, TypeError):
            pass  # Skip if pattern analysis is not available
        
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
                "total_outlier_rows": analysis["total_outlier_rows"],
                "outlier_percentage": f"{analysis['outlier_percentage']:.2%}",
                "numeric_columns_analyzed": len(analysis["numeric_columns"]),
                "methods_used": list(analysis["outlier_results"].keys())
            },
            "method_results": analysis["outlier_results"],
            "patterns": analysis["outlier_patterns"],
            "recommendations": analysis["recommendations"]
        }
