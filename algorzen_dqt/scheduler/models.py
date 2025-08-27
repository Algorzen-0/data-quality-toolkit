"""
Scheduling Models for the Algorzen Data Quality Toolkit.

This module defines the data models for:
- Scheduled quality checks
- Automated workflows
- Monitoring and alerting
- Task execution history
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid
import croniter


class ScheduleType(str, Enum):
    """Types of schedules."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Cron expression


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationType(str, Enum):
    """Notification delivery types."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    IN_APP = "in_app"


class ScheduledTaskBase(BaseModel):
    """Base scheduled task model."""
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., max_length=500)
    task_type: str  # quality_check, workflow, report, etc.
    schedule_type: ScheduleType = ScheduleType.DAILY
    schedule_config: Dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    enabled: bool = True
    timeout_minutes: int = 60
    retry_count: int = 3
    retry_delay_minutes: int = 5
    
    @validator('timeout_minutes')
    def validate_timeout(cls, v):
        if v < 1 or v > 1440:  # 1 minute to 24 hours
            raise ValueError('Timeout must be between 1 and 1440 minutes')
        return v
    
    @validator('retry_count')
    def validate_retry_count(cls, v):
        if v < 0 or v > 10:
            raise ValueError('Retry count must be between 0 and 10')
        return v


class ScheduledTaskCreate(ScheduledTaskBase):
    """Model for creating a new scheduled task."""
    pass


class ScheduledTaskUpdate(BaseModel):
    """Model for updating scheduled task information."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    schedule_type: Optional[ScheduleType] = None
    schedule_config: Optional[Dict[str, Any]] = None
    priority: Optional[TaskPriority] = None
    enabled: Optional[bool] = None
    timeout_minutes: Optional[int] = None
    retry_count: Optional[int] = None
    retry_delay_minutes: Optional[int] = None


class ScheduledTask(ScheduledTaskBase):
    """Complete scheduled task model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    average_duration: float = 0.0
    last_status: TaskStatus = TaskStatus.PENDING
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Daily Customer Data Quality Check",
                "description": "Automated daily quality checks for customer dataset",
                "task_type": "quality_check",
                "schedule_type": "daily",
                "priority": "high",
                "total_runs": 30,
                "successful_runs": 28,
                "failed_runs": 2
            }
        }
    
    def calculate_next_run(self) -> Optional[datetime]:
        """Calculate the next run time based on schedule configuration."""
        try:
            if self.schedule_type == ScheduleType.ONCE:
                return None
            
            elif self.schedule_type == ScheduleType.DAILY:
                hour = self.schedule_config.get("hour", 2)
                minute = self.schedule_config.get("minute", 0)
                base_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if base_time <= datetime.now():
                    base_time += timedelta(days=1)
                
                return base_time
            
            elif self.schedule_type == ScheduleType.WEEKLY:
                weekday = self.schedule_config.get("weekday", 0)  # Monday = 0
                hour = self.schedule_config.get("hour", 2)
                minute = self.schedule_config.get("minute", 0)
                
                current_weekday = datetime.now().weekday()
                days_ahead = weekday - current_weekday
                
                if days_ahead <= 0:
                    days_ahead += 7
                
                next_run = datetime.now() + timedelta(days=days_ahead)
                return next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            elif self.schedule_type == ScheduleType.MONTHLY:
                day = self.schedule_config.get("day", 1)
                hour = self.schedule_config.get("hour", 2)
                minute = self.schedule_config.get("minute", 0)
                
                current_date = datetime.now()
                if current_date.day >= day:
                    # Move to next month
                    if current_date.month == 12:
                        next_month = current_date.replace(year=current_date.year + 1, month=1, day=day)
                    else:
                        next_month = current_date.replace(month=current_date.month + 1, day=day)
                else:
                    next_month = current_date.replace(day=day)
                
                return next_month.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            elif self.schedule_type == ScheduleType.CUSTOM:
                cron_expr = self.schedule_config.get("cron_expression")
                if cron_expr:
                    cron = croniter.croniter(cron_expr, datetime.now())
                    return cron.get_next(datetime)
            
            return None
            
        except Exception as e:
            return None


class TaskExecution(BaseModel):
    """Task execution record model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    workspace_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.RUNNING
    duration_seconds: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    logs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "task-123",
                "status": "completed",
                "duration_seconds": 45.2,
                "retry_count": 0
            }
        }
    
    @property
    def is_completed(self) -> bool:
        """Check if task execution is completed."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]
    
    @property
    def is_successful(self) -> bool:
        """Check if task execution was successful."""
        return self.status == TaskStatus.COMPLETED
    
    def add_log(self, message: str):
        """Add a log message to the execution."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        
        # Keep only last 1000 log entries
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]


class QualityCheckSchedule(ScheduledTask):
    """Scheduled quality check task."""
    dataset_id: str
    check_types: List[str] = Field(default_factory=list)
    quality_threshold: float = 0.8
    alert_on_failure: bool = True
    generate_report: bool = True
    report_format: str = "html"  # html, pdf, json, csv
    recipients: List[str] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Customer Data Quality Check",
                "dataset_id": "customer-dataset-123",
                "check_types": ["missing_values", "duplicates", "outliers"],
                "quality_threshold": 0.85,
                "alert_on_failure": True
            }
        }


class WorkflowSchedule(ScheduledTask):
    """Scheduled workflow task."""
    workflow_id: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_format: str = "json"
    dependencies: List[str] = Field(default_factory=list)
    parallel_execution: bool = False
    max_concurrent_tasks: int = 5
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Data Pipeline Workflow",
                "workflow_id": "pipeline-123",
                "input_data": {"source": "s3://bucket/data", "format": "csv"},
                "parallel_execution": True
            }
        }


class AlertRule(BaseModel):
    """Alert rule configuration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., max_length=500)
    workspace_id: str
    enabled: bool = True
    severity: AlertSeverity = AlertSeverity.WARNING
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Quality Score Below Threshold",
                "description": "Alert when data quality score drops below 0.8",
                "severity": "warning",
                "conditions": [
                    {"metric": "quality_score", "operator": "<", "value": 0.8}
                ],
                "actions": [
                    {"type": "email", "recipients": ["team@company.com"]}
                ]
            }
        }


class Alert(BaseModel):
    """Alert instance model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    workspace_id: str
    severity: AlertSeverity
    title: str
    message: str
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    status: str = "active"  # active, acknowledged, resolved
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "rule_id": "rule-123",
                "severity": "warning",
                "title": "Data Quality Alert",
                "message": "Quality score dropped to 0.75",
                "status": "active"
            }
        }


class Notification(BaseModel):
    """Notification delivery model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str
    notification_type: NotificationType
    recipient: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    status: str = "sent"  # sent, delivered, failed
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScheduleStatistics(BaseModel):
    """Scheduling system statistics."""
    total_tasks: int
    active_tasks: int
    completed_tasks_today: int
    failed_tasks_today: int
    average_execution_time: float
    success_rate: float
    next_scheduled_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    system_health: str = "healthy"  # healthy, warning, critical
