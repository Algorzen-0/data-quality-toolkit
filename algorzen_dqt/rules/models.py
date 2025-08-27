"""
Custom Business Rules Models for the Algorzen Data Quality Toolkit.

This module defines the data models for:
- Custom business rules
- Data validation rules
- Compliance requirements
- Rule execution and results
"""

from typing import List, Optional, Dict, Any, Union, Callable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid
import re


class RuleType(str, Enum):
    """Types of business rules."""
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    CALCULATION = "calculation"
    COMPLIANCE = "compliance"
    BUSINESS_LOGIC = "business_logic"
    CUSTOM_FUNCTION = "custom_function"


class RuleSeverity(str, Enum):
    """Rule severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RuleStatus(str, Enum):
    """Rule status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class DataType(str, Enum):
    """Supported data types for rule validation."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    CUSTOM = "custom"


class Operator(str, Enum):
    """Comparison operators for rule conditions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_EQUAL = "greater_equal"
    LESS_THAN = "less_than"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCH = "regex_match"
    REGEX_NOT_MATCH = "regex_not_match"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"


class RuleCondition(BaseModel):
    """Rule condition model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    field_name: str
    operator: Operator
    value: Any
    value_type: DataType = DataType.STRING
    case_sensitive: bool = True
    custom_regex: Optional[str] = None
    
    @validator('custom_regex')
    def validate_regex(cls, v):
        if v and operator in [Operator.REGEX_MATCH, Operator.REGEX_NOT_MATCH]:
            try:
                re.compile(v)
                return v
            except re.error:
                raise ValueError('Invalid regex pattern')
        return v


class RuleAction(BaseModel):
    """Rule action model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str  # log, alert, transform, reject, etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    
    class Config:
        schema_extra = {
            "example": {
                "action_type": "alert",
                "parameters": {"severity": "warning", "message": "Data quality issue detected"},
                "description": "Send alert notification"
            }
        }


class BusinessRuleBase(BaseModel):
    """Base business rule model."""
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., max_length=500)
    rule_type: RuleType = RuleType.VALIDATION
    severity: RuleSeverity = RuleSeverity.WARNING
    status: RuleStatus = RuleStatus.ACTIVE
    workspace_id: str
    dataset_id: Optional[str] = None
    column_name: Optional[str] = None
    conditions: List[RuleCondition] = Field(default_factory=list)
    actions: List[RuleAction] = Field(default_factory=list)
    priority: int = 1
    tags: List[str] = Field(default_factory=list)
    
    @validator('priority')
    def validate_priority(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Priority must be between 1 and 10')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return [tag.lower().strip() for tag in v if tag.strip()]


class BusinessRuleCreate(BusinessRuleBase):
    """Model for creating a new business rule."""
    pass


class BusinessRuleUpdate(BaseModel):
    """Model for updating business rule information."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rule_type: Optional[RuleType] = None
    severity: Optional[RuleSeverity] = None
    status: Optional[RuleStatus] = None
    conditions: Optional[List[RuleCondition]] = None
    actions: Optional[List[RuleAction]] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None


class BusinessRule(BusinessRuleBase):
    """Complete business rule model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_executed: Optional[datetime] = None
    average_execution_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Email Format Validation",
                "description": "Validate email addresses follow proper format",
                "rule_type": "validation",
                "severity": "error",
                "execution_count": 150,
                "success_count": 145,
                "failure_count": 5
            }
        }


class RuleExecution(BaseModel):
    """Rule execution record model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    workspace_id: str
    dataset_id: Optional[str] = None
    execution_id: str  # Links to data quality check execution
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, skipped
    duration_seconds: float = 0.0
    rows_processed: int = 0
    rows_passed: int = 0
    rows_failed: int = 0
    rows_skipped: int = 0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "rule_id": "rule-123",
                "execution_id": "exec-456",
                "rows_processed": 1000,
                "rows_passed": 950,
                "rows_failed": 50
            }
        }
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.rows_processed == 0:
            return 0.0
        return (self.rows_passed / self.rows_processed) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.rows_processed == 0:
            return 0.0
        return (self.rows_failed / self.rows_processed) * 100


class RuleViolation(BaseModel):
    """Rule violation record model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    execution_id: str
    row_index: int
    column_name: str
    value: Any
    expected_value: Optional[Any] = None
    violation_type: str
    message: str
    severity: RuleSeverity
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "rule_id": "rule-123",
                "row_index": 42,
                "column_name": "email",
                "value": "invalid-email",
                "violation_type": "format_violation",
                "message": "Invalid email format",
                "severity": "error"
            }
        }


class ComplianceRule(BusinessRule):
    """Compliance-specific business rule."""
    compliance_standard: str  # GDPR, HIPAA, SOX, etc.
    regulation_reference: str
    required_action: str
    audit_trail_required: bool = True
    reporting_frequency: str = "immediate"  # immediate, daily, weekly, monthly
    responsible_party: str
    review_frequency: str = "quarterly"
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "compliance_standard": "GDPR",
                "regulation_reference": "Article 17 - Right to erasure",
                "required_action": "Delete personal data upon request",
                "audit_trail_required": True
            }
        }


class DataTransformationRule(BusinessRule):
    """Data transformation rule."""
    transformation_type: str  # format, calculate, derive, clean, etc.
    source_columns: List[str] = Field(default_factory=list)
    target_column: str
    transformation_logic: str  # Python expression or function name
    validation_rules: List[str] = Field(default_factory=list)
    rollback_enabled: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "transformation_type": "format",
                "source_columns": ["first_name", "last_name"],
                "target_column": "full_name",
                "transformation_logic": "f'{first_name} {last_name}'.title()"
            }
        }


class RuleTemplate(BaseModel):
    """Predefined rule template."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str
    rule_type: RuleType
    template_code: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Email Format Validation",
                "category": "Data Format",
                "rule_type": "validation",
                "template_code": "email_validation",
                "parameters": [
                    {"name": "column_name", "type": "string", "required": True}
                ]
            }
        }


class RuleEngineConfig(BaseModel):
    """Rule engine configuration."""
    max_execution_time: int = 300  # seconds
    max_memory_mb: int = 512
    parallel_execution: bool = True
    max_parallel_rules: int = 5
    caching_enabled: bool = True
    cache_ttl_seconds: int = 3600
    logging_level: str = "INFO"
    performance_monitoring: bool = True
    rule_validation: bool = True
    sandbox_mode: bool = False  # For testing rules safely


class RuleExecutionSummary(BaseModel):
    """Summary of rule execution results."""
    total_rules: int
    executed_rules: int
    passed_rules: int
    failed_rules: int
    skipped_rules: int
    total_violations: int
    critical_violations: int
    error_violations: int
    warning_violations: int
    info_violations: int
    execution_time: float
    success_rate: float
    compliance_score: float
    recommendations: List[str] = Field(default_factory=list)
