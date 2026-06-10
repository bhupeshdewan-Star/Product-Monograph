from __future__ import annotations

import csv
import io
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from .normalizer import build_evidence_context, build_vancouver_references
from .schemas import EvidencePackage, EvidenceRecord, EvidenceSourceResult

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx", ".html", ".htm"}


def collect_local_evidence(
    uploaded_files: Iterable[Any] | None = None,
    folder_paths: Iterable[str] | None = None,
    *,
    include_full_paths: bool = False,
    max_files: int = 25,
) -> tuple[EvidenceSourceResult, dict[str, Any]]:
    records: list[EvidenceRecord] = []
    errors: list[str] = []
    details: list[dict[str, Any]] = []
    seen_files = 0
    total_words = 0

    for item in _iter_local_inputs(uploaded_files, folder_paths, max_files=max_files):
        seen_files += 1
        try:
            text, extraction_details = _extract_local_text(item)
            words = _word_count(text)
            total_words += words
            display_name = item["name"]
            safe_path = item["display_path"]
            metadata = {
                "source_type": "local",
                "source_name": display_name,
                "source_path": safe_path,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "full_source_path": item.get("full_path", "") if include_full_paths else "",
                "file_type": item["suffix"].lstrip("."),
                "word_count": words,
                "extraction_details": extraction_details,
                "included_chunks": _chunk_text(text),
            }
            record = EvidenceRecord(
                source="local",
                source_type="local",
                source_name=display_name,
                source_path=safe_path,
                retrieved_at=metadata["retrieved_at"],
                title=display_name,
                abstract=_summarize_text(text),
                year=str(datetime.now(timezone.utc).year),
                summary=_summarize_text(text, max_words=120),
                metadata=metadata,
            )
            records.append(record)
            details.append(
                {
                    "source_name": display_name,
                    "source_path": safe_path,
                    "full_source_path": item.get("full_path", "") if include_full_paths else "",
                    "word_count": words,
                    "extraction_details": extraction_details,
                    "included_chunks": metadata["included_chunks"],
                }
            )
        except Exception as exc:
            errors.append(f"{item['name']}: {exc}")
            details.append(
                {
                    "source_name": item["name"],
                    "source_path": item["display_path"],
                    "full_source_path": item.get("full_path", "") if include_full_paths else "",
                    "error": str(exc),
                }
            )

    if records:
        status = "found"
    elif errors:
        status = "failed"
    else:
        status = "empty"

    result = EvidenceSourceResult(
        source="local",
        status=status,
        count=len(records),
        records=records,
        error="; ".join(errors[:5]),
    )
    summary = {
        "files_loaded": len(records),
        "file_names": [record.source_name or record.title for record in records],
        "word_count": total_words,
        "source_errors": errors,
        "extraction_details": details,
        "include_full_paths": include_full_paths,
    }
    return result, summary


def merge_local_evidence_package(
    package: EvidencePackage,
    local_result: EvidenceSourceResult,
    local_summary: dict[str, Any],
    *,
    include_local_evidence_in_references: bool = True,
) -> EvidencePackage:
    merged = EvidencePackage.model_validate(package.model_dump())
    merged.sources = dict(merged.sources or {})
    merged.sources["local"] = list(local_result.records)
    merged.source_status = dict(merged.source_status or {})
    merged.source_status["local"] = local_result
    merged.summary.local_count = len(local_result.records)
    merged.summary.total_records += len(local_result.records)
    merged.limitations = list(merged.limitations or [])
    if local_result.error:
        merged.source_errors = list(merged.source_errors or []) + [f"LOCAL: {local_result.error}"]
        if not local_result.records:
            merged.limitations.append("Local evidence could not be loaded.")
    merged.retrieved_with = dict(merged.retrieved_with or {})
    merged.retrieved_with["include_local_evidence_in_references"] = include_local_evidence_in_references
    merged.retrieved_with["local_vault_summary"] = local_summary
    merged.evidence_context = build_evidence_context(merged)
    merged.evidence_references = build_vancouver_references(merged)
    return merged


def _iter_local_inputs(
    uploaded_files: Iterable[Any] | None,
    folder_paths: Iterable[str] | None,
    *,
    max_files: int,
):
    yielded = 0
    for uploaded in uploaded_files or []:
        if yielded >= max_files:
            break
        name = getattr(uploaded, "name", "uploaded-file")
        suffix = Path(name).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue
        yielded += 1
        yield {
            "name": name,
            "suffix": suffix,
            "bytes": uploaded.getvalue(),
            "display_path": name,
            "full_path": "",
            "origin": "upload",
        }

    for folder in folder_paths or []:
        if yielded >= max_files:
            break
        folder = folder.strip()
        if not folder:
            continue
        root = Path(folder)
        if not root.exists() or not root.is_dir():
            yield {
                "name": root.name or folder,
                "suffix": "",
                "bytes": b"",
                "display_path": root.name or folder,
                "full_path": str(root),
                "origin": "folder_error",
                "error": "Folder not found or not accessible.",
            }
            continue
        for path in sorted(root.rglob("*")):
            if yielded >= max_files:
                break
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                continue
            yielded += 1
            yield {
                "name": path.name,
                "suffix": suffix,
                "bytes": path.read_bytes(),
                "display_path": path.name,
                "full_path": str(path.resolve()),
                "origin": "folder",
            }


