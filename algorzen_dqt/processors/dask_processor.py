"""
Dask Processor for the Algorzen Data Quality Toolkit.

This module provides:
- Distributed data processing with Dask
- Parallel quality checks
- Memory-efficient large dataset handling
- Dask DataFrame operations
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
import dask.dataframe as dd
import dask.array as da
from dask.distributed import Client, LocalCluster
import pandas as pd
import numpy as np
from dask_ml.feature_extraction.text import HashingVectorizer
from dask_ml.preprocessing import StandardScaler
from dask_ml.cluster import KMeans
import dask.bag as db

from ..utils.logging import get_logger

logger = get_logger(__name__)


class DaskProcessor:
    """Dask-based distributed data processor for big data quality checks."""
    
    def __init__(self, n_workers: int = 4, threads_per_worker: int = 2, memory_limit: str = "2GB"):
        """Initialize Dask processor with distributed client."""
        try:
            # Create local cluster
            self.cluster = LocalCluster(
                n_workers=n_workers,
                threads_per_worker=threads_per_worker,
                memory_limit=memory_limit,
                dashboard_address=":8787"
            )
            
            # Create distributed client
            self.client = Client(self.cluster)
            
            logger.info(f"Dask cluster initialized with {n_workers} workers, {threads_per_worker} threads each")
            logger.info(f"Dashboard available at: {self.client.dashboard_link}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Dask: {e}")
            raise
    
    def load_data(self, source_path: str, file_format: str = "auto", **kwargs) -> dd.DataFrame:
        """Load data from various sources into Dask DataFrame."""
        try:
            if file_format == "auto":
                file_format = self._detect_file_format(source_path)
            
            if file_format == "csv":
                df = dd.read_csv(source_path, **kwargs)
            elif file_format == "parquet":
                df = dd.read_parquet(source_path, **kwargs)
            elif file_format == "json":
                df = dd.read_json(source_path, **kwargs)
            elif file_format == "hdf5":
                df = dd.read_hdf(source_path, **kwargs)
            elif file_format == "sql":
                # For SQL databases, you'd need to specify table name
                table_name = kwargs.get("table_name", "data")
                df = dd.read_sql_table(table_name, source_path, **kwargs)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            # Get basic info
            n_partitions = df.npartitions
            logger.info(f"Data loaded from {source_path}: {n_partitions} partitions")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def _detect_file_format(self, source_path: str) -> str:
        """Detect file format from path."""
        if source_path.endswith('.csv'):
            return 'csv'
        elif source_path.endswith('.parquet'):
            return 'parquet'
        elif source_path.endswith('.json'):
            return 'json'
        elif source_path.endswith('.h5') or source_path.endswith('.hdf5'):
            return 'hdf5'
        else:
            return 'csv'  # Default
    
    def get_data_profile(self, df: dd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive data profile using Dask."""
        try:
            profile = {
                "basic_stats": {},
                "column_stats": {},
                "data_quality": {},
                "partition_info": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Basic statistics
            total_rows = df.shape[0].compute()
            total_columns = df.shape[1].compute()
            
            profile["basic_stats"] = {
                "total_rows": total_rows,
                "total_columns": total_columns,
                "n_partitions": df.npartitions,
                "partition_size": total_rows / df.npartitions
            }
            
            # Partition information
            profile["partition_info"] = {
                "n_partitions": df.npartitions,
                "partition_sizes": df.map_partitions(len).compute().tolist(),
                "memory_usage_per_partition": df.memory_usage_per_partition().compute().tolist()
            }
            
            # Column statistics
            for column in df.columns:
                col_stats = self._get_column_statistics(df, column)
                profile["column_stats"][column] = col_stats
            
            # Data quality metrics
            profile["data_quality"] = self._calculate_data_quality_metrics(df)
            
            logger.info(f"Data profile generated for {total_rows} rows across {df.npartitions} partitions")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to generate data profile: {e}")
            raise
    
    def _get_column_statistics(self, df: dd.DataFrame, column: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific column."""
        try:
            col_df = df[column]
            
            stats = {
                "dtype": str(col_df.dtype),
                "null_count": col_df.isnull().sum().compute(),
                "distinct_count": col_df.nunique().compute()
            }
            
            # Numeric column statistics
            if np.issubdtype(col_df.dtype, np.number):
                numeric_stats = col_df.describe().compute()
                for stat_name, value in numeric_stats.items():
                    stats[stat_name] = float(value)
                
                # Additional numeric stats
                stats["skewness"] = float(col_df.skew().compute())
                stats["kurtosis"] = float(col_df.kurt().compute())
            
            # String column statistics
            elif col_df.dtype == 'object':
                # String length statistics
                str_lengths = col_df.str.len()
                stats["avg_length"] = float(str_lengths.mean().compute())
                stats["max_length"] = int(str_lengths.max().compute())
                stats["min_length"] = int(str_lengths.min().compute())
                
                # Pattern analysis
                patterns = self._analyze_string_patterns(col_df)
                stats["patterns"] = patterns
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get column statistics for {column}: {e}")
            return {"error": str(e)}
    
    def _analyze_string_patterns(self, col_df: dd.Series) -> Dict[str, Any]:
        """Analyze patterns in string columns."""
        try:
            # Sample data for pattern analysis
            sample_size = min(1000, col_df.count().compute())
            sample_data = col_df.dropna().sample(n=sample_size).compute()
            
            patterns = {
                "email_pattern": sum(1 for v in sample_data if '@' in str(v) and '.' in str(v)),
                "phone_pattern": sum(1 for v in sample_data if any(c.isdigit() for c in str(v))),
                "date_pattern": sum(1 for v in sample_data if '/' in str(v) or '-' in str(v)),
                "numeric_pattern": sum(1 for v in sample_data if str(v).replace('.', '').replace('-', '').isdigit()),
                "url_pattern": sum(1 for v in sample_data if 'http' in str(v).lower() or 'www' in str(v).lower())
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze string patterns: {e}")
            return {"error": str(e)}
    
    def _calculate_data_quality_metrics(self, df: dd.DataFrame) -> Dict[str, Any]:
        """Calculate overall data quality metrics."""
        try:
            total_rows = df.shape[0].compute()
            
            # Missing values analysis
            missing_counts = {}
            for column in df.columns:
                missing_count = df[column].isnull().sum().compute()
                missing_counts[column] = {
                    "count": int(missing_count),
                    "percentage": (missing_count / total_rows) * 100
                }
            
            # Duplicate analysis
            duplicate_count = df.shape[0].compute() - df.drop_duplicates().shape[0].compute()
            
            # Data type consistency
            type_consistency = {}
            for column in df.columns:
                try:
                    # Test data type consistency
                    test_df = df[column].astype('string')
                    test_df.compute()
                    type_consistency[column] = "consistent"
                except:
                    type_consistency[column] = "inconsistent"
            
            return {
                "missing_values": missing_counts,
                "duplicate_rows": {
                    "count": int(duplicate_count),
                    "percentage": (duplicate_count / total_rows) * 100
                },
                "type_consistency": type_consistency,
                "completeness_score": self._calculate_completeness_score(missing_counts, total_rows)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate data quality metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_completeness_score(self, missing_counts: Dict, total_rows: int) -> float:
        """Calculate data completeness score."""
        try:
            total_missing = sum(missing_counts[col]["count"] for col in missing_counts)
            total_cells = total_rows * len(missing_counts)
            completeness = ((total_cells - total_missing) / total_cells) * 100
            return round(completeness, 2)
        except:
            return 0.0
    
    def run_quality_checks(self, df: dd.DataFrame, check_types: List[str]) -> Dict[str, Any]:
        """Run quality checks on Dask DataFrame."""
        try:
            results = {
                "checks": {},
                "summary": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for check_type in check_types:
                if check_type == "missing_values":
                    results["checks"]["missing_values"] = self._check_missing_values(df)
                elif check_type == "duplicates":
                    results["checks"]["duplicates"] = self._check_duplicates(df)
                elif check_type == "outliers":
                    results["checks"]["outliers"] = self._check_outliers(df)
                elif check_type == "data_types":
                    results["checks"]["data_types"] = self._check_data_types(df)
                elif check_type == "patterns":
                    results["checks"]["patterns"] = self._check_patterns(df)
                elif check_type == "distributions":
                    results["checks"]["distributions"] = self._check_distributions(df)
                else:
                    logger.warning(f"Unknown check type: {check_type}")
            
            # Generate summary
            results["summary"] = self._generate_check_summary(results["checks"])
            
            logger.info(f"Quality checks completed: {len(results['checks'])} checks")
            return results
            
        except Exception as e:
            logger.error(f"Failed to run quality checks: {e}")
            raise
    
    def _check_missing_values(self, df: dd.DataFrame) -> Dict[str, Any]:
        """Check for missing values in DataFrame."""
        try:
            missing_stats = {}
            total_rows = df.shape[0].compute()
            
            for column in df.columns:
                null_count = df[column].isnull().sum().compute()
                missing_stats[column] = {
                    "null_count": int(null_count),
                    "null_percentage": (null_count / total_rows) * 100,
                    "completeness": ((total_rows - null_count) / total_rows) * 100
                }
            
            return {
                "total_columns": len(df.columns),
                "columns_with_missing": len([c for c in missing_stats if missing_stats[c]["null_count"] > 0]),
                "column_details": missing_stats,
                "overall_completeness": sum(missing_stats[c]["completeness"] for c in missing_stats) / len(missing_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to check missing values: {e}")
            return {"error": str(e)}
    
    def _check_duplicates(self, df: dd.DataFrame) -> Dict[str, Any]:
        """Check for duplicate rows in DataFrame."""
        try:
            total_rows = df.shape[0].compute()
            unique_rows = df.drop_duplicates().shape[0].compute()
            duplicate_count = total_rows - unique_rows
            
            # Check for duplicates based on specific columns
            key_columns = df.columns[:min(3, len(df.columns))]  # Use first 3 columns as key
            key_duplicates = df.groupby(key_columns).size().reset_index(name='count')
            key_duplicate_count = key_duplicates[key_duplicates['count'] > 1].shape[0].compute()
            
            return {
                "total_rows": int(total_rows),
                "unique_rows": int(unique_rows),
                "duplicate_rows": int(duplicate_count),
                "duplicate_percentage": (duplicate_count / total_rows) * 100,
                "key_based_duplicates": int(key_duplicate_count),
                "key_columns": key_columns
            }
            
        except Exception as e:
            logger.error(f"Failed to check duplicates: {e}")
            return {"error": str(e)}
    
    def _check_outliers(self, df: dd.DataFrame) -> Dict[str, Any]:
        """Check for outliers in numeric columns."""
        try:
            numeric_columns = [col for col in df.columns if np.issubdtype(df[col].dtype, np.number)]
            
            outlier_stats = {}
            for column in numeric_columns:
                col_stats = df[column].describe().compute()
                
                if len(col_stats) >= 4:  # Ensure we have quartiles
                    q1 = col_stats['25%']
                    q3 = col_stats['75%']
                    iqr = q3 - q1
                    
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    # Count outliers
                    outlier_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
                    outlier_count = outlier_mask.sum().compute()
                    
                    outlier_stats[column] = {
                        "q1": float(q1),
                        "q3": float(q3),
                        "iqr": float(iqr),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                        "outlier_count": int(outlier_count),
                        "outlier_percentage": (outlier_count / df.shape[0].compute()) * 100
                    }
            
            return {
                "numeric_columns": len(numeric_columns),
                "columns_with_outliers": len([c for c in outlier_stats if outlier_stats[c]["outlier_count"] > 0]),
                "column_details": outlier_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to check outliers: {e}")
            return {"error": str(e)}
    
    def _check_data_types(self, df: dd.DataFrame) -> Dict[str, Any]:
        """Check data type consistency and validity."""
        try:
            type_analysis = {}
            
            for column in df.columns:
                col_type = str(df[column].dtype)
                type_analysis[column] = {
                    "declared_type": col_type,
                    "sample_values": df[column].dropna().head(5).compute().tolist()
                }
            
            return {
                "total_columns": len(df.columns),
                "column_types": type_analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to check data types: {e}")
            return {"error": str(e)}
    
    def _check_patterns(self, df: dd.DataFrame) -> Dict[str, Any]:
        """Check for patterns in data."""
        try:
            pattern_analysis = {}
            
            for column in df.columns:
                col_type = str(df[column].dtype)
                
                if col_type == 'object':
                    patterns = self._analyze_string_patterns(df[column])
                    pattern_analysis[column] = {
                        "data_type": col_type,
                        "patterns": patterns
                    }
            
            return {
                "string_columns": len([c for c in pattern_analysis if pattern_analysis[c]["data_type"] == "object"]),
                "pattern_details": pattern_analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to check patterns: {e}")
            return {"error": str(e)}
    
    def _check_distributions(self, df: dd.DataFrame) -> Dict[str, Any]:
        """Check data distributions for numeric columns."""
        try:
            numeric_columns = [col for col in df.columns if np.issubdtype(df[col].dtype, np.number)]
            
            distribution_stats = {}
            for column in numeric_columns:
                col_stats = df[column].describe().compute()
                
                distribution_stats[column] = {
                    "mean": float(col_stats['mean']),
                    "std": float(col_stats['std']),
                    "min": float(col_stats['min']),
                    "max": float(col_stats['max']),
                    "skewness": float(df[column].skew().compute()),
                    "kurtosis": float(df[column].kurt().compute())
                }
            
            return {
                "numeric_columns": len(numeric_columns),
                "distribution_details": distribution_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to check distributions: {e}")
            return {"error": str(e)}
    
    def _generate_check_summary(self, checks: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of all quality checks."""
        try:
            summary = {
                "total_checks": len(checks),
                "checks_passed": 0,
                "checks_failed": 0,
                "overall_score": 0.0
            }
            
            scores = []
            for check_name, check_result in checks.items():
                if "error" not in check_result:
                    # Calculate score based on check type
                    if check_name == "missing_values":
                        score = check_result.get("overall_completeness", 0) / 100
                    elif check_name == "duplicates":
                        score = 1 - (check_result.get("duplicate_percentage", 0) / 100)
                    elif check_name == "outliers":
                        total_outliers = sum(check_result["column_details"][c]["outlier_count"] for c in check_result["column_details"])
                        total_rows = sum(check_result["column_details"][c].get("total_rows", 1000) for c in check_result["column_details"])
                        score = 1 - (total_outliers / total_rows) if total_rows > 0 else 1.0
                    else:
                        score = 0.8  # Default score for other checks
                    
                    scores.append(score)
                    if score >= 0.8:
                        summary["checks_passed"] += 1
                    else:
                        summary["checks_failed"] += 1
                else:
                    summary["checks_failed"] += 1
                    scores.append(0.0)
            
            if scores:
                summary["overall_score"] = round(sum(scores) / len(scores) * 100, 2)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate check summary: {e}")
            return {"error": str(e)}
    
    def save_results(self, df: dd.DataFrame, output_path: str, format: str = "parquet") -> bool:
        """Save processed DataFrame to output path."""
        try:
            if format == "parquet":
                df.to_parquet(output_path, write_index=False)
            elif format == "csv":
                df.to_csv(output_path, single_file=False, index=False)
            elif format == "json":
                df.to_json(output_path)
            else:
                raise ValueError(f"Unsupported output format: {format}")
            
            logger.info(f"Results saved to {output_path} in {format} format")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Get information about the Dask cluster."""
        try:
            info = {
                "n_workers": len(self.cluster.workers),
                "n_threads": sum(w.nthreads for w in self.cluster.workers.values()),
                "memory_limit": str(self.cluster.memory_limit),
                "dashboard_link": self.client.dashboard_link,
                "cluster_status": "active"
            }
            
            # Get worker information
            workers_info = {}
            for worker_id, worker in self.cluster.workers.items():
                workers_info[worker_id] = {
                    "nthreads": worker.nthreads,
                    "memory_limit": str(worker.memory_limit),
                    "status": "active"
                }
            
            info["workers"] = workers_info
            return info
            
        except Exception as e:
            logger.error(f"Failed to get cluster info: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """Clean up Dask resources."""
        try:
            if hasattr(self, 'client'):
                self.client.close()
            if hasattr(self, 'cluster'):
                self.cluster.close()
            logger.info("Dask cluster and client closed")
        except Exception as e:
            logger.error(f"Failed to cleanup Dask: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
