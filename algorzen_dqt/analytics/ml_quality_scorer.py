"""
Machine Learning Quality Scorer for the Algorzen Data Quality Toolkit.

This module provides:
- ML-based quality scoring
- Anomaly detection
- Pattern recognition
- Predictive quality analysis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import silhouette_score

from ..utils.logging import get_logger

logger = get_logger(__name__)


class MLQualityScorer:
    """Machine Learning-based quality scoring engine."""
    
    def __init__(self):
        """Initialize ML quality scorer."""
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
        # Initialize default models
        self._initialize_default_models()
        
        logger.info("ML Quality Scorer initialized")
    
    def _initialize_default_models(self):
        """Initialize default ML models."""
        try:
            # Anomaly detection models
            self.models['isolation_forest'] = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
            self.models['dbscan'] = DBSCAN(
                eps=0.5,
                min_samples=5
            )
            
            # Clustering models
            self.models['kmeans'] = KMeans(
                n_clusters=5,
                random_state=42,
                n_init=10
            )
            
            # Quality prediction model
            self.models['quality_predictor'] = RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            
            # Preprocessing scalers
            self.scalers['standard'] = StandardScaler()
            
            logger.info("Default ML models initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize default models: {e}")
            raise
    
    def calculate_ml_quality_score(self, data: pd.DataFrame, 
                                 features: Optional[List[str]] = None,
                                 method: str = "ensemble") -> Dict[str, Any]:
        """Calculate ML-based quality score for dataset."""
        try:
            if data.empty:
                return {"error": "Empty dataset provided"}
            
            # Prepare features
            if features is None:
                features = self._select_features(data)
            
            # Extract feature matrix
            X = self._prepare_features(data, features)
            
            if X is None or X.empty:
                return {"error": "No valid features found"}
            
            # Calculate different quality scores
            scores = {}
            
            if method == "ensemble" or method == "anomaly":
                scores["anomaly_score"] = self._calculate_anomaly_score(X)
            
            if method == "ensemble" or method == "clustering":
                scores["clustering_score"] = self._calculate_clustering_score(X)
            
            if method == "ensemble" or method == "statistical":
                scores["statistical_score"] = self._calculate_statistical_score(X)
            
            # Calculate ensemble score
            if method == "ensemble":
                scores["ensemble_score"] = self._calculate_ensemble_score(scores)
            
            # Add metadata
            scores["metadata"] = {
                "features_used": features,
                "method": method,
                "timestamp": datetime.utcnow().isoformat(),
                "data_shape": data.shape
            }
            
            logger.info(f"ML quality score calculated using {method} method")
            return scores
            
        except Exception as e:
            logger.error(f"Failed to calculate ML quality score: {e}")
            return {"error": str(e)}
    
    def _select_features(self, data: pd.DataFrame) -> List[str]:
        """Automatically select relevant features for ML analysis."""
        try:
            features = []
            
            # Numeric features
            numeric_features = data.select_dtypes(include=[np.number]).columns.tolist()
            features.extend(numeric_features[:10])  # Limit to first 10 numeric features
            
            # Categorical features (convert to numeric)
            categorical_features = data.select_dtypes(include=['object', 'category']).columns.tolist()
            for col in categorical_features[:5]:  # Limit to first 5 categorical features
                try:
                    unique_count = data[col].nunique()
                    if 2 <= unique_count <= 50:  # Reasonable range for ML
                        features.append(col)
                except:
                    continue
            
            logger.info(f"Selected {len(features)} features for ML analysis")
            return features
            
        except Exception as e:
            logger.error(f"Failed to select features: {e}")
            return []
    
    def _prepare_features(self, data: pd.DataFrame, features: List[str]) -> Optional[pd.DataFrame]:
        """Prepare feature matrix for ML analysis."""
        try:
            feature_data = []
            
            for feature in features:
                if feature in data.columns:
                    col_data = data[feature].copy()
                    
                    # Handle missing values
                    if col_data.isnull().any():
                        if col_data.dtype in ['object', 'category']:
                            col_data = col_data.fillna('MISSING')
                        else:
                            col_data = col_data.fillna(col_data.median())
                    
                    # Convert categorical to numeric
                    if col_data.dtype in ['object', 'category']:
                        if col_data.nunique() <= 50:  # Categorical
                            encoder = LabelEncoder()
                            col_data = encoder.fit_transform(col_data.astype(str))
                            self.encoders[feature] = encoder
                        else:  # Text data - use length as feature
                            col_data = col_data.astype(str).str.len()
                    
                    feature_data.append(col_data)
            
            if not feature_data:
                return None
            
            # Combine features
            X = pd.DataFrame(dict(zip(features, feature_data)))
            
            # Handle infinite values
            X = X.replace([np.inf, -np.inf], np.nan)
            X = X.fillna(X.median())
            
            # Scale features
            X_scaled = self.scalers['standard'].fit_transform(X)
            
            return pd.DataFrame(X_scaled, columns=features, index=data.index)
            
        except Exception as e:
            logger.error(f"Failed to prepare features: {e}")
            return None
    
    def _calculate_anomaly_score(self, X: pd.DataFrame) -> Dict[str, Any]:
        """Calculate anomaly detection score."""
        try:
            results = {}
            
            # Isolation Forest
            iso_forest = self.models['isolation_forest']
            iso_predictions = iso_forest.fit_predict(X)
            iso_anomalies = (iso_predictions == -1).sum()
            iso_score = 1 - (iso_anomalies / len(X))
            
            results["isolation_forest"] = {
                "anomaly_count": int(iso_anomalies),
                "anomaly_percentage": float(iso_anomalies / len(X) * 100),
                "quality_score": float(iso_score)
            }
            
            # DBSCAN
            dbscan = self.models['dbscan']
            dbscan_predictions = dbscan.fit_predict(X)
            dbscan_anomalies = (dbscan_predictions == -1).sum()
            dbscan_score = 1 - (dbscan_anomalies / len(X))
            
            results["dbscan"] = {
                "anomaly_count": int(dbscan_anomalies),
                "anomaly_percentage": float(dbscan_anomalies / len(X) * 100),
                "quality_score": float(dbscan_score)
            }
            
            # Overall anomaly score
            results["overall_score"] = float((iso_score + dbscan_score) / 2)
            results["total_anomalies"] = int(iso_anomalies + dbscan_anomalies)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to calculate anomaly score: {e}")
            return {"error": str(e)}
    
    def _calculate_clustering_score(self, X: pd.DataFrame) -> Dict[str, Any]:
        """Calculate clustering quality score."""
        try:
            results = {}
            
            # K-Means clustering
            kmeans = self.models['kmeans']
            kmeans_labels = kmeans.fit_predict(X)
            
            # Calculate clustering metrics
            silhouette = silhouette_score(X, kmeans_labels)
            
            # Normalize scores to 0-1 range
            silhouette_norm = max(0, (silhouette + 1) / 2)  # Silhouette ranges from -1 to 1
            
            results["kmeans"] = {
                "silhouette_score": float(silhouette),
                "silhouette_normalized": float(silhouette_norm),
                "n_clusters": int(kmeans.n_clusters)
            }
            
            # Overall clustering score
            results["overall_score"] = float(silhouette_norm)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to calculate clustering score: {e}")
            return {"error": str(e)}
    
    def _calculate_statistical_score(self, X: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistical quality score."""
        try:
            results = {}
            
            # Calculate basic statistics
            mean_values = X.mean()
            std_values = X.std()
            skew_values = X.skew()
            
            # Calculate distribution quality
            distribution_scores = []
            for col in X.columns:
                col_data = X[col]
                
                # Check for normal distribution (lower is better for skewness)
                skew_score = 1 - min(1, abs(skew_values[col]) / 2)
                
                # Check for reasonable variance (not too low, not too high)
                std_score = 1 - min(1, abs(std_values[col] - 1) / 2)
                
                # Check for reasonable range
                range_score = 1 - min(1, (col_data.max() - col_data.min()) / 10)
                
                # Average score for this column
                col_score = (skew_score + std_score + range_score) / 3
                distribution_scores.append(col_score)
            
            results["distribution_analysis"] = {
                "mean_values": mean_values.to_dict(),
                "std_values": std_values.to_dict(),
                "skew_values": skew_values.to_dict(),
                "average_distribution_score": float(np.mean(distribution_scores))
            }
            
            # Overall statistical score
            results["overall_score"] = float(np.mean(distribution_scores))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to calculate statistical score: {e}")
            return {"error": str(e)}
    
    def _calculate_ensemble_score(self, scores: Dict[str, Any]) -> float:
        """Calculate ensemble quality score from all individual scores."""
        try:
            ensemble_scores = []
            
            # Extract overall scores from each method
            for method, result in scores.items():
                if method != "metadata" and isinstance(result, dict):
                    if "overall_score" in result:
                        ensemble_scores.append(result["overall_score"])
                    elif "quality_score" in result:
                        ensemble_scores.append(result["quality_score"])
            
            if ensemble_scores:
                # Simple average
                ensemble_score = np.mean(ensemble_scores)
                return float(ensemble_score)
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"Failed to calculate ensemble score: {e}")
            return 1.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models."""
        try:
            info = {
                "models": {},
                "scalers": list(self.scalers.keys()),
                "encoders": list(self.encoders.keys()),
                "total_models": len(self.models)
            }
            
            for name, model in self.models.items():
                model_info = {
                    "type": type(model).__name__
                }
                
                # Add model-specific info
                if hasattr(model, 'n_estimators'):
                    model_info["n_estimators"] = model.n_estimators
                if hasattr(model, 'n_clusters'):
                    model_info["n_clusters"] = model.n_clusters
                
                info["models"][name] = model_info
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}
