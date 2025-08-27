"""
Authentication API endpoints for the Algorzen Data Quality Toolkit.

This module provides REST API endpoints for:
- User authentication (login/logout)
- Token management (refresh, validate)
- User management (CRUD operations)
- Password management
- Audit logging
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse

from .models import (
    LoginRequest, LoginResponse, RefreshTokenResponse, UserCreate, UserUpdate,
    UserPasswordChange, User, UserRole, Permission, AuditLog
)
from .service import auth_service
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Create router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request):
    """Authenticate user and return access token."""
    try:
        # Get client IP and user agent
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Perform login
        response = await auth_service.login(login_data, client_ip, user_agent)
        
        logger.info(f"User login successful: {login_data.username}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@auth_router.post("/logout")
async def logout(request: Request, current_user: User = Depends(auth_service.get_current_user)):
    """Logout user and invalidate session."""
    try:
        # Get authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        # Perform logout
        success = await auth_service.logout(current_user.id, token)
        
        if success:
            logger.info(f"User logout successful: {current_user.username}")
            return {"message": "Logout successful"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Logout failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )


@auth_router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(refresh_data: dict):
    """Refresh access token using refresh token."""
    try:
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Refresh token
        response = await auth_service.refresh_token(refresh_token)
        
        logger.info("Token refresh successful")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )


@auth_router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(auth_service.get_current_user)):
    """Get current user information."""
    try:
        return current_user
    except Exception as e:
        logger.error(f"Get current user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.get("/permissions", response_model=List[Permission])
async def get_user_permissions(current_user: User = Depends(auth_service.get_current_user)):
    """Get current user permissions."""
    try:
        from .service import auth_service
        permissions = auth_service.roles.get(current_user.role.value, {}).get("permissions", [])
        return permissions
    except Exception as e:
        logger.error(f"Get user permissions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Create a new user (admin only)."""
    try:
        new_user = await auth_service.create_user(user_data, current_user)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user creation"
        )


@auth_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(auth_service.get_current_user)):
    """Get all users (admin only)."""
    try:
        # Check permissions
        await auth_service.require_permission(current_user, Permission.VIEW_USERS)
        
        # Return all users (excluding password hashes)
        users = []
        for user in auth_service.users.values():
            user_dict = user.dict()
            user_dict.pop("hashed_password", None)
            users.append(User(**user_dict))
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get user by ID (admin only)."""
    try:
        # Check permissions
        await auth_service.require_permission(current_user, Permission.VIEW_USERS)
        
        user = auth_service.users.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return user without password hash
        user_dict = user.dict()
        user_dict.pop("hashed_password", None)
        return User(**user_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Update user (admin only)."""
    try:
        updated_user = await auth_service.update_user(user_id, user_data, current_user)
        
        # Return user without password hash
        user_dict = updated_user.dict()
        user_dict.pop("hashed_password", None)
        return User(**user_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user update"
        )


@auth_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Delete user (admin only)."""
    try:
        # Check permissions
        await auth_service.require_permission(current_user, Permission.DELETE_USERS)
        
        # Check if trying to delete self
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Check if user exists
        user = auth_service.users.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete user
        del auth_service.users[user_id]
        
        # Log deletion
        auth_service._log_audit_event(
            user_id=current_user.id,
            username=current_user.username,
            action="delete_user",
            resource_type="user",
            resource_id=user_id,
            details={"deleted_username": user.username},
            success=True
        )
        
        logger.info(f"User deleted: {user.username} by {current_user.username}")
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user deletion"
        )


@auth_router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Change current user password."""
    try:
        success = await auth_service.change_password(current_user, password_data)
        
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during password change"
        )


@auth_router.get("/roles", response_model=List[dict])
async def get_roles(current_user: User = Depends(auth_service.get_current_user)):
    """Get available roles and their permissions."""
    try:
        roles = []
        for role_name, role_info in auth_service.roles.items():
            roles.append({
                "name": role_name,
                "description": role_info.get("description", ""),
                "permissions": [p.value for p in role_info.get("permissions", [])]
            })
        
        return roles
        
    except Exception as e:
        logger.error(f"Get roles error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get audit logs (admin only)."""
    try:
        logs = await auth_service.get_audit_logs(current_user, limit)
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audit logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.get("/health")
async def health_check():
    """Health check endpoint for authentication service."""
    try:
        return {
            "status": "healthy",
            "service": "authentication",
            "timestamp": auth_service.users.get("admin") is not None
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service unhealthy"
        )
