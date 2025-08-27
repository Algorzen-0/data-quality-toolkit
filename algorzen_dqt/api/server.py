"""
FastAPI server for Algorzen Data Quality Toolkit API endpoints.

This server provides RESTful API endpoints for the React frontend,
including business rules, scheduler, monitoring, workspaces, and projects.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import random

# Import the API routers
from .business_rules import router as business_rules_router
from .scheduler import router as scheduler_router
from .monitoring import router as monitoring_router
from .workspaces import router as workspaces_router
from .projects import router as projects_router

# Create FastAPI app
app = FastAPI(
    title="Algorzen Data Quality Toolkit API",
    description="Enterprise-grade data quality toolkit API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(business_rules_router, tags=["Business Rules"])
app.include_router(scheduler_router, tags=["Scheduler"])
app.include_router(monitoring_router, tags=["Monitoring"])
app.include_router(workspaces_router, tags=["Workspaces"])
app.include_router(projects_router, tags=["Projects"])

@app.get("/")
async def root():
    """Root endpoint - redirects to React frontend."""
    return {
        "message": "Algorzen Data Quality Toolkit API",
        "version": "0.1.0",
        "docs": "/docs",
        "frontend": "Use the React dashboard in the frontend/ directory"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/health")
async def api_health():
    """API health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
