from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# Models
class WorkspaceCreate(BaseModel):
    name: str
    team: str
    description: Optional[str] = None

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    team: Optional[str] = None
    description: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: str
    name: str
    team: str
    description: Optional[str] = None
    members: int
    projects: int
    created_at: datetime
    updated_at: datetime

# In-memory storage (replace with database in production)
workspaces_db = [
    {
        "id": "1",
        "name": "Data Science Lab",
        "team": "Data Science",
        "description": "Advanced analytics and ML research workspace",
        "members": 8,
        "projects": 12,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": "2",
        "name": "Engineering Hub",
        "team": "Engineering",
        "description": "Software development and infrastructure workspace",
        "members": 15,
        "projects": 24,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": "3",
        "name": "Analytics Center",
        "team": "Analytics",
        "description": "Business intelligence and reporting workspace",
        "members": 6,
        "projects": 8,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])

@router.get("/", response_model=List[WorkspaceResponse])
async def get_workspaces():
    """Get all workspaces"""
    return workspaces_db

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str):
    """Get a specific workspace by ID"""
    for workspace in workspaces_db:
        if workspace["id"] == workspace_id:
            return workspace
    raise HTTPException(status_code=404, detail="Workspace not found")

@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(workspace: WorkspaceCreate):
    """Create a new workspace"""
    new_workspace = {
        "id": str(uuid.uuid4()),
        "name": workspace.name,
        "team": workspace.team,
        "description": workspace.description,
        "members": 1,  # Creator is first member
        "projects": 0,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    workspaces_db.append(new_workspace)
    return new_workspace

@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(workspace_id: str, workspace_update: WorkspaceUpdate):
    """Update an existing workspace"""
    for i, workspace in enumerate(workspaces_db):
        if workspace["id"] == workspace_id:
            # Update only provided fields
            if workspace_update.name is not None:
                workspace["name"] = workspace_update.name
            if workspace_update.team is not None:
                workspace["team"] = workspace_update.team
            if workspace_update.description is not None:
                workspace["description"] = workspace_update.description
            
            workspace["updated_at"] = datetime.now()
            workspaces_db[i] = workspace
            return workspace
    
    raise HTTPException(status_code=404, detail="Workspace not found")

@router.delete("/{workspace_id}")
async def delete_workspace(workspace_id: str):
    """Delete a workspace"""
    for i, workspace in enumerate(workspaces_db):
        if workspace["id"] == workspace_id:
            deleted_workspace = workspaces_db.pop(i)
            return {"message": f"Workspace '{deleted_workspace['name']}' deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Workspace not found")

@router.post("/{workspace_id}/members")
async def add_member(workspace_id: str, member_email: str):
    """Add a member to a workspace"""
    for workspace in workspaces_db:
        if workspace["id"] == workspace_id:
            workspace["members"] += 1
            workspace["updated_at"] = datetime.now()
            return {"message": f"Member {member_email} added to workspace {workspace['name']}"}
    
    raise HTTPException(status_code=404, detail="Workspace not found")

@router.delete("/{workspace_id}/members/{member_email}")
async def remove_member(workspace_id: str, member_email: str):
    """Remove a member from a workspace"""
    for workspace in workspaces_db:
        if workspace["id"] == workspace_id:
            if workspace["members"] > 1:  # Keep at least one member
                workspace["members"] -= 1
                workspace["updated_at"] = datetime.now()
                return {"message": f"Member {member_email} removed from workspace {workspace['name']}"}
            else:
                raise HTTPException(status_code=400, detail="Cannot remove last member from workspace")
    
    raise HTTPException(status_code=404, detail="Workspace not found")
