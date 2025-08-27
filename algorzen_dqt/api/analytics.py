"""
Advanced Analytics API for the Algorzen Data Quality Toolkit.

This module provides:
- ML quality scoring endpoints
- Anomaly detection API
- Pattern recognition endpoints
- Analytics dashboard data
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import pandas as pd
import numpy as np

from ..analytics.ml_quality_scorer import MLQualityScorer
from ..auth.service import auth_service, User
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Initialize ML quality scorer
ml_scorer = MLQualityScorer()

# Create router
analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Pydantic models
class MLQualityRequest(BaseModel):
    """Request model for ML quality scoring."""
    data: Dict[str, Any]  # JSON data or file path
    features: Optional[List[str]] = None
    method: str = "ensemble"  # ensemble, anomaly, clustering, statistical

class AnalyticsResponse(BaseModel):
    """Response model for analytics endpoints."""
    success: bool
    data: Dict[str, Any]
    message: str
    timestamp: str

class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection."""
    data: Dict[str, Any]
    threshold: float = 0.1
    method: str = "isolation_forest"  # isolation_forest, dbscan

class PatternRecognitionRequest(BaseModel):
    """Request model for pattern recognition."""
    data: Dict[str, Any]
    pattern_types: List[str] = ["email", "phone", "date", "numeric"]
    min_confidence: float = 0.7

# Helper function to convert data to DataFrame
def _data_to_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """Convert JSON data to pandas DataFrame."""
    try:
        if isinstance(data, dict):
            # If data contains 'data' key, extract it
            if 'data' in data and isinstance(data['data'], list):
                return pd.DataFrame(data['data'])
            elif 'data' in data and isinstance(data['data'], dict):
                return pd.DataFrame([data['data']])
            else:
                return pd.DataFrame([data])
        else:
            return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Failed to convert data to DataFrame: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid data format: {str(e)}")

