"""
Pydantic models for the Compliance Platform API
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PriorityLevel(str, Enum):
    IMMEDIATE = "IMMEDIATE"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ─── Organization Profiling ───────────────────────────────────────────────────

class OrgProfileRequest(BaseModel):
    description: str = Field(
        ...,
        description="3-4 word description of the organization",
        example="Indian healthcare SaaS startup"
    )
    website: Optional[str] = Field(None, description="Organization website URL")
    country: Optional[str] = Field(None, description="Primary country of operation")
    employee_count: Optional[str] = Field(None, description="Employee range e.g. '50-200'")
    revenue: Optional[str] = Field(None, description="Annual revenue range")


class FrameworkMatch(BaseModel):
    id: str
    name: str
    icon: str
    color: str
    region: str
    description: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    relevance_reason: str
    is_mandatory: bool = False
    max_fine: str
    notification_window: str


class OrgProfileResponse(BaseModel):
    org_description: str
    org_type: str
    industries_detected: List[str]
    regions_detected: List[str]
    recommended_frameworks: List[FrameworkMatch]
    analysis_summary: str
    timestamp: str
    session_id: Optional[int] = None


# ─── Compliance Selection ─────────────────────────────────────────────────────

class ComplianceSelectionRequest(BaseModel):
    org_description: str
    selected_frameworks: List[str] = Field(..., description="List of framework IDs to analyze")
    org_context: Optional[Dict[str, Any]] = None


# ─── Policy Generation ────────────────────────────────────────────────────────

class PolicySection(BaseModel):
    title: str
    content: str
    references: List[str] = []


class GeneratedPolicy(BaseModel):
    policy_id: str
    framework: str
    policy_type: str
    title: str
    version: str = "1.0"
    effective_date: str
    review_date: str
    sections: List[PolicySection]
    applicable_to: str
    owner: str
    classification: str = "Internal"


class PolicyGenerationRequest(BaseModel):
    org_description: str
    org_name: Optional[str] = "Your Organization"
    framework: str = Field(..., description="Framework ID e.g. GDPR, HIPAA")
    policy_types: List[str] = Field(
        default=["data_protection", "incident_response", "access_control"],
        description="Types of policies to generate"
    )
    org_context: Optional[Dict[str, Any]] = None


class PolicyGenerationResponse(BaseModel):
    org_name: str
    framework: str
    policies: List[GeneratedPolicy]
    summary: str
    timestamp: str


# ─── Procedure Generation ─────────────────────────────────────────────────────

class ProcedureStep(BaseModel):
    step_number: int
    title: str
    description: str
    responsible_role: str
    timeline: str
    tools_required: List[str] = []
    documentation: str = ""


class GeneratedProcedure(BaseModel):
    procedure_id: str
    framework: str
    procedure_type: str
    title: str
    purpose: str
    scope: str
    steps: List[ProcedureStep]
    frequency: str
    owner: str
    escalation_path: str


class ProcedureGenerationRequest(BaseModel):
    org_description: str
    org_name: Optional[str] = "Your Organization"
    framework: str
    procedure_types: List[str] = Field(
        default=["incident_response", "data_breach", "access_review"],
        description="Types of procedures to generate"
    )
    org_context: Optional[Dict[str, Any]] = None


class ProcedureGenerationResponse(BaseModel):
    org_name: str
    framework: str
    procedures: List[GeneratedProcedure]
    summary: str
    timestamp: str


# ─── Compliance Violation Analysis (from original code) ──────────────────────

class ComplianceViolation(BaseModel):
    regulation: str
    article_section: str
    violation_description: str
    severity: SeverityLevel


class ComplianceRecommendation(BaseModel):
    action: str
    priority: PriorityLevel
    timeline: str


class ComplianceAnalysis(BaseModel):
    alert_id: str
    compliance_framework: str
    is_compliant: bool
    violations: List[ComplianceViolation] = []
    recommendations: List[ComplianceRecommendation] = []
    risk_assessment: str
    legal_implications: str
    estimated_fine_range: Optional[str] = None
    analysis_timestamp: str


# ─── Conversational Personalization ───────────────────────────────────────────

class ConversationMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ExtractedInfo(BaseModel):
    key: str = Field(..., description="snake_case key (e.g., 'siem_tool', 'ciso_contact')")
    value: str = Field(..., description="Extracted value")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level 0-1")


class PersonalizationChatRequest(BaseModel):
    session_id: int
    user_message: str
    frameworks: List[str] = Field(..., description="Selected frameworks")
    policy_types: List[str] = Field(..., description="Selected policy types")
    procedure_types: List[str] = Field(..., description="Selected procedure types")
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    extracted_info: Dict[str, str] = Field(default_factory=dict, description="Previously extracted info")
    org_context: Dict[str, Any] = Field(default_factory=dict)


class PersonalizationChatResponse(BaseModel):
    extracted_info: List[ExtractedInfo] = Field(description="Newly extracted information from user message")
    accumulated_info: Dict[str, str] = Field(description="All accumulated information so far")
    suggestions: List[str] = Field(description="Context-aware suggestions for user")
    missing_info: List[Dict[str, str]] = Field(description="List of missing important info with prompts")
    assistant_message: str = Field(description="Assistant response to user")
    conversation_history: List[ConversationMessage]
    is_complete: bool = Field(description="Whether we have sufficient info to proceed")


# ─── Status / Health ─────────────────────────────────────────────────────────

class SystemStatus(BaseModel):
    status: str
    groq_keys: int
    groq_models: List[str]
    groq_total_slots: int
    tavily_available: bool
    supported_frameworks: List[str]
    version: str = "1.0.0"