def _extract_local_text(item: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    suffix = item["suffix"]
    raw = item.get("bytes", b"")
    if item.get("origin") == "folder_error":
        raise RuntimeError(item.get("error", "Folder unavailable."))
    if suffix in {".txt", ".md"}:
        text = raw.decode("utf-8", errors="ignore")
        return text, {"parser": suffix.lstrip("."), "bytes": len(raw)}
    if suffix == ".csv":
        text = _extract_csv_text(raw)
        return text, {"parser": "csv", "bytes": len(raw)}
    if suffix in {".html", ".htm"}:
        text = _extract_html_text(raw)
        return text, {"parser": "html", "bytes": len(raw)}
    if suffix == ".docx":
        text = _extract_docx_text(raw)
        return text, {"parser": "docx", "bytes": len(raw)}
    if suffix == ".xlsx":
        text = _extract_xlsx_text(raw)
        return text, {"parser": "xlsx", "bytes": len(raw)}
    if suffix == ".pdf":
        text = _extract_pdf_text(raw)
        return text, {"parser": "pdf", "bytes": len(raw)}
    raise RuntimeError(f"Unsupported file type: {suffix}")


def _extract_pdf_text(data: bytes) -> str:
    text = data.decode("latin-1", errors="ignore")
    streams = re.findall(r"stream\s*(.*?)\s*endstream", text, flags=re.S | re.I)
    extracted: list[str] = []
    for stream in streams or [text]:
        extracted.extend(re.findall(r"\((?:\\.|[^()])*\)\s*Tj", stream, flags=re.S))
        for array in re.findall(r"\[(.*?)\]\s*TJ", stream, flags=re.S):
            extracted.extend(re.findall(r"\((?:\\.|[^()])*\)", array, flags=re.S))
    if not extracted:
        extracted = re.findall(r"\(([^()]{2,})\)", text)
    clean = [_unescape_pdf_string(item) for item in extracted]
    return _normalize_text("\n".join(clean))


def _extract_docx_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for para in root.findall(".//w:p", namespace):
        text_bits = [node.text or "" for node in para.findall(".//w:t", namespace)]
        paragraph = "".join(text_bits).strip()
        if paragraph:
            paragraphs.append(paragraph)
    return _normalize_text("\n".join(paragraphs))


def _extract_csv_text(data: bytes) -> str:
    text = data.decode("utf-8", errors="ignore")
    rows = list(csv.reader(io.StringIO(text)))
    return _normalize_text("\n".join(", ".join(row) for row in rows if any(cell.strip() for cell in row)))


def _extract_html_text(data: bytes) -> str:
    soup = BeautifulSoup(data, "html.parser")
    return _normalize_text(soup.get_text(" ", strip=True))


def _extract_xlsx_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        shared_strings = _read_xlsx_shared_strings(zf)
        sheet_names = [name for name in zf.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")]
        rows: list[str] = []
        for sheet_name in sorted(sheet_names):
            xml = ET.fromstring(zf.read(sheet_name))
            namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for row in xml.findall(".//x:row", namespace):
                values: list[str] = []
                for cell in row.findall("x:c", namespace):
                    cell_type = cell.attrib.get("t", "")
                    value_node = cell.find("x:v", namespace)
                    if value_node is None:
                        continue
                    raw_value = value_node.text or ""
                    if cell_type == "s":
                        try:
                            values.append(shared_strings[int(raw_value)])
                        except (ValueError, IndexError):
                            values.append(raw_value)
                    else:
                        values.append(raw_value)
                if values:
                    rows.append(", ".join(values))
        return _normalize_text("\n".join(rows))


def _read_xlsx_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        xml = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values: list[str] = []
    for node in xml.findall(".//x:si", namespace):
        text_bits = [part.text or "" for part in node.findall(".//x:t", namespace)]
        values.append("".join(text_bits))
    return values


def _unescape_pdf_string(value: str) -> str:
    value = value.strip()
    if value.startswith("(") and value.endswith(")"):
        value = value[1:-1]
    value = value.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
    return value


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _word_count(text: str) -> int:
    return len([word for word in re.split(r"\s+", text or "") if word.strip()])


def _summarize_text(text: str, max_words: int = 60) -> str:
    words = [word for word in re.split(r"\s+", text or "") if word.strip()]
    return " ".join(words[:max_words])


def _chunk_text(text: str, chunk_size: int = 180) -> list[dict[str, Any]]:
    words = [word for word in re.split(r"\s+", text or "") if word.strip()]
    chunks: list[dict[str, Any]] = []
    for index in range(0, len(words), chunk_size):
        slice_words = words[index : index + chunk_size]
        if not slice_words:
            continue
        chunks.append(
            {
                "chunk_index": len(chunks) + 1,
                "word_count": len(slice_words),
                "text": " ".join(slice_words[:120]),
            }
        )
    return chunks
