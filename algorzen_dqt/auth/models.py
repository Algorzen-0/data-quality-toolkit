"""
Authentication Models for the Algorzen Data Quality Toolkit.

This module defines the data models for:
- User management
- Role-based access control (RBAC)
- Permissions and authorization
- Session management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator
import uuid


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(str, Enum):
    """System permissions."""
    # Dashboard permissions
    VIEW_DASHBOARD = "view_dashboard"
    EXPORT_REPORTS = "export_reports"
    
    # Data permissions
    VIEW_DATA = "view_data"
    UPLOAD_DATA = "upload_data"
    DELETE_DATA = "delete_data"
    
    # Quality check permissions
    RUN_CHECKS = "run_checks"
    VIEW_CHECK_RESULTS = "view_check_results"
    MODIFY_CHECK_CONFIG = "modify_check_config"
    
    # User management permissions
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    MODIFY_USERS = "modify_users"
    DELETE_USERS = "delete_users"
    
    # System permissions
    VIEW_SYSTEM_STATUS = "view_system_status"
    MODIFY_SYSTEM_CONFIG = "modify_system_config"
    ACCESS_LOGS = "access_logs"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_ACTIVATION = "pending_activation"


class UserBase(BaseModel):
    """Base user model."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.PENDING_ACTIVATION
    
    @validator('username')
    def validate_username(cls, v):
        if v.lower() in ['root', 'system', 'guest']:
            raise ValueError('Username is reserved')
        return v


class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseModel):
    """Model for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """Model for changing user password."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class User(UserBase):
    """Complete user model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "john_doe",
                "email": "john.doe@algorzen.com",
                "full_name": "John Doe",
                "role": "analyst",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-15T10:30:00Z"
            }
        }


class Role(BaseModel):
    """Role model with associated permissions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., max_length=200)
    permissions: List[Permission] = Field(default_factory=list)
    is_system_role: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Data Analyst",
                "description": "Can run quality checks and view results",
                "permissions": ["view_dashboard", "run_checks", "view_check_results"]
            }
        }


class UserSession(BaseModel):
    """User session model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User
    permissions: List[Permission]


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model."""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserPreferences(BaseModel):
    """User preferences model."""
    theme: str = "light"  # light, dark, auto
    language: str = "en"
    timezone: str = "UTC"
    dashboard_layout: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    data_quality_thresholds: Dict[str, float] = Field(default_factory=dict)


class AuditLog(BaseModel):
    """Audit log entry model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None


# Default roles with permissions
DEFAULT_ROLES = {
    UserRole.ADMIN: [
        Permission.VIEW_DASHBOARD, Permission.EXPORT_REPORTS,
        Permission.VIEW_DATA, Permission.UPLOAD_DATA, Permission.DELETE_DATA,
        Permission.RUN_CHECKS, Permission.VIEW_CHECK_RESULTS, Permission.MODIFY_CHECK_CONFIG,
        Permission.VIEW_USERS, Permission.CREATE_USERS, Permission.MODIFY_USERS, Permission.DELETE_USERS,
        Permission.VIEW_SYSTEM_STATUS, Permission.MODIFY_SYSTEM_CONFIG, Permission.ACCESS_LOGS
    ],
    UserRole.MANAGER: [
        Permission.VIEW_DASHBOARD, Permission.EXPORT_REPORTS,
        Permission.VIEW_DATA, Permission.UPLOAD_DATA,
        Permission.RUN_CHECKS, Permission.VIEW_CHECK_RESULTS, Permission.MODIFY_CHECK_CONFIG,
        Permission.VIEW_USERS, Permission.CREATE_USERS, Permission.MODIFY_USERS,
        Permission.VIEW_SYSTEM_STATUS
    ],
    UserRole.ANALYST: [
        Permission.VIEW_DASHBOARD, Permission.EXPORT_REPORTS,
        Permission.VIEW_DATA, Permission.UPLOAD_DATA,
        Permission.RUN_CHECKS, Permission.VIEW_CHECK_RESULTS
    ],
    UserRole.VIEWER: [
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_DATA,
        Permission.VIEW_CHECK_RESULTS
    ],
    UserRole.GUEST: [
        Permission.VIEW_DASHBOARD
    ]
}
