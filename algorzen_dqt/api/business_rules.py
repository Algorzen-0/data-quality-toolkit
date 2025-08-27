from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime
import uuid
import re

# Models
class RuleCondition(BaseModel):
    field: str
    operator: str
    value: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    threshold: Optional[float] = None
    severity: str = "error"

class BusinessRuleCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    conditions: RuleCondition

class BusinessRuleUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[RuleCondition] = None
    status: Optional[str] = None

class BusinessRuleResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    status: str
    conditions: RuleCondition
    created_at: datetime
    updated_at: datetime
    applied_count: int = 0

# In-memory storage (replace with database in production)
business_rules_db = [
    {
        "id": "1",
        "name": "Email Format Validation",
        "type": "data_validation",
        "description": "Ensures email addresses follow proper format",
        "status": "active",
        "conditions": {
            "field": "email",
            "operator": "regex",
            "value": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            "severity": "error"
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "applied_count": 1247
    },
    {
        "id": "2",
        "name": "Age Range Check",
        "type": "business_logic",
        "description": "Age must be between 18 and 100",
        "status": "active",
        "conditions": {
            "field": "age",
            "operator": "range",
            "min_value": 18,
            "max_value": 100,
            "severity": "warning"
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "applied_count": 892
    },
    {
        "id": "3",
        "name": "Data Completeness",
        "type": "quality_threshold",
        "description": "Required fields must be 95% complete",
        "status": "active",
        "conditions": {
            "field": "required_fields",
            "operator": "completeness",
            "threshold": 0.95,
            "severity": "error"
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "applied_count": 2156
    }
]

router = APIRouter(prefix="/api/business-rules", tags=["business-rules"])

@router.get("/", response_model=List[BusinessRuleResponse])
async def get_business_rules():
    """Get all business rules"""
    return business_rules_db

@router.get("/{rule_id}", response_model=BusinessRuleResponse)
async def get_business_rule(rule_id: str):
    """Get a specific business rule by ID"""
    for rule in business_rules_db:
        if rule["id"] == rule_id:
            return rule
    raise HTTPException(status_code=404, detail="Business rule not found")

@router.post("/", response_model=BusinessRuleResponse)
async def create_business_rule(rule: BusinessRuleCreate):
    """Create a new business rule"""
    new_rule = {
        "id": str(uuid.uuid4()),
        "name": rule.name,
        "type": rule.type,
        "description": rule.description,
        "status": "active",
        "conditions": rule.conditions.dict(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "applied_count": 0
    }
    business_rules_db.append(new_rule)
    return new_rule

@router.put("/{rule_id}", response_model=BusinessRuleResponse)
async def update_business_rule(rule_id: str, rule_update: BusinessRuleUpdate):
    """Update an existing business rule"""
    for i, rule in enumerate(business_rules_db):
        if rule["id"] == rule_id:
            # Update only provided fields
            if rule_update.name is not None:
                rule["name"] = rule_update.name
            if rule_update.type is not None:
                rule["type"] = rule_update.type
            if rule_update.description is not None:
                rule["description"] = rule_update.description
            if rule_update.conditions is not None:
                rule["conditions"] = rule_update.conditions.dict()
            if rule_update.status is not None:
                rule["status"] = rule_update.status
            
            rule["updated_at"] = datetime.now()
            business_rules_db[i] = rule
            return rule
    
    raise HTTPException(status_code=404, detail="Business rule not found")

@router.delete("/{rule_id}")
async def delete_business_rule(rule_id: str):
    """Delete a business rule"""
    for i, rule in enumerate(business_rules_db):
        if rule["id"] == rule_id:
            deleted_rule = business_rules_db.pop(i)
            return {"message": f"Business rule '{deleted_rule['name']}' deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Business rule not found")

@router.put("/{rule_id}/status")
async def toggle_rule_status(rule_id: str):
    """Toggle business rule status (active/paused)"""
    for i, rule in enumerate(business_rules_db):
        if rule["id"] == rule_id:
            rule["status"] = "paused" if rule["status"] == "active" else "active"
            rule["updated_at"] = datetime.now()
            business_rules_db[i] = rule
            return {"message": f"Rule '{rule['name']}' status changed to {rule['status']}"}
    
    raise HTTPException(status_code=404, detail="Business rule not found")

@router.post("/{rule_id}/test")
async def test_business_rule(rule_id: str, test_data: dict):
    """Test a business rule with sample data"""
    for rule in business_rules_db:
        if rule["id"] == rule_id:
            conditions = rule["conditions"]
            field = conditions["field"]
            operator = conditions["operator"]
            
            if field not in test_data:
                return {
                    "rule_id": rule_id,
                    "rule_name": rule["name"],
                    "test_result": "failed",
                    "message": f"Field '{field}' not found in test data",
                    "severity": conditions["severity"]
                }
            
            field_value = test_data[field]
            
            # Apply the rule based on operator
            if operator == "regex":
                try:
                    pattern = re.compile(conditions["value"])
                    is_valid = bool(pattern.match(str(field_value)))
                except re.error:
                    return {
                        "rule_id": rule_id,
                        "rule_name": rule["name"],
                        "test_result": "error",
                        "message": "Invalid regular expression pattern",
                        "severity": "error"
                    }
            
            elif operator == "range":
                try:
                    numeric_value = float(field_value)
                    min_val = conditions.get("min_value")
                    max_val = conditions.get("max_value")
                    is_valid = True
                    if min_val is not None:
                        is_valid = is_valid and numeric_value >= min_val
                    if max_val is not None:
                        is_valid = is_valid and numeric_value <= max_val
                except (ValueError, TypeError):
                    is_valid = False
            
            elif operator == "completeness":
                threshold = conditions.get("threshold", 0.95)
                if isinstance(field_value, (list, dict)):
                    completeness = len([v for v in field_value.values() if v is not None and v != ""]) / len(field_value)
                else:
                    completeness = 1.0 if field_value is not None and field_value != "" else 0.0
                is_valid = completeness >= threshold
            
            else:
                is_valid = True  # Default to valid for unknown operators
            
            # Update applied count
            rule["applied_count"] += 1
            
            return {
                "rule_id": rule_id,
                "rule_name": rule["name"],
                "test_result": "passed" if is_valid else "failed",
                "message": f"Field '{field}' validation {'passed' if is_valid else 'failed'}",
                "severity": conditions["severity"],
                "field_value": field_value,
                "operator": operator
            }
    
    raise HTTPException(status_code=404, detail="Business rule not found")

@router.get("/types", response_model=List[str])
async def get_rule_types():
    """Get available rule types"""
    return ["data_validation", "business_logic", "quality_threshold"]

@router.get("/operators", response_model=List[str])
async def get_operators():
    """Get available operators"""
    return ["regex", "range", "completeness", "equals", "not_equals", "contains", "not_contains"]

@router.get("/severities", response_model=List[str])
async def get_severities():
    """Get available severity levels"""
    return ["error", "warning", "info"]
