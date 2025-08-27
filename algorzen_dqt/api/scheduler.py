from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import croniter

# Models
class ScheduledTaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    frequency: str  # 'daily', 'weekly', 'monthly'
    time: str  # HH:MM format
    day: str  # day of week for weekly, day of month for monthly
    workspace: str
    project: str

class ScheduledTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    time: Optional[str] = None
    day: Optional[str] = None
    workspace: Optional[str] = None
    project: Optional[str] = None
    status: Optional[str] = None

class ScheduledTaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    frequency: str
    time: str
    day: str
    status: str
    last_run: Optional[str] = None
    next_run: str
    workspace: str
    project: str
    created_at: datetime
    updated_at: datetime

# In-memory storage (replace with database in production)
scheduled_tasks_db = [
    {
        "id": "1",
        "name": "Daily Quality Check",
        "description": "Automated daily data quality validation",
        "frequency": "daily",
        "time": "09:00",
        "day": "monday",
        "status": "active",
        "last_run": "2024-01-15 09:00",
        "next_run": "2024-01-16 09:00",
        "workspace": "Data Science Lab",
        "project": "Customer Data Quality Pipeline",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": "2",
        "name": "Weekly Report Generation",
        "description": "Generate weekly data quality reports",
        "frequency": "weekly",
        "time": "08:00",
        "day": "monday",
        "status": "active",
        "last_run": "2024-01-15 08:00",
        "next_run": "2024-01-22 08:00",
        "workspace": "Analytics Center",
        "project": "Sales Analytics Dashboard",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": "3",
        "name": "Monthly Data Cleanup",
        "description": "Monthly data archiving and cleanup",
        "frequency": "monthly",
        "time": "06:00",
        "day": "1st",
        "status": "paused",
        "last_run": "2024-01-01 06:00",
        "next_run": "2024-02-01 06:00",
        "workspace": "Engineering Hub",
        "project": "ML Model Training Pipeline",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])

def calculate_next_run(frequency: str, time: str, day: str) -> str:
    """Calculate the next run time based on frequency, time, and day"""
    now = datetime.now()
    hour, minute = map(int, time.split(':'))
    
    if frequency == "daily":
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
    
    elif frequency == "weekly":
        days = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        target_day = days.get(day.lower(), 0)
        current_day = now.weekday()
        days_ahead = (target_day - current_day) % 7
        if days_ahead == 0 and now.time() >= datetime.strptime(time, '%H:%M').time():
            days_ahead = 7
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
    
    elif frequency == "monthly":
        try:
            day_num = int(day.replace('st', '').replace('nd', '').replace('rd', '').replace('th', ''))
            next_run = now.replace(day=day_num, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
        except ValueError:
            next_run = now + timedelta(days=1)
    
    else:
        next_run = now + timedelta(days=1)
    
    return next_run.strftime("%Y-%m-%d %H:%M")

@router.get("/", response_model=List[ScheduledTaskResponse])
async def get_scheduled_tasks():
    """Get all scheduled tasks"""
    return scheduled_tasks_db

@router.get("/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(task_id: str):
    """Get a specific scheduled task by ID"""
    for task in scheduled_tasks_db:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Scheduled task not found")

@router.post("/", response_model=ScheduledTaskResponse)
async def create_scheduled_task(task: ScheduledTaskCreate):
    """Create a new scheduled task"""
    next_run = calculate_next_run(task.frequency, task.time, task.day)
    
    new_task = {
        "id": str(uuid.uuid4()),
        "name": task.name,
        "description": task.description,
        "frequency": task.frequency,
        "time": task.time,
        "day": task.day,
        "status": "active",
        "last_run": None,
        "next_run": next_run,
        "workspace": task.workspace,
        "project": task.project,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    scheduled_tasks_db.append(new_task)
    return new_task

@router.put("/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(task_id: str, task_update: ScheduledTaskUpdate):
    """Update an existing scheduled task"""
    for i, task in enumerate(scheduled_tasks_db):
        if task["id"] == task_id:
            # Update only provided fields
            if task_update.name is not None:
                task["name"] = task_update.name
            if task_update.description is not None:
                task["description"] = task_update.description
            if task_update.frequency is not None:
                task["frequency"] = task_update.frequency
            if task_update.time is not None:
                task["time"] = task_update.time
            if task_update.day is not None:
                task["day"] = task_update.day
            if task_update.workspace is not None:
                task["workspace"] = task_update.workspace
            if task_update.project is not None:
                task["project"] = task_update.project
            if task_update.status is not None:
                task["status"] = task_update.status
            
            # Recalculate next run if frequency, time, or day changed
            if any([task_update.frequency, task_update.time, task_update.day]):
                task["next_run"] = calculate_next_run(
                    task["frequency"], 
                    task["time"], 
                    task["day"]
                )
            
            task["updated_at"] = datetime.now()
            scheduled_tasks_db[i] = task
            return task
    
    raise HTTPException(status_code=404, detail="Scheduled task not found")

@router.delete("/{task_id}")
async def delete_scheduled_task(task_id: str):
    """Delete a scheduled task"""
    for i, task in enumerate(scheduled_tasks_db):
        if task["id"] == task_id:
            deleted_task = scheduled_tasks_db.pop(i)
            return {"message": f"Scheduled task '{deleted_task['name']}' deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Scheduled task not found")

@router.put("/{task_id}/status")
async def toggle_task_status(task_id: str):
    """Toggle scheduled task status (active/paused)"""
    for i, task in enumerate(scheduled_tasks_db):
        if task["id"] == task_id:
            task["status"] = "paused" if task["status"] == "active" else "active"
            task["updated_at"] = datetime.now()
            scheduled_tasks_db[i] = task
            return {"message": f"Task '{task['name']}' status changed to {task['status']}"}
    
    raise HTTPException(status_code=404, detail="Scheduled task not found")

@router.post("/{task_id}/run")
async def run_task_now(task_id: str):
    """Execute a scheduled task immediately"""
    for i, task in enumerate(scheduled_tasks_db):
        if task["id"] == task_id:
            # Update last run and next run
            task["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            task["next_run"] = calculate_next_run(task["frequency"], task["time"], task["day"])
            task["updated_at"] = datetime.now()
            scheduled_tasks_db[i] = task
            
            return {
                "message": f"Task '{task['name']}' executed successfully",
                "last_run": task["last_run"],
                "next_run": task["next_run"]
            }
    
    raise HTTPException(status_code=404, detail="Scheduled task not found")

@router.get("/frequencies", response_model=List[str])
async def get_frequencies():
    """Get available frequencies"""
    return ["daily", "weekly", "monthly"]

@router.get("/statuses", response_model=List[str])
async def get_statuses():
    """Get available statuses"""
    return ["active", "paused"]

@router.get("/upcoming", response_model=List[ScheduledTaskResponse])
async def get_upcoming_tasks(hours: int = 24):
    """Get tasks scheduled to run in the next N hours"""
    now = datetime.now()
    upcoming = []
    
    for task in scheduled_tasks_db:
        if task["status"] == "active":
            try:
                next_run = datetime.strptime(task["next_run"], "%Y-%m-%d %H:%M")
                if next_run <= now + timedelta(hours=hours):
                    upcoming.append(task)
            except ValueError:
                continue
    
    return sorted(upcoming, key=lambda x: x["next_run"])
