from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

SourceName = Literal["local", "pubmed", "fda", "ema", "clinicaltrials"]
SourceStatus = Literal["searching", "found", "failed", "unavailable", "empty", "cached", "disabled"]


class EvidenceRecord(BaseModel):
    source: str
    source_type: str = ""
    source_name: str = ""
    source_path: str = ""
    retrieved_at: str = ""
    title: str = ""
    abstract: str = ""
    journal: str = ""
    year: str = ""
    identifier: str = ""
    doi: str = ""
    authors: List[str] = Field(default_factory=list)
    url: str = ""
    status: str = ""
    phase: str = ""
    conditions: List[str] = Field(default_factory=list)
    interventions: List[str] = Field(default_factory=list)
    outcomes: List[str] = Field(default_factory=list)
    sponsor: str = ""
    enrollment: str = ""
    start_date: str = ""
    completion_date: str = ""
    indications: str = ""
    warnings: str = ""
    contraindications: str = ""
    dosage: str = ""
    adverse_reactions: str = ""
    pharmacology: str = ""
    summary: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceSourceResult(BaseModel):
    source: SourceName
    status: SourceStatus = "searching"
    count: int = 0
    records: List[EvidenceRecord] = Field(default_factory=list)
    error: str = ""
    elapsed_ms: int = 0
    cached: bool = False
    request_url: str = ""


class EvidenceSummary(BaseModel):
    local_count: int = 0
    total_records: int = 0
    pubmed_count: int = 0
    fda_count: int = 0
    ema_count: int = 0
    clinicaltrials_count: int = 0


class EvidenceRetrievalRequest(BaseModel):
    molecule: str
    max_results: int = 30
    include_pubmed: bool = True
    include_fda: bool = True
    include_ema: bool = True
    include_clinicaltrials: bool = True
    force_refresh: bool = False
    allow_limited_evidence: bool = False


class EvidencePackage(BaseModel):
    molecule: str
    retrieved_at: datetime
    sources: Dict[str, List[EvidenceRecord]] = Field(default_factory=dict)
    summary: EvidenceSummary = Field(default_factory=EvidenceSummary)
    limitations: List[str] = Field(default_factory=list)
    source_errors: List[str] = Field(default_factory=list)
    source_status: Dict[str, EvidenceSourceResult] = Field(default_factory=dict)
    cache_status: Dict[str, Any] = Field(default_factory=dict)
    evidence_context: str = ""
    evidence_references: str = ""
    retrieved_with: Dict[str, Any] = Field(default_factory=dict)
