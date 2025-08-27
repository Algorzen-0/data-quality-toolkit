"""
Apache Spark Processor for the Algorzen Data Quality Toolkit.

This module provides:
- Spark-based data quality checks
- Large-scale data processing
- Distributed computing capabilities
- Spark SQL integration
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, when, isnan, isnull, count, sum as spark_sum
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation
from pyspark.ml.clustering import KMeans
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, lag, lead

from ..utils.logging import get_logger

logger = get_logger(__name__)


class SparkProcessor:
    """Apache Spark-based data processor for big data quality checks."""
    
    def __init__(self, app_name: str = "AlgorzenDQT", master: str = "local[*]"):
        """Initialize Spark processor."""
        try:
            self.spark = SparkSession.builder \
                .appName(app_name) \
                .master(master) \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
                .config("spark.sql.adaptive.skewJoin.enabled", "true") \
                .getOrCreate()
            
            logger.info(f"Spark session initialized: {app_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Spark: {e}")
            raise
    
    def load_data(self, source_path: str, file_format: str = "auto") -> DataFrame:
        """Load data from various sources into Spark DataFrame."""
        try:
            if file_format == "auto":
                file_format = self._detect_file_format(source_path)
            
            if file_format == "csv":
                df = self.spark.read.csv(source_path, header=True, inferSchema=True)
            elif file_format == "parquet":
                df = self.spark.read.parquet(source_path)
            elif file_format == "json":
                df = self.spark.read.json(source_path)
            elif file_format == "orc":
                df = self.spark.read.orc(source_path)
            elif file_format == "avro":
                df = self.spark.read.format("avro").load(source_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            logger.info(f"Data loaded from {source_path}: {df.count()} rows, {len(df.columns)} columns")
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
        elif source_path.endswith('.orc'):
            return 'orc'
        elif source_path.endswith('.avro'):
            return 'avro'
        else:
            return 'csv'  # Default
    
    def get_data_profile(self, df: DataFrame) -> Dict[str, Any]:
        """Generate comprehensive data profile using Spark."""
        try:
            profile = {
                "basic_stats": {},
                "column_stats": {},
                "data_quality": {},
                "correlations": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Basic statistics
            total_rows = df.count()
            total_columns = len(df.columns)
            
            profile["basic_stats"] = {
                "total_rows": total_rows,
                "total_columns": total_columns,
                "memory_usage_mb": self._estimate_memory_usage(df),
                "partition_count": df.rdd.getNumPartitions()
            }
            
            # Column statistics
            for column in df.columns:
                col_stats = self._get_column_statistics(df, column)
                profile["column_stats"][column] = col_stats
            
            # Data quality metrics
            profile["data_quality"] = self._calculate_data_quality_metrics(df)
            
            # Correlation analysis for numeric columns
            numeric_columns = [f.name for f in df.schema.fields if isinstance(f.dataType, (IntegerType, DoubleType))]
            if len(numeric_columns) > 1:
                profile["correlations"] = self._calculate_correlations(df, numeric_columns)
            
            logger.info(f"Data profile generated for {total_rows} rows")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to generate data profile: {e}")
            raise
    
    def _get_column_statistics(self, df: DataFrame, column: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific column."""
        try:
            col_df = df.select(column)
            col_type = str(col_df.schema[column].dataType)
            
            stats = {
                "data_type": col_type,
                "null_count": col_df.filter(col(column).isNull()).count(),
                "distinct_count": col_df.distinct().count()
            }
            
            # Numeric column statistics
            if col_type in ["IntegerType", "DoubleType"]:
                numeric_stats = col_df.summary("count", "min", "25%", "50%", "75%", "max", "mean", "stddev")
                for row in numeric_stats.collect():
                    if row[column] is not None:
                        stats[row["summary"]] = float(row[column])
            
            # String column statistics
            elif col_type == "StringType":
                string_stats = col_df.agg(
                    col_df.select(column).rdd.map(lambda x: len(str(x[0])) if x[0] else 0).stats()
                )
                stats["avg_length"] = string_stats.mean()
                stats["max_length"] = string_stats.max()
                stats["min_length"] = string_stats.min()
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get column statistics for {column}: {e}")
            return {"error": str(e)}
    
    def _calculate_data_quality_metrics(self, df: DataFrame) -> Dict[str, Any]:
        """Calculate overall data quality metrics."""
        try:
            total_rows = df.count()
            
            # Missing values analysis
            missing_counts = {}
            for column in df.columns:
                missing_count = df.filter(col(column).isNull()).count()
                missing_counts[column] = {
                    "count": missing_count,
                    "percentage": (missing_count / total_rows) * 100
                }
            
            # Duplicate analysis
            duplicate_count = df.count() - df.dropDuplicates().count()
            
            # Data type consistency
            type_consistency = {}
            for column in df.columns:
                try:
                    # Try to cast to expected type
                    test_df = df.select(col(column).cast("string"))
                    test_df.collect()
                    type_consistency[column] = "consistent"
                except:
                    type_consistency[column] = "inconsistent"
            
            return {
                "missing_values": missing_counts,
                "duplicate_rows": {
                    "count": duplicate_count,
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
    
    def _calculate_correlations(self, df: DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """Calculate correlations between numeric columns."""
        try:
            if len(numeric_columns) < 2:
                return {}
            
            # Prepare data for correlation
            assembler = VectorAssembler(inputCols=numeric_columns, outputCol="features")
            df_vector = assembler.transform(df.select(numeric_columns))
            
            # Calculate correlation matrix
            correlation_matrix = Correlation.corr(df_vector, "features").collect()[0][0]
            
            correlations = {}
            for i, col1 in enumerate(numeric_columns):
                correlations[col1] = {}
                for j, col2 in enumerate(numeric_columns):
                    correlations[col1][col2] = float(correlation_matrix[i, j])
            
            return correlations
            
        except Exception as e:
            logger.error(f"Failed to calculate correlations: {e}")
            return {}
    
    def _estimate_memory_usage(self, df: DataFrame) -> float:
        """Estimate memory usage of DataFrame in MB."""
        try:
            # Sample a small portion to estimate
            sample_size = min(1000, df.count())
            sample_df = df.limit(sample_size)
            
            # Get memory usage from Spark
            memory_usage = sample_df.storageLevel.useMemory
            if memory_usage:
                estimated_total = (memory_usage / sample_size) * df.count()
                return round(estimated_total / (1024 * 1024), 2)  # Convert to MB
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Failed to estimate memory usage: {e}")
            return 0.0
    
    def run_quality_checks(self, df: DataFrame, check_types: List[str]) -> Dict[str, Any]:
        """Run quality checks on Spark DataFrame."""
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
                else:
                    logger.warning(f"Unknown check type: {check_type}")
            
            # Generate summary
            results["summary"] = self._generate_check_summary(results["checks"])
            
            logger.info(f"Quality checks completed: {len(results['checks'])} checks")
            return results
            
        except Exception as e:
            logger.error(f"Failed to run quality checks: {e}")
            raise
    
    def _check_missing_values(self, df: DataFrame) -> Dict[str, Any]:
        """Check for missing values in DataFrame."""
        try:
            missing_stats = {}
            total_rows = df.count()
            
            for column in df.columns:
                null_count = df.filter(col(column).isNull()).count()
                missing_stats[column] = {
                    "null_count": null_count,
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
    
    def _check_duplicates(self, df: DataFrame) -> Dict[str, Any]:
        """Check for duplicate rows in DataFrame."""
        try:
            total_rows = df.count()
            unique_rows = df.dropDuplicates().count()
            duplicate_count = total_rows - unique_rows
            
            # Check for duplicates based on specific columns
            key_columns = df.columns[:min(3, len(df.columns))]  # Use first 3 columns as key
            key_duplicates = df.groupBy(key_columns).count().filter(col("count") > 1)
            key_duplicate_count = key_duplicates.count()
            
            return {
                "total_rows": total_rows,
                "unique_rows": unique_rows,
                "duplicate_rows": duplicate_count,
                "duplicate_percentage": (duplicate_count / total_rows) * 100,
                "key_based_duplicates": key_duplicate_count,
                "key_columns": key_columns
            }
            
        except Exception as e:
            logger.error(f"Failed to check duplicates: {e}")
            return {"error": str(e)}
    
    def _check_outliers(self, df: DataFrame) -> Dict[str, Any]:
        """Check for outliers in numeric columns."""
        try:
            numeric_columns = [f.name for f in df.schema.fields if isinstance(f.dataType, (IntegerType, DoubleType))]
            
            outlier_stats = {}
            for column in numeric_columns:
                col_stats = df.select(column).summary("25%", "75%").collect()
                
                if len(col_stats) >= 2:
                    q1 = float(col_stats[0][column])
                    q3 = float(col_stats[1][column])
                    iqr = q3 - q1
                    
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    outlier_count = df.filter(
                        (col(column) < lower_bound) | (col(column) > upper_bound)
                    ).count()
                    
                    outlier_stats[column] = {
                        "q1": q1,
                        "q3": q3,
                        "iqr": iqr,
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound,
                        "outlier_count": outlier_count,
                        "outlier_percentage": (outlier_count / df.count()) * 100
                    }
            
            return {
                "numeric_columns": len(numeric_columns),
                "columns_with_outliers": len([c for c in outlier_stats if outlier_stats[c]["outlier_count"] > 0]),
                "column_details": outlier_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to check outliers: {e}")
            return {"error": str(e)}
    
    def _check_data_types(self, df: DataFrame) -> Dict[str, Any]:
        """Check data type consistency and validity."""
        try:
            type_analysis = {}
            
            for column in df.columns:
                col_type = str(df.schema[column].dataType)
                type_analysis[column] = {
                    "declared_type": col_type,
                    "sample_values": df.select(column).limit(5).rdd.map(lambda x: str(x[0])).collect()
                }
            
            return {
                "total_columns": len(df.columns),
                "column_types": type_analysis,
                "type_distribution": df.schema.json()
            }
            
        except Exception as e:
            logger.error(f"Failed to check data types: {e}")
            return {"error": str(e)}
    
    def _check_patterns(self, df: DataFrame) -> Dict[str, Any]:
        """Check for patterns in data."""
        try:
            pattern_analysis = {}
            
            for column in df.columns:
                col_type = str(df.schema[column].dataType)
                
                if col_type == "StringType":
                    # Check for common patterns
                    sample_values = df.select(column).limit(100).rdd.map(lambda x: str(x[0])).collect()
                    
                    patterns = {
                        "email_pattern": sum(1 for v in sample_values if '@' in v and '.' in v),
                        "phone_pattern": sum(1 for v in sample_values if any(c.isdigit() for c in v)),
                        "date_pattern": sum(1 for v in sample_values if '/' in v or '-' in v),
                        "numeric_pattern": sum(1 for v in sample_values if v.replace('.', '').replace('-', '').isdigit())
                    }
                    
                    pattern_analysis[column] = {
                        "data_type": col_type,
                        "patterns": patterns,
                        "most_common_pattern": max(patterns, key=patterns.get) if patterns else "none"
                    }
            
            return {
                "string_columns": len([c for c in pattern_analysis if pattern_analysis[c]["data_type"] == "StringType"]),
                "pattern_details": pattern_analysis
            }
            
        except Exception as e:
            logger.error(f"Failed to check patterns: {e}")
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
    
    def save_results(self, df: DataFrame, output_path: str, format: str = "parquet") -> bool:
        """Save processed DataFrame to output path."""
        try:
            if format == "parquet":
                df.write.mode("overwrite").parquet(output_path)
            elif format == "csv":
                df.write.mode("overwrite").csv(output_path, header=True)
            elif format == "json":
                df.write.mode("overwrite").json(output_path)
            else:
                raise ValueError(f"Unsupported output format: {format}")
            
            logger.info(f"Results saved to {output_path} in {format} format")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False
    
    def cleanup(self):
        """Clean up Spark resources."""
        try:
            if hasattr(self, 'spark'):
                self.spark.stop()
                logger.info("Spark session stopped")
        except Exception as e:
            logger.error(f"Failed to cleanup Spark: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