@analytics_router.post("/ml-quality-score", response_model=AnalyticsResponse)
async def calculate_ml_quality_score(
    request: MLQualityRequest,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Calculate ML-based quality score for dataset."""
    try:
        # Check permissions
        if not auth_service.has_permission(current_user, "analytics:read"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Convert data to DataFrame
        df = _data_to_dataframe(request.data)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Empty dataset provided")
        
        # Calculate ML quality score
        scores = ml_scorer.calculate_ml_quality_score(
            data=df,
            features=request.features,
            method=request.method
        )
        
        if "error" in scores:
            raise HTTPException(status_code=400, detail=scores["error"])
        
        logger.info(f"ML quality score calculated for user {current_user.username}")
        
        return AnalyticsResponse(
            success=True,
            data=scores,
            message="ML quality score calculated successfully",
            timestamp=scores.get("metadata", {}).get("timestamp", "")
        )
        
    except Exception as e:
        logger.error(f"Failed to calculate ML quality score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.post("/anomaly-detection", response_model=AnalyticsResponse)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Detect anomalies in dataset using ML models."""
    try:
        # Check permissions
        if not auth_service.has_permission(current_user, "analytics:read"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Convert data to DataFrame
        df = _data_to_dataframe(request.data)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Empty dataset provided")
        
        # Select features for anomaly detection
        features = request.features if request.features else ml_scorer._select_features(df)
        
        # Prepare features
        X = ml_scorer._prepare_features(df, features)
        
        if X is None:
            raise HTTPException(status_code=400, detail="Failed to prepare features")
        
        # Detect anomalies
        if request.method == "isolation_forest":
            model = ml_scorer.models['isolation_forest']
            predictions = model.fit_predict(X)
            anomalies = (predictions == -1)
        elif request.method == "dbscan":
            model = ml_scorer.models['dbscan']
            predictions = model.fit_predict(X)
            anomalies = (predictions == -1)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {request.method}")
        
        # Calculate anomaly statistics
        anomaly_count = int(anomalies.sum())
        anomaly_percentage = float(anomaly_count / len(df) * 100)
        
        # Get anomaly indices
        anomaly_indices = np.where(anomalies)[0].tolist()
        
        # Get anomaly data
        anomaly_data = df.iloc[anomaly_indices].to_dict('records')
        
        results = {
            "method": request.method,
            "total_records": len(df),
            "anomaly_count": anomaly_count,
            "anomaly_percentage": anomaly_percentage,
            "anomaly_indices": anomaly_indices,
            "anomaly_data": anomaly_data,
            "threshold": request.threshold,
            "quality_score": 1 - anomaly_percentage / 100
        }
        
        logger.info(f"Anomaly detection completed for user {current_user.username}: {anomaly_count} anomalies found")
        
        return AnalyticsResponse(
            success=True,
            data=results,
            message=f"Anomaly detection completed: {anomaly_count} anomalies found",
            timestamp=pd.Timestamp.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to detect anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.post("/pattern-recognition", response_model=AnalyticsResponse)
async def recognize_patterns(
    request: PatternRecognitionRequest,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Recognize patterns in dataset columns."""
    try:
        # Check permissions
        if not auth_service.has_permission(current_user, "analytics:read"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Convert data to DataFrame
        df = _data_to_dataframe(request.data)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Empty dataset provided")
        
        # Pattern recognition logic
        patterns = {}
        total_columns = len(df.columns)
        
        for column in df.columns:
            col_data = df[column].dropna()
            
            if col_data.empty:
                continue
            
            column_patterns = {}
            
            # Email pattern
            if "email" in request.pattern_types:
                email_count = col_data.astype(str).str.contains(r'@.*\.', regex=True).sum()
                email_confidence = email_count / len(col_data)
                if email_confidence >= request.min_confidence:
                    column_patterns["email"] = {
                        "count": int(email_count),
                        "confidence": float(email_confidence),
                        "percentage": float(email_confidence * 100)
                    }
            
            # Phone pattern
            if "phone" in request.pattern_types:
                phone_count = col_data.astype(str).str.contains(r'\d{10,}', regex=True).sum()
                phone_confidence = phone_count / len(col_data)
                if phone_confidence >= request.min_confidence:
                    column_patterns["phone"] = {
                        "count": int(phone_count),
                        "confidence": float(phone_confidence),
                        "percentage": float(phone_confidence * 100)
                    }
            
            # Date pattern
            if "date" in request.pattern_types:
                date_count = col_data.astype(str).str.contains(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', regex=True).sum()
                date_confidence = date_count / len(col_data)
                if date_confidence >= request.min_confidence:
                    column_patterns["date"] = {
                        "count": int(date_count),
                        "confidence": float(date_confidence),
                        "percentage": float(date_confidence * 100)
                    }
            
            # Numeric pattern
            if "numeric" in request.pattern_types:
                numeric_count = col_data.astype(str).str.match(r'^-?\d+\.?\d*$').sum()
                numeric_confidence = numeric_count / len(col_data)
                if numeric_confidence >= request.min_confidence:
                    column_patterns["numeric"] = {
                        "count": int(numeric_count),
                        "confidence": float(numeric_confidence),
                        "percentage": float(numeric_confidence * 100)
                    }
            
            if column_patterns:
                patterns[column] = column_patterns
        
        # Calculate overall pattern statistics
        total_patterns = sum(len(col_patterns) for col_patterns in patterns.values())
        pattern_coverage = len(patterns) / total_columns if total_columns > 0 else 0
        
        results = {
            "patterns": patterns,
            "total_columns": total_columns,
            "columns_with_patterns": len(patterns),
            "total_patterns": total_patterns,
            "pattern_coverage": float(pattern_coverage),
            "min_confidence": request.min_confidence,
            "pattern_types": request.pattern_types
        }
        
        logger.info(f"Pattern recognition completed for user {current_user.username}: {total_patterns} patterns found")
        
        return AnalyticsResponse(
            success=True,
            data=results,
            message=f"Pattern recognition completed: {total_patterns} patterns found",
            timestamp=pd.Timestamp.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to recognize patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.get("/model-info", response_model=AnalyticsResponse)
async def get_model_info(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get information about available ML models."""
    try:
        # Check permissions
        if not auth_service.has_permission(current_user, "analytics:read"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        model_info = ml_scorer.get_model_info()
        
        return AnalyticsResponse(
            success=True,
            data=model_info,
            message="Model information retrieved successfully",
            timestamp=pd.Timestamp.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.get("/analytics-dashboard", response_model=AnalyticsResponse)
async def get_analytics_dashboard(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get analytics dashboard data and statistics."""
    try:
        # Check permissions
        if not auth_service.has_permission(current_user, "analytics:read"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Generate sample analytics data for dashboard
        dashboard_data = {
            "ml_models": {
                "total_models": len(ml_scorer.models),
                "model_types": list(ml_scorer.models.keys()),
                "status": "active"
            },
            "recent_analyses": [
                {
                    "id": "analysis_001",
                    "type": "ML Quality Score",
                    "status": "completed",
                    "timestamp": pd.Timestamp.now().isoformat(),
                    "user": current_user.username
                }
            ],
            "quality_metrics": {
                "average_score": 0.85,
                "total_analyses": 150,
                "success_rate": 0.98
            },
            "feature_usage": {
                "anomaly_detection": 45,
                "pattern_recognition": 32,
                "clustering_analysis": 28,
                "statistical_analysis": 45
            }
        }
        
        return AnalyticsResponse(
            success=True,
            data=dashboard_data,
            message="Analytics dashboard data retrieved successfully",
            timestamp=pd.Timestamp.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@analytics_router.get("/health", response_model=AnalyticsResponse)
async def analytics_health():
    """Health check for analytics service."""
    try:
        health_status = {
            "status": "healthy",
            "ml_scorer": "active",
            "models_loaded": len(ml_scorer.models),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        return AnalyticsResponse(
            success=True,
            data=health_status,
            message="Analytics service is healthy",
            timestamp=health_status["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
