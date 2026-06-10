from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable


SOURCE_MARKER_RE = re.compile(r"\[(PMID:\d+|FDA:[^\]]+|NCT\d{8,}|EMA:[^\]]+)\]")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def build_traceability_payload(
    evidence_package: Any,
    *,
    section_name: str,
) -> dict[str, Any]:
    source_markers = collect_source_markers(evidence_package)
    section_markers = markers_for_section(section_name, source_markers)
    return {
        "source_markers": section_markers,
        "retrieved_at": _retrieved_at_text(evidence_package),
    }


def collect_source_markers(evidence_package: Any) -> dict[str, list[str]]:
    sources = _get_sources(evidence_package)
    markers: dict[str, list[str]] = {
        "pubmed": [],
        "fda": [],
        "ema": [],
        "clinicaltrials": [],
    }

    for record in sources.get("pubmed", []) or []:
        marker = _clean_marker(f"PMID:{_record_value(record, 'identifier') or _record_value(record, 'pmid')}")
        if marker and marker not in markers["pubmed"]:
            markers["pubmed"].append(marker)

    for record in sources.get("fda", []) or []:
        identifier = _record_value(record, "identifier") or _record_value(record, "title") or "label"
        sections = _fda_sections(record)
        section_text = ",".join(sections) if sections else "label"
        marker = _clean_marker(f"FDA:{identifier}|section={section_text}")
        if marker not in markers["fda"]:
            markers["fda"].append(marker)

    for record in sources.get("ema", []) or []:
        identifier = _record_value(record, "identifier") or _record_value(record, "title") or "ema"
        marker = _clean_marker(f"EMA:{identifier}")
        if marker not in markers["ema"]:
            markers["ema"].append(marker)

    for record in sources.get("clinicaltrials", []) or []:
        identifier = _record_value(record, "identifier") or _record_value(record, "nct_id")
        if identifier:
            marker = _clean_marker(f"NCT{str(identifier).replace('NCT', '')}")
            if marker not in markers["clinicaltrials"]:
                markers["clinicaltrials"].append(marker)

    return markers


def markers_for_section(section_name: str, source_markers: dict[str, list[str]]) -> list[str]:
    section = (section_name or "").strip().lower()
    if section in {"clinical_efficacy"}:
        sources = ("pubmed", "clinicaltrials", "fda", "ema")
    elif section in {"pharmacology", "pharmacokinetics"}:
        sources = ("pubmed", "fda", "ema")
    elif section in {"safety", "dosage", "contraindications", "drug_interactions"}:
        sources = ("fda", "pubmed", "ema", "clinicaltrials")
    elif section in {"introduction", "rationale"}:
        sources = ("pubmed", "fda", "ema")
    else:
        sources = ("pubmed", "fda", "ema", "clinicaltrials")

    markers: list[str] = []
    for source in sources:
        markers.extend(source_markers.get(source, []))
    return _dedupe(markers)


def annotate_section_with_traceability(
    content: str,
    source_markers: Iterable[str],
) -> tuple[str, list[dict[str, Any]]]:
    markers = [marker for marker in source_markers if marker]
    if not content.strip() or not markers:
        return content, []

    retrievable_marker_text = "[" + "; ".join(markers) + "]"
    rows: list[dict[str, Any]] = []
    annotated_blocks: list[str] = []
    for block in _split_blocks(content):
        stripped = block.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            annotated_blocks.append(stripped)
            continue

        if _contains_marker(stripped):
            annotated_blocks.append(stripped)
            rows.extend(_rows_from_block(stripped))
            continue

        if stripped.startswith("- "):
            annotated_lines = []
            for line in stripped.splitlines():
                if line.startswith("- ") and not _contains_marker(line):
                    claim = line[2:].strip()
                    if claim:
                        annotated_sentence, line_rows = _annotate_sentence_text(claim, markers)
                        line = f"- {annotated_sentence}"
                        rows.extend(line_rows)
                annotated_lines.append(line)
            annotated_blocks.append("\n".join(annotated_lines))
            continue

        if _looks_scientific(stripped):
            annotated, sentence_rows = _annotate_sentence_text(stripped, markers)
            annotated_blocks.append(annotated)
            rows.extend(sentence_rows)
        else:
            annotated_blocks.append(stripped)

    return "\n\n".join(annotated_blocks), rows


def build_traceability_appendix(rows: list[dict[str, Any]], retrieved_at: str) -> str:
    lines = [
        "This appendix links evidence-backed claims to retrieved sources and retrieval timing.",
        "",
        "Claim | Source | Database | Retrieval date",
        "--- | --- | --- | ---",
    ]
    if not rows:
        lines.extend(
            [
                "No source-mapped claims were available for this draft. | None | None | " + retrieved_at,
                "",
                "This appendix is required to link each scientific statement to retrieved evidence. If it is empty, the monograph should not be released.",
            ]
        )
        return "\n".join(lines)

    for row in rows:
        claim = _sanitize_table_cell(str(row.get("claim", "")))
        source = _sanitize_table_cell(str(row.get("source", "")))
        database = _sanitize_table_cell(str(row.get("database", "")))
        row_date = _sanitize_table_cell(str(row.get("retrieval_date", retrieved_at)))
        lines.append(f"{claim} | {source} | {database} | {row_date}")
    return "\n".join(lines)


