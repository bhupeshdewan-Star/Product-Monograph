from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from ..a11y.schemas import AIProviderRequest


class AuditBuildRequest(BaseModel):
    checklist_url: str
    ai_provider: Optional[AIProviderRequest] = None


class AuditRunRequest(BaseModel):
    target_url: str
    audit_schema_id: str
    ai_provider: Optional[AIProviderRequest] = None


class AuditBuildAndRunRequest(BaseModel):
    checklist_url: str
    target_url: str
    ai_provider: Optional[AIProviderRequest] = None


class AuditIssue(BaseModel):
    id: str
    title: str
    severity: str
    category: str
    description: str
    impact: str
    evidence: List[str] = Field(default_factory=list)
    recommended_fixes: List[str] = Field(default_factory=list)
    target: Optional[str] = None
    criterion_id: Optional[str] = None


class AuditCriterion(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    weight: int = 5
    category: str = "general"
    check_type: str = "llm"
    keywords: List[str] = Field(default_factory=list)
    evidence_hints: List[str] = Field(default_factory=list)
    remediation_hints: List[str] = Field(default_factory=list)


class AuditSchema(BaseModel):
    schema_id: str
    audit_type: str
    name: str
    source_url: str
    source_title: str
    version: str = "1.0"
    criteria: List[AuditCriterion]
    scoring: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class AuditSummary(BaseModel):
    human_readable: str
    score: int
    issue_counts: dict


class AuditResponse(BaseModel):
    success: bool = True
    audit_type: str
    schema_id: str
    source_url: str
    target_url: str
    score: int
    summary: AuditSummary
    issues: List[AuditIssue]
    recommendations: List[str]
    coverage_notes: List[str] = Field(default_factory=list)
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    audit_schema: Optional[AuditSchema] = None
    generated_schema_path: Optional[str] = None
