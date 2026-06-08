from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class AIProviderRequest(BaseModel):
    provider: str = Field(..., description="LLM provider name")
    model: str = Field(..., description="Model identifier")
    api_key: Optional[str] = Field(default=None, description="Runtime API key")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    base_url: Optional[str] = Field(default=None, description="Optional provider base URL")


class A11yCheckRequest(BaseModel):
    url: str
    ai_provider: Optional[AIProviderRequest] = None


class Issue(BaseModel):
    id: str
    title: str
    severity: str
    category: str
    description: str
    impact: str
    evidence: List[str] = Field(default_factory=list)
    recommended_fixes: List[str] = Field(default_factory=list)
    wcag_references: List[str] = Field(default_factory=list)
    target: Optional[str] = None


class Summary(BaseModel):
    human_readable: str
    score: int
    issue_counts: dict


class A11yCheckResponse(BaseModel):
    success: bool = True
    audit_type: str = "accessibility"
    url: str
    final_url: Optional[str] = None
    score: int
    summary: Summary
    issues: List[Issue]
    recommendations: List[str]
    coverage_notes: List[str] = Field(default_factory=list)
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    raw_snapshot: Optional[dict] = None

