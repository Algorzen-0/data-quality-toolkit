"""
Collaboration Models for the Algorzen Data Quality Toolkit.

This module defines the data models for:
- Team workspaces
- Shared resources and permissions
- Collaboration workflows
- Team member management
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class WorkspaceType(str, Enum):
    """Types of workspaces."""
    PERSONAL = "personal"
    TEAM = "team"
    PROJECT = "project"
    ORGANIZATION = "organization"


class ResourceType(str, Enum):
    """Types of shared resources."""
    DATASET = "dataset"
    QUALITY_CHECK = "quality_check"
    REPORT = "report"
    WORKFLOW = "workflow"
    DASHBOARD = "dashboard"
    CONFIGURATION = "configuration"


class PermissionLevel(str, Enum):
    """Permission levels for shared resources."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


class MemberRole(str, Enum):
    """Team member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"


class WorkspaceStatus(str, Enum):
    """Workspace status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


class WorkspaceBase(BaseModel):
    """Base workspace model."""
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., max_length=500)
    workspace_type: WorkspaceType = WorkspaceType.TEAM
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    tags: List[str] = Field(default_factory=list)
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return [tag.lower().strip() for tag in v if tag.strip()]


class WorkspaceCreate(WorkspaceBase):
    """Model for creating a new workspace."""
    pass


class WorkspaceUpdate(BaseModel):
    """Model for updating workspace information."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[WorkspaceStatus] = None
    tags: Optional[List[str]] = None


class Workspace(WorkspaceBase):
    """Complete workspace model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    member_count: int = 0
    resource_count: int = 0
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Data Quality Team",
                "description": "Main workspace for data quality initiatives",
                "workspace_type": "team",
                "status": "active",
                "owner_id": "user-123",
                "member_count": 5,
                "resource_count": 12
            }
        }


class WorkspaceMember(BaseModel):
    """Workspace member model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    username: str
    full_name: str
    email: str
    role: MemberRole = MemberRole.MEMBER
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    permissions: List[PermissionLevel] = Field(default_factory=list)
    is_active: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "workspace_id": "workspace-123",
                "user_id": "user-456",
                "username": "john_doe",
                "full_name": "John Doe",
                "email": "john@example.com",
                "role": "member",
                "permissions": ["read", "write"]
            }
        }


class SharedResource(BaseModel):
    """Shared resource model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    resource_type: ResourceType
    resource_id: str
    name: str
    description: str = ""
    owner_id: str
    shared_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    access_level: PermissionLevel = PermissionLevel.READ
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "workspace_id": "workspace-123",
                "resource_type": "dataset",
                "resource_id": "dataset-789",
                "name": "Customer Data",
                "description": "Customer transaction dataset",
                "access_level": "read",
                "tags": ["customer", "transactions"]
            }
        }


class ResourcePermission(BaseModel):
    """Resource permission model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_id: str
    user_id: str
    permission_level: PermissionLevel
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    granted_by: str
    expires_at: Optional[datetime] = None
    is_active: bool = True


class CollaborationInvite(BaseModel):
    """Workspace invitation model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    invited_by: str
    invited_email: str
    invited_username: Optional[str] = None
    role: MemberRole = MemberRole.MEMBER
    permissions: List[PermissionLevel] = Field(default_factory=list)
    message: str = ""
    status: str = "pending"  # pending, accepted, declined, expired
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "workspace_id": "workspace-123",
                "invited_by": "admin@example.com",
                "invited_email": "newuser@example.com",
                "role": "member",
                "permissions": ["read", "write"],
                "message": "Welcome to our data quality team!",
                "expires_at": "2024-02-01T00:00:00Z"
            }
        }


class WorkspaceActivity(BaseModel):
    """Workspace activity log model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    username: str
    action: str
    resource_type: Optional[ResourceType] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None


class WorkspaceSettings(BaseModel):
    """Workspace configuration settings."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    data_retention_days: int = 365
    max_file_size_mb: int = 100
    allowed_file_types: List[str] = Field(default_factory=lambda: ["csv", "json", "parquet", "xlsx"])
    auto_backup_enabled: bool = True
    backup_frequency_hours: int = 24
    quality_check_auto_run: bool = False
    quality_check_schedule: str = "0 2 * * *"  # Cron expression
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    security_settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "data_retention_days": 365,
                "max_file_size_mb": 100,
                "allowed_file_types": ["csv", "json", "parquet"],
                "auto_backup_enabled": True,
                "quality_check_auto_run": False
            }
        }


class TeamWorkflow(BaseModel):
    """Team workflow model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    name: str
    description: str = ""
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    triggers: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    run_count: int = 0
    success_rate: float = 0.0
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Daily Data Quality Check",
                "description": "Automated daily quality checks for customer data",
                "triggers": ["daily", "data_upload"],
                "steps": [
                    {"name": "Data Validation", "type": "quality_check"},
                    {"name": "Report Generation", "type": "report"}
                ]
            }
        }


class WorkspaceStatistics(BaseModel):
    """Workspace statistics and metrics."""
    workspace_id: str
    total_members: int
    active_members: int
    total_resources: int
    total_quality_checks: int
    total_reports: int
    data_processed_gb: float
    quality_score_avg: float
    last_activity: datetime
    member_activity: Dict[str, int] = Field(default_factory=dict)
    resource_usage: Dict[str, int] = Field(default_factory=dict)
    quality_trends: List[Dict[str, Any]] = Field(default_factory=list)
