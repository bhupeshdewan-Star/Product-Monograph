from __future__ import annotations

import json
import re
from typing import Any, Iterable, List

SEVERITY_WEIGHTS = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
}


def slugify(value: str, default: str = "schema") -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or default


def truncate_text(value: str, limit: int = 12000) -> str:
    if not value:
        return ""
    return value[:limit]


def extract_json_object(text: str) -> Any:
    if not text:
        raise ValueError("Empty model response")

    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()

    try:
        return json.loads(stripped)
    except Exception:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start : end + 1]
        return json.loads(candidate)

    raise ValueError("Model response did not contain valid JSON")


def count_by_severity(issues: Iterable[dict]) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for issue in issues:
        severity = str(issue.get("severity", "low")).lower()
        if severity in counts:
            counts[severity] += 1
    return counts


def score_from_issues(issues: List[dict], start: int = 100) -> int:
    score = start
    for issue in issues:
        severity = str(issue.get("severity", "low")).lower()
        score -= SEVERITY_WEIGHTS.get(severity, 3)
    return max(0, min(100, score))


def merge_unique_issues(*issue_groups: Iterable[dict]) -> list[dict]:
    seen = set()
    merged: list[dict] = []
    for group in issue_groups:
        for issue in group:
            key = (
                str(issue.get("title", "")).strip().lower(),
                str(issue.get("target", "")).strip().lower(),
                str(issue.get("severity", "low")).strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(issue)
    return merged

