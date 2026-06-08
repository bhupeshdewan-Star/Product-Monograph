from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from config import MEDICAL_DISCLAIMER


class MonographSection(BaseModel):
    title: str
    content: str
    source_count: int = 0
    citations: List[str] = Field(default_factory=list)


class MonographDocument(BaseModel):
    molecule_name: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    total_tokens_used: int = 0
    sections: Dict[str, str] = Field(default_factory=dict)
    validation: Dict[str, Any] = Field(default_factory=dict)
    audit_results: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = MEDICAL_DISCLAIMER


class MonographExportBundle(BaseModel):
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    pdf_path: Optional[str] = None
    word_path: Optional[str] = None
    google_docs_path: Optional[str] = None
