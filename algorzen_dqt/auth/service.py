"""
Authentication Service for the Algorzen Data Quality Toolkit.

This module provides:
- User authentication and authorization
- JWT token management
- Password hashing and verification
- User session management
- Role-based access control
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import hashlib
import secrets

from .models import (
    User, UserCreate, UserUpdate, UserPasswordChange, UserSession,
    LoginRequest, LoginResponse, RefreshTokenResponse, UserRole, Permission,
    DEFAULT_ROLES, UserStatus, AuditLog
)
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-here-change-in-production"  # Change in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()


class AuthService:
    """Authentication and authorization service."""
    
    def __init__(self):
        """Initialize the auth service."""
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, UserSession] = {}
        self.roles: Dict[str, Dict[str, List[Permission]]] = {}
        self.audit_logs: List[AuditLog] = []
        
        # Initialize default roles
        self._initialize_default_roles()
        
        # Create default admin user
        self._create_default_admin()
    
    def _initialize_default_roles(self):
        """Initialize default system roles."""
        for role_name, permissions in DEFAULT_ROLES.items():
            self.roles[role_name.value] = {
                "permissions": permissions,
                "description": f"Default {role_name.value} role"
            }
    
    def _create_default_admin(self):
        """Create default admin user."""
        admin_user = User(
            username="admin",
            email="admin@algorzen.com",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            hashed_password=self._hash_password("admin"),  # Change in production!
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.users[admin_user.id] = admin_user
        logger.info("Default admin user created")
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def _create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def _create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token."""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def _verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        try:
            # Find user by username
            user = None
            for u in self.users.values():
                if u.username == username:
                    user = u
                    break
            
            if not user:
                return None
            
            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is temporarily locked due to failed login attempts"
                )
            
            # Check if account is active
            if user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is not active"
                )
            
            # Verify password
            if not self._verify_password(password, user.hashed_password):
                # Increment failed login attempts
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                    logger.warning(f"Account locked for user: {username}")
                
                return None
            
            # Reset failed login attempts on successful login
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def login(self, login_data: LoginRequest, ip_address: str = None, user_agent: str = None) -> LoginResponse:
        """Authenticate user and create session."""
        try:
            # Authenticate user
            user = await self.authenticate_user(login_data.username, login_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password"
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self._create_access_token(
                data={"sub": user.id, "username": user.username, "role": user.role.value},
                expires_delta=access_token_expires
            )
            
            # Create refresh token
            refresh_token = self._create_refresh_token(user.id)
            
            # Create session
            session = UserSession(
                user_id=user.id,
                token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.sessions[session.id] = session
            
            # Get user permissions
            permissions = self.roles.get(user.role.value, {}).get("permissions", [])
            
            # Log successful login
            self._log_audit_event(
                user_id=user.id,
                username=user.username,
                action="login",
                resource_type="auth",
                success=True,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"User logged in successfully: {user.username}")
            
            return LoginResponse(
                access_token=access_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=user,
                permissions=permissions
            )
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise
    
    async def refresh_token(self, refresh_token: str) -> RefreshTokenResponse:
        """Refresh an access token using a refresh token."""
        try:
            # Verify refresh token
            payload = self._verify_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Check if session exists and is active
            session = None
            for s in self.sessions.values():
                if s.token == refresh_token and s.user_id == user_id and s.is_active:
                    session = s
                    break
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            
            # Check if session is expired
            if session.is_expired:
                session.is_active = False
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token expired"
                )
            
            # Update session activity
            session.last_activity = datetime.utcnow()
            
            # Create new access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self._create_access_token(
                data={"sub": user_id, "username": session.username, "role": session.role},
                expires_delta=access_token_expires
            )
            
            return RefreshTokenResponse(
                access_token=access_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise
    
    async def logout(self, user_id: str, token: str) -> bool:
        """Logout user and invalidate session."""
        try:
            # Find and deactivate session
            for session_id, session in self.sessions.items():
                if session.user_id == user_id and session.token == token:
                    session.is_active = False
                    
                    # Log logout event
                    self._log_audit_event(
                        user_id=user_id,
                        action="logout",
                        resource_type="auth",
                        success=True
                    )
                    
                    logger.info(f"User logged out: {user_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current authenticated user from token."""
        try:
            token = credentials.credentials
            payload = self._verify_token(token)
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            user = self.users.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is not active"
                )
            
            return user
            
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            raise
    
    def check_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        try:
            user_permissions = self.roles.get(user.role.value, {}).get("permissions", [])
            return permission in user_permissions
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
    
    async def require_permission(self, user: User, permission: Permission):
        """Require a specific permission or raise HTTP exception."""
        if not self.check_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
    
    async def create_user(self, user_data: UserCreate, created_by: User) -> User:
        """Create a new user."""
        try:
            # Check permissions
            await self.require_permission(created_by, Permission.CREATE_USERS)
            
            # Check if username already exists
            for user in self.users.values():
                if user.username == user_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already exists"
                    )
                
                if user.email == user_data.email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists"
                    )
            
            # Create new user
            new_user = User(
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                role=user_data.role,
                hashed_password=self._hash_password(user_data.password),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.users[new_user.id] = new_user
            
            # Log user creation
            self._log_audit_event(
                user_id=created_by.id,
                username=created_by.username,
                action="create_user",
                resource_type="user",
                resource_id=new_user.id,
                details={"new_username": new_user.username, "new_role": new_user.role.value},
                success=True
            )
            
            logger.info(f"User created: {new_user.username} by {created_by.username}")
            return new_user
            
        except Exception as e:
            logger.error(f"Create user error: {e}")
            raise
    
    async def update_user(self, user_id: str, user_data: UserUpdate, updated_by: User) -> User:
        """Update an existing user."""
        try:
            # Check permissions
            await self.require_permission(updated_by, Permission.MODIFY_USERS)
            
            user = self.users.get(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Update user fields
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            
            # Log user update
            self._log_audit_event(
                user_id=updated_by.id,
                username=updated_by.username,
                action="update_user",
                resource_type="user",
                resource_id=user_id,
                details=update_data,
                success=True
            )
            
            logger.info(f"User updated: {user.username} by {updated_by.username}")
            return user
            
        except Exception as e:
            logger.error(f"Update user error: {e}")
            raise
    
    async def change_password(self, user: User, password_data: UserPasswordChange) -> bool:
        """Change user password."""
        try:
            # Verify current password
            if not self._verify_password(password_data.current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Update password
            user.hashed_password = self._hash_password(password_data.new_password)
            user.updated_at = datetime.utcnow()
            
            # Log password change
            self._log_audit_event(
                user_id=user.id,
                username=user.username,
                action="change_password",
                resource_type="user",
                success=True
            )
            
            logger.info(f"Password changed for user: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Change password error: {e}")
            raise
    
    def _log_audit_event(self, **kwargs):
        """Log an audit event."""
        try:
            audit_log = AuditLog(**kwargs)
            self.audit_logs.append(audit_log)
            
            # Keep only last 1000 audit logs in memory
            if len(self.audit_logs) > 1000:
                self.audit_logs = self.audit_logs[-1000:]
                
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    async def get_audit_logs(self, user: User, limit: int = 100) -> List[AuditLog]:
        """Get audit logs (admin only)."""
        try:
            await self.require_permission(user, Permission.ACCESS_LOGS)
            return self.audit_logs[-limit:]
        except Exception as e:
            logger.error(f"Get audit logs error: {e}")
            raise


# Global auth service instance
auth_service = AuthService()
