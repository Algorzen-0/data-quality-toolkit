"""
Duplicate Detection Quality Check Implementation.

This module provides advanced duplicate detection using multiple algorithms:
- Exact matching
- Fuzzy matching with configurable thresholds
- Business key-based detection
- Semantic similarity analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
import hashlib
from difflib import SequenceMatcher
import re

from .base import QualityCheck, CheckConfig, CheckResult
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DuplicatesConfig(CheckConfig):
    """Configuration for duplicate detection check."""
    
    # Detection methods
    exact_matching: bool = True
    fuzzy_matching: bool = True
    business_key_matching: bool = True
    semantic_matching: bool = False
    
    # Thresholds
    fuzzy_threshold: float = 0.8  # Similarity threshold for fuzzy matching
    business_key_columns: Optional[List[str]] = None  # Columns to use as business key
    
    # Analysis options
    analyze_duplicate_patterns: bool = True
    suggest_deduplication: bool = True
    include_similarity_scores: bool = True
    
    # Performance options
    max_fuzzy_comparisons: int = 10000  # Limit fuzzy comparisons for performance
    use_sampling: bool = True  # Use sampling for large datasets
    sample_size: int = 10000  # Sample size for large datasets


class DuplicatesCheck(QualityCheck):
    """
    Advanced duplicate detection quality check.
    
    This check provides comprehensive duplicate detection including:
    - Exact duplicate detection
    - Fuzzy matching with configurable thresholds
    - Business key-based duplicate detection
    - Pattern analysis and deduplication recommendations
    """
    
    def __init__(self, config: Optional[DuplicatesConfig] = None):
        """Initialize the duplicates check."""
        if config is None:
            config = DuplicatesConfig()
        config.check_name = "Duplicate Detection Analysis"
        config.check_type = "duplicates"
        super().__init__(config)
        self.config = self.config  # Type hint for IDE
        
    def validate_config(self) -> bool:
        """Validate the configuration."""
        if not 0 <= self.config.fuzzy_threshold <= 1:
            logger.error("Fuzzy threshold must be between 0 and 1")
            return False
        
        if self.config.max_fuzzy_comparisons < 100:
            logger.error("Max fuzzy comparisons must be at least 100")
            return False
            
        if self.config.sample_size < 100:
            logger.error("Sample size must be at least 100")
            return False
            
        return True
    
    async def execute(self, data: pd.DataFrame) -> CheckResult:
        """Execute the duplicate detection check."""
        start_time = datetime.now()
        
        try:
            # Validate configuration
            if not self.validate_config():
                raise ValueError("Invalid configuration")
            
            # Detect duplicates using multiple methods
            duplicate_analysis = await self._detect_duplicates(data)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(duplicate_analysis)
            
            # Determine status
            status = self._determine_status(quality_score, duplicate_analysis)
            
            # Generate detailed results
            details = self._generate_details(duplicate_analysis)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CheckResult(
                check_name="Duplicate Detection Analysis",
                check_type="duplicates",
                status=status,
                score=quality_score,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                details=details,
                affected_rows=duplicate_analysis["total_duplicate_rows"],
                affected_columns=list(data.columns)
            )
            
        except Exception as e:
            logger.error(f"Error in duplicate detection check: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return CheckResult(
                check_name="Duplicate Detection Analysis",
                check_type="duplicates",
                status="error",
                score=0.0,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                details={"error": str(e)}
            )
    
    async def _detect_duplicates(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect duplicates using multiple methods."""
        analysis = {
            "total_rows": len(data),
            "exact_duplicates": {},
            "fuzzy_duplicates": {},
            "business_key_duplicates": {},
            "semantic_duplicates": {},
            "total_duplicate_rows": 0,
            "duplicate_percentage": 0.0,
            "duplicate_patterns": {},
            "recommendations": []
        }
        
        # Detect exact duplicates
        if self.config.exact_matching:
            analysis["exact_duplicates"] = self._detect_exact_duplicates(data)
        
        # Detect fuzzy duplicates
        if self.config.fuzzy_matching:
            analysis["fuzzy_duplicates"] = await self._detect_fuzzy_duplicates(data)
        
        # Detect business key duplicates
        if self.config.business_key_matching:
            analysis["business_key_duplicates"] = self._detect_business_key_duplicates(data)
        
        # Detect semantic duplicates
        if self.config.semantic_matching:
            analysis["semantic_duplicates"] = await self._detect_semantic_duplicates(data)
        
        # Calculate overall statistics
        all_duplicate_rows = set()
        
        for method_results in [analysis["exact_duplicates"], analysis["fuzzy_duplicates"], 
                             analysis["business_key_duplicates"], analysis["semantic_duplicates"]]:
            if isinstance(method_results, dict) and "duplicate_rows" in method_results:
                all_duplicate_rows.update(method_results["duplicate_rows"])
        
        analysis["total_duplicate_rows"] = len(all_duplicate_rows)
        analysis["duplicate_percentage"] = analysis["total_duplicate_rows"] / analysis["total_rows"]
        
        # Analyze patterns if enabled
        if self.config.analyze_duplicate_patterns:
            analysis["duplicate_patterns"] = self._analyze_duplicate_patterns(data, all_duplicate_rows)
        
        # Generate recommendations if enabled
        if self.config.suggest_deduplication:
            analysis["recommendations"] = self._generate_deduplication_recommendations(analysis)
        
        return analysis
    
    def _detect_exact_duplicates(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect exact duplicates in the dataset."""
        # Find duplicate rows
        duplicate_mask = data.duplicated(keep=False)
        duplicate_indices = data[duplicate_mask].index.tolist()
        
        # Group duplicates
        duplicate_groups = {}
        for idx in duplicate_indices:
            row_hash = self._hash_row(data.loc[idx])
            if row_hash not in duplicate_groups:
                duplicate_groups[row_hash] = []
            duplicate_groups[row_hash].append(idx)
        
        # Filter groups with more than one row
        duplicate_groups = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
        
        return {
            "duplicate_rows": duplicate_indices,
            "duplicate_groups": duplicate_groups,
            "total_groups": len(duplicate_groups),
            "method": "exact_matching"
        }
    
    async def _detect_fuzzy_duplicates(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect fuzzy duplicates using similarity algorithms."""
        if len(data) > self.config.max_fuzzy_comparisons and self.config.use_sampling:
            # Use sampling for large datasets
            sample_data = data.sample(n=min(self.config.sample_size, len(data)), random_state=42)
            logger.info(f"Using sampling for fuzzy duplicate detection: {len(sample_data)} rows")
        else:
            sample_data = data
        
        duplicate_pairs = []
        similarity_scores = {}
        
        # Compare rows for similarity
        for i in range(len(sample_data)):
            for j in range(i + 1, len(sample_data)):
                similarity = self._calculate_row_similarity(
                    sample_data.iloc[i], 
                    sample_data.iloc[j]
                )
                
                if similarity >= self.config.fuzzy_threshold:
                    duplicate_pairs.append((i, j))
                    similarity_scores[f"{i}_{j}"] = similarity
        
        # Group similar rows
        duplicate_groups = self._group_similar_rows(sample_data, duplicate_pairs)
        
        return {
            "duplicate_rows": list(set([idx for pair in duplicate_pairs for idx in pair])),
            "duplicate_pairs": duplicate_pairs,
            "duplicate_groups": duplicate_groups,
            "similarity_scores": similarity_scores,
            "total_groups": len(duplicate_groups),
            "method": "fuzzy_matching",
            "threshold": self.config.fuzzy_threshold
        }
    
    def _detect_business_key_duplicates(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect duplicates based on business key columns."""
        if not self.config.business_key_columns:
            # Use first few columns as default business key
            key_columns = data.columns[:min(3, len(data.columns))]
            logger.info(f"No business key specified, using columns: {key_columns}")
        else:
            key_columns = [col for col in self.config.business_key_columns if col in data.columns]
            if not key_columns:
                logger.warning("Specified business key columns not found in data")
                return {"duplicate_rows": [], "duplicate_groups": {}, "total_groups": 0, "method": "business_key"}
        
        # Find duplicates based on business key
        duplicate_mask = data.duplicated(subset=key_columns, keep=False)
        duplicate_indices = data[duplicate_mask].index.tolist()
        
        # Group by business key
        duplicate_groups = {}
        for idx in duplicate_indices:
            key_values = tuple(data.loc[idx, key_columns].values)
            if key_values not in duplicate_groups:
                duplicate_groups[key_values] = []
            duplicate_groups[key_values].append(idx)
        
        return {
            "duplicate_rows": duplicate_indices,
            "duplicate_groups": duplicate_groups,
            "total_groups": len(duplicate_groups),
            "method": "business_key",
            "key_columns": key_columns
        }
    
    async def _detect_semantic_duplicates(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect semantic duplicates using advanced text analysis."""
        # This is a placeholder for semantic analysis
        # In a real implementation, you might use:
        # - Word embeddings (Word2Vec, BERT)
        # - TF-IDF similarity
        # - Semantic similarity algorithms
        
        logger.info("Semantic duplicate detection not yet implemented")
        return {
            "duplicate_rows": [],
            "duplicate_groups": {},
            "total_groups": 0,
            "method": "semantic",
            "status": "not_implemented"
        }
    
    def _calculate_row_similarity(self, row1: pd.Series, row2: pd.Series) -> float:
        """Calculate similarity between two rows."""
        similarities = []
        
        for col in row1.index:
            val1 = str(row1[col])
            val2 = str(row2[col])
            
            if pd.isna(val1) or pd.isna(val2):
                similarities.append(0.0)
            elif val1 == val2:
                similarities.append(1.0)
            else:
                # Use sequence matcher for string similarity
                similarity = SequenceMatcher(None, val1, val2).ratio()
                similarities.append(similarity)
        
        # Return average similarity
        return np.mean(similarities)
    
    def _group_similar_rows(self, data: pd.DataFrame, duplicate_pairs: List[Tuple[int, int]]) -> Dict[str, List[int]]:
        """Group similar rows into duplicate groups."""
        # Create graph of similar rows
        from collections import defaultdict
        graph = defaultdict(set)
        
        for i, j in duplicate_pairs:
            graph[i].add(j)
            graph[j].add(i)
        
        # Find connected components (groups)
        visited = set()
        groups = []
        
        for node in graph:
            if node not in visited:
                group = []
                stack = [node]
                visited.add(node)
                
                while stack:
                    current = stack.pop()
                    group.append(current)
                    
                    for neighbor in graph[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            stack.append(neighbor)
                
                if len(group) > 1:
                    groups.append(group)
        
        # Convert to dictionary
        return {f"group_{i}": group for i, group in enumerate(groups)}
    
    def _hash_row(self, row: pd.Series) -> str:
        """Create a hash for a row to identify exact duplicates."""
        row_str = "|".join([str(val) for val in row.values])
        return hashlib.md5(row_str.encode()).hexdigest()
    
    def _analyze_duplicate_patterns(self, data: pd.DataFrame, duplicate_rows: Set[int]) -> Dict[str, Any]:
        """Analyze patterns in duplicate data."""
        patterns = {
            "column_duplication": {},
            "value_frequency": {},
            "systematic_duplicates": []
        }
        
        # Analyze column-level duplication
        for column in data.columns:
            value_counts = data[column].value_counts()
            duplicate_values = value_counts[value_counts > 1]
            
            if len(duplicate_values) > 0:
                patterns["column_duplication"][column] = {
                    "duplicate_values": len(duplicate_values),
                    "total_duplicates": duplicate_values.sum() - len(duplicate_values)
                }
        
        # Find systematic duplicates (same pattern repeated)
        if len(duplicate_rows) > 0:
            duplicate_data = data.loc[list(duplicate_rows)]
            row_patterns = duplicate_data.apply(tuple, axis=1)
            pattern_counts = row_patterns.value_counts()
            
            systematic = pattern_counts[pattern_counts > 1]
            if len(systematic) > 0:
                patterns["systematic_duplicates"] = [
                    {"pattern": str(pattern), "count": count}
                    for pattern, count in systematic.items()
                ]
        
        return patterns
    
    def _generate_deduplication_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate deduplication recommendations."""
        recommendations = []
        
        # Overall recommendations
        if analysis["duplicate_percentage"] > 0.1:
            recommendations.append("CRITICAL: Dataset has >10% duplicate data. Implement deduplication immediately.")
        elif analysis["duplicate_percentage"] > 0.05:
            recommendations.append("WARNING: Dataset has >5% duplicate data. Consider deduplication.")
        
        # Method-specific recommendations
        if analysis["exact_duplicates"]["total_groups"] > 0:
            recommendations.append(f"EXACT: {analysis['exact_duplicates']['total_groups']} exact duplicate groups found. Remove exact duplicates first.")
        
        if analysis["fuzzy_duplicates"]["total_groups"] > 0:
            recommendations.append(f"FUZZY: {analysis['fuzzy_duplicates']['total_groups']} fuzzy duplicate groups found. Review similarity threshold.")
        
        if analysis["business_key_duplicates"]["total_groups"] > 0:
            recommendations.append(f"BUSINESS KEY: {analysis['business_key_duplicates']['total_groups']} business key duplicates. Verify business logic.")
        
        # Pattern-based recommendations
        if analysis["duplicate_patterns"]["systematic_duplicates"]:
            recommendations.append("PATTERN: Systematic duplicates detected. Investigate data generation process.")
        
        return recommendations
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate quality score based on duplicate analysis."""
        base_score = 1.0
        
        # Penalize based on duplicate percentage
        duplicate_penalty = analysis["duplicate_percentage"] * 0.6
        base_score -= duplicate_penalty
        
        # Penalize based on number of duplicate groups
        total_groups = sum([
            analysis["exact_duplicates"].get("total_groups", 0),
            analysis["fuzzy_duplicates"].get("total_groups", 0),
            analysis["business_key_duplicates"].get("total_groups", 0)
        ])
        
        if total_groups > 0:
            group_penalty = min(0.2, total_groups / 100)  # Cap at 20%
            base_score -= group_penalty
        
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
                "total_duplicate_rows": analysis["total_duplicate_rows"],
                "duplicate_percentage": f"{analysis['duplicate_percentage']:.2%}",
                "total_duplicate_groups": sum([
                    analysis["exact_duplicates"].get("total_groups", 0),
                    analysis["fuzzy_duplicates"].get("total_groups", 0),
                    analysis["business_key_duplicates"].get("total_groups", 0)
                ])
            },
            "method_results": {
                "exact_matching": analysis["exact_duplicates"],
                "fuzzy_matching": analysis["fuzzy_duplicates"],
                "business_key": analysis["business_key_duplicates"]
            },
            "patterns": analysis["duplicate_patterns"],
            "recommendations": analysis["recommendations"]
        }
