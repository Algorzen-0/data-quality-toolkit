"""
Authentication package for the Algorzen Data Quality Toolkit.

This package provides:
- User authentication and authorization
- Role-based access control (RBAC)
- JWT token management
- User management
- Audit logging
"""

from .models import (
    User, UserCreate, UserUpdate, UserPasswordChange, UserSession,
    LoginRequest, LoginResponse, RefreshTokenResponse, UserRole, Permission,
    UserStatus, Role, UserPreferences, AuditLog, DEFAULT_ROLES
)

from .service import AuthService, auth_service
from .api import auth_router

__all__ = [
    # Models
    "User", "UserCreate", "UserUpdate", "UserPasswordChange", "UserSession",
    "LoginRequest", "LoginResponse", "RefreshTokenResponse", "UserRole", "Permission",
    "UserStatus", "Role", "UserPreferences", "AuditLog", "DEFAULT_ROLES",
    
    # Services
    "AuthService", "auth_service",
    
    # API
    "auth_router"
]
