from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import psutil
import os
import json
import logging

# Models
class SystemHealth(BaseModel):
    status: str
    uptime: str
    last_check: datetime
    cpu: float
    memory: float
    disk: float
    network: float

class QualityMetrics(BaseModel):
    total_checks: int
    passed_checks: int
    failed_checks: int
    success_rate: float
    avg_response_time: float
    last_hour_checks: int

class Alert(BaseModel):
    id: str
    type: str  # 'error', 'warning', 'info'
    message: str
    timestamp: datetime
    severity: str  # 'low', 'medium', 'high'
    acknowledged: bool = False

class Integration(BaseModel):
    name: str
    status: str  # 'connected', 'disconnected', 'error'
    url: str
    last_sync: Optional[datetime] = None
    config: Optional[Dict[str, Any]] = None

class MonitoringConfig(BaseModel):
    alert_thresholds: Dict[str, float]
    check_intervals: Dict[str, int]
    integrations: List[Integration]

# In-memory storage (replace with database in production)
monitoring_db = {
    "system_health": {
        "status": "healthy",
        "uptime": "99.8%",
        "last_check": datetime.now(),
        "cpu": 23.5,
        "memory": 45.2,
        "disk": 12.8,
        "network": 67.3
    },
    "quality_metrics": {
        "total_checks": 1247,
        "passed_checks": 1189,
        "failed_checks": 58,
        "success_rate": 95.3,
        "avg_response_time": 2.3,
        "last_hour_checks": 23
    },
    "alerts": [
        {
            "id": "1",
            "type": "warning",
            "message": "Data quality score dropped below threshold",
            "timestamp": datetime.now() - timedelta(minutes=30),
            "severity": "medium",
            "acknowledged": False
        },
        {
            "id": "2",
            "type": "error",
            "message": "Database connection timeout",
            "timestamp": datetime.now() - timedelta(minutes=15),
            "severity": "high",
            "acknowledged": False
        },
        {
            "id": "3",
            "type": "info",
            "message": "Scheduled task completed successfully",
            "timestamp": datetime.now() - timedelta(minutes=5),
            "severity": "low",
            "acknowledged": True
        }
    ],
    "integrations": {
        "grafana": {
            "name": "grafana",
            "status": "connected",
            "url": "http://localhost:3000",
            "last_sync": datetime.now(),
            "config": {
                "api_key": "***",
                "dashboard_id": "dqt-overview",
                "refresh_interval": 30
            }
        },
        "prometheus": {
            "name": "prometheus",
            "status": "connected",
            "url": "http://localhost:9090",
            "last_sync": datetime.now(),
            "config": {
                "scrape_interval": 15,
                "retention_days": 15
            }
        },
        "elasticsearch": {
            "name": "elasticsearch",
            "status": "disconnected",
            "url": "http://localhost:9200",
            "last_sync": None,
            "config": {
                "index_pattern": "dqt-logs-*",
                "username": "elastic"
            }
        },
        "datadog": {
            "name": "datadog",
            "status": "connected",
            "url": "https://app.datadoghq.com",
            "last_sync": datetime.now(),
            "config": {
                "api_key": "***",
                "app_key": "***",
                "site": "datadoghq.com"
            }
        }
    }
}

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