def build_source_mapping_rows(
    sections: dict[str, str],
    evidence_package: Any,
) -> list[dict[str, Any]]:
    traceability_markers = collect_source_markers(evidence_package)
    retrieved_at = _retrieved_at_text(evidence_package)
    rows: list[dict[str, Any]] = []

    for section_name, content in sections.items():
        if section_name in {"references", "evidence_traceability_appendix"}:
            continue
        section_markers = markers_for_section(section_name, traceability_markers)
        if not section_markers:
            continue
        _, section_rows = annotate_section_with_traceability(content, section_markers)
        for row in section_rows:
            row["section"] = section_name
            row["retrieval_date"] = retrieved_at
            rows.append(row)
    return rows


def apply_section_traceability(
    sections: dict[str, str],
    evidence_package: Any,
) -> tuple[dict[str, str], list[dict[str, Any]], str]:
    traceability_markers = collect_source_markers(evidence_package)
    retrieved_at = _retrieved_at_text(evidence_package)
    annotated_sections: dict[str, str] = {}
    rows: list[dict[str, Any]] = []

    for section_name, content in sections.items():
        if section_name in {"references", "evidence_traceability_appendix"}:
            annotated_sections[section_name] = content
            continue
        section_markers = markers_for_section(section_name, traceability_markers)
        annotated_content, section_rows = annotate_section_with_traceability(content, section_markers)
        annotated_sections[section_name] = annotated_content
        for row in section_rows:
            row["section"] = section_name
            row["retrieval_date"] = retrieved_at
            rows.append(row)

    return annotated_sections, rows, retrieved_at


def _rows_from_block(block: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sentence in _split_sentences(block):
        if not sentence.strip():
            continue
        if _contains_marker(sentence):
            markers = _extract_markers(sentence)
            claim = _strip_markers(sentence)
            rows.append(_make_row(claim, markers))
    return rows


def _annotate_sentence_text(text: str, markers: list[str]) -> tuple[str, list[dict[str, Any]]]:
    bundle = "[" + "; ".join(markers) + "]"
    sentences = _split_sentences(text) or [text]
    annotated_sentences: list[str] = []
    rows: list[dict[str, Any]] = []
    for sentence in sentences:
        if _looks_scientific(sentence) and not _contains_marker(sentence):
            annotated_sentence = f"{sentence.rstrip()} {bundle}"
            annotated_sentences.append(annotated_sentence)
            rows.append(_make_row(sentence, markers))
        else:
            annotated_sentences.append(sentence)
            if _contains_marker(sentence):
                rows.append(_make_row(_strip_markers(sentence), _extract_markers(sentence)))
    return " ".join(annotated_sentences).strip(), rows


def _make_row(claim: str, markers: list[str]) -> dict[str, Any]:
    databases = sorted({ _marker_database(marker) for marker in markers })
    return {
        "claim": _strip_markers(claim).strip(),
        "source": "; ".join(markers),
        "database": "; ".join(database for database in databases if database),
    }


def _marker_database(marker: str) -> str:
    if marker.startswith("PMID:"):
        return "PubMed"
    if marker.startswith("FDA:"):
        return "FDA"
    if marker.startswith("NCT"):
        return "ClinicalTrials.gov"
    if marker.startswith("EMA:"):
        return "EMA"
    return "Unknown"


def _strip_markers(text: str) -> str:
    return SOURCE_MARKER_RE.sub("", text).replace("[]", "").strip()


def _extract_markers(text: str) -> list[str]:
    return [match.group(1) for match in SOURCE_MARKER_RE.finditer(text)]


def _contains_marker(text: str) -> bool:
    return bool(SOURCE_MARKER_RE.search(text))


def _looks_scientific(text: str) -> bool:
    lowered = text.lower()
    if any(term in lowered for term in (
        "trial",
        "study",
        "evidence",
        "efficacy",
        "safety",
        "dose",
        "dosage",
        "contraindication",
        "interaction",
        "pharmac",
        "fracture",
        "glyc",
        "pain",
        "renal",
        "hepatic",
        "calcium",
        "bioavailability",
        "randomized",
        "meta-analysis",
        "confidence",
        "adverse",
    )):
        return True
    if bool(re.search(r"\d", text)):
        return True
    return len(text.split()) >= 4


def _split_blocks(text: str) -> list[str]:
    return [block for block in re.split(r"\n\s*\n", text or "") if block.strip()]


def _split_sentences(text: str) -> list[str]:
    return [piece.strip() for piece in SENTENCE_SPLIT_RE.split(text or "") if piece.strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _retrieve_at_value(evidence_package: Any) -> Any:
    return getattr(evidence_package, "retrieved_at", None) if not isinstance(evidence_package, dict) else evidence_package.get("retrieved_at")


def _retrieved_at_text(evidence_package: Any) -> str:
    value = _retrieve_at_value(evidence_package)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")


def _get_sources(evidence_package: Any) -> dict[str, list[Any]]:
    if isinstance(evidence_package, dict):
        return evidence_package.get("sources", {}) or {}
    return getattr(evidence_package, "sources", {}) or {}


def _record_value(record: Any, field: str) -> str:
    if isinstance(record, dict):
        value = record.get(field)
    else:
        value = getattr(record, field, None)
    if isinstance(value, list):
        for item in value:
            if item:
                return str(item).strip()
        return ""
    return str(value).strip() if value else ""


def _fda_sections(record: Any) -> list[str]:
    if isinstance(record, dict):
        metadata = record.get("metadata", {}) or {}
        sections = metadata.get("sections", [])
        return [str(item).strip() for item in sections if str(item).strip()]
    metadata = getattr(record, "metadata", {}) or {}
    sections = metadata.get("sections", [])
    return [str(item).strip() for item in sections if str(item).strip()]


def _clean_marker(marker: str) -> str:
    return marker.replace("  ", " ").strip()


def _sanitize_table_cell(value: str) -> str:
    return value.replace("|", "/").replace("\n", " ").strip()