def get_system_metrics() -> Dict[str, Any]:
    """Get real-time system metrics using psutil"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Calculate uptime
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_days = uptime_seconds / (24 * 3600)
        uptime_percent = min(99.9, max(0, 100 - (uptime_days * 0.1)))
        
        return {
            "cpu": round(cpu_percent, 1),
            "memory": round(memory.percent, 1),
            "disk": round((disk.used / disk.total) * 100, 1),
            "network": round((network.bytes_sent + network.bytes_recv) / (1024 * 1024 * 1024), 1),  # GB
            "uptime": f"{uptime_percent:.1f}%",
            "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "warning"
        }
    except Exception as e:
        logging.error(f"Error getting system metrics: {e}")
        return {
            "cpu": 0,
            "memory": 0,
            "disk": 0,
            "network": 0,
            "uptime": "0%",
            "status": "error"
        }

@router.get("/system-health", response_model=SystemHealth)
async def get_system_health():
    """Get current system health metrics"""
    metrics = get_system_metrics()
    
    system_health = {
        "status": metrics["status"],
        "uptime": metrics["uptime"],
        "last_check": datetime.now(),
        "cpu": metrics["cpu"],
        "memory": metrics["memory"],
        "disk": metrics["disk"],
        "network": metrics["network"]
    }
    
    # Update stored metrics
    monitoring_db["system_health"].update(system_health)
    
    return system_health

@router.get("/quality-metrics", response_model=QualityMetrics)
async def get_quality_metrics():
    """Get data quality metrics"""
    return monitoring_db["quality_metrics"]

@router.get("/alerts", response_model=List[Alert])
async def get_alerts(acknowledged: Optional[bool] = None):
    """Get alerts, optionally filtered by acknowledgment status"""
    alerts = monitoring_db["alerts"]
    if acknowledged is not None:
        alerts = [alert for alert in alerts if alert["acknowledged"] == acknowledged]
    return alerts

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    for alert in monitoring_db["alerts"]:
        if alert["id"] == alert_id:
            alert["acknowledged"] = True
            return {"message": f"Alert {alert_id} acknowledged successfully"}
    
    raise HTTPException(status_code=404, detail="Alert not found")

@router.post("/alerts")
async def create_alert(alert: Alert):
    """Create a new alert"""
    new_alert = {
        "id": str(uuid.uuid4()),
        "type": alert.type,
        "message": alert.message,
        "timestamp": datetime.now(),
        "severity": alert.severity,
        "acknowledged": False
    }
    monitoring_db["alerts"].append(new_alert)
    return new_alert

@router.get("/integrations", response_model=List[Integration])
async def get_integrations():
    """Get monitoring integrations status"""
    return list(monitoring_db["integrations"].values())

@router.get("/integrations/{integration_name}")
async def get_integration(integration_name: str):
    """Get specific integration details"""
    if integration_name not in monitoring_db["integrations"]:
        raise HTTPException(status_code=404, detail="Integration not found")
    return monitoring_db["integrations"][integration_name]

@router.post("/integrations/{integration_name}/test")
async def test_integration(integration_name: str):
    """Test integration connectivity"""
    if integration_name not in monitoring_db["integrations"]:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    integration = monitoring_db["integrations"][integration_name]
    
    # Simulate testing connection
    if integration["status"] == "connected":
        # Update last sync time
        integration["last_sync"] = datetime.now()
        return {
            "message": f"{integration_name} connection test successful",
            "status": "connected",
            "last_sync": integration["last_sync"]
        }
    else:
        return {
            "message": f"{integration_name} is not connected",
            "status": integration["status"]
        }

@router.put("/integrations/{integration_name}")
async def update_integration(integration_name: str, integration: Integration):
    """Update integration configuration"""
    if integration_name not in monitoring_db["integrations"]:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    monitoring_db["integrations"][integration_name].update(integration.dict())
    return {"message": f"Integration {integration_name} updated successfully"}

@router.get("/metrics/history")
async def get_metrics_history(hours: int = 24):
    """Get historical metrics for the last N hours"""
    # This would typically query a time-series database
    # For now, return simulated historical data
    now = datetime.now()
    history = []
    
    for i in range(hours):
        timestamp = now - timedelta(hours=i)
        history.append({
            "timestamp": timestamp,
            "cpu": round(20 + (i % 10), 1),
            "memory": round(40 + (i % 15), 1),
            "disk": round(10 + (i % 5), 1),
            "quality_score": round(90 + (i % 10), 1)
        })
    
    return history

@router.get("/health")
async def health_check():
    """Overall monitoring system health check"""
    try:
        system_health = get_system_metrics()
        active_alerts = len([a for a in monitoring_db["alerts"] if not a["acknowledged"]])
        connected_integrations = len([i for i in monitoring_db["integrations"].values() if i["status"] == "connected"])
        
        overall_status = "healthy"
        if system_health["status"] != "healthy" or active_alerts > 5:
            overall_status = "warning"
        if system_health["status"] == "error" or active_alerts > 10:
            overall_status = "critical"
        
        return {
            "status": overall_status,
            "system_health": system_health["status"],
            "active_alerts": active_alerts,
            "connected_integrations": connected_integrations,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/config", response_model=MonitoringConfig)
async def get_monitoring_config():
    """Get monitoring configuration"""
    return {
        "alert_thresholds": {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "quality_score_warning": 85.0,
            "quality_score_critical": 70.0
        },
        "check_intervals": {
            "system_health": 30,  # seconds
            "quality_metrics": 60,  # seconds
            "integration_status": 300  # seconds
        },
        "integrations": list(monitoring_db["integrations"].values())
    }

@router.post("/config")
async def update_monitoring_config(config: MonitoringConfig):
    """Update monitoring configuration"""
    # This would typically validate and save to a config file or database
    # For now, just return success
    return {"message": "Monitoring configuration updated successfully"}

# Import time module for uptime calculation
import time
